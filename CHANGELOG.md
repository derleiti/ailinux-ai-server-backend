# Changelog

Alle wichtigen Änderungen an TriForce werden hier dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [2.80] - 2024-12-31

### Added
- **mesh_resources API**: Live Federation Hardware-Status
  - GET /v1/mesh/resources mit format=summary|nodes|full
  - MCP Tool mesh_resources hinzugefügt
- **Business Plan v2.0**: Zwei-Produkt-Modell (Hub + Client Lizenzen)
- **Dokumentation komplett überarbeitet**
  - README.md mit Badges und Quick Links
  - INSTALL.md für Server und Client
  - QUICKSTART.md für schnellen Einstieg
  - API-Referenz (REST + MCP)
  - Architecture-Dokumentation

### Changed
- Repository umbenannt: ailinux-ai-server-backend → triforce
- Federation-Konfiguration auf 3 Nodes erweitert (64 Cores, 156GB RAM)
- Backup VPS Upgrade: 28 Cores, 64GB RAM

### Fixed
- mesh_resources Import-Fehler in mcp.py
- MESH_HANDLERS Definition korrigiert

---

## [2.75] - 2024-12-30

### Added
- **Server Federation v1.0**
  - WireGuard VPN Mesh
  - 4-Layer Security (VPN, IP Whitelist, PSK, Timestamp)
  - Multi-Node Load Balancing
- **Mesh Brain v2.0**
  - Gemini als Lead-Agent
  - Parallel/Sequential/Consensus Strategien
  - 3.2x Speedup bei Workflows

### Changed
- Backup VPS als Federation-Node integriert
- zombie-pc mit RX 6800 XT eingebunden

---

## [2.70] - 2024-12-28

### Added
- AILinux Client v4.2.0 "Brumo"
  - JWT Authentication
  - Tier-basierte Modell-Auswahl
  - WebSocket MCP Integration
- AIWindows Client v4.2.0
  - Native Windows Build
  - Installer + Portable Version

### Changed
- Client-Repos als Submodule eingebunden
- Deployment-Skripte aktualisiert

---

## [2.60] - 2024-12-25

### Added
- **MCP Tool Registry v4**
  - 134 Tools implementiert
  - Kategorien: Core, Code, Memory, Mesh, Ollama, Agents
- **Prisma Memory System**
  - 4-Layer Memory (Session, User, Persistent, Shared)
  - 38+ Memory-Einträge

### Changed
- mcp.py auf 149k Zeilen gewachsen
- Ollama-Integration verbessert

---

## [2.50] - 2024-12-20

### Added
- **Multi-Agent System**
  - claude-mcp, codex-mcp, gemini-mcp, opencode-mcp
  - Agent Broadcast mit Strategien
- **Evolve System**
  - Auto-Evolution für Code-Qualität
  - Security/Performance/Quality Focus

### Fixed
- Redis Deprecation Warnings
- JWT Tier-Lookup optimiert

---

## [2.40] - 2024-12-15

### Added
- **Tier System**
  - Free: 10k Tokens/Tag
  - Pro: 250k Tokens/Tag (€17.99)
  - Unlimited: ∞ (€59.99)
- Rate Limiting pro User/Tier

### Changed
- Modell-Routing nach Tier
- Token-Counting für alle Provider

---

## [2.30] - 2024-12-10

### Added
- **OpenAI-kompatible API**
  - /v1/chat/completions
  - /v1/models
  - Streaming Support (SSE)
- 9 Provider integriert
  - Gemini, Anthropic, Groq, Cerebras
  - Mistral, OpenRouter, GitHub, Cloudflare
  - Ollama (lokal)

---

## [2.20] - 2024-12-05

### Added
- **SearXNG Integration**
  - Web-Suche Tool
  - Crawl Tool
- Redis Caching für Responses

### Fixed
- Memory Leaks bei langen Sessions
- Concurrent Request Handling

---

## [2.10] - 2024-12-01

### Added
- **Ollama Integration**
  - Lokale Modelle
  - GPU-Support (CUDA/ROCm)
  - Model Pull/Delete
- ollama_* Tools

---

## [2.00] - 2024-11-25

### Added
- **TriForce Backend v2.0**
  - FastAPI Framework
  - Async Architecture
  - Modular Design
- Erste MCP-Implementierung
- Basic Auth für Admin

---

## [1.x] - 2024-10-xx bis 2024-11-xx

### Legacy
- Erste Versionen (nicht öffentlich dokumentiert)
- Prototype mit Flask
- Einzelner Provider (Gemini)

---

## Roadmap

### Q1 2025
- [ ] Payment Integration (Stripe)
- [ ] Credit System für Federation
- [ ] Client v5.0

### Q2 2025
- [ ] Public Beta Launch
- [ ] 100+ User
- [ ] Mobile App (Android/iOS)

### Q3 2025
- [ ] AILinux 1.0 ISO
- [ ] Enterprise Edition
- [ ] SLA Support

### Q4 2025
- [ ] 1000+ User
- [ ] 50+ Hubs
- [ ] Quantum Computing Integration (experimentell)
