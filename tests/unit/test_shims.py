"""Shims com prazo (roteiro §2, regra 3): todo adaptador temporário leva `# SHIM(<etapa>)`, e
só os listados aqui são permitidos. A etapa que remove o shim tira a linha; a H2 exige zero."""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASTAS = ('source', 'tests', 'tools')

# (caminho relativo à raiz com '/', etapa que remove) -> quantidade de marcas no arquivo
PERMITIDOS = {}

MARCA = re.compile(r'#\s*SHIM\((\w+(?:\.\w+)?)\)')


def _shims_no_repo():
    encontrados = {}
    for pasta in PASTAS:
        for raiz, _, arquivos in os.walk(os.path.join(RAIZ, pasta)):
            for nome in arquivos:
                if not nome.endswith('.py') or nome == 'test_shims.py':
                    continue
                caminho = os.path.join(raiz, nome)
                with open(caminho, encoding='utf-8') as f:
                    for etapa in MARCA.findall(f.read()):
                        chave = (os.path.relpath(caminho, RAIZ).replace(os.sep, '/'), etapa)
                        encontrados[chave] = encontrados.get(chave, 0) + 1
    return encontrados


def test_so_existem_os_shims_permitidos():
    assert _shims_no_repo() == PERMITIDOS


def test_marca_e_reconhecida():
    assert MARCA.findall('x = 1  # SHIM(B3): motivo') == ['B3']
    assert MARCA.findall('# SHIM(F5.2)') == ['F5.2']
    assert MARCA.findall('# shim sem etapa') == []
