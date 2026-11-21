# Testes

**Framework:** pytest 9 (`requirements-dev.txt`). A configuração fica em `pytest.ini`. Não há CI.

```powershell
.venv\Scripts\python.exe -m pytest                       # tudo (35–75 s conforme a máquina)
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
  - `MapaSemImagem` reúne os mixins do `Mapa` sem precisar de imagem, para usar com `.tmj` sintéticos.

## Estrutura e cobertura
| Arquivo | Cobre |
|---|---|
| `unit/test_core_utils.py` | `GameClock` (incluindo o congelamento fora de `jogando`), `path` (com e sem `_MEIPASS`), `direcao_segura`, `projetar_fora_da_linha` |
| `unit/test_ranking_data.py` | Ida e volta, gravação atômica, ordenação e limite, formato legado, sanitização, JSON corrompido com backup, falha de escrita |
| `unit/test_map.py` | Parser de `.tmj` (retângulo, polilinha, polígono, spawns, portal, void, navegação), `caminho_livre`, filtro e cache de paredes |
| `unit/test_player.py` | Dano (i-frames, escudo, transbordo, veículo, morte), regeneração de escudo, espinhos, XP com vários níveis e fila de telas, upgrade forçado, buff de cooldown |
| `unit/test_levelup_e_armas.py` | Integridade de `ARMAS_REGISTRO` e `weapon_data`, `_deve_melhorar`, `min_val`, sorteio e navegação da `TelaDeUpgrade`, equipar e subir **cada** arma até o nível 21 |
| `unit/test_sistemas.py` | Config do spawner (pools, bosses, cronograma), ritmo, teto e trava de boss, colisão, escudo e escala de inimigos, drops e coleta de itens, pontuação, transição e fim de campanha, portal, estados |
| `unit/test_regressoes.py` | Um teste por bug corrigido. Inclui um **teste genérico de MRO** (nenhum mixin de inimigo pode ser anulado por `BaseEnemy`), os grupos de todas as armas, o Fuel Rod (DoT e quique), a rajada sem alvo, o Warden, o EMP, o Pelican e o caminho do ranking |
| `integration/test_smoke_simulacao.py` | Cada mapa real; uma partida de 10 s; cada inimigo comum por 8 s; **cada boss por 15 s**; cada arma no nível 10 em combate. Também verifica que o Renderer não engoliu nenhum erro |

**Fora da cobertura:** aparência visual, áudio, balanceamento, menus e ranking interativos (`handle_event` das telas), HUD em detalhe e performance.

## Escrevendo testes novos
- Use o jogo real (as fixtures `novo_jogo` e `player`) em vez de mocks pesados. Os mixins dependem de muitos atributos de `self`.
- Use `relogio.avancar(segundos)` para fazer o tempo passar. Nunca use `sleep`.
- Para aleatoriedade, use `random.seed(...)` ou `monkeypatch.setattr(random, 'uniform', ...)`.
- **Nunca** escreva em `assets/data/ranking.json`. Use `RankingData(str(tmp_path / ...))`.
- **Boss novo:** entra automaticamente no smoke test pelo `PHASE_BOSSES`. **Arma nova:** entra pelo `ARMAS_REGISTRO`.
- **Bug encontrado e não corrigido:** use `@pytest.mark.xfail(strict=True, raises=<Erro>, reason="BUG conhecido ...")` e registre em `docs/log.md`. O `strict=True` faz o teste falhar quando o bug for corrigido, lembrando de remover a marca.
- **Bug corrigido:** adicione a regressão em `unit/test_regressoes.py`. Hoje a suíte não tem nenhum `xfail` (347 testes).
