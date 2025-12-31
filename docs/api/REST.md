# TriForce REST API Reference

**Base URL**: `https://api.ailinux.me/v1`

---

## Authentication

### Header Authentication

```
Authorization: Bearer <JWT_TOKEN>
```

### Basic Auth (Legacy)

```
Authorization: Basic <base64(username:password)>
```

---

## Endpoints

### Health & Status

#### GET /health

System-Gesundheitsstatus.

```bash
curl https://api.ailinux.me/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-31T08:00:00Z",
  "services": {
    "backend": {"status": "healthy"},
    "ollama": {"status": "healthy", "models_available": 33},
    "redis": {"status": "healthy"},
    "searxng": {"status": "healthy"}
  }
}
```

#### GET /v1/mesh/resources

Live Federation-Status.

**Query Parameters:**
- `format`: `summary` | `nodes` | `full` (default: `summary`)

```bash
curl https://api.ailinux.me/v1/mesh/resources?format=nodes
```

---

### Chat Completions

#### POST /v1/chat/completions

OpenAI-kompatible Chat-API.

**Request:**
```json
{
  "model": "gemini/gemini-2.0-flash",
  "messages": [
    {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
    {"role": "user", "content": "Hallo!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "gemini/gemini-2.0-flash",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hallo! Wie kann ich dir helfen?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

**Streaming:**

Mit `"stream": true` wird SSE genutzt:

```bash
curl -N https://api.ailinux.me/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model": "gemini/gemini-2.0-flash", "messages": [...], "stream": true}'
```

---

### Models

#### GET /v1/models

Liste aller verfügbaren Modelle.

```bash
curl https://api.ailinux.me/v1/models \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gemini/gemini-2.0-flash",
      "object": "model",
      "owned_by": "google",
      "provider": "gemini"
    },
    {
      "id": "anthropic/claude-sonnet-4",
      "object": "model",
      "owned_by": "anthropic",
      "provider": "anthropic"
    }
  ]
}
```

#### GET /v1/client/models

Modelle für den aktuellen Tier.

---

### Client Authentication

#### POST /v1/client/register

Neuen Account erstellen.

```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "username": "optional_username"
}
```

#### POST /v1/client/login

Anmelden und Token erhalten.

```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

Response:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "tier": "pro",
  "expires": "2025-01-31T00:00:00Z",
  "user": {
    "email": "user@example.com",
    "username": "optional_username"
  }
}
```

#### GET /v1/client/profile

Aktuelles Profil abrufen.

---

### MCP (Model Context Protocol)

#### POST /v1/mcp

MCP-Anfragen senden.

**Initialize:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {}
  }
}
```

**List Tools:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

**Call Tool:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {"query": "TriForce AI"}
  }
}
```

#### GET /v1/mcp/sse

SSE-Endpoint für MCP-Streaming.

---

### Mesh & Federation

#### GET /v1/mesh/status

Mesh-Koordinator Status.

#### GET /v1/mesh/agents

Liste der Mesh-Agents.

#### POST /v1/mesh/submit

Task an Mesh senden.

```json
{
  "title": "Code Review",
  "description": "Überprüfe die Datei main.py auf Bugs"
}
```

#### POST /v1/federation/health

Federation Health-Check (intern).

---

## Error Codes

| Code | Bedeutung |
|------|-----------|
| 400 | Bad Request - Ungültige Parameter |
| 401 | Unauthorized - Token fehlt/ungültig |
| 403 | Forbidden - Tier-Berechtigung fehlt |
| 404 | Not Found - Endpoint existiert nicht |
| 429 | Rate Limited - Zu viele Anfragen |
| 500 | Server Error - Interner Fehler |
| 503 | Service Unavailable - Provider nicht erreichbar |

Error Response Format:
```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error",
    "code": 429
  }
}
```

---

## Rate Limits

| Tier | Requests/Min | Tokens/Tag |
|------|--------------|------------|
| Free | 10 | 10,000 |
| Pro | 60 | 250,000 |
| Unlimited | 300 | Unbegrenzt |
| Team | 600 | 1,000,000 |

---

## Model IDs

Format: `provider/model-name`

### Providers

| Provider | Prefix | Beispiel |
|----------|--------|----------|
| Google Gemini | `gemini/` | `gemini/gemini-2.0-flash` |
| Anthropic | `anthropic/` | `anthropic/claude-sonnet-4` |
| Groq | `groq/` | `groq/llama-3.3-70b` |
| Cerebras | `cerebras/` | `cerebras/llama-3.3-70b` |
| Mistral | `mistral/` | `mistral/mistral-large` |
| OpenRouter | `openrouter/` | `openrouter/meta-llama/llama-3` |
| Ollama | `ollama/` | `ollama/llama3.2:3b` |

---

## Webhooks (Coming Soon)

Webhooks für asynchrone Benachrichtigungen sind in Planung.
