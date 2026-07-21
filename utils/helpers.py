"""
utils/helpers.py - Funzioni di utilità per il CLI
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_active_wallet_name(active_wallet_name_file: Path) -> Optional[str]:
    """
    Ottiene il nome del wallet attivo.
    Restituisce None se non esiste o è vuoto.
    """
    if active_wallet_name_file.exists():
        try:
            with open(active_wallet_name_file, 'r') as f:
                name = f.read().strip()
                if name:
                    return name
        except Exception as e:
            logger.warning(f"Errore lettura wallet attivo: {e}")
    return None


def get_wallet_display(active_wallet_name_file: Path) -> str:
    """Restituisce il nome del wallet o 'nessuno'"""
    name = get_active_wallet_name(active_wallet_name_file)
    return name if name else "nessun wallet"


def ensure_wallet_settings(cli_instance) -> bool:
    """
    Legge il wallet attivo e imposta network e crypto di conseguenza.
    Modifica direttamente l'istanza del CLI.
    
    Returns:
        bool: True se il wallet è stato caricato correttamente
    """
    wallet_name = get_active_wallet_name(cli_instance.active_wallet_name_file)
    if not wallet_name:
        logger.debug("Nessun wallet attivo")
        return False

    wallet_file = cli_instance.wallets_dir / f"{wallet_name}.json"
    if not wallet_file.exists():
        logger.warning(f"File wallet {wallet_file} non trovato")
        return False

    try:
        with open(wallet_file, 'r') as f:
            data = json.load(f)

        saved_network = data.get("network", "testnet")
        saved_crypto = data.get("crypto_type", "XRP")

        # Imposta rete se diversa
        if saved_network != cli_instance._network:
            logger.info(f"🌐 Passo a rete: {saved_network.upper()}")
            cli_instance._set_network(saved_network)

        # Imposta crypto se diversa
        if saved_crypto != cli_instance._crypto:
            logger.info(f"🪙 Passo a crypto: {saved_crypto}")
            cli_instance._set_crypto(saved_crypto)

        # Carica il wallet nel manager se non è già caricato
        if not cli_instance.manager.is_loaded():
            try:
                # Carica i dati del wallet
                cli_instance.manager.seed_type = data.get("seed_type")
                cli_instance.manager.seed_phrase = data.get("seed_phrase")
                cli_instance.manager.seed_numbers = data.get("seed_numbers")
                cli_instance.manager.passphrase = data.get("passphrase", "")
                
                base_private_hex = data.get("base_private")
                if base_private_hex:
                    cli_instance.manager.base_private = bytes.fromhex(base_private_hex)
                
                cli_instance.manager.base_seed_xrp = data.get("base_seed_xrp")
                cli_instance.manager.base_seed_stellar = data.get("base_seed_stellar")
                cli_instance.manager._correct_address = data.get("current_address")
                cli_instance.manager.crypto_type = saved_crypto
                cli_instance.manager.network = saved_network
                
                # Carica wallet derivati
                cli_instance.manager._derived_wallets = {}
                for w_data in data.get("derived_wallets", []):
                    try:
                        from wallet_manager import WalletInfo
                        info = WalletInfo.from_dict(w_data)
                        cli_instance.manager._derived_wallets[f"{info.keyword}:{info.index}"] = info
                    except Exception as e:
                        logger.warning(f"Errore caricamento wallet derivato: {e}")
                
                logger.info(f"✅ Wallet caricato: {wallet_name}")
            except Exception as e:
                logger.error(f"Errore caricamento wallet: {e}")
                return False

        return True

    except json.JSONDecodeError as e:
        logger.error(f"File wallet corrotto: {e}")
        return False
    except Exception as e:
        logger.error(f"Errore caricamento impostazioni: {e}")
        return False


def save_address_to_wallet(cli_instance, name: str, address: str) -> bool:
    """
    Salva l'indirizzo nel file del wallet.
    """
    if not name:
        return False
    
    target = cli_instance.wallets_dir / f"{name}.json"
    if not target.exists():
        logger.warning(f"Wallet {name} non trovato per salvare indirizzo")
        return False
    
    try:
        with open(target, 'r') as f:
            data = json.load(f)
        
        data["current_address"] = address
        
        with open(target, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✅ Indirizzo salvato per wallet {name}")
        return True
    except Exception as e:
        logger.error(f"Errore salvataggio indirizzo: {e}")
        return False


def format_address(address: str, length: int = 8) -> str:
    """Formatta un indirizzo per display (es. r...xyz)"""
    if len(address) <= length * 2:
        return address
    return f"{address[:length]}...{address[-length:]}"


def validate_xrp_address(address: str) -> bool:
    """Valida un indirizzo XRP"""
    return address.startswith('r') and len(address) >= 25


def validate_xlm_address(address: str) -> bool:
    """Valida un indirizzo XLM"""
    return address.startswith('G') and len(address) >= 56


def get_network_display(network: str) -> str:
    """Restituisce il nome display della rete"""
    display = {
        "mainnet": "MAINNET",
        "testnet": "TESTNET",
        "devnet": "DEVNET"
    }
    return display.get(network, network.upper())