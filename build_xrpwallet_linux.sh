#!/bin/bash
# build_linux.sh - Crea eseguibile per Linux

echo "========================================="
echo "📦 Creazione eseguibile XRPWallet per Linux"
echo "========================================="

# 1. Pulisci build precedenti
echo ""
echo "🧹 Pulizia build precedenti..."
rm -rf build/ dist/ *.spec

# 2. Crea l'eseguibile
echo ""
echo "🔨 Compilazione in corso (potrebbe richiedere qualche minuto)..."
echo ""

pyinstaller --onefile \
    --name xrpwallet \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "commands:commands" \
    --add-data "utils:utils" \
    --hidden-import flask \
    --hidden-import qrcode \
    --hidden-import stellar_sdk \
    --hidden-import stellar_sdk.sep \
    --hidden-import stellar_sdk.sep.mnemonic \
    --hidden-import xrpl \
    --hidden-import xrpl.clients \
    --hidden-import xrpl.account \
    --hidden-import xrpl.transaction \
    --hidden-import xrpl.models \
    --hidden-import xrpl.wallet \
    --hidden-import xrpl.core \
    --hidden-import xrpl.core.keypairs \
    --hidden-import mnemonic \
    --hidden-import bip32 \
    --hidden-import cryptography \
    --hidden-import ecdsa \
    --hidden-import base58 \
    --hidden-import requests \
    --collect-all flask \
    --collect-all stellar_sdk \
    xrpwallet_cli.py

# 3. Verifica
echo ""
echo "========================================="
if [ -f "dist/xrpwallet" ]; then
    echo "✅ Eseguibile creato con successo!"
    echo ""
    echo "📁 Posizione: dist/xrpwallet"
    echo "📏 Dimensione: $(du -h dist/xrpwallet | cut -f1)"
    echo ""
    echo "🚀 Per eseguire:"
    echo "   ./dist/xrpwallet"
    echo "   ./dist/xrpwallet --tui"
    echo "   ./dist/xrpwallet --gui"
else
    echo "❌ Errore: eseguibile non trovato!"
fi
echo "========================================="