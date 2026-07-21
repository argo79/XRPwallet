#!/usr/bin/env python3
"""
Wrapper per Web/GUI - Mantiene compatibilità con la struttura esistente
"""

import sys
import os
from pathlib import Path

# Aggiungi la directory corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main(host="0.0.0.0", port=5000):
    """Avvia il server web"""
    try:
        from ui_web import app
        
        print(f"\n🌐 Server web in esecuzione su http://{host}:{port}")
        print("   Premi CTRL+C per fermare il server\n")
        app.run(host=host, port=port, debug=False)
    except ImportError as e:
        print(f"❌ Errore: {e}")
        print("Assicurati che ui_web.py sia presente nella stessa directory")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    main(host=args.host, port=args.port)