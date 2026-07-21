#!/usr/bin/env python3
"""
XRP/XLM Wallet Manager - Punto di ingresso unificato
"""

import sys
import os
import argparse
from pathlib import Path

def main():
    """Punto di ingresso principale"""
    parser = argparse.ArgumentParser(
        description="XRP/XLM Wallet Manager v1.0.0",
        epilog="Esempi:\n  xrpwallet wallet MEW\n  xrpwallet --tui\n  xrpwallet --gui\n  xrpwallet balance"
    )
    parser.add_argument("--cli", action="store_true", help="Avvia interfaccia CLI (default)")
    parser.add_argument("--tui", action="store_true", help="Avvia interfaccia TUI")
    parser.add_argument("--gui", action="store_true", help="Avvia interfaccia Web/GUI")
    parser.add_argument("--port", type=int, default=5000, help="Porta per GUI (default: 5000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host per GUI (default: 0.0.0.0)")
    parser.add_argument("--version", action="store_true", help="Mostra versione")
    
    # Passa gli argomenti rimanenti al comando
    args, unknown = parser.parse_known_args()
    
    if args.version:
        print("XRPWallet v1.0.0")
        return
    
    # 🔑 DEFAULT: CLI (se non ci sono flag specifici)
    # Se l'utente ha passato comandi (es. xrpwallet balance), usa CLI
    if unknown or len(sys.argv) > 1:
        # Se non ci sono flag --tui o --gui, usa CLI
        if not (args.tui or args.gui):
            args.cli = True
    
    # Se nessuna flag e nessun comando, mostra help
    if not (args.cli or args.tui or args.gui):
        parser.print_help()
        return
    
    if args.cli:
        from xrpwallet_cli import main as cli_main
        # Passa i comandi originali al CLI
        sys.argv = [sys.argv[0]] + unknown
        cli_main()
    elif args.tui:
        from xrpwallet_tui import main as tui_main
        tui_main()
    else:  # GUI
        from xrpwallet_web import main as web_main
        web_main(host=args.host, port=args.port)

if __name__ == "__main__":
    main()