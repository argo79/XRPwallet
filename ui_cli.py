#!/usr/bin/env python3
"""
ui_tui.py - Interfaccia terminale TUI per XRP/XLM Wallet Manager
by Arg0net - v2.5 - CON SCROLL ORIZZONTALE
"""

import curses
import json
import sys
import time
from datetime import datetime
import re
from pathlib import Path
from cli import XRPCLI


class XRPWalletTUI:
    def __init__(self):
        self.cli = XRPCLI()
        self.selected_wallet = 0
        self.wallet_scroll = 0
        self.wallets = []
        self.message = ""
        self.message_type = "info"
        self.running = True
        
        self.output_lines = []
        self.output_title = ""
        self.output_scroll = 0
        self.output_hscroll = 0  # 🔑 SCROLL ORIZZONTALE
        self.output_visible = False
        self.focus = "wallets"
        
        # Rubrica
        self.contacts = []
        self.selected_contact = 0
        self.contact_scroll = 0
        self.show_contacts_mode = False
        self.selected_contact_address = ""
        self.selected_contact_name = ""
        
        self.version = "v2.5"
        self.author = "Arg0net"
        
    def setup_colors(self):
        curses.start_color()
        
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)
        
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(9, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_BLACK)
        
        curses.init_pair(11, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(12, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(13, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(14, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(15, curses.COLOR_RED, curses.COLOR_BLACK)
        
    def _get_crypto_color(self, crypto: str):
        return curses.color_pair(6) if crypto == "XRP" else curses.color_pair(7)
    
    def _get_network_color(self, network: str):
        return curses.color_pair(9) if network == "mainnet" else curses.color_pair(10)
    
    def draw_header(self, stdscr):
        height, width = stdscr.getmaxyx()
        symbol = "⧫" if self.cli._crypto == "XRP" else "✦"
        
        header_left = f" {symbol} {self.cli._crypto} WALLET MANAGER - TUI "
        header_right = f" {self.version} by {self.author} "
        
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(0, 0, "=" * (width - 1))
        stdscr.addstr(1, (width - len(header_left)) // 2, header_left)
        stdscr.addstr(1, width - len(header_right) - 1, header_right)
        stdscr.addstr(2, 0, "=" * (width - 1))
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        
        active = self.cli._get_active_wallet_name() or "Nessuno"
        network = self.cli._network.upper()
        crypto = self.cli._crypto
        
        crypto_color = self._get_crypto_color(crypto)
        stdscr.attron(crypto_color | curses.A_BOLD)
        stdscr.addstr(3, 2, f"🪙 {crypto}")
        stdscr.attroff(crypto_color | curses.A_BOLD)
        
        network_color = self._get_network_color(self.cli._network)
        stdscr.attron(network_color | curses.A_BOLD)
        stdscr.addstr(3, 12, f"🔗 {network}")
        stdscr.attroff(network_color | curses.A_BOLD)
        
        stdscr.addstr(3, 22, f" |  📂 {active}")
        
        if self.selected_contact_address:
            contact_display = f"📒 {self.selected_contact_name}"
            stdscr.attron(curses.color_pair(14) | curses.A_BOLD)
            stdscr.addstr(3, 40, contact_display)
            stdscr.attroff(curses.color_pair(14) | curses.A_BOLD)
        
        if self.cli.manager.is_loaded():
            try:
                address = self.cli.manager.get_address()
                max_addr_len = width - 50
                if max_addr_len < 10:
                    max_addr_len = 10
                
                if len(address) <= max_addr_len:
                    addr_display = address
                else:
                    addr_display = address[:max_addr_len-3] + "..."
                
                addr_x = width - len(addr_display) - 3
                if addr_x < 0:
                    addr_x = 2
                stdscr.addstr(3, addr_x, f"🏠 {addr_display}")
            except:
                pass
        
        stdscr.addstr(4, 0, "-" * (width - 1))
        return 5
        
    def draw_footer(self, stdscr, start_row):
        height, width = stdscr.getmaxyx()
        if start_row < height - 1:
            stdscr.addstr(start_row, 0, "-" * (width - 1))
        
        if self.show_contacts_mode:
            focus_indicator = "📒 RUBRICA"
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(start_row + 1, 2, f"FOCUS: {focus_indicator}")
            stdscr.attroff(curses.A_BOLD)
            commands = ["↑↓:Nav", "Enter:Seleziona", "t:Invia", "a:Aggiungi", "d:Elimina", "r:Esci", "q:Esci"]
            cmd_str = " | ".join(commands)
            if len(cmd_str) < width - 40:
                stdscr.addstr(start_row + 1, 25, cmd_str[:width-45])
        else:
            focus_indicator = "[WALLET]" if self.focus == "wallets" else "[OUTPUT]"
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(start_row + 1, 2, f"FOCUS: {focus_indicator}")
            stdscr.attroff(curses.A_BOLD)
            commands = ["Tab:Focus", "↑↓:Nav", "←→:HScroll", "Enter:Az", "w:Wallet", "s:Switch", "i:Info", "b:Bal", "t:Send", "h:Hist", "c:Crypto", "r:Rubrica"]
            cmd_str = " | ".join(commands)
            if len(cmd_str) < width - 40:
                stdscr.addstr(start_row + 1, 25, cmd_str[:width-45])
        
        stdscr.addstr(start_row + 1, width - 8, "q:Esci")
        
        return start_row + 2
        
    def load_wallets(self):
        self.wallets = []
        for file in self.cli.wallets_dir.glob("*.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    address = data.get("current_address", "sconosciuto")
                    crypto = data.get("crypto_type", "XRP")
                    network = data.get("network", "testnet")
                    self.wallets.append({
                        "name": file.stem,
                        "address": address,
                        "crypto": crypto,
                        "network": network,
                        "balance": "---"
                    })
            except:
                pass
        
        active = self.cli._get_active_wallet_name()
        self.wallets.sort(key=lambda w: (0 if w["name"] == active else 1, w["crypto"], w["name"]))
        
        if self.selected_wallet >= len(self.wallets):
            self.selected_wallet = 0
        if self.wallet_scroll >= len(self.wallets):
            self.wallet_scroll = 0
        
        if active:
            for i, w in enumerate(self.wallets):
                if w["name"] == active:
                    self.selected_wallet = i
                    if self.selected_wallet < self.wallet_scroll:
                        self.wallet_scroll = self.selected_wallet
                    break
    
    def load_contacts(self):
        self.contacts = []
        if self.cli.rubrica_file.exists():
            try:
                with open(self.cli.rubrica_file) as f:
                    data = json.load(f)
                    all_contacts = data.get("contatti", [])
                    
                    for c in all_contacts:
                        if c.get("crypto", "XRP") == self.cli._crypto:
                            c_network = c.get("network", "testnet")
                            if c_network == self.cli._network:
                                self.contacts.append(c)
            except:
                pass
        
        if self.selected_contact >= len(self.contacts):
            self.selected_contact = 0
        if self.contact_scroll >= len(self.contacts):
            self.contact_scroll = 0
    
    def save_contacts(self):
        all_contacts = []
        if self.cli.rubrica_file.exists():
            try:
                with open(self.cli.rubrica_file, 'r') as f:
                    data = json.load(f)
                    all_contacts = data.get("contatti", [])
            except Exception as e:
                print(f"⚠️ Errore lettura rubrica: {e}")
        
        other_contacts = [c for c in all_contacts if c.get("crypto", "XRP") != self.cli._crypto]
        all_contacts = other_contacts + self.contacts
        
        try:
            with open(self.cli.rubrica_file, 'w') as f:
                json.dump({"contatti": all_contacts}, f, indent=2)
            print(f"✅ Rubrica salvata: {len(self.contacts)} contatti")
        except Exception as e:
            print(f"❌ Errore salvataggio rubrica: {e}")
    
    def draw_wallet_list(self, stdscr, start_row):
        height, width = stdscr.getmaxyx()
        row = start_row
        
        if not self.wallets:
            self.load_wallets()
        
        if not self.wallets:
            stdscr.addstr(row, 4, "❌ Nessun wallet salvato.")
            return row + 2
        
        active = self.cli._get_active_wallet_name()
        
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(row, 2, "📋 WALLET")
        row += 1
        stdscr.addstr(row, 2, " #  Nome          Crypto  Rete    Indirizzo")
        row += 1
        stdscr.addstr(row, 2, "-" * (width - 3))
        row += 1
        stdscr.attroff(curses.A_BOLD)
        
        total_rows = height - start_row - 12
        max_wallets = max(10, total_rows - 2)
        if max_wallets > len(self.wallets):
            max_wallets = len(self.wallets)
        if max_wallets < 1:
            max_wallets = 1
        
        total_wallets = len(self.wallets)
        
        if self.wallet_scroll > total_wallets - max_wallets:
            self.wallet_scroll = max(0, total_wallets - max_wallets)
        if self.wallet_scroll < 0:
            self.wallet_scroll = 0
        
        visible_wallets = self.wallets[self.wallet_scroll:self.wallet_scroll + max_wallets]
        
        for i, w in enumerate(visible_wallets):
            actual_index = self.wallet_scroll + i
            
            if actual_index == self.selected_wallet and self.focus == "wallets" and not self.show_contacts_mode:
                stdscr.attron(curses.color_pair(5) | curses.A_REVERSE)
            
            marker = "▶" if w["name"] == active else " "
            
            addr = w["address"]
            fixed_width = 36
            max_addr_len = width - fixed_width - 3
            
            if max_addr_len < 10:
                max_addr_len = 10
            
            if len(addr) <= max_addr_len:
                addr_display = addr
            else:
                addr_display = addr[:max_addr_len-3] + "..."
            
            num_part = f" {marker} {actual_index+1:2}."
            name_part = f" {w['name'][:12]:12}"
            crypto_part = f" {w['crypto']:6}"
            network_part = f" {w['network'][:7]:7}"
            addr_part = f" {addr_display}"
            
            stdscr.addstr(row, 2, num_part)
            stdscr.addstr(row, 2 + len(num_part), name_part)
            
            crypto_color = self._get_crypto_color(w["crypto"])
            stdscr.attron(crypto_color)
            stdscr.addstr(row, 2 + len(num_part) + len(name_part), crypto_part)
            stdscr.attroff(crypto_color)
            
            network_color = self._get_network_color(w["network"])
            stdscr.attron(network_color)
            stdscr.addstr(row, 2 + len(num_part) + len(name_part) + len(crypto_part), network_part)
            stdscr.attroff(network_color)
            
            stdscr.addstr(row, 2 + len(num_part) + len(name_part) + len(crypto_part) + len(network_part), addr_part)
            
            if actual_index == self.selected_wallet and self.focus == "wallets" and not self.show_contacts_mode:
                stdscr.attroff(curses.color_pair(5) | curses.A_REVERSE)
            row += 1
        
        if total_wallets > max_wallets:
            scroll_info = f"📜 [{self.wallet_scroll+1}-{min(self.wallet_scroll+max_wallets, total_wallets)}/{total_wallets}]  (↑↓ per scorrere)"
            stdscr.addstr(row, 2, scroll_info)
            row += 1
        
        return row
    
    def draw_contacts_list(self, stdscr, start_row):
        height, width = stdscr.getmaxyx()
        row = start_row
        
        if not self.contacts:
            self.load_contacts()
        
        if self.selected_contact_address:
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(row, 2, f"✅ Selezionato: {self.selected_contact_name} -> {self.selected_contact_address[:20]}...")
            row += 1
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
        
        stdscr.attron(curses.A_BOLD | curses.color_pair(14))
        filter_info = f"📒 RUBRICA - {self.cli._crypto} / {self.cli._network.upper()}"
        stdscr.addstr(row, 2, f"{filter_info}  (t=Invia  a=Aggiungi  d=Elimina  r=Esci)")
        row += 1
        stdscr.attroff(curses.color_pair(14) | curses.A_BOLD)
        
        if not self.contacts:
            stdscr.addstr(row, 4, f"❌ Nessun contatto per {self.cli._crypto} su {self.cli._network.upper()}")
            row += 1
            stdscr.addstr(row, 4, "💡 Premi 'a' per aggiungere un contatto")
            return row + 2
        
        stdscr.addstr(row, 2, f"{'#':<3} {'Nome':<18} {'Rete':<8} {'Indirizzo'}")
        row += 1
        stdscr.addstr(row, 2, "-" * (width - 3))
        row += 1
        
        max_contacts = height - row - 6
        if max_contacts < 1:
            max_contacts = 1
        
        total = len(self.contacts)
        
        if self.contact_scroll > total - max_contacts:
            self.contact_scroll = max(0, total - max_contacts)
        if self.contact_scroll < 0:
            self.contact_scroll = 0
        
        visible = self.contacts[self.contact_scroll:self.contact_scroll + max_contacts]
        
        for i, c in enumerate(visible):
            actual_index = self.contact_scroll + i
            
            if actual_index == self.selected_contact:
                stdscr.attron(curses.color_pair(5) | curses.A_REVERSE)
            
            nome = c.get("nome", "?")[:18]
            network = c.get("network", "testnet")[:7]
            indirizzo = c.get("indirizzo", "?")
            
            network_color = self._get_network_color(network)
            
            if len(indirizzo) > width - 40:
                indirizzo = indirizzo[:width-43] + "..."
            
            stdscr.addstr(row, 2, f" {actual_index+1:2}  ")
            stdscr.addstr(row, 7, f"{nome:<18} ")
            
            stdscr.attron(network_color)
            stdscr.addstr(row, 26, f"{network:<8} ")
            stdscr.attroff(network_color)
            
            stdscr.addstr(row, 35, indirizzo)
            
            if actual_index == self.selected_contact:
                stdscr.attroff(curses.color_pair(5) | curses.A_REVERSE)
            row += 1
        
        if total > max_contacts:
            scroll_info = f"📜 [{self.contact_scroll+1}-{min(self.contact_scroll+max_contacts, total)}/{total}]"
            stdscr.addstr(row, 2, scroll_info)
            row += 1
        
        stdscr.addstr(row, 2, f"Totale: {len(self.contacts)} contatti")
        row += 1
        
        return row
        
    def draw_output_area(self, stdscr, start_row):
        height, width = stdscr.getmaxyx()
        
        if start_row >= height - 2:
            return start_row
        
        sep_line = "=" * (width - 1)
        if self.output_title and not self.show_contacts_mode:
            title_display = f" {self.output_title} "
            sep_line = title_display.center(width - 1, "=")
        
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(start_row, 0, sep_line)
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        start_row += 1
        
        if self.show_contacts_mode:
            start_row = self.draw_contacts_list(stdscr, start_row)
            return start_row
        
        if self.output_lines and self.output_visible:
            max_output_rows = height - start_row - 4
            total_lines = len(self.output_lines)
            
            if self.output_scroll > total_lines - max_output_rows:
                self.output_scroll = max(0, total_lines - max_output_rows)
            if self.output_scroll < 0:
                self.output_scroll = 0
            
            # 🔑 CALCOLA LARGHEZZA MASSIMA DELLE RIGHE PER LO SCROLL ORIZZONTALE
            max_line_len = 0
            for line in self.output_lines:
                if len(line) > max_line_len:
                    max_line_len = len(line)
            
            # 🔑 AGGIUSTA SCROLL ORIZZONTALE
            if self.output_hscroll > max_line_len - width + 1:
                self.output_hscroll = max(0, max_line_len - width + 1)
            if self.output_hscroll < 0:
                self.output_hscroll = 0
            
            visible_lines = self.output_lines[self.output_scroll:self.output_scroll + max_output_rows]
            
            # 🔑 MOSTRA INDICATORE DI SCROLL ORIZZONTALE
            if max_line_len > width - 4:
                if self.output_hscroll > 0:
                    stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                    stdscr.addstr(start_row, 1, "◄")
                    stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
                if self.output_hscroll < max_line_len - width + 1:
                    stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                    stdscr.addstr(start_row, width - 2, "►")
                    stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
            
            for i, line in enumerate(visible_lines):
                if start_row + i < height - 1:
                    # 🔑 APPLICA SCROLL ORIZZONTALE
                    if len(line) > width - 4:
                        display_line = line[self.output_hscroll:self.output_hscroll + width - 4]
                    else:
                        display_line = line
                    
                    # 🔑 ESTRAI MEMO
                    memo_text = ""
                    main_text = display_line
                    
                    if "📝" in display_line:
                        parts = display_line.split("📝", 1)
                        main_text = parts[0].strip()
                        memo_text = "📝" + parts[1].strip() if len(parts) > 1 else ""
                    
                    # 🔑 COLORI
                    if "RICEVUTO" in display_line or "Da:" in display_line:
                        stdscr.attron(curses.color_pair(11))
                        stdscr.addstr(start_row + i, 2, main_text[:width-25])
                        stdscr.attroff(curses.color_pair(11))
                        
                        if memo_text:
                            stdscr.attron(curses.color_pair(14) | curses.A_BOLD)
                            memo_x = len(main_text[:width-25]) + 2
                            if memo_x < width - len(memo_text) - 2:
                                stdscr.addstr(start_row + i, memo_x, memo_text[:width-memo_x-2])
                            stdscr.attroff(curses.color_pair(14) | curses.A_BOLD)
                            
                    elif "INVIATO" in display_line or "A:" in display_line:
                        stdscr.attron(curses.color_pair(12))
                        stdscr.addstr(start_row + i, 2, main_text[:width-25])
                        stdscr.attroff(curses.color_pair(12))
                        
                        if memo_text:
                            stdscr.attron(curses.color_pair(14) | curses.A_BOLD)
                            memo_x = len(main_text[:width-25]) + 2
                            if memo_x < width - len(memo_text) - 2:
                                stdscr.addstr(start_row + i, memo_x, memo_text[:width-memo_x-2])
                            stdscr.attroff(curses.color_pair(14) | curses.A_BOLD)
                            
                    elif "✅" in display_line:
                        stdscr.attron(curses.color_pair(2))
                        stdscr.addstr(start_row + i, 2, display_line[:width-4])
                        stdscr.attroff(curses.color_pair(2))
                        
                    elif "❌" in display_line or "errore" in display_line.lower():
                        stdscr.attron(curses.color_pair(3))
                        stdscr.addstr(start_row + i, 2, display_line[:width-4])
                        stdscr.attroff(curses.color_pair(3))
                        
                    else:
                        stdscr.addstr(start_row + i, 2, display_line[:width-4])
            
            # 🔑 INDICATORI DI SCROLL
            if total_lines > max_output_rows:
                scroll_info = f" [{self.output_scroll+1}-{min(self.output_scroll+max_output_rows, total_lines)}/{total_lines}]"
                stdscr.addstr(start_row + max_output_rows - 1, width - len(scroll_info) - 2, scroll_info)
            
            # 🔑 INDICATORE SCROLL ORIZZONTALE
            if max_line_len > width - 4:
                hscroll_info = f" ←→ {self.output_hscroll+1}/{max_line_len-width+2}"
                stdscr.addstr(start_row + max_output_rows - 1, 2, hscroll_info[:15])
            
            start_row += max_output_rows
        else:
            cmd_line = "i=Info  b=Balance  h=History  t=Send  w=Wallet  s=Switch  c=Crypto  r=Rubrica"
            if self.selected_contact_address:
                cmd_line += f"  📒 {self.selected_contact_name}"
            stdscr.addstr(start_row, 4, cmd_line[:width-8])
            start_row += 1
        
        return start_row
        
    def draw_main_menu(self, stdscr):
        height, width = stdscr.getmaxyx()
        
        header_rows = 5
        footer_rows = 3
        
        start_row = self.draw_header(stdscr)
        row = self.draw_wallet_list(stdscr, start_row)
        
        output_start = row + 1
        self.draw_output_area(stdscr, output_start)
        self.draw_footer(stdscr, height - 3)
        
    def set_output(self, title, content):
        self.output_title = title
        self.output_lines = content.split('\n')
        self.output_scroll = 0
        self.output_hscroll = 0  # 🔑 RESET SCROLL ORIZZONTALE
        self.output_visible = True
        self.focus = "output"
        self.show_contacts_mode = False
        
        if len(self.output_lines) > 500:
            self.output_lines = self.output_lines[:500]
    
    def toggle_contacts(self):
        if self.show_contacts_mode:
            self.show_contacts_mode = False
            self.focus = "wallets"
            self.output_visible = False
        else:
            self.load_contacts()
            self.show_contacts_mode = True
            self.focus = "wallets"
            self.output_visible = False
            self.selected_contact = 0
            self.contact_scroll = 0
    
    def select_contact(self):
        if not self.contacts or self.selected_contact >= len(self.contacts):
            return
        
        contact = self.contacts[self.selected_contact]
        self.selected_contact_name = contact.get("nome", "sconosciuto")
        self.selected_contact_address = contact.get("indirizzo", "")
        
        self.set_output("✅ CONTATTO SELEZIONATO", 
                       f"📒 {self.selected_contact_name}\n🏠 {self.selected_contact_address}\n\n💡 Premi 't' per inviare a questo contatto")
        self.show_contacts_mode = False
        self.focus = "wallets"
    
    def send_to_contact(self):
        if not self.selected_contact_address:
            if self.contacts and self.selected_contact < len(self.contacts):
                self.select_contact()
            else:
                self.set_output("❌ ERRORE", "Nessun contatto selezionato!\n\nSeleziona un contatto con Enter prima di inviare.")
                return
        
        self.show_contacts_mode = False
        self.focus = "wallets"
        
        curses.endwin()
        
        print("\n📤 INVIA A CONTATTO")
        print("-" * 40)
        print(f"📒 Contatto: {self.selected_contact_name}")
        print(f"🏠 Indirizzo: {self.selected_contact_address}")
        print("-" * 40)
        
        try:
            amount = float(input("Importo: "))
        except ValueError:
            print("❌ Importo non valido")
            input("Premi Invio per continuare...")
            curses.doupdate()
            return
            
        memo = input("Memo (opzionale): ").strip()
        
        args = [self.selected_contact_address, str(amount)]
        if memo:
            args.append(f'"{memo}"')
            
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            self.cli.cmd_send(args)
        
        curses.doupdate()
        self.set_output("📤 RISULTATO INVIO", f.getvalue())
        self.load_wallets()
    
    def add_contact(self):
        curses.endwin()
        
        try:
            print("\n📒 AGGIUNGI CONTATTO")
            print("-" * 40)
            print(f"🪙 Crypto corrente: {self.cli._crypto}")
            print(f"🔗 Rete corrente: {self.cli._network.upper()}")
            print("-" * 40)
            
            nome = input("Nome: ").strip()
            if not nome:
                print("❌ Nome non valido")
                input("Premi Invio per continuare...")
                return
            
            indirizzo = input("Indirizzo: ").strip()
            if not indirizzo:
                print("❌ Indirizzo non valido")
                input("Premi Invio per continuare...")
                return
            
            if self.cli._crypto == "XRP":
                if not indirizzo.startswith('r'):
                    print(f"❌ Indirizzo XRP deve iniziare con 'r'")
                    print(f"   Hai inserito: {indirizzo[:20]}...")
                    input("Premi Invio per continuare...")
                    return
                if len(indirizzo) < 25:
                    print("❌ Indirizzo XRP troppo corto")
                    input("Premi Invio per continuare...")
                    return
            elif self.cli._crypto == "XLM":
                if not indirizzo.startswith('G'):
                    print(f"❌ Indirizzo XLM deve iniziare con 'G'")
                    print(f"   Hai inserito: {indirizzo[:20]}...")
                    input("Premi Invio per continuare...")
                    return
                if len(indirizzo) < 56:
                    print("❌ Indirizzo XLM troppo corto")
                    input("Premi Invio per continuare...")
                    return
            
            for c in self.contacts:
                if c.get("nome", "").lower() == nome.lower():
                    print(f"❌ Il contatto '{nome}' esiste già")
                    input("Premi Invio per continuare...")
                    return
            
            new_contact = {
                "nome": nome,
                "indirizzo": indirizzo,
                "crypto": self.cli._crypto,
                "network": self.cli._network,
                "created_at": datetime.now().isoformat()
            }
            self.contacts.append(new_contact)
            self.save_contacts()
            
            print(f"✅ Contatto '{nome}' aggiunto!")
            print(f"   🪙 Crypto: {self.cli._crypto}")
            print(f"   🔗 Rete: {self.cli._network.upper()}")
            print(f"   📁 Salvato in: {self.cli.rubrica_file}")
            input("Premi Invio per continuare...")
            
        except KeyboardInterrupt:
            print("\n❌ Operazione annullata")
            input("Premi Invio per continuare...")
        except Exception as e:
            print(f"❌ Errore: {e}")
            import traceback
            traceback.print_exc()
            input("Premi Invio per continuare...")
        finally:
            curses.doupdate()
            self.load_contacts()
            self.show_contacts_mode = True
            self.output_visible = False
            self.focus = "wallets"
    
    def delete_contact(self):
        if not self.contacts or self.selected_contact >= len(self.contacts):
            return
        
        contact = self.contacts[self.selected_contact]
        nome = contact.get("nome", "sconosciuto")
        
        curses.endwin()
        
        print(f"\n🗑️ ELIMINA CONTATTO")
        print("-" * 40)
        print(f"Contatto: {nome}")
        print(f"Indirizzo: {contact.get('indirizzo', '?')}")
        print("-" * 40)
        
        confirm = input(f"Eliminare '{nome}'? (s/n): ").strip().lower()
        
        if confirm == 's':
            self.contacts.pop(self.selected_contact)
            self.save_contacts()
            if self.selected_contact >= len(self.contacts):
                self.selected_contact = max(0, len(self.contacts) - 1)
            if self.selected_contact_address == contact.get("indirizzo", ""):
                self.selected_contact_address = ""
                self.selected_contact_name = ""
            print(f"✅ Contatto '{nome}' eliminato!")
        else:
            print("❌ Annullato")
        
        input("Premi Invio per continuare...")
        
        curses.doupdate()
        self.load_contacts()
        self.show_contacts_mode = True
        self.output_visible = False
    
    def wallet_menu(self):
        curses.endwin()
        
        print("\n" + "=" * 60)
        print("  🔧 GESTIONE WALLET")
        print("=" * 60)
        print("  1) Crea nuovo wallet (BIP39)")
        print("  2) Importa wallet")
        print("  3) Annulla")
        print("-" * 60)
        
        choice = input("Scelta (1-3): ").strip()
        
        if choice == "1":
            self._create_wallet()
        elif choice == "2":
            self._import_wallet()
        else:
            print("❌ Annullato")
            input("Premi Invio per continuare...")
        
        curses.doupdate()
        self.load_wallets()
        self.output_visible = False
        self.focus = "wallets"
        self.show_contacts_mode = False
    
    def _create_wallet(self):
        print("\n" + "=" * 60)
        print("  ➕ CREA NUOVO WALLET")
        print("=" * 60)
        
        print("\n🪙 Scegli criptovaluta:")
        print("  1) XRP")
        print("  2) XLM")
        crypto_choice = input("Scelta (1-2): ").strip()
        
        if crypto_choice == "1":
            crypto = "XRP"
        elif crypto_choice == "2":
            crypto = "XLM"
        else:
            print("❌ Scelta non valida")
            input("Premi Invio per continuare...")
            return
        
        print("\n🌐 Scegli rete:")
        print("  1) Mainnet")
        print("  2) Testnet")
        print("  3) Devnet")
        network_choice = input("Scelta (1-3): ").strip()
        
        if network_choice == "1":
            network = "mainnet"
        elif network_choice == "2":
            network = "testnet"
        elif network_choice == "3":
            network = "devnet"
        else:
            print("❌ Scelta non valida")
            input("Premi Invio per continuare...")
            return
        
        name = input("\n📝 Nome del wallet: ").strip()
        if not name:
            print("❌ Nome non valido")
            input("Premi Invio per continuare...")
            return
        
        passphrase = input("🔐 Passphrase (opzionale, invio per nessuna): ").strip()
        
        self.cli._set_crypto(crypto)
        self.cli._set_network(network)
        
        try:
            result = self.cli.manager.create_new_wallet_bip39(passphrase=passphrase, strength=256)
            self.cli._save_wallet_as(name)
            self.cli._set_active_wallet_name(name)
            
            print(f"\n✅ Wallet '{name}' creato con successo!")
            print(f"🏠 Indirizzo: {result['first_address']}")
            print(f"📝 Seed phrase: {result['seed_phrase']}")
            print(f"🌐 Rete: {network.upper()}")
            print(f"🪙 Crypto: {crypto}")
            
            self.message = f"✅ Wallet '{name}' creato"
            self.message_type = "success"
            
        except Exception as e:
            print(f"❌ Errore: {e}")
        
        input("\nPremi Invio per continuare...")
    
    def _import_wallet(self):
        print("\n" + "=" * 60)
        print("  📥 IMPORTA WALLET")
        print("=" * 60)
        
        print("\n🪙 Scegli criptovaluta:")
        print("  1) XRP")
        print("  2) XLM")
        crypto_choice = input("Scelta (1-2): ").strip()
        
        if crypto_choice == "1":
            crypto = "XRP"
        elif crypto_choice == "2":
            crypto = "XLM"
        else:
            print("❌ Scelta non valida")
            input("Premi Invio per continuare...")
            return
        
        print("\n🌐 Scegli rete:")
        print("  1) Mainnet")
        print("  2) Testnet")
        network_choice = input("Scelta (1-2): ").strip()
        
        if network_choice == "1":
            network = "mainnet"
        elif network_choice == "2":
            network = "testnet"
        else:
            print("❌ Scelta non valida")
            input("Premi Invio per continuare...")
            return
        
        name = input("\n📝 Nome del wallet: ").strip()
        if not name:
            print("❌ Nome non valido")
            input("Premi Invio per continuare...")
            return
        
        print("\n📝 Inserisci il seed:")
        if crypto == "XRP":
            print("  - 12-24 parole BIP39")
            print("  - Seed XRP (s...)")
            print("  - Private key (64 hex)")
            print("  - 8x6 numeri")
        else:
            print("  - 12-24 parole BIP39")
            print("  - Seed Stellar (S...)")
            print("  - Private key (64 hex)")
        
        seed_input = input("> ").strip()
        if not seed_input:
            print("❌ Seed non valido")
            input("Premi Invio per continuare...")
            return
        
        passphrase = ""
        input_type = "auto"
        
        if crypto == "XRP":
            if len(seed_input) == 64 and all(c in "0123456789abcdefABCDEF" for c in seed_input):
                input_type = "private_key"
            elif seed_input.startswith("s"):
                input_type = "xrp_seed"
            else:
                cleaned = re.sub(r'[A-Ha-h]:', '', seed_input)
                cleaned = re.sub(r',', ' ', cleaned)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                numbers_parts = cleaned.split()
                if len(numbers_parts) == 8 and all(p.isdigit() and len(p) == 6 for p in numbers_parts):
                    input_type = "numbers"
                    seed_input = numbers_parts
                else:
                    input_type = "bip39"
                    passphrase = input("🔐 Passphrase (opzionale, invio per nessuna): ").strip()
        else:
            if seed_input.startswith("S"):
                input_type = "stellar_seed"
            elif len(seed_input) == 64 and all(c in "0123456789abcdefABCDEF" for c in seed_input):
                input_type = "private_key"
            else:
                input_type = "bip39"
                passphrase = input("🔐 Passphrase (opzionale, invio per nessuna): ").strip()
        
        self.cli._set_crypto(crypto)
        self.cli._set_network(network)
        
        try:
            result = self.cli.manager.import_wallet(seed_input, passphrase=passphrase, input_type=input_type)
            self.cli._save_wallet_as(name)
            self.cli._set_active_wallet_name(name)
            
            print(f"\n✅ Wallet '{name}' importato con successo!")
            print(f"🏠 Indirizzo: {result['first_address']}")
            print(f"🌐 Rete: {network.upper()}")
            print(f"🪙 Crypto: {crypto}")
            
            self.message = f"✅ Wallet '{name}' importato"
            self.message_type = "success"
            
        except Exception as e:
            print(f"❌ Errore: {e}")
        
        input("\nPremi Invio per continuare...")
    
    def switch_wallet(self):
        if self.show_contacts_mode:
            return
        
        if self.wallets and self.selected_wallet < len(self.wallets):
            name = self.wallets[self.selected_wallet]["name"]
            self.cli._switch_wallet(name)
            self.message = f"✅ Wallet cambiato a: {name}"
            self.message_type = "success"
            self.load_wallets()
            self.output_visible = False
            self.focus = "wallets"
        else:
            self.message = "❌ Nessun wallet selezionato"
            self.message_type = "error"
    
    def show_info(self):
        if self.show_contacts_mode:
            return
        
        if self.cli.manager.is_loaded():
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                self.cli.cmd_info([])
            output = f.getvalue()
            self.set_output("📋 INFO WALLET", output)
        else:
            self.message = "❌ Nessun wallet caricato"
            self.message_type = "error"
            self.output_visible = False
    
    def show_balance(self):
        if self.show_contacts_mode:
            return
        
        if self.wallets and self.selected_wallet < len(self.wallets):
            w = self.wallets[self.selected_wallet]
            balance = self.get_balance_for_wallet(w)
            self.set_output("💰 SALDO", f"Wallet: {w['name']}\nCrypto: {w['crypto']}\nRete: {w['network']}\nSaldo: {balance}")
        else:
            self.message = "❌ Nessun wallet selezionato"
            self.message_type = "error"
            self.output_visible = False
    
    def get_balance_for_wallet(self, wallet):
        try:
            old_network = self.cli._network
            old_crypto = self.cli._crypto
            
            self.cli._set_network(wallet["network"])
            self.cli._set_crypto(wallet["crypto"])
            
            if self.cli.manager.is_loaded():
                address = self.cli.manager.get_address()
                if wallet["crypto"] == "XRP":
                    from xrpl.account import get_balance
                    balance = get_balance(address, self.cli.client)
                    return f"{balance / 1_000_000:.2f} XRP"
                else:
                    if hasattr(self.cli.manager, 'stellar_manager') and self.cli.manager.stellar_manager:
                        balance = self.cli.manager.stellar_manager.get_balance(address)
                        return f"{balance:.2f} XLM"
            
            self.cli._set_network(old_network)
            self.cli._set_crypto(old_crypto)
        except Exception as e:
            return f"❌ {str(e)}"
        return "---"
    
    def send_menu(self):
        if self.show_contacts_mode:
            return
        
        curses.endwin()
        
        print("\n📤 INVIA XRP/XLM")
        print("-" * 40)
        dest = input("Indirizzo destinazione: ")
        if not dest:
            print("❌ Operazione annullata")
            input("Premi Invio per continuare...")
            curses.doupdate()
            self.output_visible = False
            return
            
        try:
            amount = float(input("Importo: "))
        except ValueError:
            print("❌ Importo non valido")
            input("Premi Invio per continuare...")
            curses.doupdate()
            self.output_visible = False
            return
            
        memo = input("Memo (opzionale): ").strip()
        
        args = [dest, str(amount)]
        if memo:
            args.append(f'"{memo}"')
            
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            self.cli.cmd_send(args)
        
        curses.doupdate()
        self.set_output("📤 RISULTATO INVIO", f.getvalue())
        self.load_wallets()
    
    def show_history(self):
        if not self.cli.manager.is_loaded():
            self.message = "❌ Nessun wallet caricato"
            self.message_type = "error"
            self.output_visible = False
            return
        
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            if self.cli._crypto == "XLM":
                try:
                    from commands.xlm_commands import history_xlm
                    history_xlm(self.cli, ["--limit", "25"])
                except ImportError:
                    print("❌ Comando XLM non disponibile. Installa stellar-sdk")
            else:
                self.cli._show_xrp_history(["--limit", "25"])
        
        output = f.getvalue()
        
        if not output.strip():
            output = "❌ Nessuna transazione trovata."
        
        self.set_output("📜 STORICO TRANSAZIONI", output)
    
    def crypto_menu(self):
        if self.show_contacts_mode:
            return
        
        curses.endwin()
        
        print("\n🪙 Scegli criptovaluta:")
        print("-" * 40)
        print("  1) XRP")
        print("  2) XLM")
        choice = input("Scelta (1-2): ").strip()
        
        if choice == "1":
            self.cli._set_crypto("XRP")
            self.message = "✅ Crypto impostata a: XRP"
            self.message_type = "success"
        elif choice == "2":
            self.cli._set_crypto("XLM")
            self.message = "✅ Crypto impostata a: XLM"
            self.message_type = "success"
        else:
            self.message = "❌ Scelta non valida"
            self.message_type = "error"
        
        self.load_wallets()
        self.output_visible = False
        self.focus = "wallets"
        curses.doupdate()
    
    def handle_input(self, key, stdscr):
        height, width = stdscr.getmaxyx()
        
        if self.show_contacts_mode:
            if key == curses.KEY_UP:
                if self.selected_contact > 0:
                    self.selected_contact -= 1
                    if self.selected_contact < self.contact_scroll:
                        self.contact_scroll = self.selected_contact
                return True
                
            elif key == curses.KEY_DOWN:
                if self.selected_contact < len(self.contacts) - 1:
                    self.selected_contact += 1
                    max_contacts = height - 12
                    if self.selected_contact >= self.contact_scroll + max_contacts:
                        self.contact_scroll = self.selected_contact - max_contacts + 1
                return True
                
            elif key == ord('\n') or key == ord('\r'):
                self.select_contact()
                return True
                
            elif key in [ord('t'), ord('T')]:
                if self.selected_contact < len(self.contacts):
                    self.select_contact()
                    self.send_to_contact()
                return True
                
            elif key in [ord('a'), ord('A')]:
                self.add_contact()
                return True
                
            elif key in [ord('d'), ord('D')]:
                self.delete_contact()
                return True
                
            elif key in [ord('r'), ord('R')]:
                self.toggle_contacts()
                return True
                
            elif key in [ord('q'), ord('Q')]:
                self.running = False
                return True
            
            return True
        
        if self.focus == "wallets":
            if key == curses.KEY_UP:
                if self.selected_wallet > 0:
                    self.selected_wallet -= 1
                    if self.selected_wallet < self.wallet_scroll:
                        self.wallet_scroll = self.selected_wallet
                    self.message = ""
                return True
                
            elif key == curses.KEY_DOWN:
                if self.selected_wallet < len(self.wallets) - 1:
                    self.selected_wallet += 1
                    max_wallets = max(10, height - 20)
                    if max_wallets > len(self.wallets):
                        max_wallets = len(self.wallets)
                    if self.selected_wallet >= self.wallet_scroll + max_wallets:
                        self.wallet_scroll = self.selected_wallet - max_wallets + 1
                    self.message = ""
                return True
                
            elif key == ord('\n') or key == ord('\r'):
                if self.wallets and self.selected_wallet < len(self.wallets):
                    self.switch_wallet()
                return True
        
        elif self.focus == "output" and self.output_visible:
            if key == curses.KEY_UP:
                self.output_scroll = max(0, self.output_scroll - 1)
                return True
                
            elif key == curses.KEY_DOWN:
                if len(self.output_lines) > 0:
                    self.output_scroll = min(len(self.output_lines) - 1, self.output_scroll + 1)
                return True
                
            # 🔑 SCROLL ORIZZONTALE
            elif key == curses.KEY_LEFT:
                self.output_hscroll = max(0, self.output_hscroll - 10)
                return True
                
            elif key == curses.KEY_RIGHT:
                max_line_len = 0
                for line in self.output_lines:
                    if len(line) > max_line_len:
                        max_line_len = len(line)
                self.output_hscroll = min(max_line_len - width + 1, self.output_hscroll + 10)
                if self.output_hscroll < 0:
                    self.output_hscroll = 0
                return True
        
        if key == ord('\t'):
            if self.focus == "wallets" and self.output_visible:
                self.focus = "output"
            elif self.focus == "output":
                self.focus = "wallets"
            return True
        
        if key in [ord('r'), ord('R')]:
            self.toggle_contacts()
            return True
            
        elif key in [ord('w'), ord('W')]:
            self.wallet_menu()
            return True
            
        elif key in [ord('s'), ord('S')]:
            self.switch_wallet()
            return True
            
        elif key in [ord('i'), ord('I')]:
            self.show_info()
            return True
            
        elif key in [ord('b'), ord('B')]:
            self.show_balance()
            return True
            
        elif key in [ord('t'), ord('T')]:
            if self.selected_contact_address:
                self.send_to_contact()
            else:
                self.send_menu()
            return True
            
        elif key in [ord('h'), ord('H')]:
            self.show_history()
            return True
            
        elif key in [ord('c'), ord('C')]:
            self.crypto_menu()
            return True
            
        elif key in [ord('q'), ord('Q')]:
            self.running = False
            return True
        
        return False
    
    def main_loop(self, stdscr):
        curses.curs_set(0)
        self.setup_colors()
        stdscr.nodelay(0)
        self.load_wallets()
        self.load_contacts()
        self.output_visible = False
        self.focus = "wallets"
        self.wallet_scroll = 0
        self.show_contacts_mode = False
        self.selected_contact_address = ""
        self.selected_contact_name = ""
        
        while self.running:
            stdscr.clear()
            self.draw_main_menu(stdscr)
            stdscr.refresh()
            
            try:
                key = stdscr.getch()
                if key != -1:
                    self.handle_input(key, stdscr)
            except KeyboardInterrupt:
                self.running = False
            except:
                pass
        
        return


def run_tui():
    try:
        tui = XRPWalletTUI()
        curses.wrapper(tui.main_loop)
    except KeyboardInterrupt:
        print("\n👋 Arrivederci!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_tui()