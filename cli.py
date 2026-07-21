#!/usr/bin/env python3
"""
cli.py - Gestione wallet XRP/XLM con supporto multi-wallet, rubrica e storico
"""

import sys
import json
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from wallet_manager import HybridXRPManager, CryptoType, NetworkType, SeedType, WalletInfo

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importa i comandi XLM
try:
    from commands.xlm_commands import send_xlm, history_xlm, info_xlm, faucet_xlm
except ImportError:
    def send_xlm(cli, args):
        print("❌ Comando XLM non disponibile. Installa stellar-sdk")
    def history_xlm(cli, args):
        print("❌ Comando XLM non disponibile. Installa stellar-sdk")
    def info_xlm(cli, args):
        print("❌ Comando XLM non disponibile. Installa stellar-sdk")
    def faucet_xlm(cli):
        print("❌ Comando XLM non disponibile. Installa stellar-sdk")

# Importa le utility
try:
    from utils.helpers import (
        get_active_wallet_name,
        get_wallet_display,
        ensure_wallet_settings,
        save_address_to_wallet
    )
except ImportError:
    def get_active_wallet_name(filepath):
        if filepath.exists():
            return filepath.read_text().strip()
        return ""
    
    def get_wallet_display(filepath):
        name = get_active_wallet_name(filepath)
        return name if name else "nessun wallet"
    
    def ensure_wallet_settings(cli):
        if not cli.manager.is_loaded():
            print("❌ Nessun wallet caricato!")
            print("Usa 'wallet NOME' per creare o caricare un wallet.")
            return False
        return True
    
    def save_address_to_wallet(cli, name, address):
        pass


