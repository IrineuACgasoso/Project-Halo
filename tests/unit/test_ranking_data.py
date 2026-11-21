"""Persistência do ranking: nunca pode derrubar o jogo nem corromper o arquivo."""
import glob
import json

import pytest

from source.windows.ranking.ranking_data import RankingData


@pytest.fixture
def arquivo(tmp_path):
    return tmp_path / 'sub' / 'ranking.json'


def test_arquivo_inexistente_retorna_lista_vazia(arquivo):
    assert RankingData(str(arquivo)).carregar() == []


def test_roundtrip_salvar_e_carregar(arquivo):
    dados = RankingData(str(arquivo))
    assert dados.salvar([{'name': 'chief', 'score': 117}]) is True
    assert dados.carregar() == [{'name': 'CHIEF', 'score': 117}]
    conteudo = json.loads(arquivo.read_text(encoding='utf-8'))
    assert conteudo['version'] == RankingData.VERSION
    assert not (arquivo.parent / 'ranking.json.tmp').exists()   # escrita atômica


def test_ordena_desc_e_limita_a_max_entradas(arquivo):
    dados = RankingData(str(arquivo))
    dados.salvar([{'name': f'p{i}', 'score': i} for i in range(25)])
    scores = [e['score'] for e in dados.carregar()]
    assert scores == sorted(scores, reverse=True)
    assert len(scores) == RankingData.MAX_ENTRADAS
    assert scores[0] == 24


def test_formato_legado_lista_crua(arquivo):
    arquivo.parent.mkdir(parents=True)
    arquivo.write_text(json.dumps([{'name': 'arbiter', 'score': 5}]), encoding='utf-8')
    assert RankingData(str(arquivo)).carregar() == [{'name': 'ARBITER', 'score': 5}]


@pytest.mark.parametrize('entrada, esperado', [
    ({'name': '  x  ', 'score': '10'}, {'name': 'X', 'score': 10}),
    ({'name': 'a' * 40, 'score': 1}, {'name': 'A' * 16, 'score': 1}),
    ({'name': '', 'score': 1}, {'name': 'OPERADOR', 'score': 1}),
    ({'score': -50}, {'name': 'OPERADOR', 'score': 0}),
])
def test_sanitiza_entradas(entrada, esperado):
    assert RankingData('x')._sanitizar([entrada]) == [esperado]


@pytest.mark.parametrize('lixo', ['texto', None, 42, {'name': 'a', 'score': 'abc'},
                                  {'name': 'a', 'score': float('inf')}])
def test_descarta_entradas_malformadas(lixo):
    assert RankingData('x')._sanitizar([lixo]) == []


def test_json_corrompido_retorna_vazio_e_faz_backup(arquivo):
    arquivo.parent.mkdir(parents=True)
    arquivo.write_text('{ isso não é json', encoding='utf-8')
    assert RankingData(str(arquivo)).carregar() == []
    assert glob.glob(str(arquivo) + '.corrompido.*.bak')


def test_formato_inesperado_ignorado(arquivo):
    arquivo.parent.mkdir(parents=True)
    arquivo.write_text('"string solta"', encoding='utf-8')
    assert RankingData(str(arquivo)).carregar() == []


def test_falha_de_escrita_retorna_false_sem_lancar(tmp_path):
    # caminho cujo "diretório" é um arquivo: makedirs falha com OSError
    bloqueio = tmp_path / 'arquivo'
    bloqueio.write_text('x')
    assert RankingData(str(bloqueio / 'ranking.json')).salvar([{'name': 'a', 'score': 1}]) is False
