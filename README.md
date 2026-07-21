💰 XRPWallet - XRP/XLM Wallet Manager

https://img.shields.io/github/release/argo79/XRPwallet.svg
https://img.shields.io/badge/License-MIT-yellow.svg
https://img.shields.io/badge/python-3.8+-blue.svg
https://img.shields.io/badge/platform-Linux%2520%257C%2520Windows%2520%257C%2520Mac-lightgrey

    Il wallet manager definitivo per XRP e XLM con fee minime di 0.000001 XRP!

📸 Screenshot
CLI	TUI	Web
https://screenshots/cli.png	https://screenshots/tui.png	https://screenshots/web.png
✨ Caratteristiche Principali

🎯 Supporto Multi-Crypto

    ✅ XRP (Ripple) - Mainnet, Testnet, Devnet

    ✅ XLM (Stellar) - Mainnet, Testnet

    ✅ Fee minime: solo 0.000001 XRP per transazione!

🖥️ Tre Interfacce

    CLI - Command Line Interface per power users

    TUI - Terminal User Interface con colori e navigazione

    Web - Interfaccia web con Flask, QR Code e rubrica

🔐 Gestione Wallet Avanzata

    ✅ Multi-wallet (salva e gestisci infiniti wallet)

    ✅ Supporto seed BIP39 (12 o 24 parole)

    ✅ Supporto seed XRP (formato s...)

    ✅ Supporto seed Stellar (formato S...)

    ✅ Supporto numeri Xaman (8 numeri da 6 cifre)

    ✅ Supporto private key (64 caratteri hex)

    ✅ Derivazione indirizzi con keyword personalizzate

💸 Transazioni

    ✅ Invio XRP e XLM con fee minime

    ✅ Storico transazioni completo

    ✅ Saldo in tempo reale

    ✅ Fee visualizzate

    ✅ Supporto memo (XLM)

    ✅ Supporto token XRP (XPM, USD, EUR, ecc.)

📒 Rubrica Contatti

    ✅ Aggiungi contatti con nome

    ✅ Cerca contatti

    ✅ Indirizzi con nome descrittivo

    ✅ Supporto crypto e network

    ✅ Elimina e modifica contatti

📱 Funzionalità Avanzate

    ✅ QR Code per ricevere pagamenti

    ✅ Copia indirizzo negli appunti

    ✅ Esploratore integrato (XRPScan, Stellar Expert)

    ✅ Testnet faucet (XRP e XLM)

    ✅ Riconoscimento automatico token

📦 Installazione

Via pip (consigliato per sviluppatori)
bash

pip install xrpwallet

Linux - Eseguibile Singolo
bash

wget https://github.com/argo79/XRPwallet/releases/download/v1.0.0/xrpwallet-linux
chmod +x xrpwallet-linux
./xrpwallet-linux

Windows - Eseguibile
Scarica xrpwallet-windows.exe dalla pagina delle release e avvia.

MacOS - Eseguibile
bash

chmod +x xrpwallet-mac
./xrpwallet-mac

Docker
bash

docker run -it -p 5000:5000 argo79/xrpwallet

🚀 Guida Rapida

Creare un Nuovo Wallet
bash

./xrpwallet

Scegli "Crea nuovo wallet", inserisci un nome (es. "personale"), scegli XRP o XLM, scegli Mainnet o Testnet, scegli "Crea nuovo (genera 24 parole BIP39)", inserisci passphrase (opzionale).

Importare un Wallet Esistente
bash

./xrpwallet

Scegli "Importa da seed" e inserisci il seed: 12/24 parole BIP39, Seed XRP (s...), Seed Stellar (S...), 8x6 numeri Xaman (es: 123456 234567 ...), o Private key (64 hex).
📚 Guida Dettagliata
1. Creazione Wallet

🆕 Creazione da Zero (BIP39 24 Parole)
bash

./xrpwallet wallet personale

Passaggi:

    Scegli la criptovaluta (XRP o XLM)

    Scegli la rete (Mainnet/Testnet/Devnet)

    Scegli "Crea nuovo (genera 24 parole BIP39)"

    Inserisci passphrase (opzionale, per maggiore sicurezza)

    SALVA LE 24 PAROLE! Sono il tuo seed.

⚠️ ATTENZIONE: Le 24 parole sono l'unico modo per recuperare il wallet. Conservale in un luogo sicuro!

🔢 Importa da Numeri Xaman (8x6)
Xaman (ex XUMM) usa 8 numeri da 6 cifre per il seed.
bash

./xrpwallet wallet xaman

Inserisci: A:123456 B:234567 C:345678 D:456789 E:567890 F:678901 G:789012 H:890123

Formati accettati:

    A:123456 B:234567 C:345678 D:456789 E:567890 F:678901 G:789012 H:890123

    123456 234567 345678 456789 567890 678901 789012 890123

    Con o senza lettere (A-H)

📝 Importa da Seed BIP39 (12/24 Parole)
bash

