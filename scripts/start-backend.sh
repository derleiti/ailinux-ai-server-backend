#!/bin/bash
# ============================================================================
# AILinux Backend - Unified Start Script v2.80
# ============================================================================
# Startet alle Services: Ollama → Backend → CLI Agents
# Einziger Einstiegspunkt für systemd
# ============================================================================

set -e

# === KONFIGURATION ===
OWNER="${SUDO_USER:-$USER}"
BASE_DIR="/home/${OWNER}/triforce"
VENV_DIR="$BASE_DIR/.venv"
LOG_DIR="$BASE_DIR/logs"
TRISTAR_DIR="/var/tristar"
API_URL="http://localhost:9100"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
ok()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn(){ echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; }

# === VERZEICHNISSE ===
setup_directories() {
    log "Erstelle Verzeichnisse..."
    mkdir -p "$LOG_DIR"
    mkdir -p "$TRISTAR_DIR"/{projects,logs,memory,pids,agents}
    mkdir -p "$BASE_DIR/triforce"/{logs,runtime,backup}
    
    # Permissions nur wenn als root
    if [ "$(id -u)" = "0" ]; then
        chown -R "$OWNER:$OWNER" "$TRISTAR_DIR" 2>/dev/null || true
    fi
    ok "Verzeichnisse bereit"
}

# === OLLAMA ===
start_ollama() {
    log "Prüfe Ollama..."
    
    # Prüfen ob Ollama läuft
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        ok "Ollama bereits aktiv"
        return 0
    fi
    
    # Ollama starten
    log "Starte Ollama Server..."
    
    # Ollama als Hintergrund-Prozess
    nohup /usr/local/bin/ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    echo $OLLAMA_PID > "$TRISTAR_DIR/pids/ollama.pid"
    
    # Warten auf Ollama (max 30s)
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            ok "Ollama gestartet (PID: $OLLAMA_PID)"
            return 0
        fi
        sleep 1
    done
    
    err "Ollama Start fehlgeschlagen"
    return 1
}

# === REDIS CHECK ===
check_redis() {
    log "Prüfe Redis..."
    if redis-cli ping >/dev/null 2>&1; then
        ok "Redis aktiv"
        return 0
    else
        warn "Redis nicht erreichbar - starte..."
        systemctl start redis 2>/dev/null || redis-server --daemonize yes
        sleep 2
        if redis-cli ping >/dev/null 2>&1; then
            ok "Redis gestartet"
            return 0
        fi
        err "Redis Start fehlgeschlagen"
        return 1
    fi
}

# === VENV AKTIVIEREN ===
activate_venv() {
    log "Aktiviere Virtual Environment..."
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        export PYTHONPATH="$BASE_DIR"
        export PYTHONUNBUFFERED=1
        ok "venv aktiviert"
    else
        err "venv nicht gefunden: $VENV_DIR"
        exit 1
    fi
}

# === CLI AGENTS BOOTSTRAP ===
bootstrap_agents() {
    log "Bootstrap CLI Agents..."
    
    # Warten auf Backend (max 60s)
    for i in {1..60}; do
        if curl -s "$API_URL/health" >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Agents starten via API
    RESPONSE=$(curl -s -X POST "$API_URL/v1/bootstrap" \
        -H "Content-Type: application/json" \
        -d '{"sequential_lead": true}' 2>/dev/null || echo '{"error": "failed"}')
    
    if echo "$RESPONSE" | grep -q '"status"'; then
        ok "CLI Agents gebootstrapped"
        # Zeige gestartete Agents
        echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'started' in data:
        for agent in data.get('started', []):
            print(f'    → {agent}')
except: pass
" 2>/dev/null || true
    else
        warn "Agent Bootstrap fehlgeschlagen (Backend läuft trotzdem)"
    fi
}

# === HAUPTPROGRAMM ===
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          AILinux Backend v2.80 - Unified Starter           ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    cd "$BASE_DIR"
    
    # 1. Verzeichnisse
    setup_directories
    
    # 2. Redis prüfen
    check_redis || warn "Redis optional - Fortfahren..."
    
    # 3. Ollama starten
    start_ollama || warn "Ollama optional - Fortfahren..."
    
    # 4. venv aktivieren
    activate_venv
    
    # 5. Agent Bootstrap im Hintergrund (nach Backend-Start)
    (sleep 10 && bootstrap_agents) &
    
    # 6. Backend starten (exec ersetzt Shell-Prozess)
    log "Starte Backend (uvicorn)..."
    echo ""
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 9100 \
        --workers 4 \
        --log-level info \
        --no-access-log
}

# === STOP HANDLER ===
stop_services() {
    log "Stoppe Services..."
    
    # Ollama stoppen wenn wir es gestartet haben
    if [ -f "$TRISTAR_DIR/pids/ollama.pid" ]; then
        PID=$(cat "$TRISTAR_DIR/pids/ollama.pid")
        kill $PID 2>/dev/null && ok "Ollama gestoppt" || true
        rm -f "$TRISTAR_DIR/pids/ollama.pid"
    fi
    
    # CLI Agents stoppen via API
    curl -s -X POST "$API_URL/v1/cli-agents/stop-all" >/dev/null 2>&1 || true
    
    ok "Cleanup abgeschlossen"
}

trap stop_services EXIT

# Start
main "$@"
