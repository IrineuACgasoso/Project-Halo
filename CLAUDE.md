# Project Halo ("Master Chief Edge")

Shooter top-down 2D com tema Halo, no estilo survivors: hordas por fase, bosses com horário marcado, level-up com escolha de armas e companheiros.
Stack: **Python 3.13 + pygame 2.6.1**. Não tem servidor nem rede. Persistência: só o ranking (`assets/data/ranking.json` em dev; `%APPDATA%/ProjectHalo/` no executável). O executável é gerado com PyInstaller (Windows).
O código e os identificadores estão em **português**. Mantenha esse padrão.

## Comandos (sempre a partir da raiz do repo; `path()` resolve relativo ao cwd)
```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # deps (pygame + pytest)
.venv\Scripts\python.exe main.py                                  # rodar o jogo
$env:MCE_DEBUG=1; .venv\Scripts\python.exe main.py                # debug: hacks L/P/B + overlay de paredes
.venv\Scripts\python.exe -m pytest                                # suíte completa (35–75 s conforme a máquina; ~13 s são o carregamento dos assets)
.venv\Scripts\python.exe -m pytest tests/unit                     # só unitários
.venv\Scripts\python.exe -m pytest -m "not integration"           # pula as simulações longas
build.bat                                                         # exe em dist/main/ (usa o pyinstaller global 6.19)
```
Não há linter, formatter nem typecheck configurados. Não invente um comando para eles.

## Arquitetura em 6 linhas (detalhes em @docs/architecture.md)
- `main.py` chama `Game` (`source/game.py`). O loop é `eventos → update(dt) → draw`, o dt é limitado a 0.05 s e o estado fica numa string (`estado_do_jogo`).
- **Singletons globais:** `entity_manager` (grupos de sprites e `player`) e `relogio` (relógio de jogo em ms, que só avança no estado `'jogando'`).
- **Classes compostas por mixins:** `Player`, `BaseEnemy`, `Mapa` e os bosses (`core.py` + `setup/states/attacks/vfx`).
- **Dados de balanceamento:** armas e companheiros ficam em `source/data/weapon_data.py`. O registro do level-up fica em `source/systems/levelup/constants.py` (`ARMAS_REGISTRO`).
- **Fases:** mapas Tiled em `assets/img/map/<n>/m<n>.tmj`. O pool de inimigos e os bosses de cada fase ficam em `source/systems/spawner/`.
- **Import pesado:** `source/feats/assets.py` carrega **todos** os assets no import, com `pygame.init` e janela oculta.

## Regras críticas
- **Tempo:** use sempre `relogio.agora()` (ms). Nunca use `pygame.time.get_ticks()`/`time` em lógica de jogo, porque esses relógios não congelam na pausa nem no level-up.
- **Velocidades e dano contínuo:** multiplique por `delta_time` (segundos). Nada de valores "por frame".
- **Mixins:** a ordem de herança decide quem vence (MRO). Um método de mixin colocado depois de `BaseEnemy` é **silenciosamente ignorado** (já aconteceu, veja @docs/log.md).
- **Arma nova:** a ordem de `ArmaInfo.grupos` precisa bater com o desempacotamento no `__init__`. Ela também precisa de 2 coisas, e `test_levelup_e_armas.py` verifica as duas:
  - um perfil em `weapon_data.py` com a chave igual a `NOME_ASSET`;
  - um `ArmaInfo` em `ARMAS_REGISTRO`.
  - O ícone em `ASSETS['icons']` é opcional: sem ele, o HUD desenha um placeholder.
- **Boss novo:** precisa de entradas em `PHASE_BOSSES`, `BOSS_CLASSES` e `CRONOGRAMA_BOSSES`, nos três. Todo `while` dentro de uma rotina geradora precisa de `yield`.
- **Desempenho:** o gargalo medido é a horda (colisão inimigo × parede), não os bosses. Não aloque `Surface`/máscara por frame; use cache.
- **Fase nova:** precisa de um mapa em `assets/img/map/<n>/` registrado em `ASSETS['maps']`, mais um pool e um boss. Sem o mapa, `existe_proxima_fase()` encerra a campanha.
- **Commits:** mensagens em português (veja @docs/conventions.md). Nunca faça commit de `dist/`, `build/` ou `.venv/`. `assets/data/ranking.json` é versionado; não o altere em testes (use `tmp_path`).
- **Bugs:** não corrija um bug "de passagem" sem avisar. Bugs conhecidos ficam em @docs/log.md e em testes `xfail(strict=True)`.

## Princípios (inegociáveis)
1. **Senior:** prefira código simples, legível, robusto e eficiente a soluções espertas.
2. **Padrões:** siga os padrões que já existem. Não adicione dependência, padrão ou abstração sem justificar.
3. **Segurança:** valide entradas, trate erros, nunca exponha nem faça commit de segredos.
4. **Nunca invente:** documente só o que foi verificado no código. Na dúvida, escreva `TODO: confirmar`.
5. **Concisão:** cada linha de doc precisa justificar sua existência.

## Protocolo de trabalho (toda feature ou correção)
1. **ENTENDER:** leia este arquivo, @docs/organization.md e o topo de @docs/log.md. Se algo for ambíguo e caro de refazer, pergunte.
2. **PLANEJAR:** para mudanças não triviais, apresente um plano curto antes de codar.
3. **IMPLEMENTAR:** seguindo as convenções de @docs/conventions.md.
4. **TESTAR:** crie ou atualize testes em `tests/` (caminho feliz, bordas e erros) e rode a suíte **completa**.
5. **CORRIGIR:** corrija a causa raiz. Nunca remova, pule ou enfraqueça um teste para ficar verde. Se o bug não for corrigido agora, use `xfail(strict=True)` com o motivo e registre no log.
6. **SÓ ENTREGUE VERDE:** se algo não pôde ser validado (ex.: visual, áudio, balanceamento), diga explicitamente.
7. **DOCUMENTAR:** acrescente uma entrada curta em @docs/log.md e atualize @docs/organization.md se a estrutura mudou.
8. **ENCERRAR:** resuma o que foi feito e peça `/clear` se for seguro, isto é, se tudo relevante estiver no log. Se houver pendência, diga que **não** é seguro limpar e explique o motivo. Caso tudo esteja certo, dê commit + push.

## Docs
- @docs/organization.md: mapa de pastas e "onde mexer para...". Consulte sempre.
- @docs/log.md: histórico entre sessões, bugs conhecidos e pendências. Consulte sempre.
- @docs/architecture.md: loop, estados, fluxo de dano/XP/fases e decisões técnicas.
- @docs/conventions.md: nomes, mixins, dados, commits.
- @docs/testing.md: como a suíte funciona, as fixtures e como testar bosses e armas.
- @docs/roteiro_reformulacao.md: roteiro mestre da reformulação em etapas atômicas (A0…H2), com portão de qualidade. Toda etapa segue as regras da §2 e o portão da §3.
- @docs/plano_bosses.md: desenho do motor de bosses (IA, animação, desempenho). As etapas dele estão encaixadas no roteiro (C1, F1–F7). Consulte antes de mexer em bosses.
- `source/docs/BOSS_CREATION.md`: guia antigo. **Não siga**: ele descreve uma `BossBase` que não existe.
