#!/bin/bash
# build_all.sh - Compila XRPWallet per Linux, Windows e Mac

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     📦 XRPWallet - Build Multi-Piattaforma                      ║"
echo "║     by Arg0net                                                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Versione
VERSION="1.0.0"

# 🔑 TROVA definitions.json
DEF_FILE=$(find ~/blobspace/retWallet/xrp_env_311 -name "definitions.json" 2>/dev/null | head -1)

if [ -f "$DEF_FILE" ]; then
    echo -e "${GREEN}✅ Trovato definitions.json in: $DEF_FILE${NC}"
else
    echo -e "${RED}❌ definitions.json non trovato!${NC}"
    echo -e "${YELLOW}⚠️  Provo a cercare in tutto il sistema...${NC}"
    DEF_FILE=$(find / -name "definitions.json" 2>/dev/null | grep -E "xrpl.*definitions.json" | head -1)
    if [ -f "$DEF_FILE" ]; then
        echo -e "${GREEN}✅ Trovato definitions.json in: $DEF_FILE${NC}"
    else
        echo -e "${RED}❌ definitions.json non trovato! Impossibile continuare.${NC}"
        exit 1
    fi
fi

# 1. Pulisci build precedenti
echo -e "${YELLOW}🧹 Pulizia build precedenti...${NC}"
rm -rf build/ dist/ *.spec
mkdir -p dist

# 2. Verifica PyInstaller
echo -e "${YELLOW}🔍 Verifica PyInstaller...${NC}"
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}❌ PyInstaller non trovato. Installazione...${NC}"
    pip install pyinstaller
fi

# 3. Crea i file di build per ogni piattaforma
echo -e "${BLUE}📝 Preparazione build...${NC}"

