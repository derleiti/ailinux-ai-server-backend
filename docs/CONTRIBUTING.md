# Contributing to TriForce

## Willkommen!

Danke für dein Interesse an TriForce! Dieses Dokument erklärt, wie du zum Projekt beitragen kannst.

---

## Wege zum Beitragen

### 1. Bug Reports

Erstelle ein Issue auf GitHub mit:
- Klare Beschreibung des Problems
- Schritte zur Reproduktion
- Erwartetes vs. tatsächliches Verhalten
- System-Info (OS, Python-Version, etc.)

```bash
# System-Info sammeln
uname -a
python3 --version
cat /etc/os-release | head -5
```

### 2. Feature Requests

Beschreibe:
- Was soll das Feature tun?
- Warum ist es nützlich?
- Mögliche Implementierungsideen

### 3. Code Contributions

#### Workflow

```bash
# 1. Fork erstellen (auf GitHub)

# 2. Clone
git clone https://github.com/YOUR_USERNAME/triforce.git
cd triforce

# 3. Branch erstellen
git checkout -b feature/mein-feature

# 4. Entwickeln
# ... code ...

# 5. Tests ausführen
pytest tests/

# 6. Commit
git add .
git commit -m "feat: Beschreibung des Features"

# 7. Push
git push origin feature/mein-feature

# 8. Pull Request erstellen (auf GitHub)
```

#### Commit Convention

Wir nutzen [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Bedeutung |
|--------|-----------|
| `feat:` | Neues Feature |
| `fix:` | Bugfix |
| `docs:` | Dokumentation |
| `refactor:` | Code-Refactoring |
| `test:` | Tests |
| `chore:` | Maintenance |

Beispiele:
```
feat: Add mesh_resources API endpoint
fix: Correct JWT tier extraction in client_chat
docs: Update installation guide for Debian 12
```

---

## Development Setup

### Voraussetzungen

- Python 3.11+
- Redis
- Git

### Lokale Entwicklung

```bash
# Clone
git clone https://github.com/derleiti/triforce.git
cd triforce

# Virtual Environment
python3.11 -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Für Tests

# Config
cp config/triforce.env.example config/triforce.env
# API Keys eintragen

# Redis starten
sudo systemctl start redis-server

# Server starten
uvicorn app.main:app --reload --port 9000
```

### Tests

```bash
# Alle Tests
pytest tests/

# Mit Coverage
pytest tests/ --cov=app --cov-report=html

# Nur Unit Tests
pytest tests/unit/

# Nur Integration Tests
pytest tests/integration/
```

### Code Style

Wir nutzen:
- **Black** für Formatierung
- **isort** für Import-Sortierung
- **flake8** für Linting

```bash
# Formatieren
black app/
isort app/

# Linting
flake8 app/
```

---

## Projekt-Struktur

```
triforce/
├── app/
│   ├── main.py           # FastAPI Application
│   ├── config.py         # Konfiguration
│   ├── routes/           # API Endpoints
│   │   ├── chat.py       # OpenAI-kompatible Chat API
│   │   ├── client_*.py   # Client-spezifische Endpoints
│   │   ├── mesh.py       # Federation/Mesh Endpoints
│   │   └── admin.py      # Admin Endpoints
│   ├── services/         # Business Logic
│   │   ├── llm/          # LLM Provider
│   │   ├── mesh/         # Federation
│   │   └── memory/       # Prisma Memory
│   ├── mcp/              # MCP Tools
│   └── utils/            # Utilities
├── config/               # Konfigurationsdateien
├── docs/                 # Dokumentation
├── scripts/              # Install/Deploy Scripts
├── tests/                # Tests
└── client-deploy/        # Client Submodules
```

---

## Code Guidelines

### Python

- Type Hints verwenden
- Docstrings für öffentliche Funktionen
- Async/await für I/O-Operationen
- Keine globalen Variablen

```python
async def fetch_models(provider: str, timeout: int = 30) -> list[dict]:
    """
    Fetch available models from provider.
    
    Args:
        provider: Provider name (gemini, anthropic, etc.)
        timeout: Request timeout in seconds
        
    Returns:
        List of model dictionaries with name and capabilities
        
    Raises:
        ProviderError: If provider is unavailable
    """
    ...
```

### API Endpoints

- RESTful Design
- Klare Response Models
- Fehlerbehandlung mit HTTPException
- Rate Limiting für öffentliche Endpoints

```python
@router.get("/models", response_model=ModelsResponse)
async def list_models(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> ModelsResponse:
    """List available models, optionally filtered by provider."""
    ...
```

---

## Review Process

1. **Automatische Checks**: CI muss grün sein
2. **Code Review**: Mindestens 1 Approval
3. **Dokumentation**: Bei API-Änderungen Docs updaten
4. **Tests**: Neue Features brauchen Tests

---

## Kontakt

- **GitHub Issues**: Für Bugs und Features
- **Email**: admin@ailinux.me
- **Matrix**: #triforce:matrix.org (geplant)

---

## Lizenz

Mit deinem Beitrag stimmst du zu, dass dein Code unter der MIT-Lizenz veröffentlicht wird.
