# TriForce AI Platform - Business Plan v2.0

## Produkt-Strategie: Zwei-Produkt-Modell

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         TRIFORCE ÖKOSYSTEM                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌────────────────────────────┐     ┌────────────────────────────┐     ║
║   │      HUB LICENSE           │     │     CLIENT LICENSE         │     ║
║   │    (Server-Betreiber)      │     │      (Endnutzer)           │     ║
║   ├────────────────────────────┤     ├────────────────────────────┤     ║
║   │                            │     │                            │     ║
║   │  • Eigene Hardware         │     │  • Nutzt Hub-Infrastruktur │     ║
║   │  • Verdient Credits        │◄───►│  • Zahlt €/Credits         │     ║
║   │  • Federation-Teilnahme    │     │  • API + CLI + Desktop     │     ║
║   │  • Kann Clients bedienen   │     │  • Optional: Hybrid Mode   │     ║
║   │                            │     │                            │     ║
║   └────────────────────────────┘     └────────────────────────────┘     ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 1. HUB LICENSE (Server-Betreiber)

### Zielgruppe
- Unternehmen mit eigener GPU-Infrastruktur
- Homelabber mit Gaming-GPUs
- Rechenzentren
- Universitäten/Forschung

### Tiers

| Tier | Preis | Features |
|------|-------|----------|
| **Hub Community** | €0/Monat | Open Source, Self-Hosted, keine Federation |
| **Hub Pro** | €49/Monat | Federation-Zugang, Credits verdienen, Priority Support |
| **Hub Enterprise** | €299/Monat | SLA 99.9%, Custom Integration, Dedicated Support |

### Credit-Verdienst (Hub → Credits)

| Hardware | Credits/Stunde | ≈ Token-Wert |
|----------|----------------|--------------|
| RTX 3060 12GB | 10 | ~5k |
| RTX 4080 16GB | 25 | ~12.5k |
| RTX 4090 24GB | 40 | ~20k |
| A100 40GB | 100 | ~50k |
| A100 80GB | 150 | ~75k |
| Mac M3 Max | 35 | ~17.5k |

---

## 2. CLIENT LICENSE (Endnutzer)

### Tiers

| Tier | Preis | Tokens/Tag | Features |
|------|-------|------------|----------|
| **Free** | €0 | 10k | Rate-limited, Basis-Modelle |
| **Pro** | €17,99/Monat | 250k | Alle 640+ Modelle, Priority |
| **Unlimited** | €59,99/Monat | ∞ | Max Priority, API + MCP |
| **Team** | €149/Monat | 1M shared | 5 Seats, Team Dashboard |

### Credit-Verbrauch (Client → Cloud APIs)

| API | Credits/1k Tokens |
|-----|-------------------|
| Ollama (lokal) | 0 (immer kostenlos) |
| Groq/Cerebras | 1 |
| Gemini Flash/Mistral Small | 2 |
| Gemini Pro/Mistral Large | 5 |
| Claude Sonnet/GPT-4o | 10 |
| Claude Opus | 25 |

---

## 3. MESH RESOURCES API

### Endpoint
```
GET /v1/mesh/resources?format=summary|nodes|full
```

### Response (summary)
```json
{
  "status": "healthy",
  "mesh": {
    "nodes": "3/3 online",
    "compute": "64 Cores",
    "memory": "156 GB RAM",
    "gpus": ["RX 6800 XT"],
    "latency": "22ms avg"
  },
  "intelligence": {
    "providers": 8,
    "models": "291+",
    "local": 22
  }
}
```

---

## 4. AKTUELLE FEDERATION

| Node | Cores | RAM | GPU | Rolle |
|------|-------|-----|-----|-------|
| Hetzner EX63 | 20 | 62 GB | - | Master |
| Backup VPS | 28 | 64 GB | - | Hub |
| Zombie-PC | 16 | 30 GB | RX 6800 XT | Hub |
| **TOTAL** | **64** | **156 GB** | 1 GPU | |

---

## 5. ROADMAP

- **Q1 2025**: Alpha (Credit-System, 10 Tester)
- **Q2 2025**: Beta (Client v5.0, Payment, 100 User)
- **Q3 2025**: Launch (Stable, Enterprise, Marketing)
- **Q4 2025**: Scale (1000+ User, 50+ Hubs)

---

*Version 2.0 - 2024-12-31*
