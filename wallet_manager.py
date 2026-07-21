#!/usr/bin/env python3
"""
wallet_manager.py - Gestione wallet XRP e XLM (Stellar)
Versione 2.0 - Ottimizzata e completa
"""

import json
import base58
import hashlib
import re
import subprocess
import os
import sys
import logging
import time
from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

from mnemonic import Mnemonic
from bip32 import BIP32
from xrpl.core import keypairs
from xrpl.wallet import Wallet as XRPWallet
from xrpl.constants import CryptoAlgorithm
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import ecdsa

# Stellar imports con gestione errori
try:
    from stellar_sdk import Keypair, Server, TransactionBuilder, Network, Asset, Memo
    from stellar_sdk.exceptions import NotFoundError, BadRequestError
    from stellar_sdk.memo import IdMemo, TextMemo
    from stellar_sdk.sep.mnemonic import StellarMnemonic
    STELLAR_AVAILABLE = True
    STELLAR_IMPORT_ERROR = None
except ImportError as e:
    STELLAR_AVAILABLE = False
    STELLAR_IMPORT_ERROR = str(e)
    logging.warning(f"stellar-sdk non disponibile: {e}")

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CryptoType(Enum):
    XRP = "XRP"
    XLM = "XLM"


class NetworkType(Enum):
    MAINNET = "mainnet"
    TESTNET = "testnet"
    DEVNET = "devnet"


class SeedType(Enum):
    BIP39 = "bip39"
    NUMBERS = "numbers"
    PRIVATE_KEY = "private_key"
    XRP_SEED = "xrp_seed"
    STELLAR_SEED = "stellar_seed"


@dataclass
class WalletInfo:
    keyword: str
    index: int
    address: str
    private_key: str
    public_key: str
    seed_xrp: str
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WalletInfo':
        return cls(**data)


