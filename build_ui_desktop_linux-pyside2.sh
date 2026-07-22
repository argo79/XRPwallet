#!/bin/bash
# build_standalone.sh - Build con traduzioni

set -e

echo "📦 BUILD STANDALONE CON TRADUZIONI"
echo "=================================="

# 🧹 Pulisci
rm -rf build/ dist/ *.spec

# 🔑 Trova definitions.json
DEF_FILE=$(find ~/blobspace/retWallet -name "definitions.json" 2>/dev/null | head -1)
if [ ! -f "$DEF_FILE" ]; then
    echo "❌ definitions.json non trovato!"
    exit 1
fi
echo "✅ definitions.json: $DEF_FILE"

# 🔧 Verifica che locales esista
if [ ! -d "locales" ]; then
    echo "❌ Cartella locales non trovata!"
    echo "   Crea la cartella e aggiungi i file JSON"
    exit 1
fi

echo "✅ Cartella locales trovata:"
ls -la locales/

# 🔧 Trova UPX
UPX_OPTS=""
if command -v upx &> /dev/null; then
    UPX_DIR=$(which upx | sed 's/\/upx//')
    echo "✅ UPX trovato"
    UPX_OPTS="--upx-dir $UPX_DIR"
fi

# 🔨 PyInstaller CON locales
pyinstaller \
    --onefile \
    --name "xrpwallet-desktop" \
    --strip \
    $UPX_OPTS \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --exclude-module pandas \
    --exclude-module numpy \
    --exclude-module scipy \
    --exclude-module PIL \
    --exclude-module Pillow \
    --exclude-module IPython \
    --exclude-module jupyter \
    --exclude-module notebook \
    --exclude-module test \
    --exclude-module tests \
    --exclude-module unittest \
    --exclude-module distutils \
    --exclude-module setuptools \
    --exclude-module wheel \
    --exclude-module pip \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "commands:commands" \
    --add-data "utils:utils" \
    --add-data "locales:locales" \
    --add-data "ui_web.py:." \
    --add-data "wallet_manager.py:." \
    --add-data "cli.py:." \
    --add-data "ui_cli.py:." \
    --add-data "$DEF_FILE:xrpl/core/binarycodec/definitions" \
    --hidden-import flask \
    --hidden-import qrcode \
    --hidden-import PySide6 \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtWidgets \
    --hidden-import PySide6.QtWebEngineWidgets \
    --hidden-import PySide6.QtWebEngineCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtNetwork \
    --hidden-import stellar_sdk \
    --hidden-import xrpl \
    --collect-all flask \
    --collect-all stellar_sdk \
    --collect-all xrpl \
    ui_desktop.py

# ✅ Verifica
if [ -f "dist/xrpwallet-desktop" ]; then
    SIZE=$(du -h dist/xrpwallet-desktop | cut -f1)
    echo ""
    echo "✅ BUILD COMPLETATA!"
    echo "📏 Dimensione: $SIZE"
    echo ""
    echo "📂 locales inclusi:"
    ls -la dist/xrpwallet-desktop 2>/dev/null || echo "  Eseguibile creato"
    echo ""
    echo "🚀 Esegui: ./dist/xrpwallet-desktop"
else
    echo "❌ Build fallita!"
    exit 1
fi