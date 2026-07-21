#!/usr/bin/env python3
"""
ui_web.py - Interfaccia web per XRP/XLM Wallet Manager
Usa Flask con autenticazione e sessioni sicure
"""

import json
import hashlib
import secrets
import io
import base64
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, send_file
from functools import wraps
from cli import XRPCLI

# 🔑 QR CODE
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("⚠️ qrcode non installato. Installa con: pip install qrcode pillow")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(hours=1)

# Limite di tentativi di login
MAX_LOGIN_ATTEMPTS = 5
LOGIN_COOLDOWN = 300  # secondi

class SecureXRPManager:
    def __init__(self):
        self.cli = XRPCLI()
        self._load_config()
        
    def _load_config(self):
        """Carica la configurazione web"""
        config_file = Path("web_config.json")
        if config_file.exists():
            with open(config_file) as f:
                self.config = json.load(f)
            # 🔑 SE USERS È VUOTO, AGGIUNGI ADMIN
            if not self.config.get("users") or len(self.config["users"]) == 0:
                self.config["users"] = {}
                self.add_user("admin", "admin123")
                self._save_config()
                print("✅ Utente admin ricreato (password: admin123)")
        else:
            self.config = {
                "users": {},
                "session_timeout": 3600,
                "max_transfer": 1000,
                "require_2fa": False
            }
            self.add_user("admin", "admin123")
            self._save_config()
            print("🔐 Utente admin creato (password: admin123)")
            
    def _save_config(self):
        with open("web_config.json", "w") as f:
            json.dump(self.config, f, indent=2)
            
    def verify_password(self, password, hash_val):
        return hash_val == hashlib.sha256(password.encode()).hexdigest()
        
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
        
    def add_user(self, username, password):
        if username in self.config["users"]:
            return False, "Utente già esistente"
        
        self.config["users"][username] = {
            "password": self.hash_password(password),
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "failed_attempts": 0,
            "locked_until": None
        }
        self._save_config()
        return True, "Utente creato"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

xrp_manager = SecureXRPManager()

