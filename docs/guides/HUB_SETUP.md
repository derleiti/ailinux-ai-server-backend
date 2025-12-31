# TriForce Hub Setup Guide

Anleitung zum Aufsetzen eines eigenen TriForce Hub-Servers.

---

## Voraussetzungen

### Hardware (Minimum)

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| CPU | 4 Cores | 8+ Cores |
| RAM | 8 GB | 32 GB |
| Storage | 50 GB SSD | 200 GB NVMe |
| Network | 100 Mbit | 1 Gbit |

### Hardware (Mit Ollama/GPU)

| Komponente | NVIDIA | AMD |
|------------|--------|-----|
| GPU | RTX 3060 12GB | RX 6700 XT 12GB |
| VRAM | 12 GB+ | 12 GB+ |
| Driver | 535+ | ROCm 6.0+ |

---

## Schritt 1: System vorbereiten

```bash
# Ubuntu 22.04/24.04
sudo apt update && sudo apt upgrade -y

# Basis-Pakete
sudo apt install -y \
  python3.11 python3.11-venv python3-pip \
  git curl wget htop \
  redis-server \
  nginx certbot python3-certbot-nginx \
  wireguard

# Firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 51820/udp # WireGuard
sudo ufw enable
```

---

## Schritt 2: TriForce installieren

```bash
# User erstellen (optional)
sudo useradd -m -s /bin/bash triforce
sudo su - triforce

# Repository klonen
git clone https://github.com/derleiti/triforce.git
cd triforce

# Python Environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Schritt 3: Konfiguration

### triforce.env

```bash
cp config/triforce.env.example config/triforce.env
nano config/triforce.env
```

```bash
# === CORE ===
HOST=0.0.0.0
PORT=9000
DEBUG=false
LOG_LEVEL=info

# === API KEYS ===
# Mindestens einen Provider konfigurieren
GEMINI_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
CEREBRAS_API_KEY=your_cerebras_key
MISTRAL_API_KEY=your_mistral_key

# === AUTH ===
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$(openssl rand -base64 16)

# === REDIS ===
REDIS_URL=redis://localhost:6379

# === OLLAMA (optional) ===
OLLAMA_HOST=http://localhost:11434

# === FEDERATION (optional) ===
FEDERATION_ENABLED=false
FEDERATION_PSK=your_psk_here
NODE_ID=my-hub
NODE_ROLE=hub
```

### JWT Secret generieren

```bash
openssl rand -hex 32
# Ausgabe in JWT_SECRET eintragen
```

---

## Schritt 4: Ollama (Optional)

```bash
# Installieren
curl -fsSL https://ollama.com/install.sh | sh

# Service aktivieren
sudo systemctl enable ollama
sudo systemctl start ollama

# Modelle laden
ollama pull llama3.2:3b        # 2 GB
ollama pull qwen2.5:7b         # 4 GB
ollama pull codellama:7b       # 4 GB
ollama pull deepseek-r1:8b     # 5 GB

# Prüfen
ollama list
curl http://localhost:11434/api/tags
```

### GPU-spezifisch

**NVIDIA:**
```bash
# CUDA installieren
sudo apt install nvidia-cuda-toolkit
nvidia-smi  # Prüfen
```

**AMD (ROCm):**
```bash
# ROCm installieren
wget https://repo.radeon.com/amdgpu-install/latest/ubuntu/jammy/amdgpu-install_6.0.deb
sudo dpkg -i amdgpu-install_6.0.deb
sudo amdgpu-install --usecase=rocm

# Ollama mit ROCm
HSA_OVERRIDE_GFX_VERSION=10.3.0 ollama serve
```

---

## Schritt 5: Systemd Service

```bash
sudo nano /etc/systemd/system/triforce.service
```

```ini
[Unit]
Description=TriForce AI Backend
After=network.target redis.service

[Service]
Type=simple
User=triforce
WorkingDirectory=/home/triforce/triforce
Environment="PATH=/home/triforce/triforce/.venv/bin"
ExecStart=/home/triforce/triforce/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable triforce.service
sudo systemctl start triforce.service
sudo systemctl status triforce.service
```

---

## Schritt 6: Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/triforce
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE Support
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/triforce /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Schritt 7: SSL mit Let's Encrypt

```bash
sudo certbot --nginx -d api.yourdomain.com
```

---

## Schritt 8: Federation beitreten (Optional)

### WireGuard einrichten

```bash
# Keys generieren
wg genkey | tee privatekey | wg pubkey > publickey
cat publickey  # An Master senden
```

```bash
sudo nano /etc/wireguard/wg0.conf
```

```ini
[Interface]
PrivateKey = YOUR_PRIVATE_KEY
Address = 10.10.0.X/24

[Peer]
PublicKey = MASTER_PUBLIC_KEY
Endpoint = master.ailinux.me:51820
AllowedIPs = 10.10.0.0/24
PersistentKeepalive = 25
```

```bash
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
ping 10.10.0.1  # Master erreichbar?
```

### Federation aktivieren

```bash
# In triforce.env
FEDERATION_ENABLED=true
FEDERATION_PSK=shared_psk_from_master
NODE_ID=my-hub
NODE_ROLE=hub
MASTER_IP=10.10.0.1
```

---

## Schritt 9: Verifizierung

```bash
# Service Status
sudo systemctl status triforce.service

# Health Check
curl http://localhost:9000/health

# API Test
curl http://localhost:9000/v1/models

# Ollama (wenn aktiv)
curl http://localhost:11434/api/tags

# Von extern
curl https://api.yourdomain.com/health
```

---

## Monitoring

### Logs

```bash
# Service Logs
journalctl -u triforce.service -f

# Nginx Logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Metriken

```bash
# System
htop
nvidia-smi  # GPU
rocm-smi    # AMD GPU

# API
curl https://api.yourdomain.com/v1/mesh/resources
```

---

## Troubleshooting

### Service startet nicht

```bash
journalctl -u triforce.service -n 50

# Manuell starten
cd /home/triforce/triforce
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000
```

### Redis-Fehler

```bash
sudo systemctl status redis-server
redis-cli ping
```

### Ollama-Fehler

```bash
sudo systemctl status ollama
ollama serve  # Manuell starten
```

### SSL-Fehler

```bash
sudo certbot renew --dry-run
```

---

## Nächste Schritte

- [Client Setup](CLIENT_SETUP.md)
- [Federation Details](../architecture/FEDERATION.md)
- [API Referenz](../api/REST.md)
