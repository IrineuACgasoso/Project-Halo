"""Todo módulo de `source/` importa sem erro (pega import quebrado ou circular em módulo sem outro teste)."""
import importlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_todo_modulo_importa():
    arquivos = sorted((RAIZ / 'source').rglob('*.py'))
    assert len(arquivos) > 200
    for arquivo in arquivos:
        partes = arquivo.relative_to(RAIZ).with_suffix('').parts
        importlib.import_module('.'.join(partes[:-1] if partes[-1] == '__init__' else partes))
