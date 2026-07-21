"""
commands/xlm_commands.py - Comandi per XLM (Stellar)
"""

import logging
import requests
from typing import Optional, Dict, Any

from utils.helpers import (
    ensure_wallet_settings, 
    save_address_to_wallet, 
    get_wallet_display,
    format_address,
    validate_xlm_address
)

logger = logging.getLogger(__name__)

# Import condizionale per stellar_sdk
try:
    from stellar_sdk import Keypair, TransactionBuilder, Network, Asset
    from stellar_sdk.memo import IdMemo, TextMemo
    from stellar_sdk.exceptions import NotFoundError, BadRequestError
    STELLAR_SDK_AVAILABLE = True
except ImportError:
    STELLAR_SDK_AVAILABLE = False
    logger.warning("⚠️ stellar-sdk non installato. I comandi XLM non saranno disponibili.")

    # Classi stub per evitare errori di import
    class Keypair: pass
    class TransactionBuilder: pass
    class Network: pass
    class Asset: pass
    class IdMemo: pass
    class TextMemo: pass


def _check_stellar_available() -> bool:
    """Verifica che stellar-sdk sia disponibile"""
    if not STELLAR_SDK_AVAILABLE:
        print("❌ stellar-sdk non installato!")
        print("   Installa con: pip install stellar-sdk")
        return False
    return True


def send_xlm(cli_instance, args):
    """Invia XLM (Stellar) con supporto memo"""
    if not _check_stellar_available():
        return
    
    if not ensure_wallet_settings(cli_instance):
        print("❌ Nessun wallet caricato. Usa 'wallet NOME'.")
        return

    if not args or len(args) < 2:
        print("❌ Specifica destinatario e importo.")
        print("Esempio: send G... 10")
        print("         send G... 10 --memo-id 12345")
        print("         send G... 10 'memo testo'")
        return

    if not cli_instance.manager.is_loaded():
        print("❌ Nessun wallet caricato!")
        return

    dest_arg = args[0]

    try:
        amount = float(args[1])
        if amount <= 0:
            print("❌ L'importo deve essere maggiore di 0")
            return
    except ValueError:
        print("❌ Importo non valido.")
        return

    # Parsing argomenti
    memo_text = ""
    memo_id = None
    parse_args = list(args)

    if len(parse_args) > 2:
        i = 2
        while i < len(parse_args):
            if parse_args[i] == "--memo-id" and i + 1 < len(parse_args):
                try:
                    memo_id = int(parse_args[i + 1])
                    if memo_id < 0:
                        print("❌ Memo ID deve essere positivo")
                        return
                    i += 2
                except ValueError:
                    print("❌ Memo ID deve essere un numero")
                    return
            else:
                arg = parse_args[i]
                if arg.startswith('"') and arg.endswith('"'):
                    memo_text = arg[1:-1]
                elif arg.startswith("'") and arg.endswith("'"):
                    memo_text = arg[1:-1]
                else:
                    memo_text = arg
                i += 1

    # Cerca contatto in rubrica
    contatto = cli_instance._cerca_contatto(dest_arg)
    if contatto:
        destination = contatto.get("indirizzo")
        print(f"📒 Contatto trovato: {dest_arg} → {destination}")
    else:
        destination = dest_arg

    if not validate_xlm_address(destination):
        print("❌ Destinazione non valida per XLM (deve iniziare con G e avere almeno 56 caratteri)")
        return

    try:
        source_address = cli_instance.manager.get_address()
        wallet_name = get_wallet_display(cli_instance.active_wallet_name_file)
        rete = "TESTNET" if cli_instance._network == "testnet" else "MAINNET"

        print(f"\n📤 INVIO XLM ({rete})")
        print("=" * 60)
        print(f"Wallet:    {wallet_name}")
        print(f"Da:        {source_address}")
        print(f"A:         {destination}")
        print(f"Importo:   {amount} XLM")
        if memo_text:
            print(f"📝 Memo:    {memo_text}")
        if memo_id is not None:
            print(f"📝 Memo ID: {memo_id}")
        print("=" * 60)

        # Verifica che il manager Stellar sia inizializzato
        cli_instance.manager._init_stellar()
        if not cli_instance.manager.stellar_manager:
            print("❌ Manager Stellar non inizializzato")
            return

        # Verifica saldo
        balance = cli_instance.manager.stellar_manager.get_balance(source_address)
        if balance < amount:
            print(f"❌ Saldo insufficiente!")
            print(f"   Hai:    {balance:.6f} XLM")
            print(f"   Servono: {amount} XLM")
            return

        # Prepara la transazione
        keypair = Keypair.from_secret(cli_instance.manager.base_seed_stellar)
        source_account = cli_instance.manager.stellar_manager.server.load_account(keypair.public_key)

        builder = TransactionBuilder(
            source_account=source_account,
            network_passphrase=cli_instance.manager.stellar_manager.network_passphrase,
            base_fee=100
        )
        builder.set_timeout(300)

        builder.append_payment_op(
            destination=destination,
            amount=str(amount),
            asset=Asset.native()
        )

        if memo_id is not None:
            builder.add_memo(IdMemo(memo_id))
        elif memo_text:
            builder.add_memo(TextMemo(memo_text[:64]))

        # Firma e invia
        transaction = builder.build()
        transaction.sign(keypair)
        response = cli_instance.manager.stellar_manager.server.submit_transaction(transaction)

        if response.get('hash'):
            print("\n✅ TRANSAZIONE INVIATA!")
            print("=" * 60)
            print(f"Hash:   {response.get('hash', 'unknown')}")
            print(f"Ledger: {response.get('ledger', 0)}")
            print("=" * 60)

            # Mostra nuovo saldo
            new_balance = cli_instance.manager.stellar_manager.get_balance(source_address)
            print(f"💰 Nuovo saldo: {new_balance:.6f} XLM")
        else:
            print(f"❌ Errore nella transazione: {response}")

    except BadRequestError as e:
        print(f"❌ Errore richiesta: {e}")
        if "insufficient balance" in str(e):
            print("   Saldo insufficiente per la transazione (inclusa la fee)")
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore invio XLM: {e}", exc_info=True)


