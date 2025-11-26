#!/usr/bin/env bash
set -euo pipefail

# Simple image optimization wrapper that uses npx imagemin-cli and svgo
# Useful for local runs and for pre-commit hooks.

echo "Optimizing images in assets/..."
if command -v npx >/dev/null 2>&1; then
  npx -y svgo "assets/*.svg" || true
  npx -y imagemin-cli "assets/*.{png,jpg,jpeg,gif,svg}" --out-dir=assets/ || true
  echo "Optimization complete"
else
  echo "npx not found; please install Node.js to run image optimization"
  exit 0
fi
