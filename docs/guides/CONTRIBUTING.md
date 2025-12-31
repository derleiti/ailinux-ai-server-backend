# Contributing to TriForce

Danke für dein Interesse an TriForce!

---

## Wie kann ich beitragen?

### 🐛 Bug Reports

1. Prüfe, ob der Bug bereits gemeldet wurde
2. Erstelle ein [GitHub Issue](https://github.com/derleiti/triforce/issues)
3. Beschreibe:
   - Was ist passiert?
   - Was sollte passieren?
   - Schritte zur Reproduktion
   - System-Info (OS, Python-Version, etc.)

### 💡 Feature Requests

1. Erstelle ein Issue mit Label `enhancement`
2. Beschreibe das Feature und den Use Case
3. Diskutiere mit der Community

### 🔧 Code Contributions

1. Fork das Repository
2. Erstelle einen Feature-Branch: `git checkout -b feature/mein-feature`
3. Committe deine Änderungen: `git commit -m 'feat: Beschreibung'`
4. Push zum Branch: `git push origin feature/mein-feature`
5. Erstelle einen Pull Request

---

## Development Setup

```bash
# Repository klonen
git clone https://github.com/derleiti/triforce.git
cd triforce

# Virtual Environment
python3.11 -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Entwickler-Tools

# Pre-commit Hooks
pre-commit install

# Tests
pytest tests/

# Linting
ruff check app/
black app/ --check
mypy app/
```

---

## Code Style

### Python

- **Formatter**: Black
- **Linter**: Ruff
- **Type Hints**: Mypy
- **Docstrings**: Google Style

```python
def example_function(param1: str, param2: int = 10) -> dict:
    """Kurze Beschreibung.
    
    Längere Beschreibung falls nötig.
    
    Args:
        param1: Beschreibung von param1.
        param2: Beschreibung von param2.
        
    Returns:
        Dictionary mit Ergebnis.
        
    Raises:
        ValueError: Wenn param1 leer ist.
    """
    if not param1:
        raise ValueError("param1 darf nicht leer sein")
    return {"result": param1, "count": param2}
```

### Commit Messages

Wir nutzen [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: Neues Feature
- `fix`: Bugfix
- `docs`: Dokumentation
- `style`: Formatierung
- `refactor`: Code-Umbau
- `test`: Tests
- `chore`: Maintenance

**Beispiele:**
```
feat(mcp): Add mesh_resources tool
fix(auth): Fix JWT token validation
docs(api): Update REST API reference
```

---

## Projekt-Struktur

```
triforce/
├── app/
│   ├── main.py           # FastAPI Entry
│   ├── config.py         # Konfiguration
│   ├── routes/           # API Endpoints
│   ├── services/         # Business Logic
│   ├── mcp/              # MCP Tools
│   └── utils/            # Hilfsfunktionen
├── tests/
│   ├── test_api.py
│   ├── test_mcp.py
│   └── ...
├── docs/                 # Dokumentation
├── scripts/              # Deployment Scripts
└── config/               # Konfigurationsdateien
```

---

## Tests schreiben

```python
# tests/test_example.py
import pytest
from app.services.example import example_function

def test_example_success():
    result = example_function("test", 5)
    assert result["result"] == "test"
    assert result["count"] == 5

def test_example_empty_param():
    with pytest.raises(ValueError):
        example_function("")

@pytest.mark.asyncio
async def test_async_function():
    result = await async_example()
    assert result is not None
```

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=app --cov-report=html

# Einzelne Datei
pytest tests/test_mcp.py -v
```

---

## Pull Request Checklist

- [ ] Tests geschrieben/aktualisiert
- [ ] Dokumentation aktualisiert
- [ ] Linting passt (`ruff check app/`)
- [ ] Formatierung passt (`black app/ --check`)
- [ ] Type Hints korrekt (`mypy app/`)
- [ ] Commit Messages nach Convention
- [ ] PR-Beschreibung vollständig

---

## Review Process

1. Automatische CI-Checks müssen passen
2. Code Review durch Maintainer
3. Feedback einarbeiten
4. Merge nach Approval

---

## Kommunikation

- **GitHub Issues**: Bugs, Features
- **GitHub Discussions**: Fragen, Ideen
- **Discord**: discord.gg/ailinux
- **Email**: dev@ailinux.me

---

## Lizenz

Mit deinem Beitrag stimmst du zu, dass er unter der MIT-Lizenz veröffentlicht wird.

---

Danke für deine Beiträge! 🎉
