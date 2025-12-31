# Changelog

Alle wichtigen Änderungen am TriForce-Projekt werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [2.80] - 2024-12-31

### Added
- **mesh_resources API**: Live Federation Hardware-Status (`/v1/mesh/resources`)
- **Server Federation v1.0**: 3-Node Mesh mit WireGuard VPN
- **Business Plan v2.0**: Hub/Client Licensing-Modell dokumentiert
- Backup VPS Upgrade: 28 Cores, 64GB RAM (von 12c/31GB)

### Changed
- Repository umbenannt: `ailinux-ai-server-backend` → `triforce`
- Federation Totals: 64 Cores, 156GB RAM, 291+ Modelle
- JWT-Tier-Extraktion optimiert in `client_chat.py`

### Fixed
- Import-Fehler in `mesh.py` durch korrektes Handler-Placement
- Git-Sync für Client-Submodules

---

## [2.70] - 2024-12-30

### Added
- **Mesh Brain v2.0**: Workflow-Orchestrierung mit parallel/sequential/consensus
- **Production Workflow Testing**: 3.2x Speedup (18.5s vs 60s sequential)
- Federation Security: 4-Layer (WireGuard, IP-Whitelist, PSK-HMAC, Timestamp)

### Changed
- Federation von 2 auf 3 Nodes erweitert (zombie-pc hinzugefügt)
- Model-Count auf 643+ erhöht

---

## [2.60] - 2024-12-26

### Added
- **AILinux Client v4.2.0** "Brumo": JWT-Auth, Tier-basierte Modelle, WebSocket MCP
- Client-Deploy Submodule-Struktur
- Signed APT Repository unter repo.ailinux.me

### Changed
- Tier-System verfeinert: Guest, Registered, Pro, Unlimited
- Token-Limits pro Tier dokumentiert

---

## [2.50] - 2024-12-20

### Added
- **MCP Tools**: 134 integrierte Tools
- Prisma Memory System mit 38+ Einträgen
- CLI Agents: claude-mcp, codex-mcp, gemini-mcp, opencode-mcp

### Changed
- Gemini als Lead-Agent für Koordination
- Redis-Deprecation-Warnings behoben

---

## [2.40] - 2024-12-15

### Added
- **Multi-Provider Support**: 9 Provider (Gemini, Anthropic, Groq, Cerebras, Mistral, OpenRouter, GitHub, Cloudflare, Ollama)
- OpenAI-kompatible Chat API (`/v1/chat/completions`)
- Rate Limiting mit Redis

### Changed
- Model-Routing verbessert
- Error-Handling standardisiert

---

## [2.30] - 2024-12-10

### Added
- **Ollama Integration**: Lokale Modelle
- Model-Availability-Tracking
- Automatic Fallback bei Provider-Fehlern

### Fixed
- Token-Counting für verschiedene Modelle
- Streaming-Response-Encoding

---

## [2.20] - 2024-12-05

### Added
- **JWT Authentication**: Secure Token-basierte Auth
- User-Tier-System (Free, Pro, Unlimited)
- Admin-Endpoints für Config-Management

### Changed
- Von Basic Auth auf JWT migriert
- Session-Management optimiert

---

## [2.10] - 2024-11-28

### Added
- **Nginx Reverse Proxy** Konfiguration
- Let's Encrypt SSL Auto-Renewal
- Systemd Service für Production

### Changed
- Port-Struktur: 9000 intern, 443 extern
- Logging verbessert

---

## [2.00] - 2024-11-20

### Added
- **TriForce Backend v2.0**: Kompletter Rewrite
- FastAPI als Framework
- Async/Await durchgängig
- Type Hints überall

### Changed
- Von Flask auf FastAPI migriert
- Projekt-Struktur komplett neu

---

## [1.x] - Legacy

Ältere Versionen vor dem v2.0 Rewrite. Nicht mehr unterstützt.

---

## Roadmap

### Q1 2025
- [ ] Credit-System Backend (Prisma Schema)
- [ ] Hub License Registration
- [ ] 10 Alpha-Tester

### Q2 2025
- [ ] Client v5.0 mit Hub-Discovery
- [ ] Payment Integration (Stripe)
- [ ] 100 Beta-User

### Q3 2025
- [ ] Public Launch
- [ ] Contributor Rewards
- [ ] 500+ User

### Q4 2025
- [ ] Enterprise Edition
- [ ] 1000+ User
- [ ] 50+ Hubs
