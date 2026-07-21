#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    # 🔑 TUI - usa ui_cli.py (che è il tuo file TUI)
    if "--tui" in sys.argv:
        try:
            from ui_cli import run_tui
            run_tui()
        except Exception as e:
            print(f"❌ Errore TUI: {e}")
            import traceback
            traceback.print_exc()
        return
    
    # 🔑 WEB/GUI
    if "--gui" in sys.argv:
        try:
            from ui_web import app
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--port", type=int, default=5000)
            parser.add_argument("--host", default="0.0.0.0")
            args = parser.parse_known_args()[0]
            print(f"\n🌐 Server web su http://{args.host}:{args.port}")
            app.run(host=args.host, port=args.port, debug=False)
        except Exception as e:
            print(f"❌ Errore WEB: {e}")
            import traceback
            traceback.print_exc()
        return
    
    # 🔑 DEFAULT: CLI
    try:
        from cli import main as cli_main
        cli_main()
    except Exception as e:
        print(f"❌ Errore CLI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()