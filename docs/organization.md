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
│   ├── img/{player,enemies,buddies,projectiles,icons,items,menu}/
│   ├── fonts/ sounds/ audio/
├── tools/
│   ├── perf.py              # medição headless de ms/frame por cenário (roteiro A1)
│   └── perf_base.json       # última base medida (comparada pelo perf.py; ±10% = portão)
├── tests/                   # pytest — ver docs/testing.md
│   ├── conftest.py          # SDL dummy, cwd=raiz, fixtures game/novo_jogo/player
│   ├── helpers.py           # simular(), blindar_jogador(), ir_para_fase(), contar_alocacoes(), MapaSemImagem
│   ├── golden/              # fase0.json: golden master (A3); assets.json: assinatura de cada imagem (D1). Só com --atualizar-golden
│   ├── perf/                # test_catraca.py: alocações por frame ≤ teto (roteiro A2)
│   ├── unit/                # lógica isolada: player, mapa, ranking, level-up, spawner, colisão...
│   │                        # test_regressoes.py = um teste por bug já corrigido
│   └── integration/         # smoke: loop real com cada mapa/inimigo/boss/arma
└── source/
    ├── game.py              # classe Game: estado, criação da sessão, update, fim de partida
    ├── debug.py             # DEBUG = MCE_DEBUG=='1'
    ├── docs/BOSS_CREATION.md# guia antigo de bosses (BossBase inexistente); será substituído por docs/plano_bosses.md
    ├── data/
    │   ├── weapon_data.py   # BALANCEAMENTO: WEAPON_DATA, COMPANION_DATA, VEHICLES_DATA (WeaponStats)
    │   ├── enemy_data.py    # BALANCEAMENTO dos inimigos comuns: INIMIGOS (PerfilInimigo: vida, dano, velocidade, cooldowns, drops)
    │   ├── manifesto_assets.py # MANIFESTO: toda imagem (arquivo, escala, alpha, espelhar), no formato de ASSETS
    │   └── validacao.py     # validar_tudo(): lista de erros dos dados (armas, pools, bosses, inimigos, manifesto, mapas) (D5)
    ├── utils/               # paths.path(), fonts.carregar_fonte (cache), vetores, collision_utils (empurrão de parede em float),
    │                        # superficies (máscara em cache, camada alpha e rascunho reaproveitados: C3)
    ├── systems/
    │   ├── gameclock.py     # relogio (singleton, ms de jogo) + AcumuladorPassoFixo (Game.run, 1/60 s)
    │   ├── entitymanager.py # entity_manager (singleton, grupos de sprite, inclusive particulas_grupo)
    │   ├── estados.py       # constantes de estado, TRANSICOES, Tela (roteiro B2)
    │   ├── sessao.py        # SessaoJogo: estado de UMA partida, recriado a cada partida (roteiro B3)
    │   ├── eventos.py       # barramento síncrono de eventos de jogo (roteiro B4)
    │   ├── eventmanager.py  # handlers tratar_<estado> + aplicação da escolha de upgrade
    │   ├── renderer.py      # desenhar_<estado>, blindado contra exceções; culling pela câmera (C4)
    │   ├── collision.py     # CollisionManager: projéteis, contato, itens, auras, mortes; BroadphaseInimigos (C2)
    │   ├── stagemanager.py  # fade e troca de fase/mapa; fim de campanha
    │   ├── camera.py        # offset seguindo o player + shake
    │   ├── spawner/         # spawner.py (ritmo/teto), spawner_pools.py (inimigos por fase),
    │   │                    # spawner_bosses.py (PHASE_BOSSES, BOSS_CLASSES, CRONOGRAMA_BOSSES)
    │   ├── mapmanager/      # Mapa = loader(.tmj) + collision(paredes) + utils(navegação) + feats(void)
