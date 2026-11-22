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
- Chama `carregar_assets()` **uma vez por sessão**, antes da coleta (alguns módulos de teste leem `ASSETS` no nível do módulo). Leva ~1,5 s e é o custo fixo de qualquer execução. Importar o jogo não carrega nada (D3).
- Fixtures:
  - `tela` e `game` (sessão): um `Game` real.
  - `game` liga `estados_estritos`: transição de estado fora da tabela vira exceção.
  - `novo_jogo`: volta ao menu, `random.seed(1234)` e `game.iniciar_novo_jogo()`, que zera os grupos do `entity_manager` e cria player, mapa da fase 0, spawner e stage manager.
  - `player`: o `Player` real dessa partida.
- `helpers.py`:
  - `simular(game, segundos, desenhar_a_cada)` roda o `update` real com dt fixo de 1/60 e chama o `draw` a cada N frames.
  - `blindar_jogador(player)` deixa a vida enorme e o XP inalcançável, para que a simulação não pare em game over ou level-up.
  - `voltar_ao_menu(game)` encerra a partida de teste em qualquer estado, sem passar pela tabela de transições (no jogo, o menu só vem da pausa ou do game over).
  - `ir_para_fase(game, fase)` troca o mapa sem o fade; fase sem mapa usa o da fase 0. Também é usado por `tools/perf.py`.
  - `MapaSemImagem` reúne os mixins do `Mapa` sem precisar de imagem, para usar com `.tmj` sintéticos.
  - `contar_alocacoes()` (gerenciador de contexto) conta as chamadas a `pygame.Surface(...)`, `mask.from_surface`, `transform.*` e `font.Font`/`SysFont` por tipo; `contador.pausado()` tira um trecho da conta. Não alcança métodos de tipo em C (`Surface.copy`, `convert_alpha`, `Font.render`).