def history_xlm(cli_instance, args):
    """Storico transazioni per XLM (Stellar) usando l'API Horizon"""
    if not _check_stellar_available():
        return
    
    if not ensure_wallet_settings(cli_instance):
        print("❌ Nessun wallet caricato. Usa 'wallet NOME'.")
        return

    # 🔑 PARSE --limit
    limit = 100
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

    try:
        address = cli_instance.manager.get_address()
        wallet_name = get_wallet_display(cli_instance.active_wallet_name_file)

        print(f"\n📜 STORICO TRANSAZIONI XLM")
        print("=" * 80)
        print(f"Wallet:    {wallet_name}")
        print(f"Indirizzo: {address}")
        print(f"Limite:    {limit} transazioni")
        print("=" * 80)

        if cli_instance._network == "mainnet":
            horizon_url = "https://horizon.stellar.org"
        else:
            horizon_url = "https://horizon-testnet.stellar.org"

        # 🔑 LIMITE DINAMICO
        url = f"{horizon_url}/accounts/{address}/payments?limit={limit}&order=desc"
        logger.info(f"Richiesta Horizon: {url}")
        
        response = requests.get(url, timeout=30)
        data = response.json()

        if response.status_code != 200:
            error = data.get('detail', 'Errore sconosciuto')
            print(f"❌ Errore Horizon: {error}")
            return

        payments = data.get('_embedded', {}).get('records', [])
        if not payments:
            print("❌ Nessun pagamento trovato.")
            return

        # 🔑 TABELLA CON INDIRIZZI COMPLETI
        print("\n┌────┬─────────────────────┬────────────────┬──────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────┐")
        print(f"│ #  │ Data/Ora            │ Tipo           │ Importo      │ Da/A                                                                                                │")
        print("├────┼─────────────────────┼────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────┤")

        type_map = {
            'payment': 'Pagamento',
            'create_account': 'Crea Account',
            'account_merge': 'Fusione',
            'path_payment_strict_send': 'Path Pay',
            'path_payment_strict_receive': 'Path Pay',
            'manage_sell_offer': 'Offerta',
            'manage_buy_offer': 'Offerta',
            'set_options': 'Opzioni',
            'change_trust': 'Trustline',
            'allow_trust': 'Autorizza',
            'manage_data': 'Data',
            'bump_sequence': 'Sequenza',
            'inflation': 'Inflazione'
        }

        # 🔑 MOSTRA SOLO FINO AL LIMITE
        for idx, payment in enumerate(payments[:limit], 1):
            created_at = payment.get('created_at', '')
            date_str = created_at.replace('T', ' ').replace('Z', '')[:19] if created_at else ''
            op_type = payment.get('type', 'unknown')
            display_type = type_map.get(op_type, op_type[:14])

            amount_str = ""
            from_to = ""

            if op_type == 'payment':
                amount = float(payment.get('amount', 0))
                asset_type = payment.get('asset_type', 'native')
                asset_code = "XLM" if asset_type == 'native' else payment.get('asset_code', '?')
                from_acct = payment.get('from', '')
                to_acct = payment.get('to', '')
                
                # 🔑 INDIRIZZI COMPLETI
                if to_acct == address:
                    from_to = f"Da: {from_acct}"
                elif from_acct == address:
                    from_to = f"A: {to_acct}"
                else:
                    from_to = f"{from_acct} → {to_acct}"
                amount_str = f"{amount:.6f} {asset_code}"

            elif op_type == 'create_account':
                amount = float(payment.get('starting_balance', 0))
                to_acct = payment.get('account', '')
                from_acct = payment.get('funder', '')
                if to_acct == address:
                    from_to = f"Da: {from_acct}"
                else:
                    from_to = f"A: {to_acct}"
                amount_str = f"{amount:.6f} XLM"

            elif op_type == 'account_merge':
                into_acct = payment.get('into', '')
                from_acct = payment.get('account', '')
                from_to = f"{from_acct} → {into_acct}"
                amount_str = ""

            elif op_type in ['path_payment_strict_send', 'path_payment_strict_receive']:
                amount = float(payment.get('amount', 0))
                from_acct = payment.get('from', '')
                to_acct = payment.get('to', '')
                if to_acct == address:
                    from_to = f"Da: {from_acct}"
                else:
                    from_to = f"A: {to_acct}"
                amount_str = f"{amount:.6f} XLM"

            elif op_type in ['manage_sell_offer', 'manage_buy_offer']:
                selling = payment.get('selling', {})
                buying = payment.get('buying', {})
                if op_type == 'manage_sell_offer':
                    from_to = f"Vende {selling.get('asset_code', 'XLM')}"
                else:
                    from_to = f"Compra {buying.get('asset_code', 'XLM')}"
                amount_str = ""

            else:
                from_to = payment.get('source_account', '')
                amount_str = ""

            # 🔑 TRONCA SOLO PER DISPLAY SE L'INDIRIZZO È TROPPO LUNGO
            if len(from_to) > 100:
                from_to_display = from_to[:50] + "..." + from_to[-50:]
            else:
                from_to_display = from_to

            print(f"│ {idx:<2} │ {date_str[:19]:<19} │ {display_type:<14} │ {amount_str:<30} │ {from_to_display:<100} │")

        print("└────┴─────────────────────┴────────────────┴──────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────┘")

        # Link esploratore
        if cli_instance._network == "mainnet":
            explorer = f"https://stellar.expert/explorer/public/account/{address}"
        else:
            explorer = f"https://stellar.expert/explorer/testnet/account/{address}"
        print(f"\n🔗 Visualizza tutto: {explorer}")

        # Saldo attuale
        balance = cli_instance.manager.get_balance()
        print(f"💰 Saldo attuale: {balance:.6f} XLM")

        # 🔑 STATISTICHE
        print(f"📊 Mostrate {min(len(payments), limit)} di {len(payments)} transazioni")

    except requests.exceptions.Timeout:
        print("❌ Timeout nella richiesta a Horizon")
    except requests.exceptions.ConnectionError:
        print("❌ Errore di connessione a Horizon")
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore storico XLM: {e}", exc_info=True)


