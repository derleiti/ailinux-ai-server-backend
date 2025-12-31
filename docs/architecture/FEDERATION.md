# TriForce Federation Protocol

## Übersicht

Die Federation ermöglicht verteiltes Computing über mehrere Server hinweg. Jeder Node kann Anfragen verarbeiten und bei Bedarf an andere Nodes weiterleiten.

---

## Netzwerk-Topologie

```
                    ┌─────────────────┐
                    │   INTERNET      │
                    │   (Clients)     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  MASTER NODE    │
                    │  (Hetzner)      │
                    │  10.10.0.1      │
                    │  Port: 51820    │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │  HUB NODE   │   │  HUB NODE   │   │  HUB NODE   │
    │  (Backup)   │   │ (Zombie-PC) │   │  (Future)   │
    │  10.10.0.3  │   │  10.10.0.2  │   │  10.10.0.X  │
    └─────────────┘   └─────────────┘   └─────────────┘
```

---

## Security Layers

### 1. WireGuard VPN

Alle Nodes kommunizieren über ein privates VPN-Netzwerk.

**Subnet:** `10.10.0.0/24`
**Port:** `51820/UDP`

### 2. IP Whitelist

Nur bekannte VPN-IPs werden akzeptiert.

```python
ALLOWED_IPS = ["10.10.0.1", "10.10.0.2", "10.10.0.3"]
```

### 3. PSK Authentication

Pre-Shared Key für HMAC-SHA256 Signierung.

```python
signature = hmac.new(
    key=PSK.encode(),
    msg=f"{timestamp}:{node_id}:{payload}".encode(),
    digestmod=hashlib.sha256
).hexdigest()
```

### 4. Timestamp Validation

Requests älter als 30 Sekunden werden abgelehnt.

```python
if abs(time.time() - timestamp) > 30:
    raise SecurityError("Request expired")
```

---

## Node-Konfiguration

### config/federation_nodes.json

```json
{
  "hetzner": {
    "ip": "10.10.0.1",
    "port": 9000,
    "cores": 20,
    "ram": 62,
    "gpu": null,
    "role": "master",
    "name": "Hetzner EX63"
  },
  "backup": {
    "ip": "10.10.0.3",
    "port": 9100,
    "cores": 28,
    "ram": 64,
    "gpu": null,
    "role": "hub",
    "name": "Backup VPS"
  },
  "zombie-pc": {
    "ip": "10.10.0.2",
    "port": 9000,
    "cores": 16,
    "ram": 30,
    "gpu": "RX 6800 XT",
    "role": "hub",
    "name": "Zombie PC"
  }
}
```

---

## API Endpoints

### Health Check

```http
POST /v1/federation/health
```

**Headers:**
```
X-Federation-Node: hetzner
X-Federation-Timestamp: 1704067200
X-Federation-Signature: abc123...
```

### Task Distribution

```http
POST /v1/federation/task
```

**Body:**
```json
{
  "task_id": "uuid",
  "type": "chat",
  "payload": {...},
  "priority": 1
}
```

### Status

```http
GET /v1/federation/status
```

**Response:**
```json
{
  "nodes": {
    "hetzner": {"online": true, "latency_ms": 1},
    "backup": {"online": true, "latency_ms": 24},
    "zombie-pc": {"online": true, "latency_ms": 33}
  },
  "total_cores": 64,
  "total_ram_gb": 156
}
```

---

## WireGuard Setup

### Master Node

```bash
# /etc/wireguard/wg0.conf
[Interface]
PrivateKey = MASTER_PRIVATE_KEY
Address = 10.10.0.1/24
ListenPort = 51820

# Backup VPS
[Peer]
PublicKey = BACKUP_PUBLIC_KEY
AllowedIPs = 10.10.0.3/32

# Zombie PC
[Peer]
PublicKey = ZOMBIE_PUBLIC_KEY
AllowedIPs = 10.10.0.2/32
Endpoint = dynamic:51820
PersistentKeepalive = 25
```

### Hub Node

```bash
# /etc/wireguard/wg0.conf
[Interface]
PrivateKey = HUB_PRIVATE_KEY
Address = 10.10.0.3/24

[Peer]
PublicKey = MASTER_PUBLIC_KEY
AllowedIPs = 10.10.0.0/24
Endpoint = 138.201.50.230:51820
PersistentKeepalive = 25
```

### Befehle

```bash
# Aktivieren
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# Status
sudo wg show

# Ping Test
ping 10.10.0.1
```

---

## Load Balancing

### Strategie

1. **Latency-Based**: Niedrigste Latenz bevorzugt
2. **Capacity-Based**: Verfügbare Ressourcen
3. **Specialty-Based**: GPU-Tasks an GPU-Nodes

### Algorithmus

```python
def select_best_node(task_type):
    nodes = get_online_nodes()
    
    if task_type == "gpu_inference":
        gpu_nodes = [n for n in nodes if n.gpu]
        if gpu_nodes:
            return min(gpu_nodes, key=lambda n: n.latency)
    
    return min(nodes, key=lambda n: n.load * n.latency)
```

---

## Failover

### Automatisches Failover

```python
async def execute_with_failover(task, nodes):
    for node in sorted(nodes, key=lambda n: n.priority):
        try:
            return await node.execute(task, timeout=30)
        except (TimeoutError, ConnectionError):
            logger.warning(f"Node {node.id} failed, trying next")
            continue
    raise AllNodesFailedError()
```

### Health Monitoring

- Heartbeat alle 10 Sekunden
- 3 fehlgeschlagene Heartbeats = Node offline
- Automatische Wiederaufnahme bei Erfolg
