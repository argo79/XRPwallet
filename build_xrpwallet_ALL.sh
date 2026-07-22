#!/bin/bash
# build_xrpwallet_unified.sh - Build SINGOLO eseguibile con CLI, TUI, WEB-GUI

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     📦 XRPWallet - Build Unificato                             ║"
echo "║     CLI | TUI | WEB-GUI in un unico eseguibile                 ║"
echo "║     by Arg0net                                                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# 🔧 CONFIGURAZIONE UNICA
# ============================================================

VERSION="1.1.1"                    # 🔑 VERSIONE UNICA
APP_NAME="xrpwallet-${VERSION}"    # Nome eseguibile con versione
ARCHIVE_NAME="xrpwallet-linux-${VERSION}.tar.gz"

# ============================================================
# 🎨 COLORI
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================
# 🔍 VERIFICHE
# ============================================================

# 🔑 TROVA definitions.json
DEF_FILE=$(find ~/blobspace/retWallet -name "definitions.json" 2>/dev/null | head -1)

if [ -f "$DEF_FILE" ]; then
    echo -e "${GREEN}✅ Trovato definitions.json in: $DEF_FILE${NC}"
else
    echo -e "${RED}❌ definitions.json non trovato!${NC}"
    exit 1
fi

# 🔑 VERIFICA CARTELLA LOCALES
if [ ! -d "locales" ]; then
    echo -e "${YELLOW}⚠️  Cartella locales non trovata!${NC}"
    mkdir -p locales
    echo -e "${RED}❌ Aggiungi i file JSON nella cartella locales/${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Cartella locales trovata${NC}"

# 🔑 VERIFICA CARTELLA ICONS
if [ ! -d "icons" ]; then
    echo -e "${YELLOW}⚠️  Cartella icons non trovata!${NC}"
    mkdir -p icons
    echo -e "${RED}❌ Aggiungi le icone nella cartella icons/${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Cartella icons trovata${NC}"

# ============================================================
# 🧹 PULIZIA (SOLO FILE CON LO STESSO NOME)
# ============================================================

echo -e "${YELLOW}🧹 Pulizia file con lo stesso nome...${NC}"

# Pulisci build
if [ -d "build" ]; then
    rm -rf build
    echo "   rimosso build/"
fi

# Pulisci spec file
rm -f *.spec 2>/dev/null || true

# Pulisci solo i file con lo stesso nome in dist
if [ -d "dist" ]; then
    if [ -f "dist/${APP_NAME}" ]; then
        rm -f "dist/${APP_NAME}"
        echo "   rimosso dist/${APP_NAME}"
    fi
    if [ -f "dist/${ARCHIVE_NAME}" ]; then
        rm -f "dist/${ARCHIVE_NAME}"
        echo "   rimosso dist/${ARCHIVE_NAME}"
    fi
else
    mkdir -p dist
fi

# ============================================================
# 📦 VERIFICA DIPENDENZE
# ============================================================

echo -e "${YELLOW}🔍 Verifica PyInstaller...${NC}"
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}❌ PyInstaller non trovato. Installazione...${NC}"
    pip install pyinstaller
fi

# Verifica UPX
UPX_OPTS=""
if command -v upx &> /dev/null; then
    UPX_DIR=$(which upx | sed 's/\/upx//')
    echo -e "${GREEN}✅ UPX trovato${NC}"
    UPX_OPTS="--upx-dir $UPX_DIR"
else
    echo -e "${YELLOW}⚠️  UPX non trovato${NC}"
fi

# ============================================================
# 📝 CREA PUNTO DI INGRESSO UNIFICATO
# ============================================================

echo ""
echo -e "${BLUE}📝 Creazione punto di ingresso unificato...${NC}"

cat > xrpwallet_main.py << 'EOF'
#!/usr/bin/env python3
"""
xrpwallet_main.py - Punto di ingresso unificato
Usa: xrpwallet [--cli|--tui|--web] [opzioni]
"""

import sys
import os

VERSION = "1.1.1"

