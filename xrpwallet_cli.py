#!/usr/bin/env python3
"""
Wrapper per CLI/TUI/WEB - Gestisce i flag
"""

import sys
import os
from pathlib import Path

# Aggiungi la directory corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Avvia la CLI, TUI o WEB in base ai flag"""
    
    # 🔑 CONTROLLA I FLAG
    if "--tui" in sys.argv:
        try:
            from ui_cli import run_tui
            run_tui()
        except ImportError as e:
            print(f"❌ Errore TUI: {e}")
            print("Assicurati che ui_cli.py sia presente")
            sys.exit(1)
        return
    
    if "--gui" in sys.argv:
        try:
            from ui_web import app
            # Parsing per porta e host
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--port", type=int, default=5000)
            parser.add_argument("--host", default="0.0.0.0")
            args, unknown = parser.parse_known_args()
            
            print(f"\n🌐 Server web in esecuzione su http://{args.host}:{args.port}")
            print("   Premi CTRL+C per fermare il server\n")
            app.run(host=args.host, port=args.port, debug=False)
        except ImportError as e:
            print(f"❌ Errore WEB: {e}")
            print("Assicurati che ui_web.py sia presente")
            sys.exit(1)
        return
    
    # 🔑 DEFAULT: CLI
    try:
        from cli import main as cli_main
        # Rimuovi i flag che non sono per CLI
        cli_main()
    except ImportError as e:
        print(f"❌ Errore: {e}")
        print("Assicurati che cli.py sia presente nella stessa directory")
        sys.exit(1)

if __name__ == "__main__":
    main()