## Estrutura e cobertura
| Arquivo | Cobre |
|---|---|
| `unit/test_core_utils.py` | `GameClock` (incluindo o congelamento fora de `jogando`), `AcumuladorPassoFixo` e o `Game.run` com relógio falso, `path` (com e sem `_MEIPASS`), `direcao_segura`, `empurrao_do_segmento` |
| `unit/test_ranking_data.py` | Ida e volta, gravação atômica, ordenação e limite, formato legado, sanitização, JSON corrompido com backup, falha de escrita |
| `unit/test_map.py` | Parser de `.tmj` (retângulo, polilinha, polígono, spawns, portal, void, navegação), `caminho_livre` e o cache de bbox das paredes |
| `unit/test_grade_paredes.py` | `GradeParedes` (roteiro C1): montagem, degenerados, parâmetros inválidos, bordas e coordenadas negativas, raio maior que a margem, a propriedade "nenhum segmento dentro do raio fica de fora" e a **equivalência** com o empurrão antigo (cópia literal dele no teste) em 1500 posições do mapa 0 (10 mil na C1), para inimigo e jogador |
| `unit/test_dano.py` | Roteiro E1: `Dano` (validação, imutável), a **matriz** escudo × i-frames × `ignora_iframes` × transbordo do jogador e do inimigo, o gancho `ajustar_dano_recebido`, o evento `dano_causado`, os 4 overrides (Guilty, Hunter, Scarab, Warden), a fonte de projéteis e habilidades e um teste por AST: **todo ataque inimigo passa `fonte=`** |
| `unit/test_entrada.py` | Entrada (roteiro E3): validação do `ComandoJogador`, mapeamento do `Teclado` (WASD, V, hacks só com debug), `Roteiro` (ordem, fim parado, reiniciar, erros), um comando por passo, diagonal normalizada, atordoado parado, borda do V no veículo, os 3 hacks como comando; só `entrada.py` chama `get_pressed` |
| `unit/test_status.py` | Sistema de status: validação de cada efeito, acúmulo por tipo (mesma chave renova, chaves diferentes acumulam), duração e congelamento fora do jogo, imunidade de **todas** as classes de boss/miniboss, atordoamento (inimigo e jogador), velocidade, buff de dano × fraqueza × regra das costas, queimadura (ticks, total, crédito da fonte, i-frames, corte de cura), escudo e cura até o máximo, cadência e cegueira (pixels e zero alocação por frame) |
| `unit/test_player.py` | Dano (i-frames, escudo, transbordo, veículo, morte), regeneração de escudo, espinhos, XP com vários níveis e fila de telas, upgrade forçado, buff de cadência (pelo sistema de status) |
| `unit/test_validacao.py` | Roteiro D5: `validar_tudo()` vazio nos dados reais (sem iniciar o pygame) e **um caso que falha de propósito por regra** (armas e registro, pools, os 3 dicts de bosses e o cronograma, perfis de inimigos e drops, manifesto, mapas `.tmj` sintéticos); a abertura do jogo valida só com `MCE_DEBUG=1` |
| `unit/test_dados_inimigos.py` | Roteiro D4: **equivalência** das 19 classes comuns com `tests/golden/inimigos.json` (gravado com os valores antigos: stats, faixas de cooldown e drops na ordem); perfil imutável; cada classe usa o seu perfil e mudar o perfil muda o inimigo |
| `unit/test_levelup_e_armas.py` | `_deve_melhorar`, `min_val`, sorteio e navegação da `TelaDeUpgrade`, equipar e subir **cada** arma até o nível 21 |
| `unit/test_troca_de_fase.py` | Roteiro E5: sobrevivem à troca de fase exatamente os sprites com `sobrevive_troca_de_fase` (jogador, companheiros, aura do MK2; todos os Marines; a flag decide sozinha). O veículo que some na troca está em `xfail(strict=True)`; os companheiros no spawn do mapa novo, em `test_regressoes.py` |
| `unit/test_sistemas.py` | Ritmo, teto e trava de boss, colisão, escudo e escala de inimigos, drops e coleta de itens, pontuação, transição e fim de campanha, portal, estados |
| `unit/test_broadphase.py` | `BroadphaseInimigos` (roteiro C2): mesma lista e mesma ordem do `spritecollide` em sondas aleatórias (com Scarab, Didact e Jega), para o jogador e quadro a quadro em combate com armas de projétil; grupo vazio, inimigo fora do grupo, inimigo circular, reconstrução |
| `unit/test_sem_alocacao.py` | Roteiro C3: `utils/superficies.py`; **equivalência de pixels** com o código antigo (cópia literal) para artilharia, cone, onda EMP e aviso de laser, inclusive na borda e fora da tela; máscaras do cache (inimigo e projétil); update da horda sem `mask.from_surface`; partículas (teto global, fade, sorteios iguais com descarte, reset por partida); cache da granada de plasma e do brilho dos itens |
| `unit/test_render.py` | Roteiro C4: culling pela câmera (fora, borda, imagem maior que o rect, `draw` próprio sempre entra) e **o mundo idêntico pixel a pixel com e sem culling**; HUD parado = zero `Surface` e zero `Font.render` (com e sem boss); texto e barras redesenhados só quando o valor muda |
| `unit/test_regressoes.py` | Um teste por bug corrigido. Inclui um **teste genérico de MRO** (nenhum mixin de inimigo pode ser anulado por `BaseEnemy`), os grupos de todas as armas, o Fuel Rod (DoT e quique), a rajada sem alvo, o Warden, o EMP, o Pelican, o caminho do ranking e o inimigo longe do jogador colidindo com a parede perto dele (C1) |
| `unit/test_estados.py` | Tabela `TRANSICOES` (só estados conhecidos, sem beco sem saída), registro de telas, `mudar_estado` (estrito lança, no jogo loga 1× e aplica, estado inexistente é recusado), nenhum estado escrito à mão no código e os **fluxos reais** percorrendo exatamente a tabela |
| `unit/test_sessao.py` | `SessaoJogo` (roteiro B3): duas partidas seguidas não compartilham sessão, HUD, mapa, câmera, player, spawner nem stage manager; relógio e HUD zerados; partida "suja" não atrapalha a seguinte; o `Game` não guarda mais campos de sessão nem aliases de grupo |
| `unit/test_eventos.py` | Barramento (ordem, dados, nome desconhecido, assinante inválido, assinar durante a emissão, exceção sobe, limpar e limpeza a cada partida), a ordem dos passos do `Game.update` e os eventos emitidos pelo jogo; em 60 s da fase 0, cada inimigo que saiu do mundo gerou exatamente um `inimigo_morreu` |
| `unit/test_shims.py` | Só existem os `# SHIM(<etapa>)` listados em `PERMITIDOS` (roteiro §2, regra 3); hoje, nenhum |
| `unit/test_imports.py` | Todo módulo de `source/` importa sozinho (import quebrado, circular ou nome indefinido no nível do módulo). Módulo novo entra automaticamente |
| `unit/test_lint.py` | `ruff check` verde; toda exceção de `ruff.toml` ainda é necessária (entrada que sobrou falha); a config pega `F821`/`F401`/`F403` |
| `unit/test_perf_tool.py` | `tools/perf.py`: p95, comparação com a tolerância de 10%, base em disco (ausente, ida e volta, inválida), argumentos recusados, `--gravar-base` recusado na bateria, confirmação por nova medida, um cenário por boss e smoke curto (horda e troca de fase, marcado `integration`) |
| `perf/test_catraca.py` | **Catraca de alocação** (roteiro A2): alocações por frame (update + draw, depois de 1 s de aquecimento) na horda de 150, na fase 0 e em cada boss, contra `TETOS`, que só podem descer. Boss novo falha até ganhar teto (a mensagem traz o valor). Medida 10% abaixo do teto gera aviso para baixá-lo, se o teto puder descer (o mínimo é 0,1). Depois da C4 os tetos são 0,1 (Gravemind 0,7). Também testa o próprio contador |
| `integration/test_golden.py` | **Golden master** (roteiro A3): 60 s da fase 0 (seed 1234, jogador blindado, sem input, só update) comparados segundo a segundo com `tests/golden/fase0.json` (inimigos, projéteis, itens, vida, escudo, XP, nível, pontuação, posição). Uma 2ª partida no mesmo processo tem de dar o mesmo resultado; um `Roteiro` de 20 s (E3) tocado 2× também; uma partida nova tem de zerar o relógio. Regerar: `--atualizar-golden` (opção do `conftest.py`), só em mudança de comportamento declarada e com o motivo no log |
| `integration/test_smoke_simulacao.py` | Cada mapa real; uma partida de 10 s; cada inimigo comum por 8 s; **cada boss por 15 s**; cada arma no nível 10 em combate. Também verifica que o Renderer não engoliu nenhum erro |