./xrpwallet wallet mywallet

Inserisci le 12/24 parole separate da spazio, inserisci passphrase (se presente).

🔑 Importa da Seed XRP
bash

./xrpwallet wallet mywallet

Inserisci il seed XRP (inizia con s...). Esempio: sEdTVyS93eSa1P4GcWjMq4V

🌟 Importa da Seed Stellar
bash

./xrpwallet wallet mywallet

Inserisci il seed Stellar (inizia con S...). Esempio: SDV3WVDKMYCGQLMVZBG6ONQGXVSQYPPFDVQZKSR4NN33PUKAOBYZQN6O

🔐 Importa da Private Key
bash

./xrpwallet wallet mywallet

Inserisci la private key (64 caratteri hex). Esempio: 2d2bb3b3ae2012af879dfde7a8190d465f50beb56a207ca37e8871c91a8150b4
2. Gestione Wallet

📂 Cambiare Wallet
bash

./xrpwallet switch personale

Nella TUI (--tui) naviga con ↑/↓ e premi Enter. Nel Web (--gui) clicca sul wallet nella lista.

📋 Lista Wallet Salvati
bash

./xrpwallet list-wallets

Output:
text

📂 WALLET SALVATI
#   Nome          Crypto  Rete    Indirizzo
▶  1. personale    XRP    mainnet r...
    2. xaman        XRP    mainnet r...
    3. stellar      XLM    testnet G...

🗑️ Eliminare un Wallet
bash

./xrpwallet delete-wallet personale --force

3. Transazioni

💸 Inviare XRP
bash

# Verso indirizzo
./xrpwallet send rLVB5EAE62zDJvLTm46aCNW3rytsjVKtrY 10

# Verso contatto in rubrica
./xrpwallet send mario 10

# Con memo
./xrpwallet send rLVB5EAE62zDJvLTm46aCNW3rytsjVKtrY 10 "pagamento fattura"

# Da un wallet specifico
./xrpwallet send rLVB5EAE62zDJvLTm46aCNW3rytsjVKtrY 10 personale 0

💸 Inviare XLM
bash

# Verso indirizzo
./xrpwallet send GDB7BLZWZTXYB6C2BHTHAIYVVRPMAGKD2NA35KNGD4MSMW76IQYOUOLZ 10

# Con memo ID
./xrpwallet send GDB7BLZWZTXYB6C2BHTHAIYVVRPMAGKD2NA35KNGD4MSMW76IQYOUOLZ 10 --memo-id 12345

💰 Fee Minime
Rete	Fee Base	Fee per transazione
XRP Mainnet	10 drops	0.000001 XRP
XRP Testnet	10 drops	0.000001 XRP
XLM Mainnet	100 stroops	0.00001 XLM
XLM Testnet	100 stroops	0.00001 XLM

⚠️ Nota: Le fee XRP sono le più basse nel mondo crypto! Solo 0.000001 XRP per transazione!

📜 Storico Transazioni
bash

# Storico del wallet attivo
./xrpwallet history

# Storico di un indirizzo specifico
./xrpwallet history rLVB5EAE62zDJvLTm46aCNW3rytsjVKtrY

# Con limite
./xrpwallet history --limit 20

Output:
text

┌────┬─────────────────────┬────────────┬──────────────────┬────────────┬────────────────────────────────────────────┐
│ #  │ Data/Ora            │ Tipo       │ Importo          │ Fee        │ Da/A                                        │
├────┼─────────────────────┼────────────┼──────────────────┼────────────┼────────────────────────────────────────────┤
│ 1  │ 2026-07-21 14:23:57 │ RICEVUTO   │ 10.000000 XRP    │ 0.000001   │ Da: rLVB5EAE62zDJvLTm46aCNW3rytsjVKtrY    │
│ 2  │ 2026-07-21 10:15:32 │ INVIATO    │ 5.000000 XRP     │ 0.000001   │ A: rBKbetm51vuQQfg4Yo8fvweRya7gedcr9J    │
└────┴─────────────────────┴────────────┴──────────────────┴────────────┴────────────────────────────────────────────┘

4. Reti

🌐 Mainnet (Produzione)
bash

./xrpwallet --network mainnet

⚠️ ATTENZIONE: Mainnet usa XRP VERI! Fai attenzione!

🧪 Testnet (Sviluppo)
bash

./xrpwallet --network testnet
./xrpwallet faucet  # Ottieni XRP di test

Testnet usa XRP FINTI per testare senza rischi.

🛠️ Devnet (Sviluppo Avanzato)
bash

./xrpwallet --network devnet

Devnet è per sviluppatori che testano nuove funzionalità.
5. Interfacce

🖥️ CLI (Command Line Interface)
bash

./xrpwallet                  # Default
./xrpwallet wallet MEW       # Con comando
./xrpwallet balance

🎨 TUI (Terminal User Interface)
bash

./xrpwallet --tui

