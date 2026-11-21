"""Todo módulo de `source/` importa sem erro (roteiro A4).

Pega import quebrado, import circular e nome indefinido no nível do módulo, inclusive em
módulos que nenhum outro teste toca. Nome indefinido dentro de função só aparece ao rodar:
esse caso é do ruff (`test_lint.py`, regra F821).
"""
import importlib
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def listar_modulos(raiz, pacote):
    """Nomes pontuados de todo `.py` em `raiz/pacote` (`__init__.py` vira o nome do pacote)."""
    modulos = []
    for pasta, subpastas, arquivos in os.walk(os.path.join(raiz, pacote)):
        subpastas[:] = sorted(s for s in subpastas if s != '__pycache__')
        partes = os.path.relpath(pasta, raiz).split(os.sep)
        for arquivo in sorted(arquivos):
            if not arquivo.endswith('.py'):
                continue
            nome = arquivo[:-3]
            modulos.append('.'.join(partes if nome == '__init__' else partes + [nome]))
    return modulos


MODULOS = listar_modulos(RAIZ, 'source')


@pytest.mark.parametrize('modulo', MODULOS)
def test_modulo_importa(modulo):
    importlib.import_module(modulo)


def test_lista_cobre_os_modulos_conhecidos():
    # Sentinelas: se a varredura parar de achar módulos, o teste acima passaria vazio.
    assert len(MODULOS) > 200
    for esperado in ('source.game', 'source.enemies.bosses.atriox',
                     'source.enemies.bosses.atriox.core', 'source.feats.weapons.comum'):
        assert esperado in MODULOS


def test_listar_modulos_bordas(tmp_path):
    (tmp_path / 'pkg' / 'sub' / '__pycache__').mkdir(parents=True)
    (tmp_path / 'pkg' / '__init__.py').write_text('')
    (tmp_path / 'pkg' / 'a.py').write_text('')
    (tmp_path / 'pkg' / 'leia.md').write_text('')
    (tmp_path / 'pkg' / 'sub' / 'b.py').write_text('')            # pasta sem __init__ (namespace)
    (tmp_path / 'pkg' / 'sub' / '__pycache__' / 'c.py').write_text('')

    assert listar_modulos(str(tmp_path), 'pkg') == ['pkg', 'pkg.a', 'pkg.sub.b']


def test_import_quebrado_falha(tmp_path, monkeypatch):
    (tmp_path / 'pkg_quebrado').mkdir()
    (tmp_path / 'pkg_quebrado' / 'mod.py').write_text('from pkg_quebrado.nao_existe import X\n')
    monkeypatch.syspath_prepend(str(tmp_path))

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('pkg_quebrado.mod')
