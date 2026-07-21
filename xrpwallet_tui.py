#!/usr/bin/env python3
"""
Wrapper per TUI - Mantiene compatibilità con la struttura esistente
"""

import sys
import os
from pathlib import Path

# Aggiungi la directory corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Avvia la TUI"""
    try:
        from ui_cli import run_tui
        run_tui()
    except ImportError as e:
        print(f"❌ Errore: {e}")
        print("Assicurati che ui_tui.py sia presente nella stessa directory")
        sys.exit(1)

if __name__ == "__main__":
    main()