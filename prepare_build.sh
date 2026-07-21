#!/bin/bash
# prepare_build.sh - Prepara tutto per il build (Node.js + dipendenze)

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     🔧 PREPARAZIONE BUILD XRPWallet                            ║"
echo "║     by Arg0net                                                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Verifica Node.js
echo -e "${BLUE}🔍 Verifica Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js non trovato!${NC}"
    echo -e "${YELLOW}📦 Installazione Node.js...${NC}"
    
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js trovato: ${NODE_VERSION}${NC}"
else
    echo -e "${RED}❌ Node.js non installato!${NC}"
    exit 1
fi

# 2. Verifica npm
echo ""
echo -e "${BLUE}🔍 Verifica npm...${NC}"
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm non trovato!${NC}"
    echo -e "${YELLOW}📦 Installazione npm...${NC}"
    sudo apt-get install -y npm
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm trovato: ${NPM_VERSION}${NC}"
fi

# 3. Crea struttura node_bundle
echo ""
echo -e "${BLUE}📁 Creazione struttura node_bundle...${NC}"

rm -rf node_bundle/
mkdir -p node_bundle/bin
mkdir -p node_bundle/node_modules

# 4. Copia Node.js nel bundle
echo -e "${BLUE}📋 Copia Node.js nel bundle...${NC}"
NODE_PATH=$(which node)
if [ -f "$NODE_PATH" ]; then
    cp "$NODE_PATH" node_bundle/bin/node
    echo -e "${GREEN}✅ Node.js copiato da: $NODE_PATH${NC}"
else
    echo -e "${RED}❌ Node.js non trovato!${NC}"
    exit 1
fi

# 5. Crea package.json per il bundle (USA IL PACCHETTO CORRETTO)
echo -e "${BLUE}📋 Creazione package.json...${NC}"
cat > node_bundle/package.json << 'EOF'
{
  "name": "xrpwallet-node-bundle",
  "version": "1.0.0",
  "description": "Node.js bundle per XRPWallet",
  "dependencies": {
    "@xrplf/secret-numbers": "latest"
  }
}
EOF
echo -e "${GREEN}✅ package.json creato${NC}"

# In prepare_build.sh, modifica la sezione 6:

# 6. Installa xrpl-secret-numbers nel bundle (IL VECCHIO CHE FUNZIONA)
echo ""
echo -e "${BLUE}📦 Installazione xrpl-secret-numbers nel bundle...${NC}"
cd node_bundle

# 🔑 USA IL PACCHETTO VECCHIO (CHE FUNZIONA CON I NUMERI XAMAN)
npm install xrpl-secret-numbers@0.3.5 --omit=dev

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ xrpl-secret-numbers installato${NC}"
else
    echo -e "${RED}❌ Errore installazione xrpl-secret-numbers${NC}"
    exit 1
fi
cd ..

# 7. Verifica installazione
echo ""
echo -e "${BLUE}🔍 Verifica installazione...${NC}"

# Cerca il package installato
if [ -d "node_bundle/node_modules/@xrplf/secret-numbers" ]; then
    echo -e "${GREEN}✅ @xrplf/secret-numbers installato correttamente${NC}"
    VERSION=$(cat node_bundle/node_modules/@xrplf/secret-numbers/package.json 2>/dev/null | grep version | head -1 | cut -d'"' -f4)
    echo -e "${GREEN}   Versione: ${VERSION}${NC}"
elif [ -d "node_bundle/node_modules/xrpl-secret-numbers" ]; then
    echo -e "${GREEN}✅ xrpl-secret-numbers installato correttamente${NC}"
    VERSION=$(cat node_bundle/node_modules/xrpl-secret-numbers/package.json 2>/dev/null | grep version | head -1 | cut -d'"' -f4)
    echo -e "${GREEN}   Versione: ${VERSION}${NC}"
else
    echo -e "${RED}❌ Nessun package trovato!${NC}"
    exit 1
fi

# 8. Verifica dimensione del bundle
echo ""
echo -e "${BLUE}📏 Dimensione node_bundle...${NC}"
du -sh node_bundle/

# 9. Crea script di test per il bundle
echo ""
echo -e "${BLUE}📝 Creazione script di test...${NC}"

cat > node_bundle/test_xaman.js << 'EOF'
// Test per @xrplf/secret-numbers
try {
    // Prova con il package @xrplf
    const { Account } = require('@xrplf/secret-numbers');
    const numbers = ['301814', '193740', '115707', '234581', '635220', '476547', '389141', '480766'];
    const secret = numbers.join(' ');
    const account = new Account(secret);
    console.log(JSON.stringify({
        familySeed: account.getFamilySeed(),
        address: account.getAddress()
    }));
} catch (e) {
    // Prova con il package xrpl-secret-numbers
    try {
        const { Account } = require('xrpl-secret-numbers');
        const numbers = ['301814', '193740', '115707', '234581', '635220', '476547', '389141', '480766'];
        const secret = numbers.join(' ');
        const account = new Account(secret);
        console.log(JSON.stringify({
            familySeed: account.getFamilySeed(),
            address: account.getAddress()
        }));
    } catch (e2) {
        console.error('❌ Nessun package funzionante');
        process.exit(1);
    }
}
EOF

# 10. Test del bundle
echo ""
echo -e "${BLUE}🧪 Test del bundle Node.js...${NC}"
NODE_BUNDLE="./node_bundle/bin/node"
if [ -f "$NODE_BUNDLE" ]; then
    $NODE_BUNDLE node_bundle/test_xaman.js
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Test del bundle completato con successo!${NC}"
    else
        echo -e "${RED}❌ Test del bundle fallito!${NC}"
        cat node_bundle/test_xaman.js
    fi
else
    echo -e "${RED}❌ Node.js nel bundle non trovato!${NC}"
fi

# 11. Riepilogo
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  ✅ PREPARAZIONE COMPLETATA!                                    ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}📁 Struttura creata:${NC}"
echo "   node_bundle/"
echo "   ├── bin/"
echo "   │   └── node"
echo "   └── node_modules/"
echo -e "       └── ${BLUE}@xrplf/secret-numbers/${NC} (o xrpl-secret-numbers)"
echo ""
echo -e "${GREEN}📦 Dimensione bundle: $(du -sh node_bundle/ | cut -f1)${NC}"
echo ""
echo -e "${YELLOW}🚀 Prossimo passo:${NC}"
echo "   ./build_all.sh"
echo ""
echo -e "${GREEN}✅ Fatto!${NC}"