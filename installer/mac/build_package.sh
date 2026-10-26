#!/bin/bash
# Assemble SmartTrapper_Mac.zip. Usage: build_package.sh <dir with smart_trapper_b1 + smart_trapper_helper> <out dir>
# Run by .github/workflows/mac_package.yml on a GitHub Mac; also works on any Mac with python3 + zip.
set -euo pipefail
BIN="$1"; OUT="$2"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PKG="$OUT/Smart Trapper Installer"
rm -rf "$PKG"; mkdir -p "$PKG/payload"
cp "$ROOT/installer/mac/Install Smart Trapper.command" "$ROOT/installer/mac/Uninstall Smart Trapper.command" "$ROOT/installer/mac/READ ME FIRST.txt" "$PKG/"
chmod +x "$PKG/"*.command
cp "$BIN/smart_trapper_b1" "$BIN/smart_trapper_helper" "$PKG/payload/"
# The co-worker's panel = Sara's panel with the shared-copy switches (tools/dev/make_shared_copy.py)
python3 "$ROOT/tools/dev/make_shared_copy.py" "$OUT/plugin"
rm -f "$OUT/plugin/real_bridge.py"                  # the Mac uses smart_trapper_helper instead
( cd "$OUT/plugin" && rm -f "$PKG/payload/SmartTrapper.ccx" && zip -q -X -r "$PKG/payload/SmartTrapper.ccx" manifest.json index.html styles.css main.js )
{ echo "Smart Trapper Mac package"; echo "built: $(date -u +%Y-%m-%dT%H:%MZ)"; echo "commit: ${GITHUB_SHA:-$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)}"; } > "$PKG/payload/VERSION.txt"
( cd "$OUT" && rm -f SmartTrapper_Mac.zip && ditto -c -k --keepParent "Smart Trapper Installer" SmartTrapper_Mac.zip 2>/dev/null || zip -q -r SmartTrapper_Mac.zip "Smart Trapper Installer" )
echo "Built $OUT/SmartTrapper_Mac.zip"
