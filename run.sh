#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export QT_QPA_PLATFORM=xcb
export QT_PLUGIN_PATH="$SCRIPT_DIR/dist"
if [ -f "dist/xrpwallet-desktop" ]; then
    ./dist/xrpwallet-desktop "$@"
else
    echo "❌ Eseguibile non trovato!"
    exit 1
fi
