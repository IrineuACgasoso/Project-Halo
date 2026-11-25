# Organização do projeto

Pastas omitidas porque são geradas ou dependências: `.venv/`, `build/`, `dist/`, `__pycache__/` e `.vscode/`.

```
Project-Halo/
├── main.py                  # ENTRYPOINT: pygame.init, janela, Game(tela).run()
├── build.bat                # PyInstaller --onedir (assets/ e source/ vão como data) → dist/main/main.exe
├── ha.ico                   # ícone do executável
├── requirements*.txt        # pygame (runtime) / pytest + ruff (dev)
├── pytest.ini               # config da suíte (testpaths, marker integration)
├── ruff.toml                # linter: regras F + lista de exceções que só encolhe (roteiro A4)
├── CLAUDE.md                # contexto essencial para toda sessão
├── docs/                    # documentação do projeto (este arquivo, log, arquitetura, roteiro_reformulacao, plano_bosses...)
├── assets/                  # ~120 MB, carregados por carregar_assets() (menos os fundos das fases: sob demanda)
│   ├── data/ranking.json    # ranking em dev (versionado); no .exe vai para %APPDATA%/ProjectHalo
│   ├── img/map/<n>/         # m<n>.tmj (Tiled) + imagem de fundo; existem as fases 0–8
│   ├── img/{player,enemies,buddies,projectiles,effects,icons,items,menu}/
│   ├── fonts/ sounds/ audio/
├── tools/
│   ├── perf.py              # medição headless de ms/frame por cenário (roteiro A1)
│   ├── lutas.py             # métricas das lutas de boss com o bot jogador (roteiro F4)
│   └── perf_base.json       # última base medida (comparada pelo perf.py; ±10% = portão)
├── tests/                   # pytest — ver docs/testing.md
│   ├── conftest.py          # SDL dummy, cwd=raiz, fixtures game/novo_jogo/player
│   ├── helpers.py           # simular(), blindar_jogador(), ir_para_fase(), contar_alocacoes(), MapaSemImagem
│   ├── bot.py               # Bot (FonteEntrada): mantém distância e esquiva; usado por tools/lutas.py
│   ├── golden/              # fase0.json e arbiter.json. Só com --atualizar-golden
│   ├── perf/                # test_catraca.py: alocações por frame ≤ teto (roteiro A2)
│   ├── unit/                # lógica isolada: player, mapa, ranking, level-up, spawner, colisão...
│   │                        # test_regressoes.py = um teste por bug já corrigido
│   └── integration/         # smoke: loop real com cada mapa/inimigo/boss/arma
└── source/
    ├── game.py              # classe Game: estado, criação da sessão, update, fim de partida
    ├── debug.py             # DEBUG = MCE_DEBUG=='1'
    ├── data/
    │   ├── weapon_data.py   # BALANCEAMENTO: WEAPON_DATA, COMPANION_DATA, VEHICLES_DATA (WeaponStats)
    │   ├── enemy_data.py    # BALANCEAMENTO dos inimigos comuns: INIMIGOS (PerfilInimigo: vida, dano, velocidade, cooldowns, drops)
    │   ├── manifesto_assets.py # MANIFESTO: toda imagem (arquivo, escala, alpha, espelhar), no formato de ASSETS
    │   └── validacao.py     # validar_tudo(): lista de erros dos dados (armas, pools, bosses, inimigos, manifesto, mapas) (D5)
    ├── utils/               # paths.path(), fonts.carregar_fonte (cache), vetores (direcao_segura; no_cone e no_retangulo: ponto na área sem trigonometria),
    │                        # collision_utils (empurrão de parede em float),
    │                        # superficies (máscara em cache, camada alpha e rascunho reaproveitados: C3),
    │                        # reducao (o mundo afastado reduzido para a tela)
    ├── systems/
    │   ├── gameclock.py     # relogio (singleton, ms de jogo) + AcumuladorPassoFixo (Game.run, 1/60 s)
    │   ├── entitymanager.py # entity_manager (singleton, grupos de sprite, inclusive particulas_grupo)
    │   ├── estados.py       # constantes de estado, TRANSICOES, Tela (roteiro B2)
    │   ├── sessao.py        # SessaoJogo: estado de UMA partida, recriado a cada partida (roteiro B3)
    │   ├── eventos.py       # barramento síncrono de eventos de jogo (roteiro B4)
    │   ├── entrada.py       # ComandoJogador + FonteEntrada (Teclado, Roteiro): o jogador lê o comando, não o teclado (roteiro E3)
    │   ├── dano.py          # Dano (valor, tipo, fonte, ignora_iframes): contrato único de dano (roteiro E1)
    │   ├── status/          # buffs e debuffs: efeitos.py (dados validados), status.py (aplicar, StatusEntidade), cegueira.py e fogo.py (desenho)
    │   ├── eventmanager.py  # handlers tratar_<estado> + aplicação da escolha de upgrade
    │   ├── renderer.py      # desenhar_<estado>, blindado contra exceções; culling pela câmera (C4)
    │   ├── collision.py     # CollisionManager: projéteis, contato, itens, auras, mortes; BroadphaseInimigos (C2)
    │   ├── stagemanager.py  # fade e troca de fase/mapa; fim de campanha
    │   ├── camera.py        # offset seguindo o player + shake + zoom (definir_zoom, visao)
    │   ├── empurrao.py      # knockback: empurrar(alvo, origem, forca), sem atravessar paredes
    │   ├── spawner/         # spawner.py (ritmo/teto), spawner_pools.py (inimigos por fase),
    │   │                    # spawner_bosses.py (PHASE_BOSSES, BOSS_CLASSES, CRONOGRAMA_BOSSES)
    │   ├── mapmanager/      # Mapa = loader(.tmj) + collision(paredes) + utils(navegação) + feats(void)
│   │                    # grade_paredes.py: GradeParedes (segmentos por célula de 128 px, roteiro C1)
    │   ├── levelup/         # constants.py (ARMAS_REGISTRO, MAX_ARMAS=6, máximo e peso por raridade, paletas), levelup.py (gerar_opcoes, TelaDeUpgrade), draw.py
    │   └── hud/             # hud_system.py (estado) + hud_draw.py (desenho; barras, fundos e textos em cache: C4)
    ├── player/              # Player + mixins: input (aplica o ComandoJogador), movement, animation, combat (dano/escudo/espinhos),
    │                        # scaling (XP/level-up/buff), setup (valores iniciais)
    ├── enemies/
    │   ├── base/            # BaseEnemy + mixins (setup, sprites, animation, movement, collision, combat, scaling, effects)
    │   │   └── boss/        # BossBase (motor: rotinas, cooldowns, fases, anti-stuck), ContextoCombate, FaseBoss, DetectorTravamento (F1);
    │   │                    # animador.py: Clip + Animador (clips, hit frames, quadros copiados no spawn: F2);
    │   │                    # decisao.py: Habilidade, Decisor, MemoriaDeCombate (notas e memória: F3)
    │   ├── standard/        # grunt, jackal, elite, brute, infection(flood), sentinel, crawler, soldier, watcher
    │   ├── minibosses/      # hunter (config/setup/states/attacks/vfx: rotinas geradoras), zealot (idem + movement, sobre a BossBase), knight,
    │   │                    # scarab (BossBase; config/corpo/recortes/patas/movement/armas/feixe)
    │   └── bosses/          # guilty (BossBase; config/barreira/invocacoes/armadilha/luz_visivel), arbiter*, tartarus, gravemind, didact, warden, guardian, jega, escharum,
    │                        # harbinger, atriox  (*arbiter: reescrita em andamento com config.py + rotinas)
    ├── feats/
    │   ├── assets.py        # ASSETS + carregar_assets(): monta as imagens do manifesto (chamado pelo main.py; import limpo, D3); MapasSobDemanda (D2)
    │   ├── weapons/         # baseweapon.py (Arma: grupos via entity_manager; ArmaDeRajada) + pastas por raridade: comum/incomum/rara/epica/lendaria
    │   ├── projetil/        # ProjetilUniversal + subclasses (brick, carabin, needler, laserblast...)
    │   ├── buddies/         # Companheiro (IA) + wrappers Arbitro, Cortana, Marine, NobleVI
    │   ├── vehicles/        # Vehicle + Warhog, Pelican (tecla V)
    │   ├── items/           # Items (drop/coleta) + draw.py (visual/cache)
    │   ├── skills/          # artilharia, cone_strike, rect_strike (retângulo), invisibilidade (+ distorcao.py), onda_emp, purge_grid, dash (config.py + core), beam, mortar, tp...
│   │                    # artilharia, cone, rect e mortar aceitam ao_explodir (callback 1× na explosão: poeira, vfx);
│   │                    # artilharia/poca_plasma.py: PocaDePlasma, a área do Fuel Rod (queimadura: `queimadura_ms`)
    │   ├── grenades.py      # GrenadeBase, Spike, PlasmaGrenade, FuelRodGrenade (gota de plasma, quique)
    │   ├── auras.py         # EnergyAura (boss), PlayerAura (MK2)
    │   ├── particulas.py    # Particula + emitir (teto global em entity_manager.particulas_grupo, C3)
    │   └── effects.py       # Portal, poeira, raio de escudo, quebra de escudo, soco Spartan
    └── windows/             # menu/, ranking/ (ranking_data.py = persistência), settings/ (constantes de tela), colaboradores.py
```