class XRPCLI:
    def __init__(self):
        self.wallets_dir = Path("wallets")
        self.wallets_dir.mkdir(exist_ok=True)

        self.active_wallet_file = Path("wallet_data.json")
        self.rubrica_file = Path("rubrica.json")
        self.active_wallet_name_file = Path("active_wallet.txt")

        self.manager = HybridXRPManager()

        self._client = None
        self._network = "testnet"
        self._crypto = "XRP"

        self.commands = {
            "init": self.cmd_init,
            "import": self.cmd_import,
            "derive": self.cmd_derive,
            "list": self.cmd_list,
            "show": self.cmd_show,
            "info": self.cmd_info,
            "balance": self.cmd_balance,
            "send": self.cmd_send,
            "faucet": self.cmd_faucet,
            "history": self.cmd_history,
            "reset": self.cmd_reset,
            "wallet": self.cmd_wallet,
            "switch": self.cmd_switch,
            "list-wallets": self.cmd_list_wallets,
            "delete-wallet": self.cmd_delete_wallet,
            "contact-add": self.cmd_contact_add,
            "contact-list": self.cmd_contact_list,
            "contact-delete": self.cmd_contact_delete,
            "help": self.cmd_help,
            "crypto": self.cmd_crypto,
        }

    @property
    def client(self):
        if self._client is None:
            if self._crypto == "XRP":
                from xrpl.clients import JsonRpcClient
                urls = {
                    "mainnet": "https://s1.ripple.com:51234/",
                    "testnet": "https://s.altnet.rippletest.net:51234/",
                    "devnet": "https://s.devnet.rippletest.net:51234/"
                }
                url = urls.get(self._network, urls["testnet"])
                self._client = JsonRpcClient(url)
            else:
                from stellar_sdk import Server
                urls = {
                    "mainnet": "https://horizon.stellar.org",
                    "testnet": "https://horizon-testnet.stellar.org",
                    "devnet": "https://horizon-testnet.stellar.org"
                }
                url = urls.get(self._network, urls["testnet"])
                self._client = Server(url)
            
            logger.info(f"🔌 Client connesso a {self._network.upper()} ({self._crypto})")
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    def _set_network(self, network: str) -> None:
        if network not in [n.value for n in NetworkType]:
            raise ValueError(f"Rete non supportata: {network}")
        self._network = network
        self.manager.set_network(network)
        self._client = None
        _ = self.client

    def _set_crypto(self, crypto: str) -> None:
        if crypto not in [c.value for c in CryptoType]:
            raise ValueError(f"Crypto non supportata: {crypto}")
        self._crypto = crypto
        self.manager.set_crypto(crypto)
        self._client = None
        _ = self.client
        logger.info(f"🔄 Crypto impostata a: {crypto}")

    def _choose_network(self, prompt: str = "Scegli la rete") -> str:
        print(f"\n🌐 {prompt}:")
        print("  1) Mainnet (XRP VERI - ATTENZIONE!)")
        print("  2) Testnet (XRP FINTI - per test)")
        print("  3) Devnet (XRP FINTI - per sviluppo)")
        while True:
            choice = input("\nScelta (1-3): ").strip()
            if choice == "1":
                return "mainnet"
            elif choice == "2":
                return "testnet"
            elif choice == "3":
                return "devnet"
            else:
                print("❌ Scelta non valida. Inserisci 1, 2 o 3.")

    def _choose_crypto(self, prompt: str = "Scegli la criptovaluta") -> str:
        print(f"\n🪙 {prompt}:")
        print("  1) XRP (Ripple)")
        print("  2) XLM (Stellar)")
        while True:
            choice = input("\nScelta (1-2): ").strip()
            if choice == "1":
                return "XRP"
            elif choice == "2":
                return "XLM"
            else:
                print("❌ Scelta non valida. Inserisci 1 o 2.")

    def _get_active_wallet_name(self) -> str:
        return get_active_wallet_name(self.active_wallet_name_file)

    def _set_active_wallet_name(self, name: str) -> None:
        with open(self.active_wallet_name_file, "w") as f:
            f.write(name)

    def _get_wallet_display(self) -> str:
        return get_wallet_display(self.active_wallet_name_file)

    def _get_wallet_list(self) -> List[Dict]:
        wallets = []
        for file in self.wallets_dir.glob("*.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    address = data.get("current_address", "unknown")
                    if address == "unknown":
                        derived = data.get("derived_wallets", [])
                        if derived:
                            address = derived[0].get("address", "unknown")
                    
                    wallets.append({
                        "name": file.stem,
                        "address": address,
                        "address_short": address[:8] + "..." if address != "unknown" else "❌ Non disponibile",
                        "crypto": data.get("crypto_type", "XRP"),
                        "network": data.get("network", "testnet"),
                    })
            except Exception as e:
                logger.error(f"Errore lettura wallet {file}: {e}")
        return wallets

    def _switch_wallet(self, name: str) -> bool:
        source = self.wallets_dir / f"{name}.json"
        if not source.exists():
            return False

        try:
            with open(source, 'r') as f:
                wallet_data = json.load(f)

            saved_network = wallet_data.get("network", "testnet")
            saved_crypto = wallet_data.get("crypto_type", "XRP")

            if saved_network != self._network:
                print(f"🌐 Passo a {saved_network.upper()} (salvato nel wallet)")
                self._set_network(saved_network)

            if saved_crypto != self._crypto:
                print(f"🪙 Passo a {saved_crypto} (salvato nel wallet)")
                self._set_crypto(saved_crypto)

            self.manager.seed_type = wallet_data.get("seed_type")
            self.manager.seed_phrase = wallet_data.get("seed_phrase")
            self.manager.seed_numbers = wallet_data.get("seed_numbers")
            self.manager.passphrase = wallet_data.get("passphrase", "")

            base_private_hex = wallet_data.get("base_private")
            if base_private_hex:
                self.manager.base_private = bytes.fromhex(base_private_hex)
            else:
                self.manager.base_private = None

            self.manager.base_seed_xrp = wallet_data.get("base_seed_xrp")
            self.manager.base_seed_stellar = wallet_data.get("base_seed_stellar")
            self.manager._correct_address = wallet_data.get("current_address")
            self.manager.crypto_type = saved_crypto
            self.manager.network = saved_network

            self.manager._derived_wallets = {}
            for w_data in wallet_data.get("derived_wallets", []):
                try:
                    info = WalletInfo.from_dict(w_data)
                    self.manager._derived_wallets[f"{info.keyword}:{info.index}"] = info
                except Exception as e:
                    logger.warning(f"Errore caricamento wallet derivato: {e}")

            self._set_active_wallet_name(name)
            self.manager.save()

            print(f"✅ Wallet cambiato a: {name}")
            print(f"🌐 Rete: {self._network.upper()}")
            print(f"🪙 Crypto: {self._crypto}")
            return True

        except Exception as e:
            logger.error(f"Errore nel cambio wallet: {e}")
            print(f"❌ Errore nel cambio wallet: {e}")
            return False

    def _save_wallet_as(self, name: str) -> bool:
        """Salva il wallet corrente con un nome specifico - FIXATO"""
        if not self.manager.is_loaded():
            return False

        dest = self.wallets_dir / f"{name}.json"

        # 🔑 PRENDI I DATI DIRETTAMENTE DAL MANAGER - NON DA wallet_data.json
        correct_address = self.manager._correct_address
        if not correct_address:
            try:
                correct_address = self.manager.get_address("default", 0)
            except:
                correct_address = None

        data = {
            "seed_type": self.manager.seed_type,
            "seed_phrase": self.manager.seed_phrase,
            "seed_numbers": self.manager.seed_numbers,
            "passphrase": self.manager.passphrase,
            "base_private": self.manager.base_private.hex() if self.manager.base_private else None,
            "base_seed_xrp": self.manager.base_seed_xrp,
            "base_seed_stellar": self.manager.base_seed_stellar,
            "current_address": correct_address,
            "network": self._network,
            "crypto_type": self._crypto,
            "created_at": datetime.now().isoformat(),
            "derived_wallets": [info.to_dict() for info in self.manager._derived_wallets.values()]
        }

        with open(dest, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Wallet '{name}' salvato con indirizzo: {correct_address}")
        print(f"🌐 Rete: {self._network.upper()}")
        print(f"🪙 Crypto: {self._crypto}")
        return True

    def _get_contatti(self) -> List[Dict]:
        if not self.rubrica_file.exists():
            return []
        try:
            with open(self.rubrica_file) as f:
                data = json.load(f)
                return data.get("contatti", [])
        except Exception as e:
            logger.error(f"Errore lettura rubrica: {e}")
            return []

    def _save_contatti(self, contatti: List[Dict]) -> None:
        with open(self.rubrica_file, "w") as f:
            json.dump({"contatti": contatti}, f, indent=2)

    def _cerca_contatto(self, nome: str) -> Optional[Dict]:
        contatti = self._get_contatti()
        for c in contatti:
            if c.get("nome", "").lower() == nome.lower():
                return c
        return None

    def cmd_contact_add(self, args: List[str]) -> None:
        """Aggiunge un contatto alla rubrica"""
        if len(args) < 2:
            print("❌ Specifica nome e indirizzo.")
            print("Esempio: contact-add mario rPT1Sjq2...")
            return

        nome = args[0]
        indirizzo = args[1]
        keyword = args[2] if len(args) > 2 else ""
        index = int(args[3]) if len(args) > 3 and args[3].isdigit() else 0
        note = " ".join(args[4:]) if len(args) > 4 else ""

        # 🔑 VALIDAZIONE INDIRIZZO
        if self._crypto == "XRP" and not indirizzo.startswith('r'):
            print("❌ Indirizzo XRP deve iniziare con 'r'")
            return
        elif self._crypto == "XLM" and not indirizzo.startswith('G'):
            print("❌ Indirizzo XLM deve iniziare con 'G'")
            return

        contatti = self._get_contatti()
        for c in contatti:
            if c.get("nome", "").lower() == nome.lower():
                print(f"❌ Il contatto '{nome}' esiste già.")
                return

        # 🔑 AGGIUNGI CAMPI network E crypto
        contatti.append({
            "nome": nome,
            "indirizzo": indirizzo,
            "keyword": keyword,
            "index": index,
            "note": note,
            "crypto": self._crypto,           # 🔑 AGGIUNTO
            "network": self._network,         # 🔑 AGGIUNTO
            "created_at": datetime.now().isoformat()
        })
        self._save_contatti(contatti)
        print(f"✅ Contatto '{nome}' aggiunto!")

    def cmd_contact_list(self, args: List[str]) -> None:
        """Lista i contatti della rubrica"""
        contatti = self._get_contatti()
        if not contatti:
            print("❌ Rubrica vuota.")
            return

        print("\n📒 RUBRICA")
        print("=" * 110)
        print(f"{'Nome':<15} {'Indirizzo':<50} {'Crypto':<6} {'Rete':<8} {'Note'}")
        print("-" * 110)

        for c in contatti:
            nome = c.get("nome", "?")[:15]
            indirizzo = c.get("indirizzo", "?")
            crypto = c.get("crypto", "XRP")
            network = c.get("network", "testnet")
            note = c.get("note", "")
            
            # 🔑 INDIRIZZO COMPLETO
            print(f"{nome:<15} {indirizzo:<50} {crypto:<6} {network:<8} {note[:20]}")

        print("-" * 110)
        print(f"Totale: {len(contatti)} contatti")
        print("=" * 110)

    def cmd_contact_delete(self, args: List[str]) -> None:
        if not args:
            print("❌ Specifica il nome del contatto.")
            return

        nome = args[0]
        contatti = self._get_contatti()
        original_len = len(contatti)
        contatti = [c for c in contatti if c.get("nome", "").lower() != nome.lower()]
        if len(contatti) == original_len:
            print(f"❌ Contatto '{nome}' non trovato.")
            return
        self._save_contatti(contatti)
        print(f"✅ Contatto '{nome}' eliminato.")

    def cmd_crypto(self, args: List[str]) -> None:
        if not args:
            print(f"🪙 Crypto corrente: {self._crypto}")
            print("   Usa: crypto XRP  o  crypto XLM")
            return

        crypto = args[0].upper()
        if crypto not in ["XRP", "XLM"]:
            print("❌ Crypto non supportata. Usa XRP o XLM")
            return

        self._set_crypto(crypto)
        self.manager.save()

    def cmd_wallet(self, args: List[str]) -> None:
        if not args:
            name = self._get_active_wallet_name()
            if name:
                self._show_wallet_info(name)
            else:
                print("❌ Nessun wallet attivo.")
                print("Usa 'wallet NOME' per crearne uno nuovo.")
            return

        name = args[0]
        target = self.wallets_dir / f"{name}.json"

        if target.exists():
            if self._switch_wallet(name):
                print(f"✅ Wallet cambiato a: {name}")
                self.cmd_info([])
            else:
                print(f"❌ Errore nel cambiare wallet: {name}")
            return

        self._create_new_wallet(name)

    def _show_wallet_info(self, name: str) -> None:
        print(f"\n📂 WALLET ATTIVO")
        print("=" * 60)
        print(f"Nome: {name}")
        print(f"File: {self.active_wallet_file}")
        print(f"🪙 Crypto: {self._crypto}")

        if self.manager.is_loaded():
            info = self.manager.get_seed_info()
            if info.get("seed_type") == "bip39":
                print(f"Tipo: BIP39 (parole)")
                print(f"Parole: {info.get('word_count')}")
                if info.get('passphrase'):
                    print(f"🔐 Passphrase: {info.get('passphrase')}")
            elif info.get("seed_type") == "numbers":
                print(f"Tipo: Numeri 8x6")
            elif info.get("seed_type") == "private_key":
                print(f"Tipo: Private Key")
            elif info.get("seed_type") == "xrp_seed":
                print(f"Tipo: Seed XRP")
            elif info.get("seed_type") == "stellar_seed":
                print(f"Tipo: Seed Stellar")

            derived = self.manager.list_derived()
            print(f"Indirizzi derivati: {len(derived)}")

            try:
                balance = self.manager.get_balance()
                symbol = "XRP" if self._crypto == "XRP" else "XLM"
                print(f"💰 Saldo: {balance:.6f} {symbol}")
            except Exception as e:
                print(f"💰 Saldo: ❌ {e}")
        print("=" * 60)

    def _create_new_wallet(self, name: str) -> None:
        print(f"\n📂 CREA NUOVO WALLET: {name}")
        print("=" * 60)

        crypto = self._choose_crypto("Per quale criptovaluta?")
        self._set_crypto(crypto)

        network = self._choose_network("Per quale rete?")
        self._set_network(network)

        print(f"\n🌐 Creazione per: {network.upper()} - {crypto}")
        print("=" * 60)
        print("Come vuoi crearlo?")
        print("  1) Crea nuovo (genera 24 parole BIP39)")
        print("  2) Importa da seed (12-24 parole, 8x6 numeri, o private key)")
        print("  3) Annulla")

        try:
            choice = input("\nScelta (1-3): ").strip()
            
            if choice not in ["1", "2", "3"]:
                print("❌ Scelta non valida. Inserisci 1, 2 o 3.")
                return

            if choice == "1":
                self._create_new_wallet_from_bip39(name, crypto)
            elif choice == "2":
                self._import_wallet_from_seed(name, crypto)
            else:
                print("❌ Annullato.")

        except KeyboardInterrupt:
            print("\n❌ Annullato.")
        except Exception as e:
            logger.error(f"Errore: {e}", exc_info=True)
            print(f"❌ Errore: {e}")

    def _create_new_wallet_from_bip39(self, name: str, crypto: str) -> None:
        print("\n🔐 Inserisci BIP39 passphrase (opzionale, invio per nessuna):")
        passphrase = input("> ").strip()

        if crypto == "XLM":
            result = self.manager.create_new_wallet_stellar(passphrase=passphrase, strength=256)
        else:
            result = self.manager.create_new_wallet_bip39(passphrase=passphrase, strength=256)
        
        self._save_wallet_as(name)
        self._set_active_wallet_name(name)

        print(f"\n✅ Wallet '{name}' creato con successo per {self._network.upper()} ({crypto})!")
        print(f"🏠 Indirizzo: {result['first_address']}")
        
        if crypto == "XLM":
            print(f"🔑 Seed Stellar: {result['first_private_key']}")
            print(f"🔑 Public Key: {result['first_public_key']}")
        else:
            print(f"🔑 Private Key: {result['first_private_key']}")
            print(f"🔑 Public Key: {result['first_public_key']}")
        
        print(f"📝 Parole: {result['seed_phrase']}")
        if passphrase:
            print(f"🔐 Passphrase: {passphrase}")
        print(f"📁 Salvato in: {self.wallets_dir / f'{name}.json'}")

    def _import_wallet_from_seed(self, name: str, crypto: str) -> None:
        print("\nInserisci il seed:")
        if crypto == "XRP":
            print("  - 12-24 parole BIP39")
            print("  - 8x6 numeri (es: 123456 234567 ...)")
            print("  - Private key (64 hex)")
            print("  - Seed XRP (s...)")
        else:
            print("  - 12-24 parole BIP39")
            print("  - Private key (64 hex)")
            print("  - Seed Stellar (S...)")

        seed_input = input("> ").strip()

        if not seed_input:
            print("❌ Seed non valido.")
            return

        passphrase = ""
        input_type = "auto"

        if crypto == "XRP":
            if len(seed_input) == 64 and all(c in "0123456789abcdefABCDEF" for c in seed_input):
                input_type = "private_key"
                print("🔑 Rilevato: Private Key (hex)")
            elif seed_input.startswith("s"):
                input_type = "xrp_seed"
                print("🔑 Rilevato: Seed XRP")
            else:
                cleaned = re.sub(r'[A-Ha-h]:', '', seed_input)
                cleaned = re.sub(r',', ' ', cleaned)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                numbers_parts = cleaned.split()

                if len(numbers_parts) == 8 and all(p.isdigit() and len(p) == 6 for p in numbers_parts):
                    input_type = "numbers"
                    print("🔢 Rilevato: 8x6 numeri")
                    seed_input = numbers_parts
                else:
                    input_type = "bip39"
                    print("📝 Rilevato: BIP39 (12-24 parole)")
                    print("\n🔐 Inserisci BIP39 passphrase (opzionale, invio per nessuna):")
                    passphrase = input("> ").strip()
        else:
            if seed_input.startswith("S"):
                input_type = "stellar_seed"
                print("🔑 Rilevato: Seed Stellar")
            elif len(seed_input) == 64 and all(c in "0123456789abcdefABCDEF" for c in seed_input):
                input_type = "private_key"
                print("🔑 Rilevato: Private Key (hex)")
            else:
                input_type = "bip39"
                print("📝 Rilevato: BIP39 (12-24 parole)")
                print("\n🔐 Inserisci BIP39 passphrase (opzionale, invio per nessuna):")
                passphrase = input("> ").strip()

        # 🔑 IMPORTA IL WALLET - questo aggiorna il manager
        result = self.manager.import_wallet(seed_input, passphrase=passphrase, input_type=input_type)
        
        # 🔑 SALVA COME NUOVO WALLET - usa i dati del manager
        self._save_wallet_as(name)
        self._set_active_wallet_name(name)

        print(f"\n✅ Wallet '{name}' importato con successo per {self._network.upper()} ({crypto})!")
        print(f"🏠 Indirizzo: {result['first_address']}")

        if input_type == "numbers":
            print(f"🔢 Numeri: {result['secret_numbers_formatted']}")
        elif input_type == "bip39":
            print(f"📝 Parole: {result['seed_phrase']}")
            if passphrase:
                print(f"🔐 Passphrase: {passphrase}")
        elif input_type == "private_key":
            print(f"🔑 Private Key: {seed_input}")
        elif input_type == "xrp_seed":
            print(f"🔑 Seed XRP: {seed_input}")
        elif input_type == "stellar_seed":
            print(f"🔑 Seed Stellar: {seed_input}")

        print(f"📁 Salvato in: {self.wallets_dir / f'{name}.json'}")
        print(f"🌐 Rete: {self._network.upper()}")
        print(f"🪙 Crypto: {crypto}")

    def cmd_init(self, args: List[str]) -> None:
        print("ℹ️  Ora usa 'wallet NOME' per creare un nuovo wallet.")
        print("   Esempio: wallet personale")

    def cmd_import(self, args: List[str]) -> None:
        print("ℹ️  Ora usa 'wallet NOME' e scegli 'Importa'.")
        print("   Esempio: wallet personale")

    def cmd_list_wallets(self, args: List[str]) -> None:
        wallets = self._get_wallet_list()
        if not wallets:
            print("❌ Nessun wallet salvato.")
            print("Crea un wallet con 'wallet NOME'")
            return

        active = self._get_active_wallet_name()

        print("\n📂 WALLET SALVATI")
        print("=" * 80)
        print(f"{'Nome':<18} {'Crypto':<6} {'Rete':<8} {'Indirizzo':<40}")
        print("-" * 60)

        for w in wallets:
            marker = "▶" if w["name"] == active else " "
            crypto = w.get("crypto", "XRP")
            network = w.get("network", "testnet")
            print(f"{marker} {w['name']:<17} {crypto:<6} {network:<8} {w['address']}")

        print("-" * 60)
        print(f"Totale: {len(wallets)} wallet")
        if active:
            print(f"▶ Attivo: {active}")
        print("=" * 60)
        print("\n💡 Usa 'switch NOME' per cambiare wallet")
        print("   Usa 'delete-wallet NOME' per eliminare un wallet")
        print("   Usa 'crypto XRP' o 'crypto XLM' per cambiare crypto")

    def cmd_switch(self, args: List[str]) -> None:
        if not args:
            print("❌ Specifica il nome del wallet.")
            print("Esempio: switch personale")
            self.cmd_list_wallets([])
            return

        name = args[0]

        if self._switch_wallet(name):
            print(f"✅ Wallet cambiato a: {name}")
            self.cmd_info([])
        else:
            print(f"❌ Wallet '{name}' non trovato.")
            self.cmd_list_wallets([])

    def cmd_delete_wallet(self, args: List[str]) -> None:
        if not args:
            print("❌ Specifica il nome del wallet.")
            return

        name = args[0]
        target = self.wallets_dir / f"{name}.json"
        if not target.exists():
            print(f"❌ Wallet '{name}' non trovato.")
            return

        active = self._get_active_wallet_name()
        if name == active:
            print(f"⚠️  Stai eliminando il wallet attivo: {name}")

        if "--force" not in args:
            print(f"⚠️  Confermi l'eliminazione di '{name}'?")
            print("   I fondi NON vengono persi (sono sul ledger).")
            print("   Usa 'delete-wallet NOME --force' per confermare.")
            return

        target.unlink()
        print(f"✅ Wallet '{name}' eliminato.")

        if name == active:
            self.manager.reset()
            if self.active_wallet_name_file.exists():
                self.active_wallet_name_file.unlink()
            print("⚠️  Il wallet attivo è stato resettato.")
            print("   Usa 'wallet NOME' per crearne uno nuovo.")

    def cmd_info(self, args: List[str]) -> None:
        if not ensure_wallet_settings(self):
            return

        if self._crypto == "XLM":
            info_xlm(self, args)
            return

        self._show_xrp_info()

    def _show_xrp_info(self) -> None:
        if not self.manager.is_loaded():
            print("❌ Nessun wallet caricato.")
            return

        client = self.client
        info = self.manager.get_seed_info()
        rete = "TESTNET" if self._network == "testnet" else "MAINNET"
        wallet_name = self._get_wallet_display()

        try:
            address = self.manager.get_address("default", 0)
            save_address_to_wallet(self, wallet_name, address)
        except Exception as e:
            address = f"❌ {e}"

        print("\n📋 INFO WALLET")
        print("=" * 60)
        print(f"Wallet:    {wallet_name}")
        print(f"Rete:      {rete}")
        print(f"Crypto:    XRP")
        print(f"Tipo seed: {info.get('seed_type')}")
        print(f"🏠 Indirizzo: {address}")

        if address and not str(address).startswith("❌"):
            try:
                from xrpl.account import get_balance
                balance_drops = get_balance(address, client)
                balance = balance_drops / 1_000_000
                print(f"💰 Saldo:   {balance:.6f} XRP")
            except Exception as e:
                print(f"💰 Saldo:   ❌ {e}")

        if info.get('seed_type') == 'bip39':
            print(f"Parole: {info.get('word_count')}")
            print(f"Frase: {info.get('seed_phrase')}")
            if info.get('passphrase'):
                print(f"🔐 Passphrase: {info.get('passphrase')}")
        elif info.get('seed_type') == 'numbers':
            print(f"Numeri: {info.get('formatted')}")
            print(f"Seed XRP: {info.get('seed_xrp')}")
        elif info.get('seed_type') == 'private_key':
            print(f"Private Key: {info.get('private_key')}")
            print(f"Seed XRP: {info.get('seed_xrp')}")
        elif info.get('seed_type') == 'xrp_seed':
            print(f"Seed XRP: {info.get('seed_xrp')}")

        derived = self.manager.list_derived()
        print(f"\nIndirizzi derivati: {len(derived)}")

        print("\n" + "=" * 60)
        print("💰 INFORMAZIONI RETE")
        print("=" * 60)

        try:
            from xrpl.ledger import get_fee, get_latest_validated_ledger_sequence
            from xrpl.models.requests import ServerInfo

            fee_drops = get_fee(client)
            fee_xrp = int(fee_drops) / 1_000_000
            print(f"📊 Fee base (minima):")
            print(f"   {fee_drops} drops")
            print(f"   {fee_xrp} XRP")

            ledger_seq = get_latest_validated_ledger_sequence(client)
            print(f"\n📦 Ledger corrente:")
            print(f"   Sequence: {ledger_seq}")

            server_info = client.request(ServerInfo())
            reserve_base = server_info.result["info"]["validated_ledger"]["reserve_base_xrp"]
            reserve_inc = server_info.result["info"]["validated_ledger"]["reserve_inc_xrp"]

            print(f"\n🔒 Riserva minima account:")
            print(f"   Base: {reserve_base} XRP")
            print(f"   Per oggetto: {reserve_inc} XRP")

        except Exception as e:
            print(f"❌ Errore nel recupero delle fee: {e}")

        print("=" * 60)

    def cmd_balance(self, args: List[str]) -> None:
        if not ensure_wallet_settings(self):
            return

        if not self.manager.is_loaded():
            print("❌ Nessun wallet caricato!")
            return

        client = self.client
        wallet_name = self._get_wallet_display()
        symbol = "XRP" if self._crypto == "XRP" else "XLM"

        if args and (args[0].startswith('r') or args[0].startswith('G')):
            self._show_balance_for_address(args[0], wallet_name, symbol)
            return

        keyword = args[0] if args else "default"
        index = int(args[1]) if len(args) > 1 else 0

        try:
            address = self.manager.get_address(keyword, index)
            balance = self._get_balance(address)

            print(f"\n💰 SALDO ({self._network.upper()} - {self._crypto})")
            print("=" * 60)
            print(f"Wallet:    {wallet_name}")
            print(f"Indirizzo: {keyword}:{index} → {address}")
            print(f"Saldo:     {balance:.6f} {symbol}")
            print("=" * 60)
        except Exception as e:
            print(f"❌ Errore: {e}")

    def _show_balance_for_address(self, address: str, wallet_name: str, symbol: str) -> None:
        try:
            balance = self._get_balance(address)
            print(f"\n💰 SALDO ({self._network.upper()} - {self._crypto})")
            print("=" * 60)
            print(f"Wallet:    {wallet_name}")
            print(f"Indirizzo: {address}")
            print(f"Saldo:     {balance:.6f} {symbol}")
            print("=" * 60)
        except Exception as e:
            print(f"❌ Errore: {e}")

    def _get_balance(self, address: str) -> float:
        if self._crypto == "XRP":
            from xrpl.account import get_balance
            balance_drops = get_balance(address, self.client)
            return balance_drops / 1_000_000
        else:
            if hasattr(self.manager, 'stellar_manager') and self.manager.stellar_manager:
                return self.manager.stellar_manager.get_balance(address)
            return 0.0

    def cmd_send(self, args: List[str]) -> None:
        if not ensure_wallet_settings(self):
            return

        if self._crypto == "XLM":
            send_xlm(self, args)
        else:
            self._send_xrp(args)

    def _send_xrp(self, args: List[str]) -> None:
        if not args or len(args) < 2:
            print("❌ Specifica destinatario e importo.")
            print("Esempio: send r... 10")
            print("         send mario 10 (usando rubrica)")
            return

        if not self.manager.is_loaded():
            print("❌ Nessun wallet caricato!")
            return

        client = self.client
        dest_arg = args[0]

        try:
            amount = float(args[1])
        except ValueError:
            print("❌ Importo non valido.")
            return

        source_keyword = "default"
        source_index = 0
        memo_text = None

        parse_args = list(args)
        if len(parse_args) > 2:
            last_arg = parse_args[-1]
            if (last_arg.startswith('"') and last_arg.endswith('"')) or \
               (last_arg.startswith("'") and last_arg.endswith("'")):
                memo_text = last_arg[1:-1]
                parse_args = parse_args[:-1]

        if len(parse_args) > 2:
            third_arg = parse_args[2]
            if not third_arg.startswith('r') and not third_arg.replace('-', '').replace('.', '').isdigit():
                source_keyword = third_arg
                if len(parse_args) > 3 and parse_args[3].isdigit():
                    source_index = int(parse_args[3])
            elif third_arg.replace('-', '').replace('.', '').isdigit():
                source_index = int(float(third_arg))

        contatto = self._cerca_contatto(dest_arg)
        if contatto:
            destination = contatto.get("indirizzo")
            print(f"📒 Contatto trovato: {dest_arg} → {destination}")
        else:
            destination = dest_arg

        if not destination.startswith('r'):
            if ':' in destination:
                dest_keyword, dest_index_str = destination.split(':')
                dest_index = int(dest_index_str)
            else:
                dest_keyword = destination
                dest_index = 0

            try:
                destination = self.manager.get_address(dest_keyword, dest_index)
                print(f"📍 Destinazione risolta: {dest_keyword}:{dest_index} → {destination}")
            except Exception as e:
                print(f"❌ Impossibile trovare l'indirizzo per {dest_arg}: {e}")
                return

        self._execute_xrp_transaction(destination, amount, source_keyword, source_index, memo_text)

    def _execute_xrp_transaction(self, destination: str, amount: float, 
                                 source_keyword: str, source_index: int, 
                                 memo_text: Optional[str]) -> None:
        try:
            from xrpl.account import get_balance, does_account_exist
            from xrpl.models.transactions import Payment, Memo
            from xrpl.transaction import autofill, sign, submit_and_wait
            from xrpl.wallet import Wallet
            import base64

            client = self.client
            wallet = self.manager.get_wallet(source_keyword, source_index)
            source_address = wallet.classic_address
            wallet_name = self._get_wallet_display()

            rete = "TESTNET" if self._network == "testnet" else "MAINNET"
            xrp_tipo = "FINTI (solo test)" if self._network == "testnet" else "VERI (ATTENZIONE!)"

            print(f"\n📤 INVIO XRP ({rete})")
            print("=" * 60)
            print(f"⚠️  XRP: {xrp_tipo}")
            print("=" * 60)
            print(f"Wallet:    {wallet_name}")
            print(f"Da:        {source_address}")
            print(f"           ({source_keyword}:{source_index})")
            print(f"A:         {destination}")
            print(f"Importo:   {amount} XRP")
            if memo_text:
                print(f"📝 Memo:    {memo_text}")
            print("=" * 60)

            balance_drops = get_balance(source_address, client)
            balance_xrp = balance_drops / 1_000_000

            if balance_xrp < amount:
                print(f"❌ Saldo insufficiente!")
                print(f"   Hai:    {balance_xrp} XRP")
                print(f"   Servono: {amount} XRP")
                return

            if not does_account_exist(destination, client):
                print(f"⚠️  Attenzione: l'indirizzo {destination} non esiste sul ledger.")
                if self._network == "mainnet":
                    print("   SU MAINNET: se invii a un indirizzo inesistente, i fondi vanno persi!")
                confirm = input("   Continuare lo stesso? (s/n): ")
                if confirm.lower() != 's':
                    print("❌ Transazione annullata.")
                    return

            amount_drops = str(int(amount * 1_000_000))
            payment_params = {
                "account": source_address,
                "amount": amount_drops,
                "destination": destination,
            }

            if memo_text:
                if len(memo_text) > 1024:
                    print("❌ Memo troppo lungo (max 1024 caratteri)")
                    return

                memo_data = base64.b64encode(memo_text.encode()).decode()
                while len(memo_data) % 4 != 0:
                    memo_data += '='

                memo_obj = Memo(
                    memo_data=memo_data,
                    memo_type=None,
                    memo_format=None
                )
                payment_params["memos"] = [memo_obj]

            payment = Payment(**payment_params)

            print("📝 Firma transazione...")
            tx = autofill(payment, client)
            signed_tx = sign(tx, wallet)

            print("📡 Invio al ledger...")
            response = submit_and_wait(signed_tx, client)

            tx_hash = response.result.get("hash", "unknown")

            print("\n✅ TRANSAZIONE INVIATA!")
            print("=" * 60)
            print(f"Hash: {tx_hash}")
            print(f"Da:   {source_address}")
            print(f"A:    {destination}")
            print(f"Amount: {amount} XRP")
            if memo_text:
                print(f"Memo:   {memo_text}")
            print("=" * 60)

            new_balance = get_balance(source_address, client) / 1_000_000
            print(f"💰 Nuovo saldo: {new_balance} XRP")

        except Exception as e:
            logger.error(f"Errore transazione: {e}", exc_info=True)
            print(f"❌ Errore: {e}")

    def cmd_faucet(self, args: List[str]) -> None:
        if not ensure_wallet_settings(self):
            return

        if self._crypto == "XLM":
            faucet_xlm(self)
        else:
            self._faucet_xrp()

    def _faucet_xrp(self) -> None:
        if self._network != "testnet":
            print("❌ Il faucet XRP funziona SOLO su TESTNET!")
            return

        client = self.client

        try:
            from xrpl.wallet import generate_faucet_wallet
            from xrpl.account import get_balance

            print("\n💰 FAUCET XRP - CREA NUOVO WALLET CON XRP DI TEST")
            print("=" * 60)
            print("🔄 Generazione nuovo wallet...")

            wallet = generate_faucet_wallet(client, debug=True)

            print("\n✅ NUOVO WALLET CREATO E FINANZIATO!")
            print("=" * 60)
            print(f"🏠 Indirizzo: {wallet.classic_address}")
            print(f"🔑 Seed XRP: {wallet.seed}")

            try:
                balance = get_balance(wallet.classic_address, client) / 1_000_000
                print(f"💰 Saldo: {balance} XRP")
            except:
                pass

            print("=" * 60)

            print("\n💡 Vuoi importare questo wallet ora?")
            choice = input("   (s/n): ").strip().lower()

            if choice == 's':
                name = input("   Nome del wallet: ").strip()
                if name:
                    try:
                        result = self.manager.import_wallet(wallet.seed, input_type="xrp_seed")
                        self._save_wallet_as(name)
                        self._set_active_wallet_name(name)
                        print(f"\n✅ Wallet '{name}' importato con successo!")
                        print(f"🏠 Indirizzo: {result['first_address']}")
                        print(f"📁 Salvato in: {self.wallets_dir / f'{name}.json'}")
                    except Exception as e:
                        print(f"❌ Errore nell'import: {e}")
                else:
                    print("❌ Nome non valido.")
            else:
                print("\n💡 Per importare manualmente:")
                print(f"   python3 cli.py wallet NOME")
                print(f"   Inserisci seed: {wallet.seed}")

        except Exception as e:
            logger.error(f"Errore faucet: {e}")
            print(f"\n❌ Errore: {e}")
            print("   Il faucet potrebbe essere in rate limit.")
            print("   Aspetta qualche minuto e riprova.")

    def cmd_history(self, args: List[str]) -> None:
        """Mostra lo storico transazioni"""
        if not ensure_wallet_settings(self):
            return

        if not self.manager.is_loaded():
            print("❌ Nessun wallet caricato!")
            return

        # 🔑 CONTROLLA LA CRYPTO CORRENTE
        if self._crypto == "XLM":
            # Se è XLM, usa il comando XLM
            history_xlm(self, args)
        else:
            # Se è XRP, mostra storico XRP
            self._show_xrp_history(args)

    def _show_xrp_history(self, args: List[str]) -> None:
        limit = 10
        wallet_name = self._get_wallet_display()

        clean_args = []
        i = 0
        while i < len(args):
            if args[i] == "--limit" or args[i] == "-l":
                if i + 1 < len(args) and args[i + 1].isdigit():
                    limit = int(args[i + 1])
                    i += 2
                    continue
                else:
                    i += 1
                    continue
            clean_args.append(args[i])
            i += 1

        if clean_args and (clean_args[0].startswith('r') or clean_args[0].startswith('G')):
            address = clean_args[0]
            display_name = "indirizzo esterno"
        else:
            keyword = clean_args[0] if clean_args else "default"
            index = int(clean_args[1]) if len(clean_args) > 1 else 0
            try:
                address = self.manager.get_address(keyword, index)
                display_name = f"{wallet_name} ({keyword}:{index})"
            except Exception as e:
                print(f"❌ Impossibile trovare l'indirizzo per {keyword}:{index}")
                print(f"   Errore: {e}")
                return

        print(f"\n📜 STORICO TRANSAZIONI")
        print("=" * 80)
        print(f"Wallet:    {display_name}")
        print(f"Indirizzo: {address}")
        print(f"Limite:    {limit} transazioni")
        print("=" * 80)

        try:
            from xrpl.models.requests import AccountTx
            from xrpl.models.response import ResponseStatus
            import base64
            from datetime import datetime

            request = AccountTx(
                account=address,
                ledger_index_min=-1,
                ledger_index_max=-1,
                limit=limit,
                forward=False
            )

            print("🔄 Richiesta al ledger...")
            response = self.client.request(request)

            if response.status != ResponseStatus.SUCCESS:
                print(f"❌ Errore: {response.status}")
                return

            result = response.result
            transactions = result.get("transactions", [])

            if not transactions:
                print("❌ Nessuna transazione trovata.")
                return

            self._print_transactions(transactions, address)

            if self._network == "testnet":
                explorer = f"https://testnet.xrpl.org/accounts/{address}"
            else:
                explorer = f"https://xrpscan.com/account/{address}"
            print(f"\n🔗 Visualizza tutto: {explorer}")

        except Exception as e:
            logger.error(f"Errore storico: {e}", exc_info=True)
            print(f"❌ Errore: {e}")

            if self._network == "testnet":
                explorer = f"https://testnet.xrpl.org/accounts/{address}"
            else:
                explorer = f"https://xrpscan.com/account/{address}"
            print(f"\n🔗 Visualizza su: {explorer}")

    def _print_transactions(self, transactions: List, address: str) -> None:
        from datetime import datetime
        import base64

        print("\n┌────┬─────────────────────┬────────────┬──────────────────┬────────────┬────────────────────────────────────────────┐")
        print(f"│ #  │ Data/Ora            │ Tipo       │ Importo          │ Fee        │ Da/A                                        │")
        print("├────┼─────────────────────┼────────────┼──────────────────┼────────────┼────────────────────────────────────────────┤")

        for idx, tx_data in enumerate(transactions, 1):
            tx = tx_data.get("tx_json", {})
            if not tx:
                continue

            tx_type = tx.get("TransactionType", "Unknown")

            date_str = self._parse_tx_date(tx, tx_data)

            fee_drops = tx.get("Fee", "0")
            try:
                fee_xrp = int(fee_drops) / 1_000_000
                fee_str = f"{fee_xrp:.6f}".rstrip('0').rstrip('.')
                if '.' in fee_str:
                    fee_str = fee_str[:10]
            except:
                fee_str = fee_drops

            if tx_type == "Payment":
                amount = tx.get("Amount", tx.get("DeliverMax", "0"))

                if isinstance(amount, dict):
                    amount_str = f"{amount.get('value', '?')} {amount.get('currency', '?')}"
                else:
                    try:
                        amount_xrp = int(amount) / 1_000_000
                        amount_str = f"{amount_xrp:.6f}".rstrip('0').rstrip('.')
                        if '.' in amount_str:
                            amount_str = amount_str[:12]
                        amount_str += " XRP"
                    except:
                        amount_str = f"{amount} drops"

                sender = tx.get("Account", "unknown")
                destination = tx.get("Destination", "unknown")

                if destination == address:
                    direction = "RICEVUTO"
                    da_a = f"Da: {sender}"
                elif sender == address:
                    direction = "INVIATO"
                    da_a = f"A: {destination}"
                else:
                    direction = "ALTRO"
                    da_a = f"{sender[:10]}...→{destination[:10]}..."

                memos = tx.get("Memos", [])
                if memos:
                    try:
                        memo_dict = memos[0].get("Memo", {})
                        memo_data = memo_dict.get("MemoData", "")
                        if memo_data:
                            while len(memo_data) % 4 != 0:
                                memo_data += '='
                            memo_text = base64.b64decode(memo_data).decode('utf-8', errors='ignore')
                            da_a += f" 📝{memo_text[:12]}"
                    except:
                        pass

                print(f"│ {idx:<2} │ {date_str[:19]:<19} │ {direction:<10} │ {amount_str:<16} │ {fee_str:<10} │ {da_a:<40} │")
            else:
                print(f"│ {idx:<2} │ {date_str[:19]:<19} │ {tx_type:<10} │ {'':<16} │ {fee_str:<10} │ {'':<40} │")

        print("└────┴─────────────────────┴────────────┴──────────────────┴────────────┴────────────────────────────────────────────┘")
        print(f"Totale: {len(transactions)} transazioni mostrate")

    def _parse_tx_date(self, tx: Dict, tx_data: Dict) -> str:
        from datetime import datetime
        
        date_str = ""
        try:
            if "date" in tx:
                ledger_time = tx.get("date", 0)
                if ledger_time:
                    date_obj = datetime.fromtimestamp(ledger_time + 946684800)
                    date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass

        if not date_str and "close_time_iso" in tx_data:
            try:
                close_time = tx_data.get("close_time_iso", "")
                if close_time:
                    date_str = close_time.replace("T", " ").replace("Z", "")[:19]
            except:
                pass
        
        return date_str

    def cmd_derive(self, args: List[str]) -> None:
        if not args:
            print("❌ Specifica una keyword.")
            return

        if not self.manager.is_loaded():
            print("❌ Nessun wallet caricato!")
            print("Usa 'wallet NOME' per selezionare un wallet.")
            return

        wallet_name = self._get_wallet_display()
        keyword = args[0]
        count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
        show_seed = "--show-seed" in args

        results = self.manager.derive_addresses(keyword, count)
        print(f"\n📌 DERIVAZIONE INDIRIZZI ({self._crypto})")
        print("=" * 60)
        print(f"Wallet: {wallet_name}")
        print(f"Keyword: {keyword}")
        print(f"Count: {count}")
        print("-" * 60)

        for info in results:
            print(f"  [{info.index}] {info.address}")
            if show_seed:
                print(f"       Seed: {info.seed_xrp}")

        self.manager.save()
        print(f"\n✅ Generati {len(results)} indirizzi")

    def cmd_list(self, args: List[str]) -> None:
        if not self.manager.is_loaded():
            print("❌ Nessun wallet caricato!")
            print("Usa 'wallet NOME' per selezionare un wallet.")
            return

        wallet_name = self._get_wallet_display()
        keyword_filter = args[0] if args else None

        if keyword_filter:
            derived = self.manager.get_derived_by_keyword(keyword_filter)
        else:
            derived = self.manager.list_derived()

        if not derived:
            print("❌ Nessun indirizzo derivato.")
            return

        print(f"\n📋 INDIRIZZI DERIVATI ({wallet_name} - {self._crypto})")
        print("=" * 60)
        grouped = {}
        for info in derived:
            grouped.setdefault(info.keyword, []).append(info)

        for kw, wallets in sorted(grouped.items()):
            print(f"\n📂 {kw}:")
            for info in sorted(wallets, key=lambda x: x.index):
                print(f"  [{info.index}] {info.address}")

        print(f"\nTotale: {len(derived)}")

    def cmd_show(self, args: List[str]) -> None:
        if not args:
            print("❌ Specifica una keyword.")
            return

        if not self.manager.is_loaded():
            print("❌ Nessun wallet caricato!")
            return

        wallet_name = self._get_wallet_display()
        keyword = args[0]
        index = int(args[1]) if len(args) > 1 else 0

        info = self.manager.get_wallet_info(keyword, index)
        print(f"\n🔍 DETTAGLI INDIRIZZO ({self._crypto})")
        print("=" * 60)
        print(f"Wallet:    {wallet_name}")
        print(f"Keyword:   {info.keyword}")
        print(f"Index:     {info.index}")
        print(f"Indirizzo: {info.address}")
        print(f"Private Key: {info.private_key}")
        print(f"Public Key:  {info.public_key}")

        try:
            if self._crypto == "XRP":
                from xrpl.account import get_balance
                balance_drops = get_balance(info.address, self.client)
                balance = balance_drops / 1_000_000
            else:
                if hasattr(self.manager, 'stellar_manager') and self.manager.stellar_manager:
                    balance = self.manager.stellar_manager.get_balance(info.address)
                else:
                    balance = 0
            symbol = "XRP" if self._crypto == "XRP" else "XLM"
            print(f"💰 Saldo:   {balance:.6f} {symbol}")
        except Exception as e:
            print(f"💰 Saldo:   ❌ {e}")

    def cmd_reset(self, args: List[str]) -> None:
        if "--force" not in args:
            print("⚠️  Usa 'reset --force' per confermare")
            return
        self.manager.reset()
        if self.active_wallet_name_file.exists():
            self.active_wallet_name_file.unlink()
        print("✅ Wallet resettato")

    def cmd_help(self, args: Optional[List[str]] = None) -> None:
        print("""
╔══════════════════════════════════════════════════════════════════╗
║           XRP / XLM WALLET CLI - GUIDA COMPLETA                ║
╚══════════════════════════════════════════════════════════════════╝

GESTIONE WALLET:
  wallet [NOME]           Crea o cambia wallet (chiede crypto e rete)
  switch NOME             Cambia wallet attivo (usa rete salvata)
  list-wallets            Lista tutti i wallet (con indirizzo)
  delete-wallet NOME      Elimina un wallet (solo file locale)
  crypto XRP|XLM          Cambia criptovaluta

RUBRICA:
  contact-add NOME INDIRIZZO [KEYWORD] [INDEX] [NOTE]  Aggiungi contatto
  contact-list            Lista contatti
  contact-delete NOME     Elimina contatto

OPERAZIONI:
  derive KEYWORD [COUNT]  Deriva indirizzi
  list [KEYWORD]          Lista indirizzi derivati
  show KEYWORD [INDEX]    Mostra dettagli indirizzo
  info                    Info wallet + saldo + fee
  balance [KEYWORD] [INDEX]  Saldo
  send DEST AMOUNT [KEY] [IDX] ["MEMO"]  Invia XRP o XLM
  faucet                  Ottieni XRP/XLM di test (solo TESTNET)
  history [KEYWORD] [INDEX] [--limit N]  Storico transazioni
  reset --force           Cancella wallet attuale

ESEMPI:
  # Cambia crypto
  crypto XLM

  # Crea wallet XLM
  wallet stellar_wallet

  # Invia XLM
  send G... 10 "memo test"

  # Rubrica
  contact-add mario G... cliente 0 "Fornitore"
  send mario 10
══════════════════════════════════════════════════════════════════
""")

    def run(self, args: Optional[List[str]] = None) -> None:
        if args is None:
            args = sys.argv[1:]

        if not args:
            self._show_wallet_menu()
            return

        network = None
        crypto = None
        clean_args = []
        i = 0
        while i < len(args):
            if args[i] == "--network" and i + 1 < len(args):
                network = args[i + 1]
                i += 2
                continue
            if args[i] == "--crypto" and i + 1 < len(args):
                crypto = args[i + 1].upper()
                i += 2
                continue
            clean_args.append(args[i])
            i += 1

        if network is None:
            network = self._load_network_from_active_wallet()

        if crypto is None:
            crypto = self._load_crypto_from_active_wallet()

        try:
            self._set_network(network)
            self._set_crypto(crypto)
        except Exception as e:
            print(f"❌ {e}")
            return

        if not clean_args:
            self._show_wallet_menu()
            return

        command = clean_args[0]
        if command in self.commands:
            try:
                self.commands[command](clean_args[1:])
            except Exception as e:
                logger.error(f"Errore comando {command}: {e}", exc_info=True)
                print(f"❌ Errore: {e}")
        else:
            print(f"❌ Comando sconosciuto: {command}")
            self.cmd_help([])

    def _load_network_from_active_wallet(self) -> str:
        active_name = self._get_active_wallet_name()
        if active_name:
            wallet_file = self.wallets_dir / f"{active_name}.json"
            if wallet_file.exists():
                try:
                    with open(wallet_file) as f:
                        data = json.load(f)
                        network = data.get("network", "testnet")
                        logger.info(f"🌐 Usando rete salvata nel wallet: {network.upper()}")
                        return network
                except:
                    pass
        return "testnet"

    def _load_crypto_from_active_wallet(self) -> str:
        active_name = self._get_active_wallet_name()
        if active_name:
            wallet_file = self.wallets_dir / f"{active_name}.json"
            if wallet_file.exists():
                try:
                    with open(wallet_file) as f:
                        data = json.load(f)
                        crypto = data.get("crypto_type", "XRP")
                        logger.info(f"🪙 Usando crypto salvata nel wallet: {crypto}")
                        return crypto
                except:
                    pass
        return "XRP"

    def _show_wallet_menu(self) -> None:
        print("\n" + "=" * 60)
        print(f"              ⧫ {self._crypto} WALLET MANAGER")
        print("=" * 60)

        wallets = self._get_wallet_list()
        active = self._get_active_wallet_name()

        if active:
            print(f"\n📂 Wallet attivo: {active} ({self._crypto})")
        else:
            print("\n📂 Nessun wallet attivo.")

        print("\n" + "-" * 60)

        if wallets:
            self._show_wallet_menu_with_wallets(wallets, active)
        else:
            self._show_wallet_menu_empty()

        print(f"\n💡 Per usare i comandi direttamente:")
        print(f"   python3 cli.py --network {self._network} --crypto {self._crypto} balance")
        print(f"   python3 cli.py --network {self._network} --crypto {self._crypto} send ...")

    def _show_wallet_menu_with_wallets(self, wallets: List[Dict], active: str) -> None:
        print("\n📋 WALLET DISPONIBILI:")
        print(f"{'#':<3} {'Nome':<18} {'Crypto':<6} {'Rete':<8} {'Indirizzo':<35}")
        print("-" * 60)

        for i, w in enumerate(wallets, 1):
            marker = "▶" if w["name"] == active else " "
            crypto = w.get("crypto", "XRP")
            network = w.get("network", "testnet")
            address_display = w["address"] if w["address"] != "unknown" else "❌ Non disponibile"
            print(f"{i}. {marker} {w['name']:<17} {crypto:<6} {network:<8} {address_display:<35}")

        print(f"\n  {len(wallets)+1}. Crea nuovo wallet")
        print(f"  {len(wallets)+2}. Importa wallet")
        print(f"  0. Esci")

        try:
            choice = input("\nScelta: ").strip()
            if not choice:
                return

            choice_int = int(choice)

            if choice_int == 0:
                print("👋 Arrivederci!")
                sys.exit(0)

            elif choice_int == len(wallets) + 1:
                name = input("Nome del nuovo wallet: ").strip()
                if name:
                    self.cmd_wallet([name])

            elif choice_int == len(wallets) + 2:
                name = input("Nome del wallet da importare: ").strip()
                if name:
                    self.cmd_wallet([name])

            elif 1 <= choice_int <= len(wallets):
                name = wallets[choice_int - 1]["name"]
                self._switch_wallet(name)
                self.cmd_info([])

            else:
                print("❌ Scelta non valida.")

        except ValueError:
            print("❌ Inserisci un numero valido.")
        except KeyboardInterrupt:
            print("\n👋 Arrivederci!")
            sys.exit(0)

    def _show_wallet_menu_empty(self) -> None:
        print("\n📋 NESSUN WALLET SALVATO")
        print("\nCosa vuoi fare?")
        print("  1. Crea un nuovo wallet")
        print("  2. Importa un wallet")
        print("  0. Esci")

        try:
            choice = input("\nScelta: ").strip()
            if choice == "1":
                name = input("Nome del nuovo wallet: ").strip()
                if name:
                    self.cmd_wallet([name])
            elif choice == "2":
                name = input("Nome del wallet da importare: ").strip()
                if name:
                    self.cmd_wallet([name])
            elif choice == "0":
                print("👋 Arrivederci!")
                sys.exit(0)
            else:
                print("❌ Scelta non valida.")
        except KeyboardInterrupt:
            print("\n👋 Arrivederci!")
            sys.exit(0)


def main() -> None:
    cli = XRPCLI()
    cli.run()


if __name__ == "__main__":
    main()