def main():
    if len(sys.argv) == 1:
        print("XRPWallet - Gestione wallet XRP e XLM")
        print("")
        print("Utilizzo:")
        print("  xrpwallet --cli   [comandi]  # Interfaccia a riga di comando")
        print("  xrpwallet --tui              # Interfaccia terminale (TUI)")
        print("  xrpwallet --web              # Interfaccia web (GUI)")
        print("  xrpwallet --help             # Questo messaggio")
        print("")
        print("Esempi:")
        print("  xrpwallet --cli wallet personale")
        print("  xrpwallet --tui")
        print("  xrpwallet --web")
        sys.exit(0)
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print(f"XRPWallet v{VERSION}")
        print("by Arg0net")
        print("")
        print("Utilizzo: xrpwallet [--cli|--tui|--web] [opzioni]")
        print("")
        print("  --cli   Interfaccia a riga di comando")
        print("  --tui   Interfaccia terminale (TUI)")
        print("  --web   Interfaccia web (GUI)")
        print("  --help  Questo messaggio")
        sys.exit(0)
    
    if '--version' in sys.argv:
        print(f"XRPWallet v{VERSION}")
        sys.exit(0)
    
    if '--cli' in sys.argv:
        sys.argv.remove('--cli')
        from cli import main as cli_main
        cli_main()
    elif '--tui' in sys.argv:
        sys.argv.remove('--tui')
        from ui_cli import run_tui
        run_tui()
    elif '--web' in sys.argv:
        sys.argv.remove('--web')
        from ui_web import main as web_main
        web_main()
    else:
        from cli import main as cli_main
        cli_main()

if __name__ == "__main__":
    main()
EOF

# ============================================================
# 🔨 BUILD UNIFICATO
# ============================================================

echo ""
echo -e "${GREEN}📦 Building ${APP_NAME}...${NC}"

pyinstaller \
    --onefile \
    --name "${APP_NAME}" \
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
    --hidden-import xrpl.core.binarycodec \
    --hidden-import xrpl.core.binarycodec.definitions \
    --hidden-import mnemonic \
    --hidden-import bip32 \
    --hidden-import cryptography \
    --hidden-import ecdsa \
    --hidden-import base58 \
    --hidden-import requests \
    --collect-all flask \
    --collect-all qrcode \
    --collect-all PIL \
    --collect-all stellar_sdk \
    xrpwallet_main.py

# PULISCI FILE TEMPORANEO
rm -f xrpwallet_main.py

# ============================================================
# ✅ VERIFICA BUILD
# ============================================================

if [ -f "dist/${APP_NAME}" ]; then
    SIZE=$(du -h "dist/${APP_NAME}" | cut -f1)
    echo ""
    echo -e "${GREEN}✅ Build completata!${NC}"
    echo -e "${BLUE}📏 Dimensione: $SIZE${NC}"
    echo ""
    echo -e "${GREEN}📁 Eseguibile: dist/${APP_NAME}${NC}"
else
    echo -e "${RED}❌ Build fallita!${NC}"
    exit 1
fi

# ============================================================
# 📦 CREA ARCHIVIO
# ============================================================

echo ""
echo -e "${BLUE}📦 Creazione archivio...${NC}"
cd dist

# Rimuovi archivio vecchio se esiste
if [ -f "${ARCHIVE_NAME}" ]; then
    rm -f "${ARCHIVE_NAME}"
fi

tar -czvf "${ARCHIVE_NAME}" "${APP_NAME}"
echo -e "${GREEN}✅ ${ARCHIVE_NAME}${NC}"
cd ..

# ============================================================
# 📝 CREA SCRIPT DI INSTALLAZIONE
# ============================================================

echo ""
echo -e "${BLUE}📝 Creazione script di installazione...${NC}"
cat > dist/install.sh << 'EOF'
#!/bin/bash
# install.sh - Installer XRPWallet
echo "🚀 Installazione XRPWallet..."
echo "============================="
if [ -f "xrpwallet-1.1.0" ]; then
    sudo cp xrpwallet-1.1.0 /usr/local/bin/xrpwallet
    sudo chmod +x /usr/local/bin/xrpwallet
    echo "✅ Installato /usr/local/bin/xrpwallet"
    echo ""
    echo "💡 Per eseguire:"
    echo "  xrpwallet --cli   # CLI"
    echo "  xrpwallet --tui   # TUI"
    echo "  xrpwallet --web   # WEB-GUI"
    echo "  xrpwallet --help  # Help"
else
    echo "❌ File xrpwallet-1.1.0 non trovato!"
    exit 1
fi
echo ""
echo "🎉 Installazione completata!"
EOF
chmod +x dist/install.sh

# ============================================================
# 📊 RIEPILOGO
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  ✅ BUILD COMPLETATO!                                           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}📁 dist/${APP_NAME} (${SIZE})${NC}"
echo -e "${GREEN}📁 dist/${ARCHIVE_NAME}${NC}"
echo ""
echo -e "${YELLOW}💡 Per testare:${NC}"
echo "  ./dist/${APP_NAME} --web"
echo "  ./dist/${APP_NAME} --tui"
echo "  ./dist/${APP_NAME} --cli help"
echo ""
echo -e "${GREEN}🚀 Distribuisci: dist/${ARCHIVE_NAME}${NC}"