│   │                    # grade_paredes.py: GradeParedes (segmentos por célula de 128 px, roteiro C1)
    │   ├── levelup/         # constants.py (ARMAS_REGISTRO, MAX_ARMAS=6, paletas), levelup.py (TelaDeUpgrade), draw.py
    │   └── hud/             # hud_system.py (estado) + hud_draw.py (desenho; barras, fundos e textos em cache: C4)
    ├── player/              # Player + mixins: input, movement, animation, combat (dano/escudo/espinhos),
    │                        # scaling (XP/level-up/buff), setup (valores iniciais)
    ├── enemies/
    │   ├── base/            # BaseEnemy + mixins (setup, sprites, animation, movement, collision, combat, scaling, effects)
    │   ├── standard/        # grunt, jackal, elite, brute, infection(flood), sentinel, crawler, soldier, watcher
    │   ├── minibosses/      # hunter, zealot, scarab, knight  (core/setup/states/attacks)
    │   └── bosses/          # guilty, arbiter*, tartarus, gravemind, didact, warden, guardian, jega, escharum,
    │                        # harbinger, atriox  (*arbiter: reescrita em andamento com config.py + rotinas)
    ├── feats/
    │   ├── assets.py        # ASSETS + carregar_assets(): monta as imagens do manifesto (chamado pelo main.py; import limpo, D3); MapasSobDemanda (D2)
    │   ├── weapons/         # baseweapon.py (Arma) + pastas por raridade: comum/incomum/rara/epica/lendaria
    │   ├── projetil/        # ProjetilUniversal + subclasses (brick, carabin, needler, laserblast...)
    │   ├── buddies/         # Companheiro (IA) + wrappers Arbitro, Cortana, Marine, NobleVI
    │   ├── vehicles/        # Vehicle + Warhog, Pelican (tecla V)
    │   ├── items/           # Items (drop/coleta) + draw.py (visual/cache)
    │   ├── skills/          # artilharia, cone_strike, onda_emp, purge_grid (config.py + core), beam, mortar, tp...
    │   ├── grenades.py      # GrenadeBase, Spike, PlasmaGrenade, FuelRodGrenade (quique)
    │   ├── auras.py         # EnergyAura (boss), PlayerAura (MK2)
    │   ├── particulas.py    # Particula + emitir (teto global em entity_manager.particulas_grupo, C3)
    │   └── effects.py       # Portal, poeira, raio de escudo, faíscas
    └── windows/             # menu/, ranking/ (ranking_data.py = persistência), settings/ (constantes de tela), colaboradores.py
```

## Onde mexer para...
| Tarefa | Onde |
|---|---|
| Balancear arma, companion ou veículo | `source/data/weapon_data.py` |
| Nova arma | Classe em `feats/weapons/<raridade>/` com `NOME_ASSET`, exportada em `weapons/__init__.py`, perfil em `weapon_data.py`, `ArmaInfo` em `systems/levelup/constants.py`, ícone opcional em `MANIFESTO['icons']` (`data/manifesto_assets.py`) |
| Novo companion ou veículo | `feats/buddies/` ou `feats/vehicles/`, com `COMPANION_DATA`/`VEHICLES_DATA` e `ARMAS_REGISTRO` |
| Novo inimigo comum | `enemies/standard/` (herda de `BaseEnemy`), perfil em `INIMIGOS` (`data/enemy_data.py`), sprites em `MANIFESTO['enemies']`, peso em `spawner_pools.py` |
| Balancear inimigo comum (vida, dano, velocidade, cooldowns, drops) | `source/data/enemy_data.py` |
| Novo boss | Pasta em `enemies/bosses/<nome>/`, registrada em `spawner_bosses.py` nos 3 dicts. Arquitetura futura em `docs/plano_bosses.md` |
| Nova habilidade de área ou telegraph | Preset em `feats/skills/<skill>/config.py` |
| Nova fase | `assets/img/map/<n>/m<n>.tmj` + registro em `MANIFESTO['maps']`, `PHASE_POOLS[n]` e `PHASE_BOSSES[n]` |
| Drops de inimigo | `morrer()` do inimigo/boss → `Items.spawn_drop(...)` |
| Efeito de item coletado | `feats/items/items.py::_aplicar_efeito` |
| Regras de dano do jogador | `player/player_combat.py::receber_dano` |
| Curva de XP e bônus de nível | `player/player_scaling.py::level_up` |
| Escala de dificuldade dos inimigos | `enemies/base/enemy_scaling.py` |
| Nova tela ou estado | Constante e transições em `systems/estados.py`, `tratar_<estado>` em `eventmanager.py`, `desenhar_<estado>` em `renderer.py` e a linha em `Game._registrar_telas` |
| HUD | `systems/hud/hud_draw.py` |
| Resolução ou FPS | `windows/settings/settings_constants.py` |
| Regra de integridade de dados | `source/data/validacao.py` + um caso que falha em `tests/unit/test_validacao.py` |
| Testes | `tests/unit/` (lógica) ou `tests/integration/` (loop real) |
| Medir desempenho | `tools/perf.py` (cenários em `listar_cenarios()`) |
