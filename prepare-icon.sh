#!/bin/bash
# convert_jpg_to_icons.sh - Converti JPG in icone

echo "🔄 Conversione JPG in icone..."

# 🔑 Verifica che il JPG esista
if [ ! -f "icon.jpg" ]; then
    echo "❌ icon.jpg non trovato!"
    echo "   Assicurati di averlo salvato nella root del progetto"
    echo "   Se ha un nome diverso, modifica lo script"
    exit 1
fi

echo "✅ icon.jpg trovato!"

# Crea cartella per le icone
mkdir -p icons

# 1. Converti JPG in PNG (con sfondo trasparente se possibile)
echo "📦 Conversione JPG in PNG..."
convert icon.jpg -background none -flatten icon.png
echo "✅ icon.png creato"

# 2. Crea ICO per Windows
echo "📦 Creazione icon.ico per Windows..."
convert icon.jpg -resize 256x256 icon.ico
echo "✅ icon.ico creato"

# 3. Crea favicon per web
echo "📦 Creazione favicon.ico..."
convert icon.jpg -resize 32x32 favicon.ico
echo "✅ favicon.ico creato"

# 4. Crea PNG nelle dimensioni per Linux
echo "📦 Creazione PNG per Linux..."
for size in 16 32 48 64 128 256 512; do
    convert icon.jpg -resize ${size}x${size} icons/icon-${size}.png
done
echo "✅ PNG per Linux creati"

# 5. Se sei su macOS, crea ICNS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📦 Creazione icon.icns per macOS..."
    mkdir -p icons.iconset
    
    sips -z 16 16 icon.png --out icons.iconset/icon_16x16.png
    sips -z 32 32 icon.png --out icons.iconset/icon_16x16@2x.png
    sips -z 32 32 icon.png --out icons.iconset/icon_32x32.png
    sips -z 64 64 icon.png --out icons.iconset/icon_32x32@2x.png
    sips -z 128 128 icon.png --out icons.iconset/icon_128x128.png
    sips -z 256 256 icon.png --out icons.iconset/icon_128x128@2x.png
    sips -z 256 256 icon.png --out icons.iconset/icon_256x256.png
    sips -z 512 512 icon.png --out icons.iconset/icon_256x256@2x.png
    sips -z 512 512 icon.png --out icons.iconset/icon_512x512.png
    sips -z 1024 1024 icon.png --out icons.iconset/icon_512x512@2x.png
    
    iconutil -c icns icons.iconset -o icon.icns
    echo "✅ icon.icns creato"
    rm -rf icons.iconset
else
    echo "⚠️  Non sei su macOS. Per creare icon.icns servirebbe macOS."
    echo "   Puoi usare: https://cloudconvert.com/png-to-icns"
fi

echo ""
echo "✅ TUTTE LE ICONE PRONTE!"
echo ""
echo "📁 File disponibili:"
ls -lh icon.* icons/ 2>/dev/null | head -20