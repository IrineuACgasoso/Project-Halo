"""Linter (roteiro A4): `ruff check` verde e lista de exceções que só encolhe.

As exceções ficam em `ruff.toml` (`[lint.per-file-ignores]`, arquivo -> regras). Aqui:
  - o repo passa no ruff com a configuração do projeto;
  - toda exceção ainda é necessária: ao corrigir um arquivo, a entrada tem que sair;
  - a configuração pega nome indefinido (o motivo de ter linter).
Limite: a exceção é por arquivo e regra, então um 2º import não usado num arquivo que já
tem `F401` na lista passa. O que a lista garante é que ela não cresce sem aparecer no diff.
"""
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / 'ruff.toml'


def rodar_ruff(*args, cwd=RAIZ):
    res = subprocess.run([sys.executable, '-m', 'ruff', 'check', *args], cwd=cwd,
                         capture_output=True, text=True, encoding='utf-8', timeout=120)
    if 'No module named ruff' in res.stderr:
        pytest.fail('ruff não instalado: rode pip install -r requirements-dev.txt')
    return res


def violacoes_sem_excecoes():
    """{arquivo: {regras}} das violações F, ignorando a lista de exceções do ruff.toml."""
    res = rodar_ruff('--isolated', '--select', 'F', '--output-format', 'json', '--exit-zero', '.')
    assert res.returncode == 0, res.stderr
    achado = {}
    for v in json.loads(res.stdout):
        arquivo = Path(os.path.relpath(v['filename'], RAIZ)).as_posix()
        achado.setdefault(arquivo, set()).add(v['code'])
    return achado


def test_repo_passa_no_ruff():
    res = rodar_ruff()
    assert res.returncode == 0, res.stdout + res.stderr


def test_excecoes_so_encolhem():
    excecoes = tomllib.loads(CONFIG.read_text(encoding='utf-8'))['lint']['per-file-ignores']
    achado = violacoes_sem_excecoes()

    sobrando = sorted(f'{arq}: {regra}'
                      for arq, regras in excecoes.items()
                      for regra in regras
                      if regra not in achado.get(arq, set()))
    assert not sobrando, ('exceções que não são mais necessárias; apague do ruff.toml:\n'
                          + '\n'.join(sobrando))


@pytest.mark.parametrize('codigo, regra', [
    ('def f():\n    return nome_que_nao_existe\n', 'F821'),
    ('import os\n', 'F401'),
    ('from os import *\n', 'F403'),
])
def test_configuracao_pega_as_regras_f(tmp_path, codigo, regra):
    (tmp_path / 'modulo.py').write_text(codigo, encoding='utf-8')
    res = rodar_ruff('--config', str(CONFIG), '--output-format', 'concise', 'modulo.py',
                     cwd=tmp_path)
    assert res.returncode == 1
    assert regra in res.stdout


def test_codigo_limpo_passa(tmp_path):
    (tmp_path / 'modulo.py').write_text('import os\n\nprint(os.sep)\n', encoding='utf-8')
    res = rodar_ruff('--config', str(CONFIG), 'modulo.py', cwd=tmp_path)
    assert res.returncode == 0, res.stdout