def info_xlm(cli_instance, args):
    """Info wallet per XLM (Stellar)"""
    if not _check_stellar_available():
        return
    
    if not ensure_wallet_settings(cli_instance):
        print("❌ Nessun wallet caricato. Usa 'wallet NOME'.")
        return

    if not cli_instance.manager.is_loaded():
        print("❌ Nessun wallet caricato.")
        return

    info = cli_instance.manager.get_seed_info()
    rete = "TESTNET" if cli_instance._network == "testnet" else "MAINNET"
    wallet_name = get_wallet_display(cli_instance.active_wallet_name_file)

    try:
        address = cli_instance.manager.get_address("default", 0)
        save_address_to_wallet(cli_instance, wallet_name, address)
    except Exception as e:
        address = f"❌ {e}"

    print("\n📋 INFO WALLET XLM")
    print("=" * 60)
    print(f"Wallet:    {wallet_name}")
    print(f"Rete:      {rete}")
    print(f"Crypto:    XLM")
    print(f"Tipo seed: {info.get('seed_type')}")
    print(f"🏠 Indirizzo: {address}")

    if address and not str(address).startswith("❌"):
        try:
            balance = cli_instance.manager.get_balance()
            print(f"💰 Saldo:   {balance:.6f} XLM")
        except Exception as e:
            print(f"💰 Saldo:   ❌ {e}")

    # Mostra informazioni seed
    if info.get('seed_type') == 'bip39':
        print(f"Parole: {info.get('word_count')}")
        print(f"Frase: {info.get('seed_phrase')}")
        if info.get('passphrase'):
            print(f"🔐 Passphrase: {info.get('passphrase')}")
    elif info.get('seed_type') == 'stellar_seed':
        print(f"Seed Stellar: {info.get('seed_stellar')}")

    # Info account Stellar
    try:
        cli_instance.manager._init_stellar()
        if cli_instance.manager.stellar_manager:
            account_info = cli_instance.manager.stellar_manager.get_account_info(address)
            if 'error' not in account_info:
                print(f"\n📊 Info Account Stellar:")
                print(f"   Sequence: {account_info.get('sequence', 'N/A')}")
                print(f"   Signers: {len(account_info.get('signers', []))}")
                thresholds = account_info.get('thresholds', {})
                if thresholds:
                    print(f"   Thresholds: low={thresholds.get('low_threshold')}, "
                          f"med={thresholds.get('med_threshold')}, "
                          f"high={thresholds.get('high_threshold')}")
    except Exception as e:
        logger.warning(f"Errore info account: {e}")

    derived = cli_instance.manager.list_derived()
    print(f"\nIndirizzi derivati: {len(derived)}")

    print("\n" + "=" * 60)


