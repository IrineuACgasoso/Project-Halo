# Project Halo ("Master Chief Edge")

Shooter top-down 2D estilo survivors (hordas por fase, bosses com horário, level-up com armas e companheiros).
**Python 3.13 + pygame 2.6.1**, sem rede. Código, identificadores e commits em **português**. Executável: PyInstaller (Windows).

## Comandos (sempre da raiz do repo)
```powershell
.venv\Scripts\python.exe main.py                         # jogo (MCE_DEBUG=1: cheats L/P/B + overlay de paredes)
.venv\Scripts\python.exe -m pytest tests/unit/test_X.py  # durante o trabalho: só os arquivos afetados
.venv\Scripts\python.exe -m pytest                       # suíte completa: 1× no fim (~40 s)
.venv\Scripts\python.exe -m ruff check                   # só regras F
.venv\Scripts\python.exe tools/perf.py                   # ms/frame (~4 min, na tomada); só se mexer em laço quente
```
Golden (`tests/golden/`): `--atualizar-golden` só em mudança de comportamento declarada. Não há formatter nem typecheck.

## Economia de contexto (regra do usuário)
- Os docs **não** são carregados sozinhos. Leia só a seção que a tarefa pede: `docs/organization.md` ("Onde mexer para..."),
  topo de `docs/log.md` (pendências e decisões), `docs/architecture.md`, `docs/conventions.md`, `docs/testing.md`,
  `docs/plano_bosses.md` e `docs/roteiro_reformulacao.md` (só etapas do roteiro).
- Busque antes de ler; leia o trecho, não o arquivo. Nunca imprima `tests/golden/`, `.tmj`, `perf_base.json` nem saída inteira de pytest (`| tail`).
- **Testes:** só o que é crítico (dano, status, colisão, progressão, dados, travamento, regressão de bug real). Nada de teste de
  aparência, de número de balanceamento, de parâmetro inválido de config ou de equivalência com código antigo. Prefira 1 teste
  parametrizado a vários.
- **Docs:** log com 3 a 8 linhas por entrega; o histórico longo é o git.

## Arquitetura
- `main.py` → `Game` (`source/game.py`): `eventos → update(1/60) × n → draw`; estado em `estado_do_jogo`.
- Singletons: `entity_manager` (grupos, `player`) e `relogio` (ms de jogo; só anda em `'jogando'`).
- `Player`, `BaseEnemy`, `Mapa` e bosses são compostos por mixins.
- Balanceamento: `source/data/weapon_data.py`, `source/data/enemy_data.py`, `config.py` de cada boss e skill.
- Assets: `MANIFESTO` (`source/data/manifesto_assets.py`) → `carregar_assets()` preenche `ASSETS` (não leia `ASSETS` no import).

## Regras críticas
- **Tempo:** `relogio.agora()`; nunca `pygame.time.get_ticks()`/`time`. Velocidade e dano contínuo × `delta_time`.
- **Dano:** `alvo.receber_dano(Dano(valor, tipo, fonte))`; ataque de inimigo passa `fonte=self`. Regra do alvo: `ajustar_dano_recebido`.
- **Escudo que acaba:** passa por `ao_quebrar_escudo` (inimigo) ou `zerar_escudo` (jogador): é o efeito padrão. Extra: estenda com `super()`.
- **Buffs, debuffs e cura:** `aplicar(alvo, efeito, fonte, chave)`. Boss declara `imunidades_status = IMUNIDADES_CHEFE`. Fogo: `status/fogo.py` desenha sozinho quem tem `Queimadura`.
- **Tela:** o visível é `game.camera.visao`; desenho do mundo usa a `tela` recebida.
- **Mira:** toda busca de alvo usa `alvejavel`. Invisível não é mirado, mas é atingível. Teleporte é `em_teleporte`.
- **Mixins:** método de mixin depois de `BaseEnemy`/`BossBase` é ignorado em silêncio (MRO).
- **Arma nova:** `(jogador, game, **kwargs)` repassando `kwargs`; ganho em `aplicar_nivel`; perfil em `weapon_data.py` (= `NOME_ASSET`) e `ArmaInfo` em `ARMAS_REGISTRO`. Rajada: `ArmaDeRajada`.
- **Balanceamento:** com `min_val`, `valor + subidas × increase` tem de bater exato no nível máximo da raridade (`validar_armas` mostra a conta).
- **Boss novo:** `PHASE_BOSSES`, `BOSS_CLASSES` e `CRONOGRAMA_BOSSES`; herda de `BossBase`; todo `while` de rotina tem `yield`.
- **Fase nova:** mapa em `assets/img/map/<n>/` + `MANIFESTO['maps']` + pool + boss.
- **VFX:** nada de `Surface`/máscara por frame (`utils/superficies.py`, `feats/particulas.py`). Efeito só visual usa `random.Random()` próprio (o global é da simulação).
- **Commits:** nunca `dist/`, `build/`, `.venv/`. Testes não tocam `assets/data/ranking.json` (use `tmp_path`).
- **Bug achado:** avise antes de corrigir "de passagem"; não corrigido vira `xfail(strict=True)` + log.

## Protocolo
1. Entender (pergunte só se for ambíguo **e** caro). 2. Plano curto se não for trivial. 3. Implementar simples, nos padrões
existentes, sem dependência nova. 4. Testar o crítico; suíte completa verde no fim (nunca enfraqueça um teste para passar).
5. Dizer o que não foi validado (visual, áudio, balanceamento). 6. Log curto; `organization.md` só se a estrutura mudou.
7. Verde: commit + push (título em MAIÚSCULAS, itens com `+`) e dizer se é seguro dar `/clear`.