Comandi TUI:

    ↑/↓ - Naviga wallet

    Enter - Seleziona wallet

    i - Info wallet

    b - Saldo

    h - Storico

    t - Invia

    r - Rubrica

    w - Gestione wallet

    c - Cambia crypto

    q - Esci

🌐 Web (GUI)
bash

./xrpwallet --gui
./xrpwallet --gui --port 8080
./xrpwallet --gui --host 0.0.0.0

Login: admin / admin123 (cambia la password al primo accesso!)
6. Rubrica Contatti

➕ Aggiungi Contatto
bash

./xrpwallet contact-add mario rLVB5EAE62zDJvLTm46aCNW3rytsjVKtrY
./xrpwallet contact-add mario rLVB5EAE62zDJvLTm46aCNW3rytsjVKtrY "Fornitore"
./xrpwallet contact-add mario rLVB5EAE62zDJvLTm46aCNW3rytsjVKtrY cliente 0 "XRP mainnet"

📋 Lista Contatti
bash

./xrpwallet contact-list

Output:
text

📒 RUBRICA
Nome            Indirizzo                                     Crypto Rete    Note
mario           rLVB5EAE62zDJvLTm46aCNW3rytsjVKtrY           XRP    mainnet Fornitore

🗑️ Elimina Contatto
bash

./xrpwallet contact-delete mario

7. QR Code per Ricevere

Nella Web GUI (--gui) vai su "Ricevi" per vedere il QR Code. Clicca "Scarica PNG" per salvarlo.

Funzionalità:

    QR Code generato automaticamente

    Copia indirizzo negli appunti

    Link diretto all'esploratore

    Visualizza saldo e rete

8. Esploratori Integrati
Rete	XRP	XLM
Mainnet	XRPScan	Stellar Expert
Testnet	XRPL Testnet	Stellar Testnet

I link vengono generati automaticamente nello storico e nella sezione "Ricevi".
📁 Struttura Dati
text

~/.xrpwallet/
├── wallets/               # Wallet salvati
│   ├── personale.json
│   ├── xaman.json
│   └── stellar.json
├── wallet_data.json       # Wallet attivo
├── rubrica.json           # Contatti
├── active_wallet.txt      # Wallet corrente
└── web_config.json        # Configurazione web

🔧 Sviluppo

Clona il repository
bash

git clone https://github.com/argo79/XRPwallet.git
cd XRPwallet

Installa in modalità sviluppo
bash

pip install -e .

Build eseguibile
bash

./prepare_build.sh
./build_xrpwallet_linux.sh
./build_all.sh

Test
bash

xrpwallet --version
xrpwallet --tui
xrpwallet --gui --port 5000

📊 Dipendenze

Python

    xrpl-py - XRP Ledger

    stellar-sdk - Stellar Network

    flask - Web interface

    qrcode - QR Code generation

    mnemonic - BIP39 seed phrases

    bip32 - Hierarchical wallets

    cryptography - Security

    ecdsa - Signatures

    base58 - Encoding

Node.js (per numeri Xaman)

    xrpl-secret-numbers - Xaman secret numbers

🗺️ Roadmap

✅ Completato

    Supporto XRP e XLM

    CLI, TUI e Web

    Multi-wallet

    Rubrica contatti

    QR Code

    Storico transazioni

    Fee minime (0.000001 XRP)

    Numeri Xaman

    Mainnet/Testnet/Devnet

🚧 In Sviluppo

    Multi-sig

    Backup criptato

    Report fiscale (CSV)

    Exchange integrato

    Notifiche push

📝 Futuro

    App mobile (Flutter/React Native)

    Hardware wallet support

    DeFi integration

    NFT viewer

🤝 Contributi

I contributi sono benvenuti!

    Fai un fork del progetto

    Crea un branch (git checkout -b feature/nuova-funzione)

    Commit (git commit -m 'Aggiunta nuova funzione')

    Push (git push origin feature/nuova-funzione)

    Apri una Pull Request

📄 Licenza

MIT License - Copyright (c) 2024 Arg0net
🙏 Crediti

    Autore: Arg0net

    XRP Ledger: XRPL Foundation

    Stellar: Stellar Foundation

    Ispirato da: Xaman Wallet, XRP Toolkit

📞 Contatti

    GitHub: argo79/XRPwallet

    Issues: Segnala problema

⭐ Supporta il Progetto

    ⭐ Mettere una stella su GitHub

    🐛 Segnalare bug

    💡 Suggerire nuove funzionalità

    📝 Scrivere documentazione

    💰 Donare XRP/XLM

Indirizzi Donazione:

    XRP: rBKbetm51vuQQfg4Yo8fvweRya7gedcr9J

    XLM: GAHIVF4DGY6YAB42P6OTXYNQWROIPHJ2HGE4WLWNMYPPFBDYF3QI2ZNW

<div align="center"> Built with ❤️ on the XRP Ledger &amp; Stellar </div>
