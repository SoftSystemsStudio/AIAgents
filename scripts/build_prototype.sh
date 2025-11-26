#!/usr/bin/env bash
set -euo pipefail

# Simple build script for the prototype site.
OUT_DIR="build_prototype"
SOURCE_DIR="website_prototype"
mkdir -p "$OUT_DIR"

# Copy static files
cp "$SOURCE_DIR"/*.html "$OUT_DIR/"
cp "$SOURCE_DIR"/*.css "$OUT_DIR/" || true

cat > "$OUT_DIR/config.js" << 'EOF'
// Minimal config for prototype
window.APP_CONFIG = {};
EOF

echo "✅ Prototype build complete. Output in $OUT_DIR/"