@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username not in xrp_manager.config["users"]:
            return render_template('login.html', error="Credenziali non valide")
            
        user = xrp_manager.config["users"][username]
        
        if user.get("locked_until"):
            lock_time = datetime.fromisoformat(user["locked_until"])
            if datetime.now() < lock_time:
                remaining = (lock_time - datetime.now()).seconds
                return render_template('login.html', 
                    error=f"Account bloccato per {remaining//60} minuti")
        
        if xrp_manager.verify_password(password, user["password"]):
            session['logged_in'] = True
            session['username'] = username
            user["failed_attempts"] = 0
            user["last_login"] = datetime.now().isoformat()
            xrp_manager._save_config()
            
            wallets = xrp_manager.cli._get_wallet_list()
            if wallets:
                first_wallet = wallets[0]["name"]
                xrp_manager.cli._switch_wallet(first_wallet)
                print(f"✅ Wallet {first_wallet} caricato per {username}")
            else:
                print(f"ℹ️  Nessun wallet trovato")
            
            return redirect(url_for('index'))
        else:
            user["failed_attempts"] = user.get("failed_attempts", 0) + 1
            if user["failed_attempts"] >= MAX_LOGIN_ATTEMPTS:
                user["locked_until"] = (datetime.now() + 
                    timedelta(seconds=LOGIN_COOLDOWN)).isoformat()
            xrp_manager._save_config()
            return render_template('login.html', 
                error="Credenziali non valide")
    
    return render_template('login.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================================
# 🔑 API WALLET
# ============================================================

@app.route('/api/wallet/info')
@login_required
def api_wallet_info():
    try:
        if not xrp_manager.cli.manager.is_loaded():
            return jsonify({"error": "Nessun wallet caricato"}), 400
            
        info = xrp_manager.cli.manager.get_seed_info()
        address = xrp_manager.cli.manager.get_address()
        crypto = xrp_manager.cli._crypto
        network = xrp_manager.cli._network
        
        balance = xrp_manager.cli.manager.get_balance()
        
        return jsonify({
            "address": address,
            "balance": balance,
            "crypto": crypto,
            "network": network,
            "seed_type": info.get("seed_type"),
            "wallet_name": xrp_manager.cli._get_active_wallet_name()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/balance')
@login_required
def api_balance():
    try:
        if not xrp_manager.cli.manager.is_loaded():
            return jsonify({"error": "Nessun wallet caricato"}), 400
            
        address = xrp_manager.cli.manager.get_address()
        balance = xrp_manager.cli.manager.get_balance()
        crypto = xrp_manager.cli._crypto
        
        return jsonify({
            "address": address,
            "balance": balance,
            "crypto": crypto,
            "network": xrp_manager.cli._network
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/history')
@login_required
def api_history():
    try:
        if not xrp_manager.cli.manager.is_loaded():
            return jsonify({"error": "Nessun wallet caricato", "transactions": [], "balance": 0}), 200
            
        address = xrp_manager.cli.manager.get_address()
        crypto = xrp_manager.cli._crypto
        
        if crypto == "XLM":
            return api_history_xlm(address)
        
        from xrpl.models.requests import AccountTx
        from xrpl.models.response import ResponseStatus
        import base64
        
        limit = request.args.get('limit', 100, type=int)
        if limit > 100:
            limit = 100
        
        account_tx_request = AccountTx(
            account=address,
            ledger_index_min=-1,
            ledger_index_max=-1,
            limit=limit,
            forward=False
        )
        
        response = xrp_manager.cli.client.request(account_tx_request)
        
        if response.status != ResponseStatus.SUCCESS:
            return jsonify({"error": response.status, "transactions": [], "balance": 0}), 200
        
        result = response.result
        transactions = result.get("transactions", [])
        
        tx_list = []
        for idx, tx_data in enumerate(transactions[:limit], 1):
            tx = tx_data.get("tx_json", {})
            if not tx:
                continue
            
            tx_type = tx.get("TransactionType", "Unknown")
            
            date_str = ""
            try:
                if "date" in tx:
                    ledger_time = tx.get("date", 0)
                    if ledger_time:
                        from datetime import datetime
                        date_obj = datetime.fromtimestamp(ledger_time + 946684800)
                        date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            
            # 🔑 GESTIONE IMPORTI - TRONCA TOKEN LUNGHI
            amount = tx.get("Amount", tx.get("DeliverMax", "0"))
            if isinstance(amount, dict):
                token_value = amount.get('value', '0')
                token_currency = amount.get('currency', '???')
                try:
                    val_float = float(token_value)
                    amount_str = f"{val_float:.6f}".rstrip('0').rstrip('.')
                    if not amount_str or amount_str == '0':
                        amount_str = "0"
                    # 🔑 TRONCA IL SIMBOLO SE È ESADECIMALE LUNGO
                    if len(token_currency) > 8:
                        token_currency = token_currency[:8]
                    amount_str += f" {token_currency}"
                except:
                    amount_str = f"{token_value[:8]} {token_currency}"
            else:
                try:
                    amount_xrp = int(amount) / 1_000_000
                    amount_str = f"{amount_xrp:.6f}".rstrip('0').rstrip('.')
                    if not amount_str or amount_str == '0':
                        amount_str = "0"
                    amount_str += " XRP"
                except:
                    amount_str = f"{amount} drops"
            
            fee_drops = tx.get("Fee", "0")
            try:
                fee_xrp = int(fee_drops) / 1_000_000
                fee_str = f"{fee_xrp:.6f}".rstrip('0').rstrip('.')
                if not fee_str or fee_str == '0':
                    fee_str = "0"
                fee_str += " XRP"
            except:
                fee_str = fee_drops
            
            sender = tx.get("Account", "unknown")
            destination = tx.get("Destination", "unknown")
            
            if destination == address:
                direction = "RICEVUTO"
                from_to = f"Da: {sender}"
            elif sender == address:
                direction = "INVIATO"
                from_to = f"A: {destination}"
            else:
                direction = "ALTRO"
                from_to = f"{sender} → {destination}"
            
            # 🔑 DECODIFICA MEMO
            memo_text = ""
            memos = tx.get("Memos", [])
            if memos:
                try:
                    memo_dict = memos[0].get("Memo", {})
                    memo_data = memo_dict.get("MemoData", "")
                    if memo_data:
                        try:
                            memo_bytes = bytes.fromhex(memo_data)
                            memo_text = memo_bytes.decode('utf-8', errors='ignore')
                        except:
                            try:
                                while len(memo_data) % 4 != 0:
                                    memo_data += '='
                                memo_bytes = base64.b64decode(memo_data)
                                memo_text = memo_bytes.decode('utf-8', errors='ignore')
                            except:
                                memo_text = memo_data[:20]
                        if memo_text:
                            memo_text = ''.join(c for c in memo_text if c.isprintable() or c == ' ')
                except:
                    pass
            
            tx_list.append({
                "index": idx,
                "date": date_str,
                "type": direction,
                "amount": amount_str,
                "fee": fee_str,
                "from_to": from_to,
                "memo": memo_text
            })
        
        balance = xrp_manager.cli.manager.get_balance()
        
        return jsonify({
            "transactions": tx_list,
            "address": address,
            "balance": balance,
            "crypto": crypto,
            "network": xrp_manager.cli._network,
            "count": len(tx_list),
            "limit": limit
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "transactions": [], "balance": 0}), 500

def api_history_xlm(address):
    """Storico XLM via Horizon con importi corretti usando /payments"""
    try:
        import requests
        
        if xrp_manager.cli._network == "mainnet":
            horizon_url = "https://horizon.stellar.org"
        else:
            horizon_url = "https://horizon-testnet.stellar.org"
        
        # 🔑 USA /payments CHE FUNZIONA
        url = f"{horizon_url}/accounts/{address}/payments?limit=10&order=desc"
        response = requests.get(url, timeout=30)
        data = response.json()
        
        if response.status_code != 200:
            return jsonify({"error": "Errore Horizon", "transactions": [], "balance": 0}), 200
        
        payments = data.get('_embedded', {}).get('records', [])
        
        tx_list = []
        for idx, payment in enumerate(payments[:10], 1):
            created_at = payment.get('created_at', '')
            date_str = created_at.replace('T', ' ').replace('Z', '')[:19] if created_at else ''
            
            # 🔑 OTTIENI IL TIPO E L'IMPORTO DIRETTAMENTE DA PAYMENT
            op_type = payment.get('type', 'unknown')
            amount_str = ""
            from_to = ""
            direction = "TRANSAZIONE"
            memo_text = ""
            
            if op_type == 'payment':
                amount = float(payment.get('amount', 0))
                asset_type = payment.get('asset_type', 'native')
                asset_code = "XLM" if asset_type == 'native' else payment.get('asset_code', '?')
                from_acct = payment.get('from', '')
                to_acct = payment.get('to', '')
                
                if to_acct == address:
                    from_to = f"Da: {from_acct}"
                    direction = "RICEVUTO"
                elif from_acct == address:
                    from_to = f"A: {to_acct}"
                    direction = "INVIATO"
                else:
                    from_to = f"{from_acct} → {to_acct}"
                    direction = "ALTRO"
                
                amount_str = f"{amount:.6f} {asset_code}"
                
                # 🔑 MEMO VIENE DALLA TRANSAZIONE ASSOCIATA
                # Proviamo a prenderlo dai _links
                tx_link = payment.get('_links', {}).get('transaction', {}).get('href', '')
                if tx_link:
                    try:
                        tx_resp = requests.get(tx_link, timeout=5)
                        if tx_resp.status_code == 200:
                            tx_data = tx_resp.json()
                            memo_type = tx_data.get('memo_type', '')
                            if memo_type == 'text':
                                memo_text = tx_data.get('memo', '')
                            elif memo_type == 'id':
                                memo_text = f"ID: {tx_data.get('memo', '')}"
                    except:
                        pass
                
            elif op_type == 'create_account':
                amount = float(payment.get('starting_balance', 0))
                to_acct = payment.get('account', '')
                from_acct = payment.get('funder', '')
                if to_acct == address:
                    from_to = f"Da: {from_acct}"
                    direction = "RICEVUTO"
                else:
                    from_to = f"A: {to_acct}"
                    direction = "INVIATO"
                amount_str = f"{amount:.6f} XLM"
                
            elif op_type == 'account_merge':
                into_acct = payment.get('into', '')
                from_acct = payment.get('account', '')
                from_to = f"{from_acct} → {into_acct}"
                amount_str = ""
                direction = "FUSIONE"
                
            elif op_type in ['path_payment_strict_send', 'path_payment_strict_receive']:
                amount = float(payment.get('amount', 0))
                from_acct = payment.get('from', '')
                to_acct = payment.get('to', '')
                if to_acct == address:
                    from_to = f"Da: {from_acct}"
                    direction = "RICEVUTO"
                else:
                    from_to = f"A: {to_acct}"
                    direction = "INVIATO"
                amount_str = f"{amount:.6f} XLM"
                
            elif op_type in ['manage_sell_offer', 'manage_buy_offer']:
                selling = payment.get('selling', {})
                buying = payment.get('buying', {})
                if op_type == 'manage_sell_offer':
                    from_to = f"Vende {selling.get('asset_code', 'XLM')}"
                else:
                    from_to = f"Compra {buying.get('asset_code', 'XLM')}"
                amount_str = ""
                direction = "OFFERTA"
                
            else:
                from_to = payment.get('source_account', '')
                amount_str = ""
                direction = op_type[:14]
            
            # 🔑 FEE (stimata, Horizon non la dà nei payments)
            fee_str = "0.0000100 XLM"
            
            tx_list.append({
                "index": idx,
                "date": date_str,
                "type": direction,
                "amount": amount_str,
                "fee": fee_str,
                "from_to": from_to,
                "memo": memo_text
            })
        
        balance = xrp_manager.cli.manager.get_balance()
        
        return jsonify({
            "transactions": tx_list,
            "address": address,
            "balance": balance,
            "crypto": "XLM",
            "network": xrp_manager.cli._network,
            "count": len(tx_list)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "transactions": [], "balance": 0}), 500

@app.route('/api/wallet/send', methods=['POST'])
@login_required
def api_send():
    try:
        data = request.get_json()
        destination = data.get('destination')
        amount = data.get('amount')
        memo = data.get('memo', '')
        crypto = data.get('crypto', 'XRP')
        
        if not destination or not amount:
            return jsonify({"error": "Destinazione e importo richiesti"}), 400
            
        if float(amount) > xrp_manager.config["max_transfer"]:
            return jsonify({"error": f"Importo supera il limite di {xrp_manager.config['max_transfer']} XRP"}), 400
        
        if crypto == "XLM":
            args = [destination, str(amount)]
            if memo:
                args.append(f'"{memo}"')
                
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                from commands.xlm_commands import send_xlm
                send_xlm(xrp_manager.cli, args)
            
            return jsonify({
                "success": True,
                "message": "Transazione XLM inviata",
                "details": f.getvalue()
            })
        
        args = [destination, str(amount)]
        if memo:
            args.append(f'"{memo}"')
            
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            xrp_manager.cli.cmd_send(args)
        
        return jsonify({
            "success": True,
            "message": "Transazione inviata",
            "details": f.getvalue()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/switch', methods=['POST'])
@login_required
def api_switch_wallet():
    try:
        data = request.get_json()
        wallet_name = data.get('wallet_name')
        
        if not wallet_name:
            return jsonify({"error": "Nome wallet richiesto"}), 400
            
        if xrp_manager.cli._switch_wallet(wallet_name):
            return jsonify({
                "success": True,
                "message": f"Wallet cambiato a {wallet_name}",
                "crypto": xrp_manager.cli._crypto,
                "network": xrp_manager.cli._network
            })
        else:
            return jsonify({"error": f"Wallet {wallet_name} non trovato"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/list')
@login_required
def api_list_wallets():
    try:
        wallets = xrp_manager.cli._get_wallet_list()
        active = xrp_manager.cli._get_active_wallet_name()
        
        for w in wallets:
            wallet_file = Path(f"wallets/{w['name']}.json")
            if wallet_file.exists():
                with open(wallet_file) as f:
                    data = json.load(f)
                    w['network'] = data.get('network', 'testnet')
                    w['crypto'] = data.get('crypto_type', 'XRP')
        
        return jsonify({
            "wallets": wallets,
            "active": active
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/create', methods=['POST'])
@login_required
def api_create_wallet():
    try:
        data = request.get_json()
        name = data.get('name', '')
        passphrase = data.get('passphrase', '')
        network = data.get('network', 'testnet')
        crypto = data.get('crypto', 'XRP')
        strength = data.get('strength', 256)
        
        if not name:
            return jsonify({"error": "Nome wallet richiesto"}), 400
        
        xrp_manager.cli._set_crypto(crypto)
        xrp_manager.cli._set_network(network)
        
        result = xrp_manager.cli.manager.create_new_wallet_bip39(
            passphrase=passphrase, 
            strength=strength
        )
        
        xrp_manager.cli._save_wallet_as(name)
        xrp_manager.cli._set_active_wallet_name(name)
        
        return jsonify({
            "success": True,
            "message": f"Wallet '{name}' creato con successo",
            "address": result['first_address'],
            "seed_phrase": result['seed_phrase'],
            "private_key": result['first_private_key'],
            "crypto": crypto,
            "network": network
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/import', methods=['POST'])
@login_required
def api_import_wallet():
    try:
        data = request.get_json()
        name = data.get('name', '')
        seed_input = data.get('seed_input', '')
        passphrase = data.get('passphrase', '')
        network = data.get('network', 'testnet')
        crypto = data.get('crypto', 'XRP')
        input_type = data.get('input_type', 'auto')
        
        if not name or not seed_input:
            return jsonify({"error": "Nome e seed richiesti"}), 400
        
        xrp_manager.cli._set_crypto(crypto)
        xrp_manager.cli._set_network(network)
        
        result = xrp_manager.cli.manager.import_wallet(
            seed_input=seed_input,
            passphrase=passphrase,
            input_type=input_type
        )
        
        xrp_manager.cli._save_wallet_as(name)
        xrp_manager.cli._set_active_wallet_name(name)
        
        return jsonify({
            "success": True,
            "message": f"Wallet '{name}' importato con successo",
            "address": result['first_address'],
            "crypto": crypto,
            "network": network
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/delete', methods=['POST'])
@login_required
def api_delete_wallet():
    try:
        data = request.get_json()
        name = data.get('name', '')
        
        if not name:
            return jsonify({"error": "Nome wallet richiesto"}), 400
        
        target = Path(f"wallets/{name}.json")
        if not target.exists():
            return jsonify({"error": f"Wallet '{name}' non trovato"}), 404
        
        active = xrp_manager.cli._get_active_wallet_name()
        
        target.unlink()
        
        if name == active:
            xrp_manager.cli.manager.reset()
            if xrp_manager.cli.active_wallet_name_file.exists():
                xrp_manager.cli.active_wallet_name_file.unlink()
        
        return jsonify({
            "success": True,
            "message": f"Wallet '{name}' eliminato"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/change_crypto', methods=['POST'])
@login_required
def api_change_crypto():
    try:
        data = request.get_json()
        crypto = data.get('crypto', 'XRP')
        
        if crypto not in ['XRP', 'XLM']:
            return jsonify({"error": "Crypto non supportata"}), 400
        
        xrp_manager.cli._set_crypto(crypto)
        xrp_manager.cli.manager.save()
        
        return jsonify({
            "success": True,
            "message": f"Crypto cambiata a {crypto}",
            "crypto": crypto
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/change_network', methods=['POST'])
@login_required
def api_change_network():
    try:
        data = request.get_json()
        network = data.get('network', 'testnet')
        
        if network not in ['mainnet', 'testnet', 'devnet']:
            return jsonify({"error": "Rete non supportata"}), 400
        
        xrp_manager.cli._set_network(network)
        xrp_manager.cli.manager.save()
        
        return jsonify({
            "success": True,
            "message": f"Rete cambiata a {network}",
            "network": network
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# 🔑 API QR CODE
# ============================================================

@app.route('/api/wallet/qrcode')
@login_required
def api_qrcode():
    """Genera un QR code per l'indirizzo del wallet corrente"""
    try:
        if not QRCODE_AVAILABLE:
            return jsonify({"error": "Libreria qrcode non installata. pip install qrcode pillow"}), 500
            
        if not xrp_manager.cli.manager.is_loaded():
            return jsonify({"error": "Nessun wallet caricato"}), 400
        
        address = xrp_manager.cli.manager.get_address()
        crypto = xrp_manager.cli._crypto
        network = xrp_manager.cli._network
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=2,
        )
        qr.add_data(address)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#00d4ff", back_color="#1a1a2e")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        balance = xrp_manager.cli.manager.get_balance()
        
        return jsonify({
            "success": True,
            "address": address,
            "crypto": crypto,
            "network": network,
            "balance": balance,
            "wallet_name": xrp_manager.cli._get_active_wallet_name(),
            "qrcode": f"data:image/png;base64,{img_str}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/qrcode_download')
@login_required
def api_qrcode_download():
    """Scarica il QR code come PNG"""
    try:
        if not QRCODE_AVAILABLE:
            return jsonify({"error": "Libreria qrcode non installata"}), 500
            
        if not xrp_manager.cli.manager.is_loaded():
            return jsonify({"error": "Nessun wallet caricato"}), 400
        
        address = xrp_manager.cli.manager.get_address()
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(address)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#00d4ff", back_color="#1a1a2e")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        
        return send_file(buffered, mimetype='image/png', as_attachment=True, download_name='wallet_qrcode.png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# 🔑 API CONTATTI (con crypto e network)
# ============================================================

@app.route('/api/contacts/list')
@login_required
def api_contacts_list():
    try:
        contacts = xrp_manager.cli._get_contatti()
        crypto = xrp_manager.cli._crypto
        network = xrp_manager.cli._network
        
        filtered = [c for c in contacts if c.get("crypto", "XRP") == crypto and c.get("network", "testnet") == network]
        
        return jsonify({
            "success": True, 
            "contacts": filtered,
            "crypto": crypto,
            "network": network
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contacts/add', methods=['POST'])
@login_required
def api_contacts_add():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        address = data.get('address', '').strip()
        note = data.get('note', '')
        crypto = data.get('crypto', 'XRP')
        network = data.get('network', 'testnet')
        
        if not name or not address:
            return jsonify({"error": "Nome e indirizzo richiesti"}), 400
        
        if crypto == "XRP" and not address.startswith('r'):
            return jsonify({"error": "Indirizzo XRP deve iniziare con 'r'"}), 400
        elif crypto == "XLM" and not address.startswith('G'):
            return jsonify({"error": "Indirizzo XLM deve iniziare con 'G'"}), 400
        
        contacts = xrp_manager.cli._get_contatti()
        for c in contacts:
            if c.get("nome", "").lower() == name.lower() and c.get("crypto", "XRP") == crypto:
                return jsonify({"error": f"Il contatto '{name}' esiste già per {crypto}"}), 400
        
        contacts.append({
            "nome": name,
            "indirizzo": address,
            "keyword": "",
            "index": 0,
            "note": note,
            "crypto": crypto,
            "network": network,
            "created_at": datetime.now().isoformat()
        })
        xrp_manager.cli._save_contatti(contacts)
        
        return jsonify({"success": True, "message": f"Contatto '{name}' aggiunto"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contacts/delete', methods=['POST'])
@login_required
def api_contacts_delete():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        crypto = data.get('crypto', 'XRP')
        
        if not name:
            return jsonify({"error": "Nome contatto richiesto"}), 400
        
        contacts = xrp_manager.cli._get_contatti()
        original_len = len(contacts)
        contacts = [c for c in contacts if not (c.get("nome", "").lower() == name.lower() and c.get("crypto", "XRP") == crypto)]
        
        if len(contacts) == original_len:
            return jsonify({"error": f"Contatto '{name}' non trovato per {crypto}"}), 404
        
        xrp_manager.cli._save_contatti(contacts)
        
        return jsonify({"success": True, "message": f"Contatto '{name}' eliminato"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contacts/all')
@login_required
def api_contacts_all():
    try:
        contacts = xrp_manager.cli._get_contatti()
        return jsonify({"success": True, "contacts": contacts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/donate/info')
@login_required
def api_donate_info():
    """Restituisce gli indirizzi per le donazioni"""
    return jsonify({
        "xrp": {
            "mainnet": "rBKbetm51vuQQfg4Yo8fvweRya7gedcr9J",      # 🔑 METTI IL TUO INDIRIZZO XRP MAINNET
            "testnet": "r93Yu6oRvwahF264kpAMtqVk5WGa12Xpxb"       # 🔑 METTI IL TUO INDIRIZZO XRP TESTNET
        },
        "xlm": {
            "mainnet": "GAHIVF4DGY6YAB42P6OTXYNQWROIPHJ2HGE4WLWNMYPPFBDYF3QI2ZNW",  # 🔑 METTI IL TUO INDIRIZZO XLM MAINNET
            "testnet": "GBZ6353S4ZEGQMYZVXD7N74DKFDJNVRTXY5EWBMXIVBRRY2P4AEW5RAI"   # 🔑 METTI IL TUO INDIRIZZO XLM TESTNET
        },
        "suggested": {
            "xrp": 1.0,
            "xlm": 5.0
        },
        "message": "Supporta lo sviluppo di XRPWallet! ❤️"
    })


if __name__ == "__main__":
    if "admin" not in xrp_manager.config["users"]:
        print("🔐 Creazione utente admin...")
        xrp_manager.add_user("admin", "admin123")
        print("✅ Utente admin creato (password: admin123)")
    
    print("🌐 Server web in esecuzione su http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)