class XamanSecretNumbersBridge:
    """Bridge per convertire i numeri segreti Xaman in seed XRP"""
    
    def __init__(self):
        self._use_python_fallback = False
        self._nodejs_available = self._check_nodejs()
        if self._nodejs_available:
            self._ensure_library()
        else:
            logger.warning("Node.js non disponibile, uso fallback Python")
            self._use_python_fallback = True
    
    def _get_node_modules_path(self) -> Optional[str]:
        """Trova il percorso di node_modules (nel bundle o nella directory corrente)"""
        if hasattr(sys, '_MEIPASS'):
            bundle_path = os.path.join(sys._MEIPASS, "node_modules")
            if os.path.exists(bundle_path):
                return bundle_path
        
        # Cerca nella directory corrente
        possible_paths = [
            "./node_modules",
            "./node_bundle/node_modules",
            "../node_modules",
            "../../node_modules"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _check_nodejs(self) -> bool:
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, 
                                  check=True,
                                  timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _ensure_library(self) -> None:
        """Assicura che la libreria sia disponibile"""
        node_modules_path = self._get_node_modules_path()
        
        if node_modules_path is None:
            logger.warning("node_modules non trovata")
            self._use_python_fallback = True
            return
        
        # Verifica se esiste il package
        pkg_new = os.path.join(node_modules_path, "@xrplf", "secret-numbers")
        pkg_old = os.path.join(node_modules_path, "xrpl-secret-numbers")
        
        if os.path.exists(pkg_new):
            logger.info(f"✅ @xrplf/secret-numbers trovato in: {node_modules_path}")
        elif os.path.exists(pkg_old):
            logger.info(f"✅ xrpl-secret-numbers trovato in: {node_modules_path}")
        else:
            logger.warning("Nessun package trovato, uso fallback Python")
            self._use_python_fallback = True
    
    def numbers_to_seed(self, numbers: List[str]) -> str:
        if self._use_python_fallback:
            return self._numbers_to_seed_python(numbers)
        return self._numbers_to_seed_nodejs(numbers)
    
    def numbers_to_address(self, numbers: List[str]) -> str:
        if self._use_python_fallback:
            seed = self._numbers_to_seed_python(numbers)
            public_key, _ = keypairs.derive_keypair(seed)
            return keypairs.derive_classic_address(public_key)
        return self._numbers_to_address_nodejs(numbers)
    
    def _numbers_to_seed_nodejs(self, numbers: List[str]) -> str:
        """Conversione via Node.js - usa il package corretto"""
        node_modules_path = self._get_node_modules_path()
        
        if node_modules_path is None:
            node_modules_path = "./node_modules"
        
        script = f'''
        const path = require('path');
        const modulePath = path.resolve('{node_modules_path}');
        
        let Account;
        let useOld = false;
        
        try {{
            const pkg = require(path.join(modulePath, '@xrplf', 'secret-numbers'));
            Account = pkg.Account;
        }} catch (e) {{
            try {{
                const pkg = require(path.join(modulePath, 'xrpl-secret-numbers'));
                Account = pkg.Account;
                useOld = true;
            }} catch (e2) {{
                console.error('Nessun package trovato');
                process.exit(1);
            }}
        }}
        
        const secret = '{ " ".join(numbers) }';
        let account;
        
        if (useOld) {{
            account = new Account(secret);
        }} else {{
            try {{
                account = new Account(secret);
            }} catch (e) {{
                const numbersArray = secret.split(' ');
                account = new Account(numbersArray);
            }}
        }}
        
        console.log(JSON.stringify({{
            familySeed: account.getFamilySeed(),
            address: account.getAddress()
        }}));
        '''
        
        try:
            result = subprocess.run(['node', '-e', script], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode != 0:
                raise RuntimeError(f"Errore Node.js: {result.stderr}")
            data = json.loads(result.stdout)
            return data['familySeed']
        except Exception as e:
            raise RuntimeError(f"Errore conversione numeri: {e}")
    
    def _numbers_to_address_nodejs(self, numbers: List[str]) -> str:
        """Conversione via Node.js per indirizzo"""
        node_modules_path = self._get_node_modules_path()
        
        if node_modules_path is None:
            node_modules_path = "./node_modules"
        
        script = f'''
        const path = require('path');
        const modulePath = path.resolve('{node_modules_path}');
        
        let Account;
        let useOld = false;
        
        try {{
            const pkg = require(path.join(modulePath, '@xrplf', 'secret-numbers'));
            Account = pkg.Account;
        }} catch (e) {{
            try {{
                const pkg = require(path.join(modulePath, 'xrpl-secret-numbers'));
                Account = pkg.Account;
                useOld = true;
            }} catch (e2) {{
                console.error('Nessun package trovato');
                process.exit(1);
            }}
        }}
        
        const secret = '{ " ".join(numbers) }';
        let account;
        
        if (useOld) {{
            account = new Account(secret);
        }} else {{
            try {{
                account = new Account(secret);
            }} catch (e) {{
                const numbersArray = secret.split(' ');
                account = new Account(numbersArray);
            }}
        }}
        
        console.log(JSON.stringify({{
            familySeed: account.getFamilySeed(),
            address: account.getAddress()
        }}));
        '''
        
        try:
            result = subprocess.run(['node', '-e', script], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode != 0:
                raise RuntimeError(f"Errore Node.js: {result.stderr}")
            data = json.loads(result.stdout)
            return data['address']
        except Exception as e:
            raise RuntimeError(f"Errore conversione numeri: {e}")
    
    def _numbers_to_seed_python(self, numbers: List[str]) -> str:
        """Fallback Python - usa 3 bytes per numero"""
        if len(numbers) != 8:
            raise ValueError(f"Servono 8 numeri, hai {len(numbers)}")
        
        for num in numbers:
            if not num.isdigit() or len(num) != 6:
                raise ValueError(f"Numero non valido: {num}")
            if not (0 <= int(num) <= 999999):
                raise ValueError(f"Numero fuori range: {num}")
        
        entropy = bytearray()
        for num_str in numbers:
            num = int(num_str)
            entropy.extend(num.to_bytes(3, 'big'))
        
        full_bytes = bytes([0x01]) + bytes(entropy)
        return base58.b58encode(full_bytes).decode()


class StellarManager:
    """Gestione wallet Stellar (XLM)"""
    
    def __init__(self, network: str = "testnet"):
        if not STELLAR_AVAILABLE:
            raise ImportError(f"stellar-sdk non installato: {STELLAR_IMPORT_ERROR}")
        
        self.network = network
        self._init_server(network)
    
    def _init_server(self, network: str) -> None:
        if network == "mainnet":
            self.server = Server("https://horizon.stellar.org")
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
        else:
            self.server = Server("https://horizon-testnet.stellar.org")
            self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
    
    def set_network(self, network: str) -> None:
        self.network = network
        self._init_server(network)
    
    def create_wallet(self) -> Dict[str, str]:
        keypair = Keypair.random()
        return {
            "public_key": keypair.public_key,
            "secret_key": keypair.secret,
            "seed": keypair.secret
        }
    
    def from_seed(self, seed: str) -> Dict[str, str]:
        try:
            keypair = Keypair.from_secret(seed)
            return {
                "public_key": keypair.public_key,
                "secret_key": keypair.secret,
                "address": keypair.public_key
            }
        except Exception as e:
            raise ValueError(f"Seed Stellar non valido: {e}")
    
    def get_balance(self, address: str) -> float:
        try:
            account = self.server.accounts().account_id(address).call()
            for balance in account.get('balances', []):
                if balance['asset_type'] == 'native':
                    return float(balance['balance'])
            return 0.0
        except NotFoundError:
            return 0.0
        except Exception as e:
            logger.error(f"Errore saldo Stellar: {e}")
            return 0.0
    
    def fund_testnet(self, address: str) -> bool:
        if self.network != "testnet":
            logger.error("Friendbot funziona solo su TESTNET!")
            return False
        
        try:
            import requests
            url = f"https://friendbot.stellar.org?addr={address}"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                logger.info(f"✅ Wallet {address} finanziato su Testnet!")
                return True
            else:
                logger.error(f"Errore Friendbot: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Errore: {e}")
            return False
    
    def send_payment(self, from_secret: str, to_address: str, amount: float, 
                    memo_text: str = "", memo_id: int = None) -> Dict:
        try:
            keypair = Keypair.from_secret(from_secret)
            source_account = self.server.load_account(keypair.public_key)
            
            builder = TransactionBuilder(
                source_account=source_account,
                network_passphrase=self.network_passphrase,
                base_fee=100
            )
            builder.set_timeout(300)
            
            builder.append_payment_op(
                destination=to_address,
                amount=str(amount),
                asset=Asset.native()
            )
            
            if memo_id is not None:
                builder.add_memo(IdMemo(memo_id))
            elif memo_text:
                builder.add_memo(TextMemo(memo_text[:28]))
            
            transaction = builder.build()
            transaction.sign(keypair)
            response = self.server.submit_transaction(transaction)
            
            return {
                "success": True,
                "hash": response.get("hash", "unknown"),
                "ledger": response.get("ledger", 0)
            }
        except Exception as e:
            logger.error(f"Errore invio XLM: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_account_info(self, address: str) -> Dict:
        try:
            account = self.server.accounts().account_id(address).call()
            return {
                "address": address,
                "balance": self.get_balance(address),
                "sequence": account.get('sequence', 0),
                "signers": account.get('signers', []),
                "thresholds": account.get('thresholds', {}),
                "flags": account.get('flags', {})
            }
        except NotFoundError:
            return {"error": "Account non trovato su questa rete"}
        except Exception as e:
            return {"error": str(e)}


class HybridXRPManager:
    """Manager principale per wallet XRP e XLM"""
    
    def __init__(self, data_file: str = "wallet_data.json"):
        self.data_file = Path(data_file)
        self.mnemo = Mnemonic("english")
        
        # Stato wallet
        self.seed_type: Optional[str] = None
        self.seed_phrase: Optional[str] = None
        self.seed_numbers: Optional[List[str]] = None
        self.passphrase: str = ""
        self.base_private: Optional[bytes] = None
        self.base_seed_xrp: Optional[str] = None
        self.base_seed_stellar: Optional[str] = None
        self._correct_address: Optional[str] = None
        self.network: str = "testnet"
        self.crypto_type: str = "XRP"
        
        # Cache e dati derivati
        self._derived_wallets: Dict[str, WalletInfo] = {}
        self._balance_cache: Dict[str, Tuple[float, float]] = {}
        self._cache_ttl: int = 60  # secondi
        
        # Managers
        self.stellar_manager: Optional[StellarManager] = None
        self._bridge: Optional[XamanSecretNumbersBridge] = None
        
        # Carica wallet salvato
        self.load()
    
    @property
    def bridge(self) -> XamanSecretNumbersBridge:
        if self._bridge is None:
            self._bridge = XamanSecretNumbersBridge()
        return self._bridge
    
    # ============================================================
    # METODI PRIVATI
    # ============================================================
    
    def _private_key_to_seed(self, private_key_hex: str) -> str:
        hash_bytes = hashlib.sha256(bytes.fromhex(private_key_hex)).digest()
        entropy = hash_bytes[:16].hex()
        return keypairs.generate_seed(entropy=entropy)
    
    def _private_key_to_keypair(self, private_key_hex: str) -> Tuple[str, str]:
        private_key_bytes = bytes.fromhex(private_key_hex)
        sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
        vk = sk.get_verifying_key()
        vk_bytes = vk.to_string()
        
        if vk_bytes[31] % 2 == 0:
            public_key_bytes = b'\x02' + vk_bytes[:32]
        else:
            public_key_bytes = b'\x03' + vk_bytes[:32]
        
        public_key_hex = public_key_bytes.hex()
        address = keypairs.derive_classic_address(public_key_hex)
        return public_key_hex, address
    
    def _format_numbers(self, numbers: List[str]) -> str:
        return " ".join(numbers)
    
    def _clean_numbers_input(self, raw_input: str) -> List[str]:
        cleaned = re.sub(r'[A-Ha-h]:', '', raw_input)
        cleaned = re.sub(r',', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned.split()
    
    def _bip39_to_private_key(self, phrase: str, passphrase: str = "") -> str:
        seed_bytes = self.mnemo.to_seed(phrase, passphrase)
        bip32 = BIP32.from_seed(seed_bytes)
        child = bip32.get_privkey_from_path("m/44'/144'/0'/0/0")
        return child.hex()
    
    def _derive_private_key(self, keyword: str = "default", index: int = 0) -> bytes:
        if self.base_private is None:
            raise ValueError("❌ Nessun wallet caricato!")
        
        salt = hashlib.sha256(f"hybrid_xrp_derivation_{self.crypto_type}".encode()).digest()
        
        hkdf = HKDF(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            info=f"{keyword}:{index}:{self.crypto_type}".encode(),
            backend=default_backend()
        )
        return hkdf.derive(self.base_private)
    
    def _init_stellar(self) -> None:
        if self.stellar_manager is None:
            if not STELLAR_AVAILABLE:
                raise ImportError(f"stellar-sdk non installato: {STELLAR_IMPORT_ERROR}")
            self.stellar_manager = StellarManager(self.network)
        else:
            self.stellar_manager.set_network(self.network)
    
    def _get_xrp_balance(self, address: str) -> float:
        try:
            from xrpl.account import get_balance
            from xrpl.clients import JsonRpcClient
            
            if self.network == "mainnet":
                client = JsonRpcClient("https://s1.ripple.com:51234/")
            else:
                client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
            
            balance = get_balance(address, client)
            return balance / 1_000_000
        except Exception as e:
            logger.error(f"Errore saldo XRP: {e}")
            return 0.0
    
    def _numbers_to_seed_fallback(self, numbers: List[str]) -> str:
        seed_bytes = b""
        for num_str in numbers:
            num = int(num_str)
            if num < 0 or num > 999999:
                raise ValueError(f"Numero fuori range: {num}")
            seed_bytes += num.to_bytes(3, 'big')
        full_bytes = bytes([0x01]) + seed_bytes
        return base58.b58encode(full_bytes).decode()
    
    # ============================================================
    # METODI PUBBLICI - CONFIGURAZIONE
    # ============================================================
    
    def set_network(self, network: str) -> None:
        if network not in [n.value for n in NetworkType]:
            raise ValueError(f"Rete non supportata: {network}")
        self.network = network
        if self.stellar_manager is not None:
            self.stellar_manager.set_network(network)
    
    def set_crypto(self, crypto_type: str) -> None:
        if crypto_type not in [c.value for c in CryptoType]:
            raise ValueError(f"Crypto non supportata: {crypto_type}")
        
        self.crypto_type = crypto_type
        if crypto_type == "XLM" and STELLAR_AVAILABLE:
            self._init_stellar()
    
    # ============================================================
    # METODI PUBBLICI - CREAZIONE WALLET
    # ============================================================
    
    def create_new_wallet_bip39(self, passphrase: str = "", strength: int = 128) -> Dict[str, Any]:
        if self.crypto_type == "XLM":
            return self.create_new_wallet_stellar(passphrase, strength)
        
        self.seed_type = SeedType.BIP39.value
        self.seed_phrase = self.mnemo.generate(strength=strength)
        self.seed_numbers = None
        self.passphrase = passphrase
        
        private_key_hex = self._bip39_to_private_key(self.seed_phrase, passphrase)
        public_key, address = self._private_key_to_keypair(private_key_hex)
        self.base_private = bytes.fromhex(private_key_hex)
        self._correct_address = address
        
        entropy = private_key_hex[:32]
        self.base_seed_xrp = keypairs.generate_seed(entropy=entropy)
        
        self.save()
        
        return {
            "seed_type": SeedType.BIP39.value,
            "seed_phrase": self.seed_phrase,
            "passphrase": passphrase,
            "word_count": len(self.seed_phrase.split()),
            "first_address": address,
            "first_private_key": private_key_hex,
            "first_public_key": public_key,
            "first_seed_xrp": self.base_seed_xrp,
        }
    
    def create_new_wallet_stellar(self, passphrase: str = "", strength: int = 128) -> Dict[str, Any]:
        if not STELLAR_AVAILABLE:
            raise ImportError(f"stellar-sdk non installato: {STELLAR_IMPORT_ERROR}")
        
        mnemonic = StellarMnemonic("english")
        seed_phrase = mnemonic.generate(strength=strength)
        
        self.seed_phrase = seed_phrase
        self.seed_type = SeedType.BIP39.value
        self.seed_numbers = None
        self.passphrase = passphrase
        self.crypto_type = "XLM"
        
        keypair = Keypair.from_mnemonic_phrase(seed_phrase)
        
        self.base_seed_stellar = keypair.secret
        self._correct_address = keypair.public_key
        self.base_private = None
        self.base_seed_xrp = None
        
        self.save()
        
        return {
            "seed_type": SeedType.BIP39.value,
            "seed_phrase": self.seed_phrase,
            "passphrase": passphrase,
            "word_count": len(self.seed_phrase.split()),
            "first_address": keypair.public_key,
            "first_private_key": keypair.secret,
            "first_public_key": keypair.public_key,
            "first_seed_stellar": keypair.secret,
        }
    
    def create_new_wallet_numbers(self) -> Dict[str, Any]:
        seed = keypairs.generate_seed(algorithm=CryptoAlgorithm.ED25519)
        public_key, private_key = keypairs.derive_keypair(seed)
        address = keypairs.derive_classic_address(public_key)
        
        decoded = base58.b58decode(seed)
        seed_bytes = decoded[1:]
        secret_numbers = [f"{int.from_bytes(seed_bytes[i:i+2], 'big'):06d}" 
                         for i in range(0, 16, 2)]
        
        self.seed_type = SeedType.NUMBERS.value
        self.seed_numbers = secret_numbers
        self.seed_phrase = None
        self.passphrase = ""
        self.base_private = bytes.fromhex(private_key)
        self.base_seed_xrp = seed
        self._correct_address = address
        
        self.save()
        
        return {
            "seed_type": SeedType.NUMBERS.value,
            "secret_numbers": secret_numbers,
            "secret_numbers_formatted": " ".join(secret_numbers),
            "first_address": address,
            "first_seed_xrp": seed,
        }
    
    # ============================================================
    # METODI PUBBLICI - IMPORTAZIONE
    # ============================================================
    
    def detect_input_type(self, seed_input: Union[str, List[str]]) -> str:
        """Rileva automaticamente il tipo di seed"""
        if isinstance(seed_input, list):
            return SeedType.NUMBERS.value
        
        if isinstance(seed_input, str):
            if len(seed_input) == 64 and all(c in "0123456789abcdefABCDEF" for c in seed_input):
                return SeedType.PRIVATE_KEY.value
            
            if seed_input.startswith("s"):
                return SeedType.XRP_SEED.value
            
            if seed_input.startswith("S"):
                return SeedType.STELLAR_SEED.value
            
            numbers = self._clean_numbers_input(seed_input)
            if len(numbers) == 8 and all(p.isdigit() and len(p) == 6 for p in numbers):
                return SeedType.NUMBERS.value
            
            return SeedType.BIP39.value
        
        return SeedType.BIP39.value
    
    def import_wallet(self, seed_input: Union[str, List[str]], 
                     passphrase: str = "", 
                     input_type: str = "auto") -> Dict[str, Any]:
        
        if input_type == "auto":
            input_type = self.detect_input_type(seed_input)
        
        if input_type == SeedType.BIP39.value:
            if self.crypto_type == "XLM":
                return self._import_bip39_as_stellar(seed_input, passphrase)
            return self._import_bip39(seed_input, passphrase)
        
        elif input_type == SeedType.NUMBERS.value:
            return self._import_numbers(seed_input)
        
        elif input_type == SeedType.PRIVATE_KEY.value:
            return self._import_private_key(seed_input)
        
        elif input_type == SeedType.XRP_SEED.value:
            return self._import_xrp_seed(seed_input)
        
        elif input_type == SeedType.STELLAR_SEED.value:
            return self._import_stellar_seed(seed_input)
        
        else:
            raise ValueError(f"Tipo non supportato: {input_type}")
    
    def _import_bip39(self, seed_phrase: str, passphrase: str = "") -> Dict[str, Any]:
        if not self.mnemo.check(seed_phrase):
            raise ValueError("❌ Seed phrase non valida!")
        
        self.seed_type = SeedType.BIP39.value
        self.seed_phrase = seed_phrase
        self.seed_numbers = None
        self.passphrase = passphrase
        
        private_key_hex = self._bip39_to_private_key(seed_phrase, passphrase)
        public_key, address = self._private_key_to_keypair(private_key_hex)
        self.base_private = bytes.fromhex(private_key_hex)
        self._correct_address = address
        
        entropy = private_key_hex[:32]
        self.base_seed_xrp = keypairs.generate_seed(entropy=entropy)
        
        self.save()
        
        return {
            "seed_type": SeedType.BIP39.value,
            "seed_phrase": seed_phrase,
            "passphrase": passphrase,
            "word_count": len(seed_phrase.split()),
            "first_address": address,
            "first_private_key": private_key_hex,
            "first_public_key": public_key,
            "first_seed_xrp": self.base_seed_xrp,
        }
    
    def _import_bip39_as_stellar(self, seed_phrase: str, passphrase: str = "") -> Dict[str, Any]:
        if not STELLAR_AVAILABLE:
            raise ImportError(f"stellar-sdk non installato: {STELLAR_IMPORT_ERROR}")
        
        mnemonic = StellarMnemonic("english")
        if not mnemonic.check(seed_phrase):
            raise ValueError("❌ Seed phrase non valida!")
        
        self.seed_type = SeedType.BIP39.value
        self.seed_phrase = seed_phrase
        self.seed_numbers = None
        self.passphrase = passphrase
        self.crypto_type = "XLM"
        
        keypair = Keypair.from_mnemonic_phrase(seed_phrase)
        
        self.base_seed_stellar = keypair.secret
        self._correct_address = keypair.public_key
        self.base_private = None
        self.base_seed_xrp = None
        
        self.save()
        
        return {
            "seed_type": SeedType.BIP39.value,
            "seed_phrase": seed_phrase,
            "passphrase": passphrase,
            "word_count": len(seed_phrase.split()),
            "first_address": keypair.public_key,
            "first_private_key": keypair.secret,
            "first_public_key": keypair.public_key,
            "first_seed_stellar": keypair.secret,
        }
    
    def _import_private_key(self, private_key_hex: str) -> Dict[str, Any]:
        try:
            public_key, address = self._private_key_to_keypair(private_key_hex)
            
            self.seed_type = SeedType.PRIVATE_KEY.value
            self.seed_phrase = None
            self.seed_numbers = None
            self.passphrase = ""
            self.base_private = bytes.fromhex(private_key_hex)
            self._correct_address = address
            
            entropy = private_key_hex[:32]
            self.base_seed_xrp = keypairs.generate_seed(entropy=entropy)
            
            self.save()
            
            return {
                "seed_type": SeedType.PRIVATE_KEY.value,
                "first_address": address,
                "first_private_key": private_key_hex,
                "first_public_key": public_key,
                "first_seed_xrp": self.base_seed_xrp,
            }
        except Exception as e:
            raise ValueError(f"Private key non valida: {e}")
    
    def _import_xrp_seed(self, xrp_seed: str) -> Dict[str, Any]:
        try:
            wallet = XRPWallet.from_seed(xrp_seed)
            
            self.seed_type = SeedType.XRP_SEED.value
            self.seed_phrase = None
            self.seed_numbers = None
            self.passphrase = ""
            self.base_private = bytes.fromhex(wallet.private_key)
            self.base_seed_xrp = xrp_seed
            self._correct_address = wallet.classic_address
            
            self.save()
            
            return {
                "seed_type": SeedType.XRP_SEED.value,
                "first_address": wallet.classic_address,
                "first_private_key": wallet.private_key,
                "first_public_key": wallet.public_key,
                "first_seed_xrp": xrp_seed,
            }
        except Exception as e:
            raise ValueError(f"Seed XRP non valido: {e}")
    
    def _import_stellar_seed(self, stellar_seed: str) -> Dict[str, Any]:
        if not STELLAR_AVAILABLE:
            raise ImportError(f"stellar-sdk non installato: {STELLAR_IMPORT_ERROR}")
        
        try:
            self._init_stellar()
            wallet = self.stellar_manager.from_seed(stellar_seed)
            
            self.seed_type = SeedType.STELLAR_SEED.value
            self.seed_phrase = None
            self.seed_numbers = None
            self.passphrase = ""
            self.base_seed_stellar = stellar_seed
            self._correct_address = wallet["public_key"]
            
            self.save()
            
            return {
                "seed_type": SeedType.STELLAR_SEED.value,
                "first_address": wallet["public_key"],
                "first_private_key": wallet["secret_key"],
                "first_seed_stellar": stellar_seed,
            }
        except Exception as e:
            raise ValueError(f"Seed Stellar non valido: {e}")
    
    def _import_numbers(self, numbers: Union[str, List[str]]) -> Dict[str, Any]:
        if isinstance(numbers, str):
            numbers = self._clean_numbers_input(numbers)
        
        if len(numbers) != 8:
            raise ValueError(f"❌ Servono 8 numeri, hai {len(numbers)}")
        
        for num in numbers:
            if not num.isdigit() or len(num) != 6:
                raise ValueError(f"❌ '{num}' non valido (servono 6 cifre)")
        
        try:
            xrp_seed = self.bridge.numbers_to_seed(numbers)
            address = self.bridge.numbers_to_address(numbers)
            wallet = XRPWallet.from_seed(xrp_seed)
            
            self.seed_type = SeedType.NUMBERS.value
            self.seed_numbers = numbers
            self.seed_phrase = None
            self.passphrase = ""
            self.base_private = bytes.fromhex(wallet.private_key)
            self.base_seed_xrp = xrp_seed
            self._correct_address = address
            
            self.save()
            
            return {
                "seed_type": SeedType.NUMBERS.value,
                "secret_numbers": numbers,
                "secret_numbers_formatted": " ".join(numbers),
                "first_address": address,
                "first_private_key": wallet.private_key,
                "first_public_key": wallet.public_key,
                "first_seed_xrp": xrp_seed,
            }
        except Exception as e:
            raise ValueError(f"Numeri non validi: {e}")
    
    def validate_seed(self, seed_input: Union[str, List[str]]) -> Dict[str, Any]:
        """Valida un seed e restituisce informazioni"""
        input_type = self.detect_input_type(seed_input)
        result = {
            "valid": False,
            "type": input_type,
            "details": ""
        }
        
        try:
            if input_type == SeedType.BIP39.value:
                if isinstance(seed_input, str):
                    result["valid"] = self.mnemo.check(seed_input)
                    if result["valid"]:
                        result["word_count"] = len(seed_input.split())
                        result["details"] = f"Valid BIP39 mnemonic with {result['word_count']} words"
                    else:
                        result["details"] = "Invalid BIP39 mnemonic"
            
            elif input_type == SeedType.NUMBERS.value:
                numbers = seed_input if isinstance(seed_input, list) else self._clean_numbers_input(seed_input)
                if len(numbers) == 8 and all(n.isdigit() and len(n) == 6 for n in numbers):
                    result["valid"] = True
                    result["details"] = f"Valid Xaman secret numbers: {len(numbers)} numbers"
                else:
                    result["details"] = "Invalid numbers format"
            
            elif input_type == SeedType.XRP_SEED.value:
                try:
                    XRPWallet.from_seed(seed_input)
                    result["valid"] = True
                    result["details"] = "Valid XRP seed"
                except:
                    result["details"] = "Invalid XRP seed"
            
            elif input_type == SeedType.STELLAR_SEED.value:
                try:
                    if STELLAR_AVAILABLE:
                        Keypair.from_secret(seed_input)
                        result["valid"] = True
                        result["details"] = "Valid Stellar seed"
                    else:
                        result["details"] = "stellar-sdk not available"
                except:
                    result["details"] = "Invalid Stellar seed"
            
            elif input_type == SeedType.PRIVATE_KEY.value:
                try:
                    bytes.fromhex(seed_input)
                    result["valid"] = True
                    result["details"] = "Valid private key (hex)"
                except:
                    result["details"] = "Invalid private key"
        
        except Exception as e:
            result["details"] = f"Error: {str(e)}"
        
        return result
    
    # ============================================================
    # METODI PUBBLICI - OTTENERE WALLET
    # ============================================================
    
    def get_wallet(self, keyword: str = "default", index: int = 0) -> Union[XRPWallet, Dict]:
        if self.crypto_type == "XLM":
            return self._get_stellar_wallet()
        return self._get_xrp_wallet(keyword, index)
    
    def _get_xrp_wallet(self, keyword: str = "default", index: int = 0) -> XRPWallet:
        if self.seed_type in [SeedType.NUMBERS.value, SeedType.XRP_SEED.value]:
            if self.base_seed_xrp is not None:
                return XRPWallet.from_seed(self.base_seed_xrp)
        
        if self.base_private is None:
            raise ValueError("❌ Nessun wallet caricato!")
        
        if keyword == "default" and index == 0:
            private_key_hex = self.base_private.hex()
        else:
            private_key_bytes = self._derive_private_key(keyword, index)
            private_key_hex = private_key_bytes.hex()
        
        public_key, _ = self._private_key_to_keypair(private_key_hex)
        return XRPWallet(
            public_key=public_key,
            private_key=private_key_hex,
            algorithm=CryptoAlgorithm.SECP256K1
        )
    
    def _get_stellar_wallet(self) -> Dict[str, str]:
        if self.base_seed_stellar:
            self._init_stellar()
            return self.stellar_manager.from_seed(self.base_seed_stellar)
        
        if self.seed_phrase and self.crypto_type == "XLM":
            from stellar_sdk import Keypair
            keypair = Keypair.from_mnemonic_phrase(self.seed_phrase)
            self.base_seed_stellar = keypair.secret
            self._correct_address = keypair.public_key
            self.save()
            return {
                "public_key": keypair.public_key,
                "secret_key": keypair.secret,
                "address": keypair.public_key
            }
        
        raise ValueError("❌ Nessun wallet Stellar caricato!")
    
    def get_address(self, keyword: str = "default", index: int = 0) -> str:
        if self._correct_address and keyword == "default" and index == 0:
            return self._correct_address
        
        wallet = self.get_wallet(keyword, index)
        if self.crypto_type == "XLM":
            return wallet.get("public_key", "")
        return wallet.classic_address
    
    def get_wallet_info(self, keyword: str = "default", index: int = 0) -> WalletInfo:
        wallet = self.get_wallet(keyword, index)
        
        if self.crypto_type == "XLM":
            return WalletInfo(
                keyword=keyword,
                index=index,
                address=wallet.get("public_key", ""),
                private_key=wallet.get("secret_key", ""),
                public_key=wallet.get("public_key", ""),
                seed_xrp=self.base_seed_stellar or "",
                created_at=datetime.now().isoformat()
            )
        
        return WalletInfo(
            keyword=keyword,
            index=index,
            address=wallet.classic_address,
            private_key=wallet.private_key,
            public_key=wallet.public_key,
            seed_xrp=self._private_key_to_seed(wallet.private_key),
            created_at=datetime.now().isoformat()
        )
    
    # ============================================================
    # METODI PUBBLICI - DERIVAZIONE
    # ============================================================
    
    def derive_addresses(self, keyword: str = "default", count: int = 5) -> List[WalletInfo]:
        results = []
        for i in range(count):
            info = self.get_wallet_info(keyword, i)
            results.append(info)
            self._derived_wallets[f"{keyword}:{i}"] = info
        self.save()
        return results
    
    def batch_derive_addresses(self, keywords: List[str], count: int = 5) -> Dict[str, List[WalletInfo]]:
        """Deriva indirizzi per multiple keywords"""
        results = {}
        for keyword in keywords:
            results[keyword] = self.derive_addresses(keyword, count)
        return results
    
    def get_addresses_by_range(self, start: int = 0, end: int = 10, keyword: str = "default") -> List[str]:
        """Ottiene una lista di indirizzi in un range"""
        addresses = []
        for i in range(start, end):
            try:
                addr = self.get_address(keyword, i)
                addresses.append(addr)
            except:
                addresses.append(None)
        return addresses
    
    def list_derived(self) -> List[WalletInfo]:
        return list(self._derived_wallets.values())
    
    def get_derived_by_keyword(self, keyword: str) -> List[WalletInfo]:
        return [w for w in self._derived_wallets.values() if w.keyword == keyword]
    
    # ============================================================
    # METODI PUBBLICI - SALDO E TRANSAZIONI
    # ============================================================
    
    def get_balance(self, force_refresh: bool = False) -> float:
        address = self.get_address()
        
        # Controlla cache
        if not force_refresh and address in self._balance_cache:
            balance, timestamp = self._balance_cache[address]
            if time.time() - timestamp < self._cache_ttl:
                return balance
        
        # Ottieni balance
        if self.crypto_type == "XLM":
            self._init_stellar()
            balance = self.stellar_manager.get_balance(address)
        else:
            balance = self._get_xrp_balance(address)
        
        # Aggiorna cache
        self._balance_cache[address] = (balance, time.time())
        return balance
    
    def get_account_info(self) -> Dict:
        """Ottiene informazioni complete dell'account"""
        address = self.get_address()
        
        if self.crypto_type == "XLM":
            self._init_stellar()
            return self.stellar_manager.get_account_info(address)
        
        # XRP account info
        try:
            from xrpl.account import get_account_info
            from xrpl.clients import JsonRpcClient
            
            if self.network == "mainnet":
                client = JsonRpcClient("https://s1.ripple.com:51234/")
            else:
                client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
            
            info = get_account_info(address, client)
            return {
                "address": address,
                "balance": self.get_balance(),
                "sequence": info.get('Sequence', 0),
                "flags": info.get('Flags', 0)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def fund_testnet(self) -> bool:
        if self.crypto_type != "XLM":
            logger.error("Friendbot funziona solo per XLM")
            return False
        
        address = self.get_address()
        self._init_stellar()
        return self.stellar_manager.fund_testnet(address)
    
    def send_payment(self, to_address: str, amount: float, 
                    memo_text: str = "", memo_id: int = None) -> Dict:
        if self.crypto_type == "XLM":
            self._init_stellar()
            from_secret = self.base_seed_stellar
            if not from_secret:
                raise ValueError("❌ Nessun seed Stellar disponibile")
            return self.stellar_manager.send_payment(
                from_secret, to_address, amount, memo_text, memo_id
            )
        
        raise NotImplementedError("Usa il metodo send del CLI per XRP")
    
    # ============================================================
    # METODI PUBBLICI - ESPORTAZIONE/IMPORTAZIONE
    # ============================================================
    
    def export_wallet(self, format: str = "json", include_private: bool = False) -> Union[str, Dict]:
        """Esporta wallet in vari formati"""
        if not self.is_loaded():
            raise ValueError("Nessun wallet caricato")
        
        data = {
            "type": self.crypto_type,
            "network": self.network,
            "seed_type": self.seed_type,
            "address": self._correct_address,
            "created_at": datetime.now().isoformat(),
            "version": "2.0"
        }
        
        if include_private:
            if self.crypto_type == "XLM" and self.base_seed_stellar:
                data["seed"] = self.base_seed_stellar
            elif self.base_seed_xrp:
                data["seed"] = self.base_seed_xrp
            elif self.base_private:
                data["private_key"] = self.base_private.hex()
        
        if self.seed_type == SeedType.BIP39.value:
            data["mnemonic"] = self.seed_phrase
            data["passphrase"] = self.passphrase
        
        elif self.seed_type == SeedType.NUMBERS.value:
            data["numbers"] = self.seed_numbers
            data["numbers_formatted"] = " ".join(self.seed_numbers)
        
        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format == "dict":
            return data
        else:
            raise ValueError(f"Formato non supportato: {format}")
    
    def import_wallet_from_file(self, filepath: str) -> Dict[str, Any]:
        """Importa wallet da file esportato"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Ripristina crypto_type se specificato
        if "type" in data:
            self.crypto_type = data["type"]
        
        if "network" in data:
            self.network = data["network"]
        
        if "mnemonic" in data:
            return self.import_wallet(
                data["mnemonic"], 
                passphrase=data.get("passphrase", ""),
                input_type=SeedType.BIP39.value
            )
        elif "numbers" in data:
            return self.import_wallet(
                data["numbers"], 
                input_type=SeedType.NUMBERS.value
            )
        elif "seed" in data:
            return self.import_wallet(data["seed"], input_type="auto")
        elif "private_key" in data:
            return self.import_wallet(
                data["private_key"], 
                input_type=SeedType.PRIVATE_KEY.value
            )
        else:
            raise ValueError("Formato file non riconosciuto")
    
    # ============================================================
    # METODI PUBBLICI - STATO E PERSISTENZA
    # ============================================================
    
    def is_loaded(self) -> bool:
        return (self.base_private is not None or 
                self.base_seed_xrp is not None or 
                self.base_seed_stellar is not None)
    
    def get_seed_info(self) -> Dict[str, Any]:
        if not self.is_loaded():
            return {"loaded": False}
        
        info = {
            "loaded": True,
            "seed_type": self.seed_type,
            "crypto_type": self.crypto_type,
            "network": self.network,
            "address": self._correct_address,
            "has_balance": False
        }
        
        # Prova a ottenere il saldo
        try:
            balance = self.get_balance()
            info["balance"] = balance
            info["has_balance"] = True
        except:
            pass
        
        if self.seed_type == SeedType.BIP39.value:
            info.update({
                "seed_phrase": self.seed_phrase,
                "word_count": len(self.seed_phrase.split()) if self.seed_phrase else 0,
                "passphrase": self.passphrase,
                "seed_xrp": self.base_seed_xrp,
                "seed_stellar": self.base_seed_stellar,
            })
        
        elif self.seed_type == SeedType.NUMBERS.value:
            info.update({
                "secret_numbers": self.seed_numbers,
                "formatted": self._format_numbers(self.seed_numbers) if self.seed_numbers else "",
                "seed_xrp": self.base_seed_xrp,
            })
        
        elif self.seed_type == SeedType.PRIVATE_KEY.value:
            info.update({
                "private_key": self.base_private.hex() if self.base_private else None,
                "seed_xrp": self.base_seed_xrp,
            })
        
        elif self.seed_type == SeedType.XRP_SEED.value:
            info.update({
                "seed_xrp": self.base_seed_xrp,
            })
        
        elif self.seed_type == SeedType.STELLAR_SEED.value:
            info.update({
                "seed_stellar": self.base_seed_stellar,
            })
        
        return info
    
    def reset(self) -> None:
        self.seed_type = None
        self.seed_phrase = None
        self.seed_numbers = None
        self.passphrase = ""
        self.base_private = None
        self.base_seed_xrp = None
        self.base_seed_stellar = None
        self._correct_address = None
        self._derived_wallets = {}
        self._balance_cache = {}
        self.stellar_manager = None
        
        if self.data_file.exists():
            self.data_file.unlink()
    
    def save(self) -> None:
        if not self.is_loaded():
            return
        
        current_address = self._correct_address
        if not current_address:
            try:
                current_address = self.get_address("default", 0)
            except:
                current_address = None
        
        data = {
            "seed_type": self.seed_type,
            "seed_phrase": self.seed_phrase,
            "seed_numbers": self.seed_numbers,
            "passphrase": self.passphrase,
            "base_private": self.base_private.hex() if self.base_private else None,
            "base_seed_xrp": self.base_seed_xrp,
            "base_seed_stellar": self.base_seed_stellar,
            "current_address": current_address,
            "crypto_type": self.crypto_type,
            "network": self.network,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "derived_wallets": [info.to_dict() for info in self._derived_wallets.values()]
        }
        
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✅ Wallet salvato in {self.data_file}")
    
    def load(self) -> bool:
        if not self.data_file.exists():
            return False
        
        try:
            with open(self.data_file) as f:
                data = json.load(f)
            
            self.seed_type = data.get("seed_type")
            self.seed_phrase = data.get("seed_phrase")
            self.seed_numbers = data.get("seed_numbers")
            self.passphrase = data.get("passphrase", "")
            self.base_seed_xrp = data.get("base_seed_xrp")
            self.base_seed_stellar = data.get("base_seed_stellar")
            self._correct_address = data.get("current_address")
            self.crypto_type = data.get("crypto_type", "XRP")
            self.network = data.get("network", "testnet")
            
            if self.crypto_type == "XLM" and STELLAR_AVAILABLE:
                self._init_stellar()
            
            base_private_hex = data.get("base_private")
            if base_private_hex:
                self.base_private = bytes.fromhex(base_private_hex)
            elif self.seed_type == SeedType.BIP39.value and self.seed_phrase:
                if self.crypto_type == "XLM":
                    from stellar_sdk import Keypair
                    keypair = Keypair.from_mnemonic_phrase(self.seed_phrase)
                    self.base_seed_stellar = keypair.secret
                    self._correct_address = keypair.public_key
                else:
                    private_key_hex = self._bip39_to_private_key(self.seed_phrase, self.passphrase)
                    self.base_private = bytes.fromhex(private_key_hex)
                    if not self._correct_address:
                        _, addr = self._private_key_to_keypair(private_key_hex)
                        self._correct_address = addr
                    if not self.base_seed_xrp:
                        entropy = private_key_hex[:32]
                        self.base_seed_xrp = keypairs.generate_seed(entropy=entropy)
            
            elif self.seed_type == SeedType.NUMBERS.value and self.seed_numbers:
                try:
                    xrp_seed = self.bridge.numbers_to_seed(self.seed_numbers)
                    self.base_seed_xrp = xrp_seed
                    wallet = XRPWallet.from_seed(xrp_seed)
                    self.base_private = bytes.fromhex(wallet.private_key)
                    if not self._correct_address:
                        self._correct_address = wallet.classic_address
                except Exception as e:
                    logger.error(f"Errore caricamento numeri: {e}")
                    xrp_seed = self._numbers_to_seed_fallback(self.seed_numbers)
                    self.base_seed_xrp = xrp_seed
                    public_key, private_key = keypairs.derive_keypair(xrp_seed)
                    self.base_private = bytes.fromhex(private_key)
                    if not self._correct_address:
                        self._correct_address = keypairs.derive_classic_address(public_key)
            
            for wallet_data in data.get("derived_wallets", []):
                try:
                    info = WalletInfo.from_dict(wallet_data)
                    self._derived_wallets[f"{info.keyword}:{info.index}"] = info
                except Exception as e:
                    logger.warning(f"Errore caricamento wallet derivato: {e}")
            
            logger.info(f"✅ Wallet caricato da {self.data_file}")
            return True
            
        except Exception as e:
            logger.error(f"Errore caricamento wallet: {e}")
            return False


# ============================================================
# FUNZIONE DI UTILITY
# ============================================================

def create_manager(data_file: str = "wallet_data.json", 
                  crypto_type: str = "XRP", 
                  network: str = "testnet") -> HybridXRPManager:
    """Factory function per creare un manager configurato"""
    manager = HybridXRPManager(data_file)
    manager.set_crypto(crypto_type)
    manager.set_network(network)
    return manager


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    # Test rapido
    manager = HybridXRPManager("test_wallet.json")
    
    print("=" * 60)
    print("🧪 TEST WALLET MANAGER")
    print("=" * 60)
    
    # Crea wallet XRP
    print("\n📤 Creazione wallet XRP...")
    wallet = manager.create_new_wallet_bip39()
    print(f"✅ Address: {wallet['first_address']}")
    print(f"✅ Seed XRP: {wallet['first_seed_xrp']}")
    
    # Ottieni saldo
    balance = manager.get_balance()
    print(f"💰 Saldo: {balance} XRP")
    
    # Deriva indirizzi
    print("\n📤 Derivazione indirizzi...")
    addresses = manager.derive_addresses("test", 3)
    for addr in addresses:
        print(f"  - {addr.address}")
    
    print("\n✅ Test completato!")