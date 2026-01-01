#!/bin/bash
#===============================================================================
# TriForce VPN Gateway Failover
# Automatisches Umschalten wenn ein Gateway ausfällt
# Installieren: systemctl enable --now triforce-gateway-failover.timer
#===============================================================================

GATEWAYS="10.10.0.1 10.10.0.3 10.10.0.2"  # Hetzner, Backup, Zombie-PC
CURRENT_GW_FILE="/var/run/triforce-gateway"
LOG="/var/log/triforce-gateway.log"
CHECK_IP="1.1.1.1"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> $LOG
    echo "$1"
}

get_current_gw() {
    cat $CURRENT_GW_FILE 2>/dev/null || echo ""
}

set_gateway() {
    local gw=$1
    
    # Entferne alte Default-Route in vpngw table
    ip route del default table vpngw 2>/dev/null
    
    # Setze neue Default-Route
    ip route add default via $gw dev wg0 table vpngw
    
    # Speichere aktiven Gateway
    echo $gw > $CURRENT_GW_FILE
    
    log "✅ Gateway switched to $gw"
}

check_gateway() {
    local gw=$1
    
    # Temporär Route setzen
    ip route replace $CHECK_IP via $gw dev wg0 2>/dev/null
    
    # Ping test
    if ping -c 1 -W 2 $CHECK_IP &>/dev/null; then
        ip route del $CHECK_IP via $gw dev wg0 2>/dev/null
        return 0
    else
        ip route del $CHECK_IP via $gw dev wg0 2>/dev/null
        return 1
    fi
}

find_working_gateway() {
    for gw in $GATEWAYS; do
        if check_gateway $gw; then
            echo $gw
            return 0
        fi
    done
    return 1
}

#--- MAIN ---

# Aktueller Gateway
CURRENT=$(get_current_gw)

# Prüfe ob aktueller Gateway noch funktioniert
if [ -n "$CURRENT" ]; then
    if check_gateway $CURRENT; then
        # Alles OK
        exit 0
    else
        log "⚠️ Gateway $CURRENT down!"
    fi
fi

# Finde funktionierenden Gateway
NEW_GW=$(find_working_gateway)

if [ -n "$NEW_GW" ]; then
    if [ "$NEW_GW" != "$CURRENT" ]; then
        set_gateway $NEW_GW
    fi
else
    log "❌ ALL GATEWAYS DOWN!"
    exit 1
fi
