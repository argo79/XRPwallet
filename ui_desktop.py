#!/usr/bin/env python3
"""
ui_desktop.py - App desktop standalone con PySide6
"""

import sys
import os
import threading
import time
from pathlib import Path
from datetime import datetime

# 🔑 IMPOSTA VARIABILI D'AMBIENTE
os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["QT_PLUGIN_PATH"] = os.path.join(os.path.dirname(sys.executable), "plugins")

# 🔑 IMPORT PYSIDE6 - CORRETTI
from PySide6.QtCore import QUrl, QTimer, Qt, QSettings, QEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QMessageBox, QFileDialog
)
from PySide6.QtGui import QIcon, QAction, QDesktopServices

# 🔑 QWebEngineView da QtWebEngineWidgets
# 🔑 QWebEnginePage, QWebEngineSettings, QWebEngineProfile da QtWebEngineCore
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineProfile

from ui_web import app as flask_app

# ============================================================
# 🔧 CONFIGURAZIONE
# ============================================================

WINDOW_TITLE = "XRP/XLM Wallet Manager - by Arg0net - 2026"
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
# 🔑 PAGINA WEB PERSONALIZZATA
# ============================================================

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        
        if parent and hasattr(parent, 'main_window'):
            self.main_window = parent.main_window
        elif parent:
            self.main_window = parent
    
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        url_str = url.toString()
        
        # 🔑 SE È IL NOSTRO SERVER, CARICA NELLA FINESTRA
        if url_str.startswith('http://127.0.0.1:5000') or url_str.startswith('http://localhost:5000'):
            print(f"✅ Navigazione interna: {url_str}")
            return True
        
        # 🔑 QUALSIASI ALTRO LINK - BLOCCA
        print(f"🚫 Navigazione bloccata: {url_str}")
        QDesktopServices.openUrl(url)
        
        if self.main_window and hasattr(self.main_window, 'status'):
            self.main_window.status.showMessage(f"🌐 Aperto nel browser", 2000)
        
        return False
    
    def createWindow(self, window_type):
        return self

# ============================================================
# 🖥️ CLASSE PRINCIPALE
# ============================================================

class DesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 🔑 DETERMINA LA ROOT DELL'APP
        if getattr(sys, 'frozen', False):
            self.app_root = os.path.dirname(sys.executable)
        else:
            self.app_root = os.path.dirname(os.path.abspath(__file__))
        
        self.download_dir = self.app_root
        self.current_url = SERVER_URL
        
        print(f"📂 App root: {self.app_root}")
        print(f"📂 Download dir: {self.download_dir}")
        
        # Configura finestra
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        if os.path.exists("favicon.ico"):
            self.setWindowIcon(QIcon("favicon.ico"))
        
        # 🔑 CREA IL BROWSER
        self.browser = QWebEngineView()
        self.page = CustomWebEnginePage(self.browser)
        self.page.main_window = self
        self.browser.setPage(self.page)
        
        # 🔑 CONFIGURA IL PROFILO PER I DOWNLOAD
        self.setup_download_handler()
        
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
        
        try:
            settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        except:
            pass
        
        # Configura profilo
        try:
            profile = QWebEngineProfile.defaultProfile()
            profile.setPersistentStoragePath(os.path.join(os.path.expanduser("~"), ".xrpwallet", "webengine"))
            profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        except:
            pass
        
        self.setCentralWidget(self.browser)
        
        # 🔑 FILTRO EVENTI PER RICARICARE LA PAGINA (SOLO RELOAD, NON RESET)
        self.installEventFilter(self)
        
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
    
    def eventFilter(self, obj, event):
        """🔑 CATTURA L'ATTIVAZIONE DELLA FINESTRA - SOLO RELOAD"""
        if event.type() == QEvent.WindowActivate:
            print("🔄 Finestra attivata - Reload pagina...")
            # 🔑 USA RELAD INVECE DI SETURL - MANTIENE LO STATO
            self.browser.reload()
            self.status.showMessage("✅ Pagina ricaricata", 1000)
            return True
        return super().eventFilter(obj, event)
    
    def setup_download_handler(self):
        try:
            profile = QWebEngineProfile.defaultProfile()
            profile.setDownloadPath(self.download_dir)
            profile.downloadRequested.connect(self.handle_download)
        except Exception as e:
            print(f"⚠️ Errore configurazione download: {e}")
    
    def get_human_filename(self):
        address = ""
        try:
            import requests
            response = requests.get("http://127.0.0.1:5000/api/wallet/address", timeout=2)
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', '')
        except:
            pass
        
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")
        
        if address and len(address) >= 8:
            short_addr = address[-8:]
            filename = f"xrpwallet_qrcode_{short_addr}_{date_str}.png"
        else:
            filename = f"xrpwallet_qrcode_{date_str}.png"
        
        return filename
    
    def handle_download(self, download):
        try:
            human_filename = self.get_human_filename()
            default_path = os.path.join(self.download_dir, human_filename)
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salva QR Code",
                default_path,
                "PNG Image (*.png);;All Files (*)"
            )
            
            if file_path:
                dir_path = os.path.dirname(file_path)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                
                download.setDownloadDirectory(os.path.dirname(file_path))
                download.setDownloadFileName(os.path.basename(file_path))
                download.finished.connect(lambda: self.on_download_finished(file_path))
                download.accept()
                
                self.status.showMessage(f"📥 Download avviato: {os.path.basename(file_path)}", 3000)
            else:
                download.cancel()
                self.status.showMessage("❌ Download annullato", 2000)
                
        except Exception as e:
            print(f"❌ Errore download: {e}")
            try:
                fallback_filename = self.get_human_filename()
                fallback_path = os.path.join(self.download_dir, fallback_filename)
                download.setDownloadDirectory(os.path.dirname(fallback_path))
                download.setDownloadFileName(os.path.basename(fallback_path))
                download.accept()
                self.status.showMessage(f"📥 Download salvato in: {fallback_path}", 5000)
            except:
                pass
    
    def on_download_finished(self, file_path):
        self.status.showMessage(f"✅ Download completato: {os.path.basename(file_path)}", 5000)
        QMessageBox.information(
            self,
            "Download completato",
            f"✅ QR Code salvato in:\n{file_path}"
        )
    
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
        website_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/argo79/XRPwallet")))
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
            <p><b>Versione:</b> v1.1.1</p>
            <p><b>Autore:</b> Arg0net</p>
            <br>
            <p>Gestisci i tuoi wallet XRP e XLM con facilità</p>
            <br>
            <p><b>📂 Cartella download:</b> {self.download_dir}</p>
            """
        )
    
    def save_window_state(self):
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("zoomFactor", str(self.browser.zoomFactor()))
    
    def restore_window_state(self):
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))
        if settings.contains("zoomFactor"):
            try:
                zoom_str = settings.value("zoomFactor")
                zoom_factor = float(zoom_str) if isinstance(zoom_str, str) else float(zoom_str)
                if 0.5 <= zoom_factor <= 2.0:
                    self.browser.setZoomFactor(zoom_factor)
            except:
                pass
    
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