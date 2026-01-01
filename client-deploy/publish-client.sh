#!/bin/bash
# ============================================================================
# AILinux Client Publisher
# Builds client, creates .deb, publishes to update.ailinux.me
# Usage: ./publish-client.sh [--bump-patch|--bump-minor|--bump-major]
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_DIR="$SCRIPT_DIR/ailinux-client"
UPDATE_DIR="/var/www/update.ailinux.me/client"
RELEASES_DIR="$UPDATE_DIR/releases"

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}>>>${NC} $1"; }

# Run existing release script
log "Building client..."
cd "$SCRIPT_DIR"
./release.sh "$@"

# Find latest built deb
LATEST_DEB=$(ls -t "$SCRIPT_DIR"/ailinux-client_*_amd64.deb 2>/dev/null | head -1)
if [ -z "$LATEST_DEB" ]; then
    echo "❌ No .deb file found!"
    exit 1
fi

# Get version from filename
VERSION=$(basename "$LATEST_DEB" | sed 's/ailinux-client_\(.*\)_amd64.deb/\1/')

log "Publishing v$VERSION to update.ailinux.me..."

# Copy to releases directory
mkdir -p "$RELEASES_DIR"
cp "$LATEST_DEB" "$RELEASES_DIR/"
DEB_NAME=$(basename "$LATEST_DEB")

# Generate checksum
CHECKSUM=$(sha256sum "$RELEASES_DIR/$DEB_NAME" | cut -d' ' -f1)
echo "$CHECKSUM" > "$RELEASES_DIR/${DEB_NAME}.sha256"

# Update current symlink
ln -sf "$RELEASES_DIR/$DEB_NAME" "$UPDATE_DIR/current/ailinux-client-latest.deb"

# Generate client manifest
cat > "$UPDATE_DIR/manifest.json" << EOF
{
  "version": "$VERSION",
  "checksum": "$CHECKSUM",
  "release_date": "$(date +%Y-%m-%d)",
  "timestamp": "$(date -Iseconds)",
  "download_url": "https://update.ailinux.me/client/releases/$DEB_NAME",
  "changelog_url": "https://update.ailinux.me/client/releases/${VERSION}.changelog",
  "filename": "$DEB_NAME"
}
EOF

# Copy changelog if exists
if [ -f "$CLIENT_DIR/CHANGELOG.md" ]; then
    cp "$CLIENT_DIR/CHANGELOG.md" "$RELEASES_DIR/${VERSION}.changelog"
fi

log "✅ Client published!"
echo ""
echo "Version:  $VERSION"
echo "Checksum: $CHECKSUM"
echo "Manifest: https://update.ailinux.me/client/manifest.json"
echo "Download: https://update.ailinux.me/client/releases/$DEB_NAME"
