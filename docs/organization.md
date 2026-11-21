# Organização do projeto

Pastas omitidas porque são geradas ou dependências: `.venv/`, `build/`, `dist/`, `__pycache__/` e `.vscode/`.

```
Project-Halo/
├── main.py                  # ENTRYPOINT: pygame.init, janela, Game(tela).run()
├── build.bat                # PyInstaller --onedir (assets/ e source/ vão como data) → dist/main/main.exe
├── ha.ico                   # ícone do executável
├── requirements*.txt        # pygame (runtime) / pytest (dev)
├── pytest.ini               # config da suíte (testpaths, marker integration)
├── CLAUDE.md                # contexto essencial para toda sessão
├── docs/                    # documentação do projeto (este arquivo, log, arquitetura, roteiro_reformulacao, plano_bosses...)
├── assets/                  # ~120 MB, carregados TODOS no import de feats/assets.py
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
│   ├── perf/                # test_catraca.py: alocações por frame ≤ teto (roteiro A2)
│   ├── unit/                # lógica isolada: player, mapa, ranking, level-up, spawner, colisão...
│   │                        # test_regressoes.py = um teste por bug já corrigido
│   └── integration/         # smoke: loop real com cada mapa/inimigo/boss/arma
└── source/
    ├── game.py              # classe Game: estado, reset de sessão, update, fim de partida
    ├── debug.py             # DEBUG = MCE_DEBUG=='1'
    ├── docs/BOSS_CREATION.md# guia antigo de bosses (BossBase inexistente); será substituído por docs/plano_bosses.md
    ├── data/
    │   ├── weapon_data.py   # BALANCEAMENTO: WEAPON_DATA, COMPANION_DATA, VEHICLES_DATA (WeaponStats)
    │   └── enemy_data.py    # vazio
    ├── utils/               # paths.path(), fonts.carregar_fonte (cache), vetores, collision_utils
    ├── systems/
    │   ├── gameclock.py     # relogio (singleton, ms de jogo)
    │   ├── entitymanager.py # entity_manager (singleton, grupos de sprite)
    │   ├── eventmanager.py  # input por estado + aplicação da escolha de upgrade
    │   ├── renderer.py      # draw por estado, blindado contra exceções
    │   ├── collision.py     # CollisionManager: projéteis, contato, itens, auras, mortes
    │   ├── stagemanager.py  # fade e troca de fase/mapa; fim de campanha
    │   ├── camera.py        # offset seguindo o player + shake
    │   ├── spawner/         # spawner.py (ritmo/teto), spawner_pools.py (inimigos por fase),
    │   │                    # spawner_bosses.py (PHASE_BOSSES, BOSS_CLASSES, CRONOGRAMA_BOSSES)
    │   ├── mapmanager/      # Mapa = loader(.tmj) + collision(paredes) + utils(navegação) + feats(void)
    │   ├── levelup/         # constants.py (ARMAS_REGISTRO, MAX_ARMAS=6, paletas), levelup.py (TelaDeUpgrade), draw.py
    │   └── hud/             # hud_system.py (estado) + hud_draw.py (desenho)
    ├── player/              # Player + mixins: input, movement, animation, combat (dano/escudo/espinhos),
    │                        # scaling (XP/level-up/buff), setup (valores iniciais)
    ├── enemies/
    │   ├── base/            # BaseEnemy + mixins (setup, sprites, animation, movement, collision, combat, scaling, effects)
    │   ├── standard/        # grunt, jackal, elite, brute, infection(flood), sentinel, crawler, soldier, watcher
    │   ├── minibosses/      # hunter, zealot, scarab, knight  (core/setup/states/attacks)
    │   └── bosses/          # guilty, arbiter*, tartarus, gravemind, didact, warden, guardian, jega, escharum,
    │                        # harbinger, atriox  (*arbiter: reescrita em andamento com config.py + rotinas)
    ├── feats/
    │   ├── assets.py        # ASSETS: carrega todas as imagens no import (efeito colateral!)
    │   ├── weapons/         # baseweapon.py (Arma) + pastas por raridade: comum/incomum/rara/epica/lendaria
    │   ├── projetil/        # ProjetilUniversal + subclasses (brick, carabin, needler, laserblast...)
    │   ├── buddies/         # Companheiro (IA) + wrappers Arbitro, Cortana, Marine, NobleVI
    │   ├── vehicles/        # Vehicle + Warhog, Pelican (tecla V)
    │   ├── items/           # Items (drop/coleta) + draw.py (visual/cache)
    │   ├── skills/          # artilharia, cone_strike, onda_emp, purge_grid (config.py + core), beam, mortar, tp...
    │   ├── grenades.py      # GrenadeBase, Spike, PlasmaGrenade, FuelRodGrenade (quique)
    │   ├── auras.py         # EnergyAura (boss), PlayerAura (MK2)
    │   └── effects.py       # Portal, partículas, faíscas
    └── windows/             # menu/, ranking/ (ranking_data.py = persistência), settings/ (constantes de tela), colaboradores.py
```

## Onde mexer para...
| Tarefa | Onde |
|---|---|
| Balancear arma, companion ou veículo | `source/data/weapon_data.py` |
| Nova arma | Classe em `feats/weapons/<raridade>/` com `NOME_ASSET`, exportada em `weapons/__init__.py`, perfil em `weapon_data.py`, `ArmaInfo` em `systems/levelup/constants.py`, ícone opcional em `feats/assets.py['icons']` |
| Novo companion ou veículo | `feats/buddies/` ou `feats/vehicles/`, com `COMPANION_DATA`/`VEHICLES_DATA` e `ARMAS_REGISTRO` |
| Novo inimigo comum | `enemies/standard/` (herda de `BaseEnemy`), sprites em `ASSETS['enemies']`, peso em `spawner_pools.py` |
| Novo boss | Pasta em `enemies/bosses/<nome>/`, registrada em `spawner_bosses.py` nos 3 dicts. Arquitetura futura em `docs/plano_bosses.md` |
| Nova habilidade de área ou telegraph | Preset em `feats/skills/<skill>/config.py` |
| Nova fase | `assets/img/map/<n>/m<n>.tmj` + registro em `ASSETS['maps']`, `PHASE_POOLS[n]` e `PHASE_BOSSES[n]` |
| Drops de inimigo | `morrer()` do inimigo/boss → `Items.spawn_drop(...)` |
| Efeito de item coletado | `feats/items/items.py::_aplicar_efeito` |
| Regras de dano do jogador | `player/player_combat.py::receber_dano` |
| Curva de XP e bônus de nível | `player/player_scaling.py::level_up` |
| Escala de dificuldade dos inimigos | `enemies/base/enemy_scaling.py` |
| Nova tela ou estado | Handler em `eventmanager.py` **e** draw em `renderer.py` (mesma chave) |
| HUD | `systems/hud/hud_draw.py` |
| Resolução ou FPS | `windows/settings/settings_constants.py` |
| Testes | `tests/unit/` (lógica) ou `tests/integration/` (loop real) |
| Medir desempenho | `tools/perf.py` (cenários em `listar_cenarios()`) |
