# Testes

pytest 9, configuração em `pytest.ini` (saída curta por padrão). Sem CI. Trabalho: só os arquivos afetados; suíte completa 1× no fim.

## O que merece teste
Só o que quebra o jogo ou já quebrou: contrato de dano e status, colisão, progressão (nível, fase, fim de partida), dados,
persistência, regras que definem uma luta (vulnerabilidade, virada de fase, softlock) e regressão de bug real.
**Não** entram: aparência, número de balanceamento, config inválida, imutabilidade, equivalência com código antigo, teste de ferramenta.

## Como funciona
- `conftest.py`: SDL dummy, cwd na raiz, `carregar_assets()` uma vez (~1,5 s). Fixtures: `game` (sessão, estados estritos),
  `novo_jogo` (partida limpa, seed 1234), `player`.
- `helpers.py`: `simular`, `blindar_jogador`, `ir_para_fase`, `voltar_ao_menu`, `MapaSemImagem`, `contar_alocacoes`.
- Tempo: `relogio.avancar(s)`, nunca `sleep`. Ranking: `RankingData(str(tmp_path / ...))`.

## Onde está cada coisa
| Arquivo | Cobre |
|---|---|
| `unit/test_dano`, `test_status`, `test_invisibilidade` | contratos de dano, buffs/debuffs e mira |
| `unit/test_player`, `test_levelup_e_armas`, `test_fuel_rod`, `test_energy_sword` | jogador, armas e level-up |
| `unit/test_efeitos`, `test_skills`, `test_empurrao`, `test_sem_alocacao` | efeitos, skills, knockback, partículas |
| `unit/test_boss_base`, `test_decisao`, `test_animador`, `test_hunter`, `test_zealot`, `test_guilty`, `test_scarab` | motor e lutas |
| `unit/test_sistemas`, `test_eventos`, `test_estados`, `test_sessao`, `test_troca_de_fase`, `test_entrada` | loop, spawner, telas, entrada |
| `unit/test_validacao`, `test_dados_inimigos`, `test_assets`, `test_imports`, `test_lint` | dados e saúde do repo |
| `unit/test_map`, `test_grade_paredes`, `test_broadphase`, `test_camera`, `test_render`, `test_core_utils`, `test_ranking_data` | infraestrutura |
| `unit/test_regressoes` | um teste por bug corrigido (inclui o teste genérico de MRO) |
| `integration/test_smoke_simulacao` | cada mapa, inimigo, boss e arma no loop real, sem erro de render (entra sozinho pelo registro) |
| `integration/test_golden*` | simulação da fase 0 e do Arbiter, e replay determinístico |
| `perf/test_catraca` | alocações por frame ≤ `TETOS` (só descem); boss novo falha até ganhar teto |
