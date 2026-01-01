#!/bin/bash
# ============================================================================
# TriForce Release Creator
# Packages current code into a versioned release tarball
# ============================================================================

set -e

TRIFORCE_DIR="/home/zombie/triforce"
UPDATE_DIR="/var/www/update.ailinux.me"
RELEASES_DIR="$UPDATE_DIR/releases"

# Get version
VERSION="${1:-$(cat $TRIFORCE_DIR/VERSION 2>/dev/null || echo "2.80.$(date +%Y%m%d%H%M)")}"
RELEASE_FILE="$RELEASES_DIR/$VERSION.tar.gz"

echo "=== Creating TriForce Release $VERSION ==="

# Ensure directories exist
mkdir -p "$RELEASES_DIR"

# Create tarball with essential directories
cd "$TRIFORCE_DIR"
tar -czf "$RELEASE_FILE" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='logs/*' \
    --exclude='*.log' \
    --exclude='.venv' \
    --exclude='node_modules' \
    --exclude='*.bak*' \
    --exclude='specs/tla/states' \
    app/ \
    config/ \
    scripts/ \
    VERSION \
    requirements.txt

# Generate checksum
sha256sum "$RELEASE_FILE" | cut -d' ' -f1 > "$RELEASES_DIR/$VERSION.sha256"

# Generate changelog from recent commits
cd "$TRIFORCE_DIR"
git log --oneline -20 > "$RELEASES_DIR/$VERSION.changelog" 2>/dev/null || echo "No git history" > "$RELEASES_DIR/$VERSION.changelog"

# Update current symlink
ln -sf "$RELEASE_FILE" "$UPDATE_DIR/current/triforce-latest.tar.gz"
ln -sf "$RELEASES_DIR/$VERSION.sha256" "$UPDATE_DIR/current/triforce-latest.sha256"

# Generate manifest
$TRIFORCE_DIR/scripts/generate-update-manifest.sh

echo "✅ Release created: $RELEASE_FILE"
echo "   Size: $(du -h "$RELEASE_FILE" | cut -f1)"
echo "   SHA256: $(cat "$RELEASES_DIR/$VERSION.sha256")"
echo ""
echo "Files:"
echo "  - $RELEASE_FILE"
echo "  - $RELEASES_DIR/$VERSION.sha256"
echo "  - $RELEASES_DIR/$VERSION.changelog"
echo "  - $UPDATE_DIR/manifest.json"
