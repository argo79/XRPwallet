#!/usr/bin/env python3
"""
ui_desktop.py - App desktop standalone con PySide6 (QT)
"""

import sys
import os
import threading
import time
from pathlib import Path

# 🔑 IMPOSTA VARIABILI D'AMBIENTE PRIMA DELL'IMPORT
os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["QT_PLUGIN_PATH"] = os.path.join(os.path.dirname(sys.executable), "plugins")

try:
    from PySide6.QtCore import QUrl, QTimer, Qt, QSettings
    from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar, QMessageBox
    from PySide6.QtGui import QIcon, QAction
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
except ImportError as e:
    print(f"⚠️ Errore import PySide6: {e}")
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtCore import QUrl, QTimer, Qt, QSettings
    from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar, QMessageBox
    from PySide6.QtGui import QIcon, QAction
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile

from ui_web import app as flask_app

# ============================================================
# 🔧 CONFIGURAZIONE
# ============================================================

WINDOW_TITLE = "💰 XRP/XLM Wallet Manager"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
MAX_RETRIES = 15
RETRY_DELAY_MS = 500
ORGANIZATION_NAME = "Arg0net"
APPLICATION_NAME = "XRPWallet"

# ============================================================
# 🖥️ CLASSE PRINCIPALE
# ============================================================

class DesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configura finestra
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Imposta icona se disponibile
        if os.path.exists("favicon.ico"):
            self.setWindowIcon(QIcon("favicon.ico"))
        
        # Crea il browser
        self.browser = QWebEngineView()
        
        # Configura il browser
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        
        # Configura profilo
        try:
            profile = QWebEngineProfile.defaultProfile()
            profile.setPersistentStoragePath(os.path.join(os.path.expanduser("~"), ".xrpwallet", "webengine"))
            profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        except:
            pass
        
        # Abilita strumenti sviluppatore in debug
        if os.getenv("DEBUG", "0") == "1":
            try:
                self.browser.page().setDevToolsPage(self.browser.page())
            except:
                pass
        
        # Imposta il browser come widget centrale
        self.setCentralWidget(self.browser)
        
        # Crea barra di stato
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("⏳ Inizializzazione...")
        
        # Crea menù
        self.create_menu()
        
        # Timer per aggiornare lo stato
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)
        
        # Ripristina stato finestra
        self.restore_window_state()
        
        # Avvia il server Flask
        self.start_flask_server()
    
    def create_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("📁 File")
        reload_action = QAction("🔄 Ricarica", self)
        reload_action.setShortcut("Ctrl+R")
        reload_action.triggered.connect(self.refresh_page)
        file_menu.addAction(reload_action)
        file_menu.addSeparator()
        exit_action = QAction("❌ Esci", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        view_menu = menubar.addMenu("👁️ Vista")
        fullscreen_action = QAction("⛶ Schermo intero", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        view_menu.addSeparator()
        
        zoom_in_action = QAction("🔍 Zoom +", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(lambda: self.browser.setZoomFactor(self.browser.zoomFactor() + 0.1))
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("🔍 Zoom -", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(lambda: self.browser.setZoomFactor(max(0.5, self.browser.zoomFactor() - 0.1)))
        view_menu.addAction(zoom_out_action)
        
        zoom_reset_action = QAction("🔍 Zoom 100%", self)
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.triggered.connect(lambda: self.browser.setZoomFactor(1.0))
        view_menu.addAction(zoom_reset_action)
        
        if os.getenv("DEBUG", "0") == "1":
            view_menu.addSeparator()
            dev_action = QAction("🛠️ Strumenti sviluppatore", self)
            dev_action.setShortcut("F12")
            dev_action.triggered.connect(self.open_dev_tools)
            view_menu.addAction(dev_action)
        
        help_menu = menubar.addMenu("ℹ️ Info")
        about_action = QAction("📋 Informazioni", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        help_menu.addSeparator()
        website_action = QAction("🌐 Sito web", self)
        website_action.triggered.connect(lambda: self.browser.setUrl(QUrl("https://github.com/argo79/XRPwallet")))
        help_menu.addAction(website_action)
    
    def start_flask_server(self):
        def run_flask():
            try:
                flask_app.run(
                    host=SERVER_HOST, 
                    port=SERVER_PORT, 
                    debug=False, 
                    use_reloader=False,
                    threaded=True
                )
            except Exception as e:
                self.status.showMessage(f"❌ Errore server: {str(e)[:30]}")
        
        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()
        
        self.status.showMessage("⏳ Avvio del server...")
        self._wait_for_server(MAX_RETRIES, RETRY_DELAY_MS / 1000.0)
    
    def _wait_for_server(self, retries, delay):
        try:
            import requests
            response = requests.get(f"{SERVER_URL}/", timeout=1)
            if response.status_code == 200:
                self.status.showMessage("✅ Server avviato")
                self.browser.setUrl(QUrl(SERVER_URL))
                return
        except:
            pass
        
        if retries > 0:
            QTimer.singleShot(int(delay * 1000), 
                            lambda: self._wait_for_server(retries - 1, delay * 1.3))
        else:
            self.status.showMessage("⚠️ Server non risponde")
            self.browser.setUrl(QUrl(SERVER_URL))
    
    def refresh_page(self):
        self.browser.reload()
        self.status.showMessage("🔄 Pagina ricaricata", 2000)
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.status.showMessage("⛶ Uscito da schermo intero", 2000)
        else:
            self.showFullScreen()
            self.status.showMessage("⛶ Schermo intero attivato", 2000)
    
    def open_dev_tools(self):
        try:
            self.browser.page().triggerAction(QWebEngineView.InspectElement)
            self.status.showMessage("🛠️ Strumenti sviluppatore aperti", 2000)
        except:
            pass
    
    def update_status(self):
        try:
            import requests
            response = requests.get(f"{SERVER_URL}/", timeout=1)
            if response.status_code == 200:
                self.status.showMessage("✅ Server attivo")
            else:
                self.status.showMessage(f"⚠️ Server: {response.status_code}")
        except:
            self.status.showMessage("⚠️ Server non raggiungibile")
    
    def show_about(self):
        QMessageBox.about(
            self,
            "Informazioni",
            f"""
            <h2>💰 XRP/XLM Wallet Manager</h2>
            <p><b>Versione:</b> v2.0.1</p>
            <p><b>Autore:</b> Arg0net</p>
            <br>
            <p>Gestisci i tuoi wallet XRP e XLM con facilità</p>
            <p>🔗 <a href="https://github.com/argo79/XRPwallet">GitHub Repository</a></p>
            """
        )
    
    def save_window_state(self):
        """Salva lo stato della finestra"""
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("zoomFactor", str(self.browser.zoomFactor()))
    
    def restore_window_state(self):
        """Ripristina lo stato della finestra"""
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))
        if settings.contains("zoomFactor"):
            try:
                # 🔑 CONVERTI STRINGA A FLOAT
                zoom_str = settings.value("zoomFactor")
                if isinstance(zoom_str, str):
                    zoom_factor = float(zoom_str)
                else:
                    zoom_factor = float(zoom_str)
                # 🔑 LIMITA LO ZOOM A VALORI SENSATI
                if 0.5 <= zoom_factor <= 2.0:
                    self.browser.setZoomFactor(zoom_factor)
            except (ValueError, TypeError):
                pass  # Ignora se non può convertire
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Conferma uscita",
            "Sei sicuro di voler uscire?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.save_window_state()
            self.browser.setUrl(QUrl("about:blank"))
            self.browser.page().deleteLater()
            if self.timer:
                self.timer.stop()
            event.accept()
        else:
            event.ignore()

# ============================================================
# 🚀 FUNZIONE PRINCIPALE
# ============================================================

def main():
    app_qt = QApplication(sys.argv)
    app_qt.setApplicationName(APPLICATION_NAME)
    app_qt.setOrganizationName(ORGANIZATION_NAME)
    app_qt.setStyle("Fusion")
    
    window = DesktopWindow()
    window.show()
    
    try:
        sys.exit(app_qt.exec())
    except KeyboardInterrupt:
        print("\n👋 Uscita forzata...")
        sys.exit(0)

if __name__ == "__main__":
    main()