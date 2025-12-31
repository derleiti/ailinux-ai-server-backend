# TriForce Client Setup Guide

Installation und Konfiguration der AILinux/AIWindows Clients.

---

## Übersicht

| Client | OS | Download |
|--------|------|----------|
| AILinux Client | Linux (Debian/Ubuntu/Arch) | .deb, AUR |
| AIWindows Client | Windows 10+ | .exe Installer |

---

## AILinux Client

### Option 1: APT Repository

```bash
# GPG Key
curl -fsSL https://repo.ailinux.me/gpg | sudo gpg --dearmor -o /usr/share/keyrings/ailinux.gpg

# Repository
echo "deb [signed-by=/usr/share/keyrings/ailinux.gpg] https://repo.ailinux.me/apt stable main" | \
  sudo tee /etc/apt/sources.list.d/ailinux.list

# Installieren
sudo apt update
sudo apt install ailinux-client
```

### Option 2: Direkter Download

```bash
# .deb Paket
wget https://repo.ailinux.me/pool/main/ailinux-client_4.2.0_amd64.deb
sudo dpkg -i ailinux-client_4.2.0_amd64.deb
sudo apt install -f  # Abhängigkeiten
```

### Option 3: Arch Linux (AUR)

```bash
yay -S ailinux-client
# oder
paru -S ailinux-client
```

### Option 4: AppImage

```bash
wget https://repo.ailinux.me/releases/AILinux-Client-4.2.0.AppImage
chmod +x AILinux-Client-4.2.0.AppImage
./AILinux-Client-4.2.0.AppImage
```

---

## AIWindows Client

### Installation

1. Download: https://github.com/derleiti/aiwindows-client/releases
2. `AILinux-Setup.exe` ausführen
3. Installationsassistent folgen
4. Optional: Autostart aktivieren

### Portable Version

```
AILinux-Portable.zip
└── Entpacken und AILinux.exe starten
```

---

## Erste Konfiguration

### 1. Starten

```bash
# Linux
ailinux-client

# Oder mit Terminal-Modus
ailinux-client --cli
```

### 2. Login/Registrierung

- Menü → Einstellungen → Account
- Email + Passwort eingeben
- Oder: API-Token direkt eintragen

### 3. Server konfigurieren

**Standard (AILinux.me):**
```
API URL: https://api.ailinux.me
```

**Eigener Hub:**
```
API URL: https://api.yourdomain.com
```

---

## Konfigurationsdatei

### Linux

```
~/.config/ailinux-client/config.json
```

### Windows

```
%APPDATA%\AILinux\config.json
```

### Beispiel

```json
{
  "api_url": "https://api.ailinux.me",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "default_model": "gemini/gemini-2.0-flash",
  "theme": "dark",
  "font_size": 14,
  "stream": true,
  "save_history": true,
  "history_path": "~/.local/share/ailinux-client/history"
}
```

---

## Tastenkürzel

| Kürzel | Aktion |
|--------|--------|
| `Ctrl+Enter` | Nachricht senden |
| `Ctrl+N` | Neuer Chat |
| `Ctrl+M` | Modell wechseln |
| `Ctrl+,` | Einstellungen |
| `Ctrl+L` | Chat leeren |
| `Ctrl+S` | Chat speichern |
| `Ctrl+O` | Chat laden |
| `Ctrl+Q` | Beenden |
| `F11` | Vollbild |
| `Ctrl+Plus` | Schrift größer |
| `Ctrl+Minus` | Schrift kleiner |

---

## CLI-Modus

```bash
# Interaktiv
ailinux-client --cli

# Einmaliger Prompt
ailinux-client --prompt "Was ist 2+2?"

# Mit spezifischem Modell
ailinux-client --model "anthropic/claude-sonnet-4" --prompt "Erkläre Rekursion"

# Pipe-Modus
echo "Erkläre Docker" | ailinux-client --pipe

# Output als JSON
ailinux-client --json --prompt "Liste 5 Programmiersprachen"
```

---

## Modelle wechseln

### Im Client

1. Dropdown oben rechts
2. Oder `Ctrl+M`
3. Modell auswählen

### Verfügbare Modelle (Tier-abhängig)

**Free:**
- gemini/gemini-2.0-flash
- groq/llama-3.3-70b
- cerebras/llama-3.3-70b
- ollama/* (alle lokalen)

**Pro (€17.99/mo):**
- Alle Free-Modelle
- anthropic/claude-sonnet-4
- mistral/mistral-large
- 640+ weitere

**Unlimited (€59.99/mo):**
- Alles unbegrenzt

---

## Lokale Modelle (Ollama)

Wenn der Hub Ollama hat:

```bash
# Verfügbare lokale Modelle
ailinux-client --list-ollama

# Lokales Modell nutzen
ailinux-client --model "ollama/llama3.2:3b" --prompt "Hallo"
```

---

## Themes

### Verfügbare Themes

- `dark` (Standard)
- `light`
- `solarized`
- `dracula`
- `nord`

### Wechseln

```bash
# Config bearbeiten
nano ~/.config/ailinux-client/config.json
# "theme": "dracula"
```

---

## Updates

### Linux (APT)

```bash
sudo apt update
sudo apt upgrade ailinux-client
```

### Linux (AUR)

```bash
yay -Syu ailinux-client
```

### Windows

- Automatische Update-Benachrichtigung
- Oder: Neue Version herunterladen

---

## Troubleshooting

### Client startet nicht

```bash
# Linux: Logs prüfen
ailinux-client --debug

# Abhängigkeiten prüfen
ldd $(which ailinux-client)
```

### Verbindungsfehler

```bash
# API erreichbar?
curl https://api.ailinux.me/health

# Token gültig?
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.ailinux.me/v1/client/profile
```

### Konfiguration zurücksetzen

```bash
# Linux
rm -rf ~/.config/ailinux-client
rm -rf ~/.local/share/ailinux-client

# Windows
rmdir /s %APPDATA%\AILinux
```

---

## Deinstallation

### Linux (APT)

```bash
sudo apt remove ailinux-client
sudo apt autoremove
```

### Linux (AUR)

```bash
yay -R ailinux-client
```

### Windows

- Systemsteuerung → Programme → AILinux deinstallieren

---

## Nächste Schritte

- [Quickstart](../QUICKSTART.md)
- [API Referenz](../api/REST.md)
- [MCP Tools](../api/MCP.md)
