"""tools/perf.py: funções puras (p95, base, comparação, argumentos) e smoke de cenários curtos.
Tempo não vira asserção (varia por máquina); só a forma e a validade do relatório."""
import json

import pytest

from source.systems.spawner.spawner_bosses import PHASE_BOSSES
from tools import perf


def _relatorio(**cenarios):
    return {'import_assets_s': 1.0, 'memoria_pico_mb': 100.0, 'cenarios': cenarios}


# ---------------- p95 ----------------
def test_p95_um_valor_e_ele_mesmo():
    assert perf.p95([7.5]) == 7.5


def test_p95_posto_mais_proximo():
    assert perf.p95(list(range(1, 101))) == 95
    assert perf.p95([3, 1, 2]) == 3   # ordena antes


def test_p95_lista_vazia_e_erro():
    with pytest.raises(ValueError):
        perf.p95([])


# ---------------- comparação ----------------
def test_comparar_dentro_da_tolerancia_nao_acusa():
    base = _relatorio(horda={'media_ms': 10.0, 'p95_ms': 20.0})
    atual = _relatorio(horda={'media_ms': 10.9, 'p95_ms': 22.0})
    assert perf.comparar(base, atual) == []


def test_comparar_acima_da_tolerancia_acusa_cada_metrica():
    base = _relatorio(horda={'media_ms': 10.0, 'p95_ms': 20.0})
    atual = _relatorio(horda={'media_ms': 11.1, 'p95_ms': 23.0})
    assert perf.comparar(base, atual) == [('horda', 'media_ms', 10.0, 11.1),
                                          ('horda', 'p95_ms', 20.0, 23.0)]


def test_comparar_ignora_cenario_novo_e_metrica_ausente():
    base = _relatorio(troca_de_fase={'media_ms': 1.0, 'max_ms': 2.0})
    atual = _relatorio(troca_de_fase={'media_ms': 1.0, 'max_ms': 9.0},
                       boss_novo={'media_ms': 99.0, 'p95_ms': 99.0})
    assert perf.comparar(base, atual) == []


def test_comparar_piora_pequena_em_ms_e_ruido():
    base = _relatorio(boss={'media_ms': 2.0, 'p95_ms': 3.0})
    assert perf.comparar(base, _relatorio(boss={'media_ms': 2.9, 'p95_ms': 3.9})) == []   # +45%, 0,9 ms
    assert perf.comparar(base, _relatorio(boss={'media_ms': 3.1, 'p95_ms': 3.0})) == [
        ('boss', 'media_ms', 2.0, 3.1)]


def test_melhora_nao_e_acusada():
    base = _relatorio(horda={'media_ms': 10.0, 'p95_ms': 20.0})
    atual = _relatorio(horda={'media_ms': 5.0, 'p95_ms': 10.0})
    assert perf.comparar(base, atual) == []


# ---------------- base em disco ----------------
def test_base_inexistente_e_none(tmp_path):
    assert perf.carregar_base(str(tmp_path / 'nao_existe.json')) is None


def test_base_ida_e_volta(tmp_path):
    caminho = str(tmp_path / 'base.json')
    rel = _relatorio(horda={'media_ms': 1.5, 'p95_ms': 2.5})
    perf.salvar(rel, caminho)
    assert perf.carregar_base(caminho) == rel


@pytest.mark.parametrize('conteudo', ['{corrompido', '[]', json.dumps({'cenarios': []})])
def test_base_invalida_e_erro(tmp_path, conteudo):
    caminho = tmp_path / 'base.json'
    caminho.write_text(conteudo, encoding='utf-8')
    with pytest.raises(ValueError):
        perf.carregar_base(str(caminho))


# ---------------- CLI ----------------
@pytest.mark.parametrize('argv', [['--gravar-base', '--cenario', 'horda'],
                                  ['--gravar-base', '--escala', '0.5'],
                                  ['--escala', '0'],
                                  ['--escala', '-1']])
def test_argumentos_invalidos_sao_recusados(argv):
    with pytest.raises(SystemExit) as erro:
        perf.main(argv)
    assert erro.value.code == 2


def test_gravar_base_na_bateria_e_recusado(monkeypatch, tmp_path):
    monkeypatch.setattr(perf, 'fonte_de_energia', lambda: 'bateria')
    caminho = tmp_path / 'base.json'
    assert perf.main(['--gravar-base', '--base', str(caminho)]) == 2
    assert not caminho.exists()


def test_fonte_de_energia_e_valor_conhecido():
    assert perf.fonte_de_energia() in ('tomada', 'bateria', None)


def test_base_ilegivel_sai_com_codigo_2(tmp_path):
    caminho = tmp_path / 'base.json'
    caminho.write_text('{corrompido', encoding='utf-8')
    assert perf.main(['--base', str(caminho)]) == 2


# ---------------- cenários ----------------
def test_todo_boss_tem_cenario():
    nomes = {nome for nome, _ in perf.listar_cenarios()}
    for bosses in PHASE_BOSSES.values():
        for boss in bosses:
            assert f'boss_{boss}' in nomes
    assert {'horda_150', 'fase0_60s', 'troca_de_fase'} <= nomes


@pytest.mark.integration
def test_smoke_horda_e_troca_de_fase(novo_jogo):
    resultados = {}
    for filtro in ('horda', 'troca'):
        resultados |= perf.medir_cenarios(novo_jogo, filtro, escala=0.02, saida=lambda m: None)

    horda = resultados['horda_150']
    assert horda['frames'] == 24   # 20 s x 0,02 a 60 FPS
    assert 0 < horda['update_media_ms'] <= horda['media_ms']
    assert horda['p95_ms'] > 0 and horda['draw_media_ms'] > 0
    troca = resultados['troca_de_fase']
    assert troca['trocas'] >= 1 and 0 < troca['media_ms'] <= troca['max_ms']
    assert novo_jogo.renderer._erros_logados == set()

    assert set(resultados) == {'horda_150', 'troca_de_fase'}
    tabela = perf.formatar_tabela(_relatorio(**resultados), base=_relatorio(**resultados))
    assert 'horda_150' in tabela and '(+0%)' in tabela


@pytest.mark.integration
def test_confirmacao_mede_de_novo_e_descarta_ruido(novo_jogo):
    """A 1ª medida (falsa, 1e6 ms) é acusada; a 2ª, real, decide."""
    falso = _relatorio(troca_de_fase={'media_ms': 1e6, 'max_ms': 1e6})
    mudo = dict(saida=lambda m: None)
    assert perf.confirmar_pioras(novo_jogo, _relatorio(troca_de_fase={'media_ms': 1e5}), falso, **mudo) == []
    # Base -PISO_MS: qualquer medida real (> 0 ms) passa do piso. Com base ~0, a 2ª medida
    # precisava passar de 1 ms, e a troca de fase mede ~1 ms: o teste oscilava.
    base_menor = _relatorio(troca_de_fase={'media_ms': -perf.PISO_MS})
    confirmadas = perf.confirmar_pioras(novo_jogo, base_menor, falso, **mudo)
    assert [c[:2] for c in confirmadas] == [('troca_de_fase', 'media_ms')]


def test_sem_suspeitos_nao_mede_nada(novo_jogo, monkeypatch):
    monkeypatch.setattr(perf, 'medir_cenarios', lambda *a, **k: pytest.fail('mediu sem suspeito'))
    rel = _relatorio(horda_150={'media_ms': 1.0, 'p95_ms': 1.0})
    assert perf.confirmar_pioras(novo_jogo, rel, rel) == []
