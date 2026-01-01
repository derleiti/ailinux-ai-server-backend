"""
Hub-seitige Endpoints für Federation Management
Verwaltet Node-Registrierung, Heartbeats und Routing
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
import logging
import secrets
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/federation", tags=["federation"])


# ============== Models ==============

class NodeRegistration(BaseModel):
    node_id: str
    role: str  # ollama_worker, api_proxy, contributor, backup
    host: str
    port: int = 9000
    models: List[str] = []
    max_concurrent: int = 10


class NodeHeartbeat(BaseModel):
    node_id: str
    status: str = "healthy"
    current_load: int = 0
    metrics: Dict = {}


class CompletionReport(BaseModel):
    node_id: str
    request_id: str
    metrics: Dict = {}


# ============== In-Memory Storage ==============
# In Production: Redis oder PostgreSQL verwenden

class NodeRegistry:
    """Zentrale Node-Verwaltung"""
    
    def __init__(self):
        self.nodes: Dict[str, dict] = {}
        self.health: Dict[str, datetime] = {}
        self.tokens: Dict[str, str] = {}  # node_id -> token
    
    def register(self, node: NodeRegistration) -> str:
        """Registriert einen Node und gibt Token zurück"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        self.nodes[node.node_id] = {
            "role": node.role,
            "host": node.host,
            "port": node.port,
            "models": node.models,
            "max_concurrent": node.max_concurrent,
            "registered_at": datetime.now().isoformat(),
            "status": "healthy",
            "current_load": 0,
            "metrics": {}
        }
        
        self.health[node.node_id] = datetime.now()
        self.tokens[node.node_id] = token_hash
        
        logger.info(f"Node registered: {node.node_id} ({node.role})")
        return token
    
    def heartbeat(self, hb: NodeHeartbeat) -> bool:
        """Aktualisiert Node-Status"""
        if hb.node_id not in self.nodes:
            return False
        
        self.health[hb.node_id] = datetime.now()
        self.nodes[hb.node_id].update({
            "status": hb.status,
            "current_load": hb.current_load,
            "last_heartbeat": datetime.now().isoformat(),
            "metrics": hb.metrics
        })
        return True
    
    def get_status(self, node_id: str) -> str:
        """Berechnet aktuellen Status basierend auf Heartbeat"""
        if node_id not in self.nodes:
            return "unknown"
        
        last_seen = self.health.get(node_id, datetime.min)
        age = (datetime.now() - last_seen).total_seconds()
        
        if age > 90:
            return "offline"
        elif age > 60:
            return "degraded"
        else:
            return self.nodes[node_id].get("status", "unknown")
    
    def get_all_nodes(self) -> List[dict]:
        """Gibt alle Nodes mit aktuellem Status zurück"""
        result = []
        now = datetime.now()
        
        for node_id, info in self.nodes.items():
            last_seen = self.health.get(node_id, datetime.min)
            age = (now - last_seen).total_seconds()
            
            result.append({
                "node_id": node_id,
                "status": self.get_status(node_id),
                "last_seen_seconds": int(age),
                **info
            })
        
        return result
    
    def get_candidates_for_model(self, model: str) -> List[dict]:
        """Findet beste Nodes für ein Model"""
        candidates = []
        
        for node_id, info in self.nodes.items():
            status = self.get_status(node_id)
            
            # Nur healthy/degraded Nodes
            if status not in ["healthy", "degraded"]:
                continue
            
            # Model muss vorhanden sein ODER Node ist API Proxy
            if model in info.get("models", []) or info.get("role") == "api_proxy":
                load_percent = info.get("current_load", 0) / max(info.get("max_concurrent", 10), 1)
                
                candidates.append({
                    "node_id": node_id,
                    "host": info.get("host"),
                    "port": info.get("port"),
                    "role": info.get("role"),
                    "status": status,
                    "load_percent": load_percent,
                    "score": (1.0 - load_percent) * (1.0 if status == "healthy" else 0.5)
                })
        
        # Sortiere nach Score (höher = besser)
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates
    
    def unregister(self, node_id: str) -> bool:
        """Entfernt einen Node"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.health.pop(node_id, None)
            self.tokens.pop(node_id, None)
            logger.info(f"Node unregistered: {node_id}")
            return True
        return False


# Global Registry Instance
registry = NodeRegistry()


# ============== API Endpoints ==============

@router.post("/register")
async def register_node(payload: NodeRegistration):
    """Node registriert sich beim Hub"""
    
    # Prüfe ob Node bereits existiert
    if payload.node_id in registry.nodes:
        logger.warning(f"Node {payload.node_id} re-registering")
    
    # Registrieren und Token generieren
    token = registry.register(payload)
    
    return {
        "status": "registered",
        "node_token": token,
        "hub_config": {
            "heartbeat_interval": 30,
            "max_failures": 3,
            "endpoints": {
                "heartbeat": "/v1/federation/heartbeat",
                "completion": "/v1/federation/completion",
                "validate": "/v1/internal/validate"
            }
        }
    }


@router.post("/heartbeat")
async def node_heartbeat(payload: NodeHeartbeat):
    """Node sendet Heartbeat"""
    
    if not registry.heartbeat(payload):
        raise HTTPException(404, f"Node {payload.node_id} not registered")
    
    return {
        "status": "ok",
        "next_heartbeat": 30,
        "server_time": datetime.now().isoformat()
    }


@router.post("/completion")
async def report_completion(payload: CompletionReport):
    """Node meldet abgeschlossenen Request"""
    
    # TODO: In Produktion an Usage-Logging-Service weiterleiten
    logger.debug(f"Completion: {payload.node_id} - {payload.request_id}")
    
    return {"status": "logged"}


@router.get("/nodes")
async def list_nodes():
    """Listet alle registrierten Nodes"""
    nodes = registry.get_all_nodes()
    
    # Statistiken
    healthy = sum(1 for n in nodes if n["status"] == "healthy")
    degraded = sum(1 for n in nodes if n["status"] == "degraded")
    offline = sum(1 for n in nodes if n["status"] == "offline")
    
    return {
        "nodes": nodes,
        "total": len(nodes),
        "stats": {
            "healthy": healthy,
            "degraded": degraded,
            "offline": offline
        }
    }


@router.get("/nodes/{node_id}")
async def get_node(node_id: str):
    """Details zu einem Node"""
    if node_id not in registry.nodes:
        raise HTTPException(404, f"Node {node_id} not found")
    
    info = registry.nodes[node_id]
    return {
        "node_id": node_id,
        "status": registry.get_status(node_id),
        **info
    }


@router.delete("/nodes/{node_id}")
async def unregister_node(node_id: str):
    """Entfernt einen Node"""
    if not registry.unregister(node_id):
        raise HTTPException(404, f"Node {node_id} not found")
    
    return {"status": "unregistered", "node_id": node_id}


@router.get("/route/{model}")
async def get_route_for_model(model: str, limit: int = 3):
    """Gibt beste Node(s) für ein Model zurück (für dynamisches LB)"""
    
    candidates = registry.get_candidates_for_model(model)
    
    return {
        "model": model,
        "candidates": candidates[:limit],
        "recommended": candidates[0] if candidates else None,
        "total_candidates": len(candidates)
    }


@router.get("/health")
async def federation_health():
    """Health Check für Federation Service"""
    nodes = registry.get_all_nodes()
    healthy = sum(1 for n in nodes if n["status"] == "healthy")
    
    return {
        "status": "ok" if healthy > 0 else "degraded",
        "nodes_total": len(nodes),
        "nodes_healthy": healthy,
        "timestamp": datetime.now().isoformat()
    }
