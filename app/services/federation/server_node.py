"""
TriForce Server Node - Worker im Load-Balanced Cluster
Kommuniziert mit Load Balancer (upstream) und Hub (downstream)
"""

import asyncio
import aiohttp
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class NodeRole(str, Enum):
    OLLAMA_WORKER = "ollama_worker"      # Lokale LLM Inference
    API_PROXY = "api_proxy"               # Cloud API Weiterleitung
    CONTRIBUTOR = "contributor"           # User-gespendete Ressourcen
    BACKUP = "backup"                     # Hot-Standby
    HUB = "hub"                          # Zentrale Koordination


class NodeStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    STARTING = "starting"


@dataclass
class ServerNode:
    """Repräsentiert einen Server Node im Cluster"""
    
    node_id: str
    role: NodeRole
    host: str
    port: int = 9000
    
    # Hub-Verbindung
    hub_url: str = "https://api.ailinux.me"
    hub_token: Optional[str] = None
    
    # Status
    status: NodeStatus = NodeStatus.STARTING
    last_heartbeat: Optional[datetime] = None
    consecutive_failures: int = 0
    max_failures: int = 3
    
    # Capabilities
    models: List[str] = field(default_factory=list)
    max_concurrent: int = 10
    current_load: int = 0
    
    # Metrics
    requests_total: int = 0
    requests_failed: int = 0
    avg_latency_ms: float = 0.0

    @classmethod
    def from_env(cls) -> "ServerNode":
        """Erstellt Node aus Umgebungsvariablen"""
        return cls(
            node_id=os.getenv("NODE_ID", f"node-{os.getpid()}"),
            role=NodeRole(os.getenv("NODE_ROLE", "ollama_worker")),
            host=os.getenv("NODE_HOST", "0.0.0.0"),
            port=int(os.getenv("NODE_PORT", "9000")),
            hub_url=os.getenv("HUB_URL", "https://api.ailinux.me"),
            hub_token=os.getenv("HUB_TOKEN"),
            max_concurrent=int(os.getenv("MAX_CONCURRENT", "10"))
        )

    async def register_with_hub(self) -> bool:
        """Registriert diesen Node beim Hub"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "node_id": self.node_id,
                    "role": self.role.value,
                    "host": self.host,
                    "port": self.port,
                    "models": self.models,
                    "max_concurrent": self.max_concurrent
                }
                
                headers = {}
                if self.hub_token:
                    headers["Authorization"] = f"Bearer {self.hub_token}"
                
                async with session.post(
                    f"{self.hub_url}/v1/federation/register",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.hub_token = data.get("node_token", self.hub_token)
                        self.status = NodeStatus.HEALTHY
                        logger.info(f"Node {self.node_id} registered with hub")
                        return True
                    else:
                        text = await resp.text()
                        logger.error(f"Registration failed: {resp.status} - {text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to register with hub: {e}")
            return False

    async def send_heartbeat(self) -> bool:
        """Sendet Heartbeat an Hub"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "node_id": self.node_id,
                    "status": self.status.value,
                    "current_load": self.current_load,
                    "metrics": {
                        "requests_total": self.requests_total,
                        "requests_failed": self.requests_failed,
                        "avg_latency_ms": self.avg_latency_ms
                    }
                }
                
                headers = {}
                if self.hub_token:
                    headers["Authorization"] = f"Bearer {self.hub_token}"
                
                async with session.post(
                    f"{self.hub_url}/v1/federation/heartbeat",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        self.last_heartbeat = datetime.now()
                        self.consecutive_failures = 0
                        return True
                    else:
                        self.consecutive_failures += 1
                        return False
                        
        except Exception as e:
            self.consecutive_failures += 1
            logger.warning(f"Heartbeat failed: {e}")
            
            if self.consecutive_failures >= self.max_failures:
                self.status = NodeStatus.DEGRADED
                
            return False

    async def forward_to_hub(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Leitet Request an Hub weiter (für Auth, Rate Limit, etc.)"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.hub_token:
                    headers["Authorization"] = f"Bearer {self.hub_token}"
                    
                async with session.post(
                    f"{self.hub_url}/v1/internal/validate",
                    json=request,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Hub forward failed: {e}")
            return {"error": str(e), "valid": False}

    async def report_completion(self, request_id: str, metrics: Dict[str, Any]):
        """Meldet abgeschlossenen Request an Hub (async, fire-and-forget)"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.hub_token:
                    headers["Authorization"] = f"Bearer {self.hub_token}"
                    
                await session.post(
                    f"{self.hub_url}/v1/federation/completion",
                    json={
                        "node_id": self.node_id,
                        "request_id": request_id,
                        "metrics": metrics
                    },
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                )
        except Exception as e:
            logger.warning(f"Completion report failed: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialisiert Node zu Dictionary"""
        return {
            "node_id": self.node_id,
            "role": self.role.value,
            "host": self.host,
            "port": self.port,
            "status": self.status.value,
            "current_load": self.current_load,
            "max_concurrent": self.max_concurrent,
            "models": self.models,
            "metrics": {
                "requests_total": self.requests_total,
                "requests_failed": self.requests_failed,
                "avg_latency_ms": self.avg_latency_ms
            },
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }


class LoadBalancerClient:
    """Client für Kommunikation mit vorgeschaltetem Load Balancer"""
    
    def __init__(self, node: ServerNode):
        self.node = node
        self.lb_healthy = True
    
    async def health_check_response(self) -> Dict[str, Any]:
        """Antwort für Load Balancer Health Check"""
        return {
            "status": "ok" if self.node.status == NodeStatus.HEALTHY else "degraded",
            "node_id": self.node.node_id,
            "role": self.node.role.value,
            "load": self.node.current_load,
            "max_load": self.node.max_concurrent,
            "models": self.node.models
        }
    
    def can_accept_request(self) -> bool:
        """Prüft ob Node neue Requests annehmen kann"""
        return (
            self.node.status in [NodeStatus.HEALTHY, NodeStatus.DEGRADED] and
            self.node.current_load < self.node.max_concurrent
        )
