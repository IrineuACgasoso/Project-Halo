# Testes

**Framework:** pytest 9 (`requirements-dev.txt`). A configuração fica em `pytest.ini`. Não há CI.

```powershell
.venv\Scripts\python.exe -m pytest                       # tudo (~90 s; ~25 s são a catraca e o golden)
.venv\Scripts\python.exe -m pytest tests/unit            # unitários
.venv\Scripts\python.exe -m pytest -m "not integration"  # sem as simulações
.venv\Scripts\python.exe -m pytest -k boss -x            # filtro por nome, parando na 1ª falha
```

## Como funciona (`tests/conftest.py`)
- Antes de qualquer import do pygame, o conftest:
  - força `SDL_VIDEODRIVER=dummy` e `SDL_AUDIODRIVER=dummy`;
  - muda o cwd para a raiz, porque `path()` é relativo ao cwd;
  - remove `MCE_DEBUG`.
- Importa `source.feats.assets` **uma vez por sessão**. Esse import leva cerca de 13 s e é o custo fixo de qualquer execução.
- Fixtures:
  - `tela` e `game` (sessão): um `Game` real.
  - `novo_jogo`: `random.seed(1234)` mais `game.iniciar_novo_jogo()`, que zera os grupos do `entity_manager` e cria player, mapa da fase 0, spawner e stage manager.
  - `player`: o `Player` real dessa partida.
- `helpers.py`:
  - `simular(game, segundos, desenhar_a_cada)` roda o `update` real com dt fixo de 1/60 e chama o `draw` a cada N frames.
  - `blindar_jogador(player)` deixa a vida enorme e o XP inalcançável, para que a simulação não pare em game over ou level-up.
  - `ir_para_fase(game, fase)` troca o mapa sem o fade; fase sem mapa usa o da fase 0. Também é usado por `tools/perf.py`.
  - `MapaSemImagem` reúne os mixins do `Mapa` sem precisar de imagem, para usar com `.tmj` sintéticos.
  - `contar_alocacoes()` (gerenciador de contexto) conta as chamadas a `pygame.Surface(...)`, `mask.from_surface`, `transform.*` e `font.Font`/`SysFont` por tipo; `contador.pausado()` tira um trecho da conta. Não alcança métodos de tipo em C (`Surface.copy`, `convert_alpha`, `Font.render`).

## Estrutura e cobertura
| Arquivo | Cobre |
|---|---|
| `unit/test_core_utils.py` | `GameClock` (incluindo o congelamento fora de `jogando`), `AcumuladorPassoFixo` e o `Game.run` com relógio falso, `path` (com e sem `_MEIPASS`), `direcao_segura`, `projetar_fora_da_linha` |
| `unit/test_ranking_data.py` | Ida e volta, gravação atômica, ordenação e limite, formato legado, sanitização, JSON corrompido com backup, falha de escrita |
| `unit/test_map.py` | Parser de `.tmj` (retângulo, polilinha, polígono, spawns, portal, void, navegação), `caminho_livre`, filtro e cache de paredes |
| `unit/test_player.py` | Dano (i-frames, escudo, transbordo, veículo, morte), regeneração de escudo, espinhos, XP com vários níveis e fila de telas, upgrade forçado, buff de cooldown |
| `unit/test_levelup_e_armas.py` | Integridade de `ARMAS_REGISTRO` e `weapon_data`, `_deve_melhorar`, `min_val`, sorteio e navegação da `TelaDeUpgrade`, equipar e subir **cada** arma até o nível 21 |
| `unit/test_sistemas.py` | Config do spawner (pools, bosses, cronograma), ritmo, teto e trava de boss, colisão, escudo e escala de inimigos, drops e coleta de itens, pontuação, transição e fim de campanha, portal, estados |
| `unit/test_regressoes.py` | Um teste por bug corrigido. Inclui um **teste genérico de MRO** (nenhum mixin de inimigo pode ser anulado por `BaseEnemy`), os grupos de todas as armas, o Fuel Rod (DoT e quique), a rajada sem alvo, o Warden, o EMP, o Pelican e o caminho do ranking |
| `unit/test_imports.py` | Todo módulo de `source/` importa sozinho (import quebrado, circular ou nome indefinido no nível do módulo). Módulo novo entra automaticamente |
| `unit/test_lint.py` | `ruff check` verde; toda exceção de `ruff.toml` ainda é necessária (entrada que sobrou falha); a config pega `F821`/`F401`/`F403` |
| `unit/test_perf_tool.py` | `tools/perf.py`: p95, comparação com a tolerância de 10%, base em disco (ausente, ida e volta, inválida), argumentos recusados, `--gravar-base` recusado na bateria, confirmação por nova medida, um cenário por boss e smoke curto (horda e troca de fase, marcado `integration`) |
| `perf/test_catraca.py` | **Catraca de alocação** (roteiro A2): alocações por frame (update + draw, depois de 1 s de aquecimento) na horda de 150, na fase 0 e em cada boss, contra `TETOS`, que só podem descer. Boss novo falha até ganhar teto (a mensagem traz o valor). Medida 10% abaixo do teto gera aviso para baixá-lo. Também testa o próprio contador |
| `integration/test_golden.py` | **Golden master** (roteiro A3): 60 s da fase 0 (seed 1234, jogador blindado, sem input, só update) comparados segundo a segundo com `tests/golden/fase0.json` (inimigos, projéteis, itens, vida, escudo, XP, nível, pontuação, posição). Uma 2ª partida no mesmo processo tem de dar o mesmo resultado. Regerar: `--atualizar-golden` (opção do `conftest.py`), só em mudança de comportamento declarada e com o motivo no log |
| `integration/test_smoke_simulacao.py` | Cada mapa real; uma partida de 10 s; cada inimigo comum por 8 s; **cada boss por 15 s**; cada arma no nível 10 em combate. Também verifica que o Renderer não engoliu nenhum erro |

**Fora da cobertura:** aparência visual, áudio, balanceamento, menus e ranking interativos (`handle_event` das telas) e HUD em detalhe. Tempo não vira asserção (varia por máquina): é medido com `tools/perf.py` e registrado no log. Alocação vira (é determinística): `perf/test_catraca.py`.

## Escrevendo testes novos
- Use o jogo real (as fixtures `novo_jogo` e `player`) em vez de mocks pesados. Os mixins dependem de muitos atributos de `self`.
- Use `relogio.avancar(segundos)` para fazer o tempo passar. Nunca use `sleep`.
- Para aleatoriedade, use `random.seed(...)` ou `monkeypatch.setattr(random, 'uniform', ...)`.
- **Nunca** escreva em `assets/data/ranking.json`. Use `RankingData(str(tmp_path / ...))`.
- **Boss novo:** entra automaticamente no smoke test pelo `PHASE_BOSSES`. **Arma nova:** entra pelo `ARMAS_REGISTRO`.
- **Bug encontrado e não corrigido:** use `@pytest.mark.xfail(strict=True, raises=<Erro>, reason="BUG conhecido ...")` e registre em `docs/log.md`. O `strict=True` faz o teste falhar quando o bug for corrigido, lembrando de remover a marca.
- **Bug corrigido:** adicione a regressão em `unit/test_regressoes.py`. Hoje há **1** `xfail` (relógio não zerado entre partidas, para a B3) em 661 testes.
