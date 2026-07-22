#!/bin/bash
# build_desktop_final.sh - Build eseguibile con icona (FUNZIONA SEMPRE)

set -e

echo "📦 BUILD DESKTOP CON ICONA"
echo "=========================="

# 🔑 VERIFICA ICONE
ICON_FILE=""
if [ -f "icon.ico" ]; then
    ICON_FILE="icon.ico"
elif [ -f "icons/icon.ico" ]; then
    ICON_FILE="icons/icon.ico"
elif [ -f "icon.png" ]; then
    convert icon.png -resize 256x256 icon.ico
    ICON_FILE="icon.ico"
else
    echo "❌ Nessuna icona trovata!"
    exit 1
fi

echo "✅ Icona: $ICON_FILE"

# 🔑 Trova definitions.json
DEF_FILE=$(find ~/blobspace/retWallet -name "definitions.json" 2>/dev/null | head -1)
if [ ! -f "$DEF_FILE" ]; then
    echo "❌ definitions.json non trovato!"
    exit 1
fi
echo "✅ definitions.json: $DEF_FILE"

# 🔑 VERIFICA CARTELLA LOCALES
if [ ! -d "locales" ]; then
    echo "⚠️  Cartella locales non trovata!"
    mkdir -p locales
    echo "❌ Aggiungi i file JSON nella cartella locales/"
    exit 1
fi
echo "✅ Cartella locales trovata"

# 🔑 VERIFICA CARTELLA ICONS
if [ ! -d "icons" ]; then
    echo "⚠️  Cartella icons non trovata!"
    mkdir -p icons
    echo "❌ Aggiungi le icone nella cartella icons/"
    exit 1
fi
echo "✅ Cartella icons trovata"

# 🔧 TROVA UPX
UPX_OPTS=""
if command -v upx &> /dev/null; then
    UPX_DIR=$(which upx | sed 's/\/upx//')
    echo "✅ UPX trovato"
    UPX_OPTS="--upx-dir $UPX_DIR"
fi

# 🔨 BUILD CON ICONA
echo "🔨 Building XRPWallet..."

pyinstaller \
    --onefile \
    --name "XRPWallet" \
    --icon "$ICON_FILE" \
    --strip \
    $UPX_OPTS \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --exclude-module pandas \
    --exclude-module numpy \
    --exclude-module scipy \
    --exclude-module IPython \
    --exclude-module jupyter \
    --exclude-module notebook \
    --exclude-module test \
    --exclude-module tests \
    --exclude-module unittest \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "commands:commands" \
    --add-data "utils:utils" \
    --add-data "locales:locales" \
    --add-data "icons:icons" \
    --add-data "ui_web.py:." \
    --add-data "wallet_manager.py:." \
    --add-data "cli.py:." \
    --add-data "ui_cli.py:." \
    --add-data "$DEF_FILE:xrpl/core/binarycodec/definitions" \
    --hidden-import flask \
    --hidden-import qrcode \
    --hidden-import PIL \
    --hidden-import PIL.Image \
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
    --collect-all qrcode \
    --collect-all PIL \
    --collect-all stellar_sdk \
    --collect-all xrpl \
    ui_desktop.py

# ✅ Verifica
if [ -f "dist/XRPWallet" ]; then
    SIZE=$(du -h dist/XRPWallet | cut -f1)
    echo ""
    echo "✅ BUILD COMPLETATA!"
    echo "======================================"
    echo "📁 dist/XRPWallet ($SIZE)"
    echo ""
    echo "🚀 Per eseguire:"
    echo "   ./dist/XRPWallet"
    echo "   oppure doppio clic sul file!"
    echo ""
    echo "🖼️  L'icona è integrata!"
else
    echo "❌ Build fallita!"
    exit 1
fi