## Onde mexer para...
| Tarefa | Onde |
|---|---|
| Balancear arma, companion ou veículo | `source/data/weapon_data.py` |
| Nível máximo ou peso no sorteio por raridade | `systems/levelup/constants.py` (`NIVEL_MAXIMO_POR_RARIDADE`, `PESO_SORTEIO_POR_RARIDADE`; a raridade de cada arma fica no `ArmaInfo`) |
| O que ganhar quando não há upgrade possível (tudo no máximo) | `player/player_scaling.py::recompensa_sem_upgrade` (provisório; `TODO(itens temporários)`) |
| Nova arma | Classe em `feats/weapons/<raridade>/` (construtor `(jogador, game, **kwargs)`, repassando os `kwargs` à base; ganho de nível próprio em `aplicar_nivel`; rajada: `ArmaDeRajada`) com `NOME_ASSET`, exportada em `weapons/__init__.py`, perfil em `weapon_data.py`, `ArmaInfo` em `systems/levelup/constants.py`, ícone opcional em `MANIFESTO['icons']` (`data/manifesto_assets.py`) |
| Novo companion ou veículo | `feats/buddies/` ou `feats/vehicles/`, com `COMPANION_DATA`/`VEHICLES_DATA` e `ARMAS_REGISTRO` |
| Novo inimigo comum | `enemies/standard/` (herda de `BaseEnemy`), perfil em `INIMIGOS` (`data/enemy_data.py`), sprites em `MANIFESTO['enemies']`, peso em `spawner_pools.py` |
| Balancear inimigo comum (vida, dano, velocidade, cooldowns, drops) | `source/data/enemy_data.py` |
| Novo boss | Pasta em `enemies/bosses/<nome>/`, registrada em `spawner_bosses.py` nos 3 dicts. Herde de `BossBase` (`enemies/base/boss/`; contrato no docstring de `boss_base.py`; exemplo: o Arbiter). Desenho em `docs/plano_bosses.md` |
| Motor comum dos bosses (ciclo do frame, cooldowns, fases, anti-stuck, mira antecipada) | `enemies/base/boss/boss_base.py`; percepção em `contexto.py` |
| Como um boss escolhe a habilidade (pesos, alcances, leitura do jogador) | `HABILIDADES` no `config.py` do boss + `pontuar_<nome>(ctx)` nos `states.py`; a conta em `enemies/base/boss/decisao.py` |
| Animação de um boss da `BossBase` (ritmo, quadros de cada estado, hit frame) | `CLIPS`/`CLIP_INICIAL` no `config.py` do boss (`Clip` em `enemies/base/boss/animador.py`); a rotina pede com `self.animador.tocar(nome)` ou espera o golpe com `yield from self._tocar(clip, ate_evento)` |
| Animação ou efeito visual próprio de um boss (brilho, poeira) | `vfx.py` no pacote do boss (ex.: `minibosses/hunter/vfx.py`) |
| Balancear o Hunter (defesa, ângulo das costas, atrasos, pesos da IA, cooldowns, camera shake) | `enemies/minibosses/hunter/config.py` |
| Balancear o Guilty Spark (barreira, ronda, pesos, intervalos das invocações, feixes, teleporte) | `enemies/bosses/guilty/config.py` (artilharias: presets `guilty_*` em `feats/skills/artilharia/config.py`) |
| Balancear o Zealot (escudo, pesos, pausas do combo, fuga, regeneração) | `enemies/minibosses/zealot/config.py` (danos e áreas: presets `zealot_*` das skills) |
| Inimigo que nasce invisível e aparece | `self.materializar()` logo depois de criar (`enemies/base/enemy_combat.py`) |
| Boss que religa os inimigos comuns | `permitir_spawns_normais = True` nele (lido por `Game._atualizar_spawner` e `Spawner.update`) |
| Camuflagem de um inimigo (tempos, distorção) | `feats/skills/invisibilidade/` (preset em `config.py`; `self.iniciar_invisibilidade(preset)` + `atualizar_invisibilidade(dt)` por passo; visual em `distorcao.py`) |
| Quem pode ser mirado ou atingido | `BaseEnemy.alvejavel` / `invulneravel` (`enemies/base/enemy_base.py`) |
| Balancear o Scarab (patas e ângulos, núcleo, passos, golpes, feixe, guarnição, zoom, tremores) | `enemies/minibosses/scarab/config.py` (artilharias: presets `scarab_*` em `feats/skills/artilharia/config.py`) |
| Arte do Scarab (recorte novo, pata danificada, pose) | PNG em `scarab/partes/<variante>/`, nome em `PARTES_SCARAB` (`data/manifesto_assets.py`), canto em `scarab/recortes.py`, desenho em `scarab/corpo.py` |
| Afastar a câmera (boss gigante, cena) | `game.camera.definir_zoom(alvo, ms)`; volte a 1 no `kill` de quem afastou |
| Sprite desenhado por cima (ou por baixo) do que a posição dele manda | `y_desenho` na classe (lido por `Renderer._profundidade`) |
| Empurrar alguém (knockback) | `knockback=<px>` no preset da artilharia, ou `empurrar(...)` de `systems/empurrao.py` |
| Nova habilidade de área ou telegraph | Preset em `feats/skills/<skill>/config.py` |
| Investida (dash) de inimigo | `feats/skills/dash/` (`Dash(inimigo, alvo, preset)`; preset em `config.py`) |
| Nova fase | `assets/img/map/<n>/m<n>.tmj` + registro em `MANIFESTO['maps']`, `PHASE_POOLS[n]` e `PHASE_BOSSES[n]` |
| Sprite que sobrevive à troca de fase | `sobrevive_troca_de_fase = True` na classe (lido por `systems/stagemanager.py`) |
| Visual do Fuel Rod (gota, rastro, poça) | `feats/grenades.py::FuelRodGrenade` (gota desenhada no código) e `feats/skills/artilharia/poca_plasma.py` (raio, pavio e cores: preset `fuel_rod`) |
| Drops de inimigo | `morrer()` do inimigo/boss → `Items.spawn_drop(...)` |
| Efeito de item coletado | `feats/items/items.py::_aplicar_efeito` |
| Teclas do jogador, replay ou bot | `systems/entrada.py` (`Teclado`, `Roteiro`; a fonte fica em `Game.entrada`) |
| Cheats L/P/B (ligar/desligar, novo cheat) | Botão em `windows/menu/pause_menu.py`, estado em `Teclado.cheats` (`Game.alternar_cheats`), efeito em `player/player_input.py::executar_hacks` |
| Fogo de quem está queimando | `systems/status/fogo.py` |
| Quebra de escudo ou soco Spartan (visual) | `feats/effects.py` (`quebra_de_escudo`, `impacto_do_soco`); ganchos `ao_quebrar_escudo` (inimigo) e `zerar_escudo` (jogador) |
| Regras de dano do jogador | `player/player_combat.py::receber_dano` |
| Buff ou debuff (aplicar, novo efeito, imunidade de boss) | `systems/status/` (`aplicar(alvo, efeito, fonte, chave)`); efeito novo = dataclass em `efeitos.py` + o cálculo em `StatusEntidade._recalcular` |
| Regra de dano própria de um inimigo (costas, imunidade) | `ajustar_dano_recebido` na classe dele (contrato em `systems/dano.py`) |
| Curva de XP e bônus de nível | `player/player_scaling.py::level_up` |
| Escala de dificuldade dos inimigos | `enemies/base/enemy_scaling.py` |
| Nova tela ou estado | Constante e transições em `systems/estados.py`, `tratar_<estado>` em `eventmanager.py`, `desenhar_<estado>` em `renderer.py` e a linha em `Game._registrar_telas` |
| HUD | `systems/hud/hud_draw.py` |
| Resolução ou FPS | `windows/settings/settings_constants.py` |
| Regra de integridade de dados | `source/data/validacao.py` + um caso que falha em `tests/unit/test_validacao.py` |
| Testes | `tests/unit/` (lógica) ou `tests/integration/` (loop real) |
| Medir desempenho | `tools/perf.py` (cenários em `listar_cenarios()`) |
| Medir uma luta de boss (tempo, acerto, uso de habilidades) | `tools/lutas.py --boss <nome>` (régua fixa: `ARSENAL`, `NIVEL_INICIAL`); o jeito de jogar está em `tests/bot.py` |
