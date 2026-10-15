"""Resolução de caminhos de assets (compatível com PyInstaller).
Módulo-folha de propósito (sem imports do projeto) para poder ser usado de qualquer lugar
sem criar import circular com assets.py / windows.settings."""
import os
import sys


def path(*args):
    """Junta os caminhos e ajusta para o PyInstaller.
    Aceita múltiplos argumentos: path('pasta', 'sub', 'arquivo.png')"""
    relative_path = os.path.join(*args)
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)   # dentro do executável
    return os.path.join(os.path.abspath("."), relative_path)  # rodando o .py
