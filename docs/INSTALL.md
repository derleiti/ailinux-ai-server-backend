# TriForce Installation Guide

## Übersicht

Diese Anleitung beschreibt die Installation von:
1. **TriForce Hub Server** - Backend für API und Federation
2. **AILinux Client** - Desktop-Client für Linux
3. **AIWindows Client** - Desktop-Client für Windows

---

## Systemanforderungen

### Hub Server (Minimum)
- **OS**: Ubuntu 22.04+ / Debian 12+
- **CPU**: 4 Cores
- **RAM**: 8 GB (16 GB empfohlen)
- **Storage**: 50 GB SSD
- **Network**: Öffentliche IP oder Domain

### Hub Server (Empfohlen für Ollama)
- **CPU**: 8+ Cores
- **RAM**: 32 GB+
- **GPU**: NVIDIA RTX 3060+ oder AMD RX 6700+
- **Storage**: 100 GB+ NVMe

### Client
- **OS**: Linux (Debian/Ubuntu/Arch) oder Windows 10+
- **RAM**: 4 GB
- **Storage**: 500 MB

---

## Hub Server Installation

### Option 1: Quick Install (Empfohlen)

```bash
# Als root oder mit sudo
curl -fsSL https://raw.githubusercontent.com/derleiti/triforce/master/scripts/install-hub.sh | bash
```

### Option 2: Manuelle Installation

#### 1. System vorbereiten

```bash
# Updates
sudo apt update && sudo apt upgrade -y

# Abhängigkeiten
sudo apt install -y \
  python3.11 python3.11-venv python3-pip \
  git curl wget \
  redis-server \
  nginx certbot python3-certbot-nginx
```

#### 2. Repository klonen

```bash
cd /home/$USER
git clone https://github.com/derleiti/triforce.git
cd triforce
```

#### 3. Python Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Konfiguration

```bash
# Config kopieren
cp config/triforce.env.example config/triforce.env

# Bearbeiten
nano config/triforce.env
```

**Wichtige Einstellungen in `triforce.env`:**

```bash
# API Keys (mindestens einen)
GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

# Server
HOST=0.0.0.0
PORT=9000

# Redis
REDIS_URL=redis://localhost:6379

# JWT Secret (generieren mit: openssl rand -hex 32)
JWT_SECRET=your_secret_here
```

#### 5. Systemd Service

```bash
sudo cp scripts/triforce.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable triforce.service
sudo systemctl start triforce.service
```

#### 6. Nginx Reverse Proxy

```bash
sudo cp scripts/nginx-triforce.conf /etc/nginx/sites-available/triforce
sudo ln -s /etc/nginx/sites-available/triforce /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 7. SSL mit Let's Encrypt

```bash
sudo certbot --nginx -d api.yourdomain.com
```

---

## Ollama Installation (Optional, für lokale Modelle)

```bash
# Ollama installieren
curl -fsSL https://ollama.com/install.sh | sh

# Service starten
sudo systemctl enable ollama
sudo systemctl start ollama

# Modelle herunterladen
ollama pull llama3.2:3b
ollama pull qwen2.5:7b
ollama pull codellama:7b
```

---

## Client Installation

### Linux (Debian/Ubuntu)

```bash
# Repository hinzufügen
echo "deb https://repo.ailinux.me/apt stable main" | sudo tee /etc/apt/sources.list.d/ailinux.list
curl -fsSL https://repo.ailinux.me/gpg | sudo gpg --dearmor -o /usr/share/keyrings/ailinux.gpg

# Installieren
sudo apt update
sudo apt install ailinux-client
```

**Oder direkt als .deb:**

```bash
wget https://repo.ailinux.me/pool/main/ailinux-client_4.2.0_amd64.deb
sudo dpkg -i ailinux-client_4.2.0_amd64.deb
sudo apt install -f  # Falls Abhängigkeiten fehlen
```

### Linux (Arch/AUR)

```bash
yay -S ailinux-client
# oder
paru -S ailinux-client
```

### Windows

1. Download: https://github.com/derleiti/aiwindows-client/releases
2. `AILinux-Setup.exe` ausführen
3. Installation folgen

---

## Verifizierung

### Hub Server

```bash
# Service Status
sudo systemctl status triforce.service

# Health Check
curl http://localhost:9000/health

# API Test
curl http://localhost:9000/v1/mesh/resources
```

### Client

```bash
# Linux
ailinux-client --version

# Verbindung testen
ailinux-client --test-connection
```

---

## Troubleshooting

### Service startet nicht

```bash
# Logs prüfen
journalctl -u triforce.service -n 100

# Manuell starten für Debug
cd /home/$USER/triforce
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000
```

### Port bereits belegt

```bash
# Prozess finden
sudo lsof -i :9000

# Oder anderen Port in triforce.env setzen
PORT=9001
```

### Redis Verbindungsfehler

```bash
# Redis Status
sudo systemctl status redis-server

# Redis testen
redis-cli ping
```

### Ollama nicht erreichbar

```bash
# Status prüfen
sudo systemctl status ollama

# Manuell starten
ollama serve

# Test
curl http://localhost:11434/api/tags
```

---

## Nächste Schritte

- [Quickstart Guide](QUICKSTART.md) - Erste Schritte
- [API Dokumentation](api/REST.md) - API Referenz
- [Federation Setup](architecture/FEDERATION.md) - Mehrere Nodes verbinden