def faucet_xlm(cli_instance):
    """Faucet per XLM (Stellar Testnet)"""
    if not _check_stellar_available():
        return
    
    if not ensure_wallet_settings(cli_instance):
        print("❌ Nessun wallet caricato. Usa 'wallet NOME'.")
        return

    if cli_instance._network != "testnet":
        print("❌ Il faucet XLM funziona SOLO su TESTNET!")
        return

    try:
        address = cli_instance.manager.get_address()
        if not address:
            print("❌ Nessun wallet caricato. Crea un wallet prima.")
            return

        print(f"\n💰 FAUCET XLM - RICHIESTA XLM DI TEST")
        print("=" * 60)
        print(f"📤 Richiesta per: {address}")

        response = requests.get(
            f"https://friendbot.stellar.org/?addr={address}",
            timeout=30
        )

        if response.status_code == 200:
            print("✅ XLM DI TEST RICEVUTI!")
            
            # Mostra nuovo saldo
            cli_instance.manager._init_stellar()
            if cli_instance.manager.stellar_manager:
                balance = cli_instance.manager.stellar_manager.get_balance(address)
                print(f"💰 Nuovo saldo: {balance:.6f} XLM")
            else:
                print("💰 Controlla il saldo con 'balance'")
        else:
            print(f"❌ Errore: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Dettaglio: {error_data.get('detail', 'N/A')}")
            except:
                print(f"   Risposta: {response.text[:200]}")
                
    except requests.exceptions.Timeout:
        print("❌ Timeout nella richiesta a Friendbot")
    except requests.exceptions.ConnectionError:
        print("❌ Errore di connessione a Friendbot")
    except Exception as e:
        print(f"❌ Errore: {e}")
        logger.error(f"Errore faucet XLM: {e}", exc_info=True)