# TriForce System Architecture

## Überblick

TriForce ist eine verteilte Multi-LLM Plattform mit folgenden Hauptkomponenten:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL ACCESS                                │
│                                                                          │
│    Internet → Cloudflare → Apache Proxy → TriForce Backend              │
│              (DDoS/WAF)    (SSL/Auth)     (FastAPI)                      │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         TRIFORCE BACKEND v2.80                           │
│                                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   Routes   │  │  Services  │  │    MCP     │  │   Agents   │        │
│  │ (FastAPI)  │  │ (Business) │  │  (Tools)   │  │  (Multi)   │        │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘        │
│                                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   Redis    │  │   Memory   │  │ Federation │  │  Mesh AI   │        │
│  │  (Cache)   │  │  (Prisma)  │  │  (P2P)     │  │  (Coord)   │        │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          LLM PROVIDERS                                   │
│                                                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Gemini  │ │Anthropic│ │  Groq   │ │Cerebras │ │ Mistral │           │
│  │  (15)   │ │   (5)   │ │  (12)   │ │   (4)   │ │   (8)   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │OpenRout │ │ GitHub  │ │Cloudfl. │ │ Ollama  │  = 640+ Models        │
│  │  (200)  │ │  (10)   │ │  (15)   │ │  (∞)    │                       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Kernkomponenten

### 1. API Gateway (Apache + FastAPI)

**Verantwortlich für:**
- SSL-Terminierung
- Rate Limiting
- Authentication (JWT/Basic)
- Request Routing

**Ports:**
- 443 (HTTPS) → Apache Proxy
- 9000 (intern) → FastAPI Backend
- 9100 (extern) → X-Forwarded-Port Auth

### 2. Backend Services

| Service | Funktion |
|---------|----------|
| `chat_router` | LLM-Anfragen verteilen |
| `model_registry` | Modell-Verfügbarkeit |
| `tier_manager` | Berechtigungen prüfen |
| `rate_limiter` | Token-Limits |
| `mesh_coordinator` | Multi-Agent Tasks |

### 3. MCP System

134 Tools in Kategorien:
- Core (15): Basis-Funktionen
- Code (12): File-Operations
- Memory (8): Wissen speichern
- Mesh (10): Federation
- Ollama (6): Lokale Modelle
- Agents (8): Multi-Agent
- Admin (12): System

### 4. Federation Mesh

3 Nodes über WireGuard VPN:
- Master (Hetzner): Koordination
- Hub (Backup): Compute
- Hub (Zombie-PC): GPU

---

## Datenfluss

### Chat Request

```
1. Client → HTTPS Request
2. Apache → SSL + Auth
3. FastAPI → Rate Check
4. Router → Provider Select
5. Provider → LLM Call
6. Response → Stream/JSON
7. Client ← Response
```

### MCP Tool Call

```
1. Client → MCP Request
2. Backend → Tool Lookup
3. Handler → Execute
4. Result → Format
5. Client ← Response
```

### Federation Request

```
1. Node A → Sign Request (PSK)
2. WireGuard → Encrypt
3. Node B → Validate Signature
4. Execute → Process
5. Node B → Response
6. Node A ← Result
```

---

## Verzeichnisstruktur

```
triforce/
├── app/
│   ├── main.py              # FastAPI Entry
│   ├── config.py            # Konfiguration
│   ├── routes/              # API Endpoints
│   │   ├── mcp.py           # MCP Handler (149k)
│   │   ├── mesh.py          # Mesh/Federation
│   │   ├── client_*.py      # Client APIs
│   │   └── ...
│   ├── services/            # Business Logic
│   │   ├── chat_router.py
│   │   ├── mesh_coordinator.py
│   │   └── ...
│   ├── mcp/                 # MCP Tools
│   │   └── tool_registry_v4.py
│   └── utils/
├── config/
│   ├── triforce.env         # Environment
│   ├── federation_nodes.json
│   └── users.json
├── client-deploy/           # Client Builds
│   ├── ailinux-client/
│   └── aiwindows-client/
├── docs/                    # Dokumentation
└── scripts/                 # Install/Deploy
```

---

## Technologie-Stack

| Komponente | Technologie |
|------------|-------------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Cache | Redis |
| Memory | Prisma + SQLite |
| Proxy | Apache 2.4 |
| VPN | WireGuard |
| Container | Docker (optional) |
| Search | SearXNG |
| GPU | Ollama (ROCm/CUDA) |

---

## Skalierung

### Horizontal (mehr Nodes)

- Neue Hubs zur Federation hinzufügen
- Load Balancing automatisch
- Modelle verteilt

### Vertikal (mehr Power)

- RAM für größere Modelle
- GPU für schnellere Inference
- CPU für mehr Parallelität

---

## Security

### Authentication

1. **JWT Tokens** - Für Clients
2. **Basic Auth** - Legacy/Admin
3. **PSK Signatures** - Federation

### Encryption

1. **TLS 1.3** - Externe Verbindungen
2. **WireGuard** - Federation
3. **HMAC-SHA256** - Request Signing

### Access Control

1. **Tier System** - Free/Pro/Unlimited
2. **IP Whitelist** - Federation
3. **Rate Limits** - Per User/Tier

---

## Monitoring

### Endpunkte

| Endpoint | Funktion |
|----------|----------|
| `/health` | System-Status |
| `/v1/mesh/resources` | Federation-Status |
| `/v1/mesh/status` | Mesh-Koordinator |

### Logs

```bash
# Service Logs
journalctl -u triforce.service -f

# Kategorien
logs?category=api|llm|mcp|error|agent
```

---

## Weiterführend

- [Installation](INSTALL.md)
- [API Reference](api/REST.md)
- [MCP Tools](api/MCP.md)
- [Federation](architecture/FEDERATION.md)