# 3a. File spec per Linux
cat > xrpwallet-linux.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['xrpwallet_cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('commands', 'commands'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'flask', 'qrcode', 'stellar_sdk', 'stellar_sdk.sep', 'stellar_sdk.sep.mnemonic',
        'xrpl', 'xrpl.clients', 'xrpl.account', 'xrpl.transaction', 'xrpl.models',
        'xrpl.wallet', 'xrpl.core', 'xrpl.core.keypairs', 'xrpl.core.binarycodec',
        'xrpl.core.binarycodec.definitions', 'mnemonic', 'bip32',
        'cryptography', 'ecdsa', 'base58', 'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyd,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='xrpwallet-linux',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

# 3b. File spec per Windows
cat > xrpwallet-windows.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['xrpwallet_cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('commands', 'commands'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'flask', 'qrcode', 'stellar_sdk', 'stellar_sdk.sep', 'stellar_sdk.sep.mnemonic',
        'xrpl', 'xrpl.clients', 'xrpl.account', 'xrpl.transaction', 'xrpl.models',
        'xrpl.wallet', 'xrpl.core', 'xrpl.core.keypairs', 'xrpl.core.binarycodec',
        'xrpl.core.binarycodec.definitions', 'mnemonic', 'bip32',
        'cryptography', 'ecdsa', 'base58', 'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyd,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='xrpwallet-windows.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

# 3c. File spec per Mac
cat > xrpwallet-mac.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['xrpwallet_cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('commands', 'commands'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'flask', 'qrcode', 'stellar_sdk', 'stellar_sdk.sep', 'stellar_sdk.sep.mnemonic',
        'xrpl', 'xrpl.clients', 'xrpl.account', 'xrpl.transaction', 'xrpl.models',
        'xrpl.wallet', 'xrpl.core', 'xrpl.core.keypairs', 'xrpl.core.binarycodec',
        'xrpl.core.binarycodec.definitions', 'mnemonic', 'bip32',
        'cryptography', 'ecdsa', 'base58', 'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyd,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='xrpwallet-mac',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

# 4. Build per Linux
echo ""
echo -e "${GREEN}🐧 Build per Linux...${NC}"
pyinstaller --onefile \
    --name xrpwallet-linux \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "commands:commands" \
    --add-data "utils:utils" \
    --add-data "node_modules:node_modules" \
    --add-data "$DEF_FILE:xrpl/core/binarycodec/definitions" \
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
    --hidden-import xrpl.core.binarycodec \
    --hidden-import xrpl.core.binarycodec.definitions \
    --hidden-import mnemonic \
    --hidden-import bip32 \
    --hidden-import cryptography \
    --hidden-import ecdsa \
    --hidden-import base58 \
    --hidden-import requests \
    --collect-all flask \
    --collect-all stellar_sdk \
    xrpwallet_cli.py

# 5. Rinomina per Linux
if [ -f "dist/xrpwallet-linux" ]; then
    echo -e "${GREEN}✅ Linux build completato!${NC}"
    # Crea un link simbolico per comodità
    ln -sf xrpwallet-linux dist/xrpwallet
else
    echo -e "${RED}❌ Linux build fallito!${NC}"
fi

# 6. Build per Windows (se siamo su Windows o con Wine)
echo ""
echo -e "${YELLOW}🪟 Build per Windows...${NC}"
echo -e "${YELLOW}   (Richiede Windows o Wine per compilare)${NC}"

# Verifica se siamo su Windows
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo -e "${BLUE}🪟 Rilevato Windows, compilazione in corso...${NC}"
    pyinstaller --onefile \
        --name xrpwallet-windows.exe \
        --add-data "templates;templates" \
        --add-data "static;static" \
        --add-data "commands;commands" \
        --add-data "utils;utils" \
        --add-data "$DEF_FILE;xrpl/core/binarycodec/definitions" \
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
        --hidden-import xrpl.core.binarycodec \
        --hidden-import xrpl.core.binarycodec.definitions \
        --hidden-import mnemonic \
        --hidden-import bip32 \
        --hidden-import cryptography \
        --hidden-import ecdsa \
        --hidden-import base58 \
        --hidden-import requests \
        --collect-all flask \
        --collect-all stellar_sdk \
        xrpwallet_cli.py
    
    if [ -f "dist/xrpwallet-windows.exe" ]; then
        echo -e "${GREEN}✅ Windows build completato!${NC}"
    fi
else
    # Crea uno stub per Windows (sarà compilato su Windows)
    echo -e "${YELLOW}⚠️  Non sei su Windows. Per compilare per Windows:${NC}"
    echo -e "${YELLOW}   1. Avvia Windows VM${NC}"
    echo -e "${YELLOW}   2. Esegui questo script su Windows${NC}"
    echo -e "${YELLOW}   3. Oppure usa il file xrpwallet-windows.spec${NC}"
    
    # Copia il file spec per Windows
    cp xrpwallet-windows.spec dist/
    echo -e "${GREEN}📁 File spec per Windows salvato in: dist/xrpwallet-windows.spec${NC}"
fi

# 7. Build per Mac (se siamo su Mac)
echo ""
echo -e "${YELLOW}🍎 Build per MacOS...${NC}"
echo -e "${YELLOW}   (Richiede MacOS per compilare)${NC}"

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}🍎 Rilevato MacOS, compilazione in corso...${NC}"
    pyinstaller --onefile \
        --name xrpwallet-mac \
        --add-data "templates:templates" \
        --add-data "static:static" \
        --add-data "commands:commands" \
        --add-data "utils:utils" \
        --add-data "$DEF_FILE:xrpl/core/binarycodec/definitions" \
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
        --hidden-import xrpl.core.binarycodec \
        --hidden-import xrpl.core.binarycodec.definitions \
        --hidden-import mnemonic \
        --hidden-import bip32 \
        --hidden-import cryptography \
        --hidden-import ecdsa \
        --hidden-import base58 \
        --hidden-import requests \
        --collect-all flask \
        --collect-all stellar_sdk \
        xrpwallet_cli.py
    
    if [ -f "dist/xrpwallet-mac" ]; then
        echo -e "${GREEN}✅ MacOS build completato!${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Non sei su MacOS. Per compilare per Mac:${NC}"
    echo -e "${YELLOW}   1. Avvia Mac VM${NC}"
    echo -e "${YELLOW}   2. Esegui questo script su Mac${NC}"
    echo -e "${YELLOW}   3. Oppure usa il file xrpwallet-mac.spec${NC}"
    
    cp xrpwallet-mac.spec dist/
    echo -e "${GREEN}📁 File spec per Mac salvato in: dist/xrpwallet-mac.spec${NC}"
fi

# 8. Crea archivi per distribuzione
echo ""
echo -e "${BLUE}📦 Creazione archivi per distribuzione...${NC}"

cd dist

# Linux
if [ -f "xrpwallet-linux" ]; then
    tar -czvf xrpwallet-linux-${VERSION}.tar.gz xrpwallet-linux
    echo -e "${GREEN}✅ xrpwallet-linux-${VERSION}.tar.gz${NC}"
fi

# Windows
if [ -f "xrpwallet-windows.exe" ]; then
    zip xrpwallet-windows-${VERSION}.zip xrpwallet-windows.exe
    echo -e "${GREEN}✅ xrpwallet-windows-${VERSION}.zip${NC}"
fi

# Mac
if [ -f "xrpwallet-mac" ]; then
    tar -czvf xrpwallet-mac-${VERSION}.tar.gz xrpwallet-mac
    echo -e "${GREEN}✅ xrpwallet-mac-${VERSION}.tar.gz${NC}"
fi

cd ..

# 9. Riepilogo
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  ✅ BUILD COMPLETATO!                                           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}📁 File disponibili in: dist/${NC}"
echo ""
echo -e "${BLUE}🐧 Linux:${NC}"
echo "   dist/xrpwallet-linux"
echo "   dist/xrpwallet-linux-${VERSION}.tar.gz"
echo ""
echo -e "${BLUE}🪟 Windows:${NC}"
echo "   dist/xrpwallet-windows.exe"
echo "   dist/xrpwallet-windows-${VERSION}.zip"
echo ""
echo -e "${BLUE}🍎 MacOS:${NC}"
echo "   dist/xrpwallet-mac"
echo "   dist/xrpwallet-mac-${VERSION}.tar.gz"
echo ""
echo -e "${YELLOW}💡 Per eseguire:${NC}"
echo "   ./dist/xrpwallet-linux       # CLI (default)"
echo "   ./dist/xrpwallet-linux --tui # TUI"
echo "   ./dist/xrpwallet-linux --gui # Web"
echo "   ./dist/xrpwallet-linux --version"
echo ""
echo -e "${GREEN}🚀 Distribuisci i file nella cartella dist/${NC}"