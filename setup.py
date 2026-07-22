#!/usr/bin/env python3
"""
Setup per XRP/XLM Wallet Manager
Mantiene la struttura esistente dei file
"""

from setuptools import setup, find_packages
import os
import re

# Leggi la versione da wallet_manager.py
version = "1.1.0"

# Leggi il README se esiste
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except:
    long_description = "XRP/XLM Wallet Manager"

setup(
    name="xrpwallet",
    version=version,
    author="Arg0net",
    description="XRP/XLM Wallet Manager - Gestisci wallet XRP e XLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/xrpwallet",
    
    # 🔑 PACCHETTI DA INCLUDERE - USA LA STRUTTURA ESISTENTE
    packages=find_packages(),
    include_package_data=True,
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    
    # 🔑 DIPENDENZE
    install_requires=[
        "xrpl-py>=2.0.0",
        "stellar-sdk>=10.0.0",
        "flask>=2.0.0",
        "qrcode>=7.0.0",
        "Pillow>=9.0.0",
        "mnemonic>=0.19",
        "bip32>=2.0.0",
        "cryptography>=39.0.0",
        "ecdsa>=0.18.0",
        "base58>=2.1.0",
        "requests>=2.28.0",
    ],
    
    # 🔑 PUNTI DI INGRESSO - COMANDI
    entry_points={
        "console_scripts": [
            "xrpwallet=xrpwallet_cli:main",  # CLI
            "xrpwallet-web=xrpwallet_web:main",  # Web
            "xrpwallet-tui=xrpwallet_tui:main",  # TUI
        ],
    },
    
    # 🔑 FILE DA INCLUDERE
    package_data={
        "": ["templates/*.html", "static/*"],
    },
    zip_safe=False,
)