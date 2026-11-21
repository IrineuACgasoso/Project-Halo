# Project Halo ("Master Chief Edge")

Shooter top-down 2D com tema Halo, no estilo survivors: hordas por fase, bosses com horário marcado, level-up com escolha de armas e companheiros.
Stack: **Python 3.13 + pygame 2.6.1**. Não tem servidor nem rede. Persistência: só o ranking (`assets/data/ranking.json` em dev; `%APPDATA%/ProjectHalo/` no executável). O executável é gerado com PyInstaller (Windows).
O código e os identificadores estão em **português**. Mantenha esse padrão.

## Comandos (sempre a partir da raiz do repo; `path()` resolve relativo ao cwd)
```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # deps (pygame + pytest)
.venv\Scripts\python.exe main.py                                  # rodar o jogo
$env:MCE_DEBUG=1; .venv\Scripts\python.exe main.py                # debug: hacks L/P/B + overlay de paredes
.venv\Scripts\python.exe -m pytest                                # suíte completa (~65 s; na bateria, até o dobro)
.venv\Scripts\python.exe -m pytest tests/unit                     # só unitários
.venv\Scripts\python.exe -m pytest -m "not integration"           # pula as simulações longas
.venv\Scripts\python.exe -m pytest tests/integration/test_golden.py --atualizar-golden  # só em mudança de comportamento declarada
build.bat                                                         # exe em dist/main/ (usa o pyinstaller global 6.19)
.venv\Scripts\python.exe tools/perf.py                            # ms/frame por cenário × tools/perf_base.json (~4 min, na tomada; --escala 0.1 = rápido)
.venv\Scripts\python.exe -m ruff check                            # linter: só regras F (ruff.toml); também roda na suíte (test_lint.py)
```
Não há formatter nem typecheck configurados. Não invente um comando para eles. As exceções do linter em `ruff.toml` só podem encolher: código novo não entra na lista.

## Arquitetura em 6 linhas (detalhes em @docs/architecture.md)
- `main.py` chama `Game` (`source/game.py`). O loop é `eventos → update(1/60) × n → draw`, com passo fixo (no máximo 5 passos por frame), e o estado fica numa string (`estado_do_jogo`).
- **Singletons globais:** `entity_manager` (grupos de sprites e `player`) e `relogio` (relógio de jogo em ms, que só avança no estado `'jogando'`).
- **Classes compostas por mixins:** `Player`, `BaseEnemy`, `Mapa` e os bosses (`core.py` + `setup/states/attacks/vfx`).
- **Dados de balanceamento:** armas e companheiros ficam em `source/data/weapon_data.py`. O registro do level-up fica em `source/systems/levelup/constants.py` (`ARMAS_REGISTRO`).
- **Fases:** mapas Tiled em `assets/img/map/<n>/m<n>.tmj`. O pool de inimigos e os bosses de cada fase ficam em `source/systems/spawner/`.
- **Assets:** o import não carrega nada; `carregar_assets()` (`source/feats/assets.py`, ~1,5 s) preenche `ASSETS` e é chamado pelo `main.py`, pelo `conftest` e pelo `tools/perf.py`. Sem janela aberta, ele faz `pygame.init` e abre uma oculta. Não leia `ASSETS` no nível do módulo nem em corpo de classe. Os fundos das fases são a exceção: `ASSETS['maps']` decodifica no 1º acesso e guarda só os 2 mais recentes. Cada imagem está no manifesto `source/data/manifesto_assets.py` (`MANIFESTO`, mesmo formato de `ASSETS`).

## Regras críticas
- **Tempo:** use sempre `relogio.agora()` (ms). Nunca use `pygame.time.get_ticks()`/`time` em lógica de jogo, porque esses relógios não congelam na pausa nem no level-up.
- **Velocidades e dano contínuo:** multiplique por `delta_time` (segundos). Nada de valores "por frame".
- **Mixins:** a ordem de herança decide quem vence (MRO). Um método de mixin colocado depois de `BaseEnemy` é **silenciosamente ignorado** (já aconteceu, veja @docs/log.md).
- **Arma nova:** a ordem de `ArmaInfo.grupos` precisa bater com o desempacotamento no `__init__`. Ela também precisa de 2 coisas, e `test_levelup_e_armas.py` verifica as duas:
  - um perfil em `weapon_data.py` com a chave igual a `NOME_ASSET`;
  - um `ArmaInfo` em `ARMAS_REGISTRO`.
  - O ícone em `MANIFESTO['icons']` é opcional: sem ele, o HUD desenha um placeholder.
- **Boss novo:** precisa de entradas em `PHASE_BOSSES`, `BOSS_CLASSES` e `CRONOGRAMA_BOSSES`, nos três. Todo `while` dentro de uma rotina geradora precisa de `yield`.
- **Desempenho:** meça com `tools/perf.py` antes de otimizar (depois do bloco C, horda e bosses mais caros ficam em ~4 ms/frame). Não aloque `Surface`/máscara por frame (a catraca está perto de zero e pega): use `utils/superficies.py` (máscara, camada alpha, rascunho) e `feats/particulas.py`.
- **Fase nova:** precisa de um mapa em `assets/img/map/<n>/` registrado em `MANIFESTO['maps']`, mais um pool e um boss. Sem o mapa, `existe_proxima_fase()` encerra a campanha.
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
