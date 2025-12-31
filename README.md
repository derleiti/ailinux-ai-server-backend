# TriForce AI Platform

<div align="center">

![Version](https://img.shields.io/badge/version-2.80-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Nodes](https://img.shields.io/badge/federation-3%20nodes-orange)
![Models](https://img.shields.io/badge/models-640%2B-purple)

**Multi-LLM Orchestration Platform with Federation Support**

[Installation](#installation) • [Quick Start](#quick-start) • [API Docs](#api) • [Architecture](#architecture) • [Contributing](#contributing)

</div>

---

## 🚀 Overview

TriForce is a decentralized AI platform that unifies 640+ LLM models from 9 providers into a single API. It features a federated mesh network, local Ollama integration, and 134 MCP tools.

### Key Features

- **Multi-Provider**: Gemini, Anthropic, Groq, Cerebras, Mistral, OpenRouter, GitHub, Cloudflare, Ollama
- **Federation**: Distributed compute across multiple nodes (currently 64 cores, 156GB RAM)
- **MCP Tools**: 134 integrated tools for code, search, files, and more
- **Local Models**: Ollama integration for private, free inference
- **OpenAI Compatible**: Drop-in replacement for OpenAI API

### Current Federation Status

| Node | Cores | RAM | GPU | Role |
|------|-------|-----|-----|------|
| Hetzner EX63 | 20 | 62 GB | - | Master |
| Backup VPS | 28 | 64 GB | - | Hub |
| Zombie-PC | 16 | 30 GB | RX 6800 XT | Hub |
| **Total** | **64** | **156 GB** | 1 GPU | |

---

## 📦 Installation

### Server (Hub) Installation

```bash
# Clone
git clone https://github.com/derleiti/triforce.git
cd triforce

# Setup
./scripts/install-hub.sh

# Start
systemctl start triforce.service
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed instructions.

### Client Installation

**Linux (Debian/Ubuntu)**:
```bash
wget https://repo.ailinux.me/pool/main/ailinux-client_4.2.0_amd64.deb
sudo dpkg -i ailinux-client_4.2.0_amd64.deb
```

**Arch Linux (AUR)**:
```bash
yay -S ailinux-client
```

---

## ⚡ Quick Start

### API Usage

```bash
# Chat completion (OpenAI compatible)
curl https://api.ailinux.me/v1/chat/completions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini/gemini-2.0-flash",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Available Models (Selection)

| Provider | Model | Speed | Quality |
|----------|-------|-------|---------|
| Gemini | gemini-2.0-flash | ⚡⚡⚡ | ★★★★ |
| Groq | llama-3.3-70b | ⚡⚡⚡ | ★★★★★ |
| Cerebras | llama-3.3-70b | ⚡⚡⚡ | ★★★★★ |
| Anthropic | claude-sonnet-4 | ⚡⚡ | ★★★★★ |
| Mistral | mistral-large | ⚡⚡ | ★★★★ |
| Ollama | * (local) | ⚡ | varies |

### Mesh Resources

```bash
# Live federation status
curl https://api.ailinux.me/v1/mesh/resources
```

```json
{
  "status": "healthy",
  "mesh": {
    "nodes": "3/3 online",
    "compute": "64 Cores",
    "memory": "156 GB RAM"
  },
  "intelligence": {
    "providers": 8,
    "models": "291+"
  }
}
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [INSTALL.md](docs/INSTALL.md) | Full installation guide |
| [QUICKSTART.md](docs/QUICKSTART.md) | Getting started in 5 minutes |
| [API Reference](docs/api/REST.md) | REST API documentation |
| [MCP Tools](docs/api/MCP.md) | MCP tools reference |
| [Architecture](docs/ARCHITECTURE.md) | System architecture |
| [Federation](docs/architecture/FEDERATION.md) | Federation protocol |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTS                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ AILinux  │  │ AIWindows│  │   API    │  │   MCP    │        │
│  │  Client  │  │  Client  │  │  Direct  │  │  Tools   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRIFORCE API GATEWAY                          │
│                   api.ailinux.me:443                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Auth/JWT    │  │ Rate Limit  │  │ Load Balance│              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FEDERATION MESH                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Hetzner    │  │   Backup    │  │  Zombie-PC  │              │
│  │  (Master)   │◄─┼─►  (Hub)   ◄┼─►│   (Hub)     │              │
│  │  20c/62GB   │  │  28c/64GB   │  │  16c/30GB   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM PROVIDERS                                 │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │Gemini  │ │Anthropic│ │ Groq   │ │Cerebras│ │Mistral │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                   │
│  │OpenRout│ │ GitHub │ │Cloudfl.│ │ Ollama │                   │
│  └────────┘ └────────┘ └────────┘ └────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💰 Pricing Tiers

| Tier | Price | Tokens/Day | Features |
|------|-------|------------|----------|
| **Free** | €0 | 10k | Basic models, rate-limited |
| **Pro** | €17.99/mo | 250k | All 640+ models, priority |
| **Unlimited** | €59.99/mo | ∞ | Max priority, all features |
| **Team** | €149/mo | 1M shared | 5 seats, dashboard |

---

## 🛠️ Development

```bash
# Setup dev environment
cd triforce
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 9000

# Run tests
pytest tests/
```

---

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

## 🔗 Links

- **API**: https://api.ailinux.me
- **Docs**: https://docs.ailinux.me
- **Status**: https://api.ailinux.me/v1/mesh/resources
- **GitHub**: https://github.com/derleiti/triforce

---

<div align="center">

**Built with ❤️ by the AILinux Team**

</div>
