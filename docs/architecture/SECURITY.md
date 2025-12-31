# TriForce Security Architecture

## Übersicht

TriForce implementiert ein mehrschichtiges Sicherheitskonzept:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                               │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Network Security                                       │
│  ├── Cloudflare DDoS Protection                                 │
│  ├── TLS 1.3 Encryption                                         │
│  └── Firewall (UFW/OPNsense)                                    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Authentication                                         │
│  ├── JWT Tokens (HS256)                                         │
│  ├── Basic Auth (Admin)                                         │
│  └── API Keys (Provider)                                        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Authorization                                          │
│  ├── Tier System (Free/Pro/Unlimited)                           │
│  ├── Rate Limiting                                              │
│  └── Resource Quotas                                            │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Federation Security                                    │
│  ├── WireGuard VPN (10.10.0.0/24)                              │
│  ├── IP Whitelist                                               │
│  ├── PSK Signatures (HMAC-SHA256)                               │
│  └── Timestamp Validation                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Network Security

### Cloudflare

- DDoS-Schutz
- WAF (Web Application Firewall)
- Bot-Management
- SSL/TLS-Terminierung (optional)

### TLS 1.3

```nginx
# Nginx SSL Config
ssl_protocols TLSv1.3;
ssl_ciphers EECDH+AESGCM:EDH+AESGCM;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
```

### Firewall

```bash
# UFW Regeln
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 51820/udp # WireGuard
```

---

## Layer 2: Authentication

### JWT Tokens

```python
# Token-Struktur
{
    "sub": "user@example.com",
    "tier": "pro",
    "exp": 1704067200,
    "iat": 1703980800
}
```

**Konfiguration:**
```bash
# triforce.env
JWT_SECRET=your_256_bit_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=720  # 30 Tage
```

### Basic Auth (Admin)

Für MCP und Admin-Endpoints:

```bash
# Header
Authorization: Basic base64(username:password)

# Konfiguration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password
```

### API Key Management

Provider-Keys werden sicher gespeichert:

```bash
# Niemals in Git!
GEMINI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
GROQ_API_KEY=xxx
```

---

## Layer 3: Authorization

### Tier System

| Tier | Rate Limit | Tokens/Tag | Modelle |
|------|------------|------------|---------|
| Free | 10/min | 10,000 | Basis |
| Pro | 60/min | 250,000 | Alle |
| Unlimited | 300/min | ∞ | Alle |
| Admin | ∞ | ∞ | Alle + System |

### Rate Limiting

```python
# Redis-basiert
from redis import Redis

class RateLimiter:
    def check(self, user_id: str, tier: str) -> bool:
        key = f"rate:{user_id}"
        current = redis.incr(key)
        if current == 1:
            redis.expire(key, 60)  # 1 Minute
        return current <= TIER_LIMITS[tier]
```

### Token Quotas

```python
# Tägliche Token-Limits
TIER_TOKEN_LIMITS = {
    "free": 10_000,
    "pro": 250_000,
    "unlimited": float("inf"),
}
```

---

## Layer 4: Federation Security

### WireGuard VPN

Alle Federation-Kommunikation über verschlüsseltes VPN:

```ini
[Interface]
PrivateKey = <key>
Address = 10.10.0.1/24

[Peer]
PublicKey = <peer_key>
AllowedIPs = 10.10.0.2/32
```

### IP Whitelist

```python
ALLOWED_FEDERATION_IPS = [
    "10.10.0.1",  # hetzner
    "10.10.0.2",  # zombie-pc
    "10.10.0.3",  # backup
]

def validate_federation_request(request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_FEDERATION_IPS:
        raise HTTPException(403, "Forbidden")
```

### PSK Signatures

```python
import hmac
import hashlib
import json

def sign_federation_request(data: dict, psk: str) -> str:
    payload = json.dumps(data, sort_keys=True)
    return hmac.new(
        psk.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_signature(data: dict, signature: str, psk: str) -> bool:
    expected = sign_federation_request(data, psk)
    return hmac.compare_digest(signature, expected)
```

### Timestamp Validation

```python
from datetime import datetime, timedelta

MAX_REQUEST_AGE = timedelta(seconds=60)

def validate_timestamp(timestamp: str) -> bool:
    request_time = datetime.fromisoformat(timestamp)
    age = datetime.utcnow() - request_time
    return age < MAX_REQUEST_AGE
```

---

## Sensitive Data

### Was wird NICHT gespeichert:

- Passwörter im Klartext (nur bcrypt-Hash)
- API-Keys der User
- Chat-Inhalte (optional, konfigurierbar)
- IP-Adressen (nur temporär für Rate Limiting)

### Verschlüsselung at Rest:

```bash
# SQLite mit Encryption (optional)
sqlcipher triforce.db
```

---

## Security Headers

```python
# FastAPI Middleware
from starlette.middleware import Middleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
}
```

---

## Incident Response

### Logging

```python
# Sicherheits-Events
logger.warning(f"Failed login attempt: {email}")
logger.error(f"Rate limit exceeded: {user_id}")
logger.critical(f"Invalid federation signature from {ip}")
```

### Alerts

Bei kritischen Events:
- Email an Admin
- Discord Webhook
- Prometheus Alert

---

## Security Checklist

### Deployment

- [ ] JWT_SECRET ist 256-bit random
- [ ] Admin-Passwort ist stark
- [ ] API-Keys nicht in Git
- [ ] TLS 1.3 aktiv
- [ ] Firewall konfiguriert
- [ ] WireGuard für Federation

### Regelmäßig

- [ ] Dependencies updaten
- [ ] SSL-Zertifikate prüfen
- [ ] Logs auf Anomalien prüfen
- [ ] Zugänge auditieren

---

## Vulnerability Reporting

Sicherheitslücken bitte melden an:

- **Email**: security@ailinux.me
- **PGP Key**: [Link]

Wir antworten innerhalb von 48 Stunden.
