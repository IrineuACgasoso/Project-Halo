"""Flags de depuração. Ative com a variável de ambiente MCE_DEBUG=1.
(PowerShell: $env:MCE_DEBUG=1 ; python main.py)"""
import os

DEBUG = os.environ.get('MCE_DEBUG') == '1'