**Fora da cobertura:** aparência visual, áudio, balanceamento, menus e ranking interativos (`handle_event` das telas) e HUD em detalhe. Tempo não vira asserção (varia por máquina): é medido com `tools/perf.py` e registrado no log. Alocação vira (é determinística): `perf/test_catraca.py`.

## Escrevendo testes novos
- Use o jogo real (as fixtures `novo_jogo` e `player`) em vez de mocks pesados. Os mixins dependem de muitos atributos de `self`.
- Use `relogio.avancar(segundos)` para fazer o tempo passar. Nunca use `sleep`.
- Para aleatoriedade, use `random.seed(...)` ou `monkeypatch.setattr(random, 'uniform', ...)`.
- **Nunca** escreva em `assets/data/ranking.json`. Use `RankingData(str(tmp_path / ...))`.
- **Boss novo:** entra automaticamente no smoke test pelo `PHASE_BOSSES`. **Arma nova:** entra pelo `ARMAS_REGISTRO`.
- **Bug encontrado e não corrigido:** use `@pytest.mark.xfail(strict=True, raises=<Erro>, reason="BUG conhecido ...")` e registre em `docs/log.md`. O `strict=True` faz o teste falhar quando o bug for corrigido, lembrando de remover a marca.
- **Bug corrigido:** adicione a regressão em `unit/test_regressoes.py`. Hoje há **1** `xfail` (fim de campanha e morte no mesmo update pontuam em dobro, achado na B4) em 799 testes.
