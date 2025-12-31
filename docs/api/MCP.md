# TriForce MCP Tools Reference

**134 integrierte Tools** für Code, Search, Files, Memory und mehr.

---

## MCP Protocol

TriForce implementiert das [Model Context Protocol](https://modelcontextprotocol.io) (MCP) von Anthropic.

### Endpoint

```
POST /v1/mcp
GET  /v1/mcp/sse  (SSE Streaming)
```

### Basis-Workflow

```bash
# 1. Initialize
curl -X POST https://api.ailinux.me/v1/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}'

# 2. List Tools
curl -X POST https://api.ailinux.me/v1/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# 3. Call Tool
curl -X POST https://api.ailinux.me/v1/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search","arguments":{"query":"test"}}}'
```

---

## Tool Categories

### 🔍 Search & Web

| Tool | Beschreibung | Parameter |
|------|--------------|-----------|
| `search` | Web-Suche via SearXNG | `query`: Suchbegriff |
| `crawl` | Website crawlen | `url`, `max_pages` |

**Beispiel:**
```json
{
  "name": "search",
  "arguments": {"query": "Python async tutorial"}
}
```

---

### 💻 Code & Files

| Tool | Beschreibung | Parameter |
|------|--------------|-----------|
| `code_read` | Datei lesen | `path` |
| `code_edit` | Datei bearbeiten | `path`, `mode`, `old_text`, `new_text` |
| `code_search` | Code durchsuchen | `query`, `path`, `regex` |
| `code_tree` | Verzeichnisstruktur | `path`, `depth` |
| `code_patch` | Diff anwenden | `diff`, `dry_run` |

**Beispiel - Datei lesen:**
```json
{
  "name": "code_read",
  "arguments": {"path": "app/main.py"}
}
```

**Beispiel - Code bearbeiten:**
```json
{
  "name": "code_edit",
  "arguments": {
    "path": "app/config.py",
    "mode": "replace",
    "old_text": "DEBUG = True",
    "new_text": "DEBUG = False"
  }
}
```

---

### 🧠 Memory & Knowledge

| Tool | Beschreibung | Parameter |
|------|--------------|-----------|
| `memory_store` | Wissen speichern | `content`, `type`, `tags` |
| `memory_search` | Wissen suchen | `query`, `type`, `limit` |
| `memory_clear` | Speicher leeren | `type`, `older_than_days` |

**Typen:** `fact`, `decision`, `code`, `summary`, `todo`

**Beispiel:**
```json
{
  "name": "memory_store",
  "arguments": {
    "content": "User bevorzugt Python für Scripting",
    "type": "fact",
    "tags": ["preferences", "programming"]
  }
}
```

---

### 🤖 Chat & Models

| Tool | Beschreibung | Parameter |
|------|--------------|-----------|
| `chat` | Nachricht an Modell | `message`, `model`, `system_prompt` |
| `models` | Modelle auflisten | - |
| `specialist` | Spezialist-Routing | `task`, `message` |

**Beispiel:**
```json
{
  "name": "chat",
  "arguments": {
    "message": "Erkläre Rekursion",
    "model": "gemini/gemini-2.0-flash"
  }
}
```

---

### 🌐 Mesh & Federation

| Tool | Beschreibung | Parameter |
|------|--------------|-----------|
| `mesh_resources` | Hardware-Status | `format`: summary/nodes/full |
| `mesh_status` | Mesh-Status | - |
| `mesh_task` | Task einreichen | `title`, `description` |
| `mesh_agents` | Agents auflisten | - |

**Beispiel:**
```json
{
  "name": "mesh_resources",
  "arguments": {"format": "nodes"}
}
```

Response:
```json
{
  "status": "healthy",
  "nodes": [
    {"id": "hetzner", "online": true, "cores": 20, "ram_gb": 62},
    {"id": "backup", "online": true, "cores": 28, "ram_gb": 64},
    {"id": "zombie-pc", "online": true, "cores": 16, "ram_gb": 30, "gpu": "RX 6800 XT"}
  ]
}
```

---

### 🖥️ System & Admin

| Tool | Beschreibung | Parameter |
|------|--------------|-----------|
| `shell` | Shell-Befehl (Admin) | `command`, `timeout`, `sudo` |
| `health` | System-Health | - |
| `status` | Voller Status | - |
| `logs` | Logs abrufen | `category`, `level`, `limit` |
| `config` | Config lesen | - |
| `config_set` | Config setzen | `key`, `value` |

⚠️ **Hinweis:** `shell` ist nur für Admins verfügbar.

---

### 🔧 Ollama (Lokal)

| Tool | Beschreibung | Parameter |
|------|--------------|-----------|
| `ollama_list` | Lokale Modelle | - |
| `ollama_run` | Inference lokal | `model`, `prompt`, `system` |
| `ollama_pull` | Modell laden | `model` |
| `ollama_delete` | Modell löschen | `model` |
| `ollama_status` | Ollama-Status | - |

**Beispiel:**
```json
{
  "name": "ollama_run",
  "arguments": {
    "model": "llama3.2:3b",
    "prompt": "Was ist 2+2?"
  }
}
```

---

### 🤝 Multi-Agent

| Tool | Beschreibung | Parameter |
|------|--------------|-----------|
| `agents` | CLI-Agents Status | - |
| `agent_call` | Agent aufrufen | `agent`, `message`, `timeout` |
| `agent_broadcast` | An alle Agents | `message`, `strategy` |
| `bootstrap` | Agents starten | `lead_first` |

**Agents:** `claude`, `codex`, `gemini`, `opencode`

**Beispiel:**
```json
{
  "name": "agent_call",
  "arguments": {
    "agent": "gemini",
    "message": "Analysiere diesen Code: ..."
  }
}
```

---

### 📊 Gemini Specials

| Tool | Beschreibung | Parameter |
|------|--------------|-----------|
| `gemini_research` | Research mit Memory | `query`, `store` |
| `gemini_coordinate` | Multi-LLM Koordination | `task`, `strategy` |
| `gemini_exec` | Python ausführen | `code`, `timeout` |

---

## MCP für Claude Desktop

Konfiguration für `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "triforce": {
      "url": "https://api.ailinux.me/v1/mcp/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Basic em9tYmllOmU5RjhEdUtiSC0="
      }
    }
  }
}
```

---

## MCP für Continue.dev

Konfiguration für `.continue/config.json`:

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "sse",
          "url": "https://api.ailinux.me/v1/mcp/sse"
        }
      }
    ]
  }
}
```

---

## Tool Kategorien (Intern)

| Kategorie | Anzahl | Beschreibung |
|-----------|--------|--------------|
| Core | 15 | Basis-Tools |
| Code | 12 | Code-Bearbeitung |
| Memory | 8 | Wissen & Speicher |
| Mesh | 10 | Federation |
| Ollama | 6 | Lokale Modelle |
| Agents | 8 | Multi-Agent |
| Admin | 12 | System-Tools |
| Search | 4 | Web & Crawl |
| **Total** | **134** | |
