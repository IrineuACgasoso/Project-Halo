# Log entre sessões

Entradas curtas, a mais recente no topo. Quando o arquivo passar de cerca de 300 linhas, comprima as entradas antigas num resumo.

## 2026-11-21 | Roteiro de reformulação (só documentação)
**O que foi feito**
- Criado `docs/roteiro_reformulacao.md`, com 8 blocos (A–H) de etapas atômicas, as regras de transição (estrangulamento, shims com prazo, golden master, catraca de alocação) e o portão de qualidade de cada etapa.
- `plano_bosses.md` foi encaixado no roteiro (etapa 0 → C1, etapas 1–6 → F1–F7). `CLAUDE.md`, `organization.md` e `testing.md` passaram a apontar para ele.
- Nenhum código de produção mudou. Suíte de base: **347 verdes em 74 s** (a doc dizia ~35 s).

**Bug novo encontrado (não corrigido, por ser parte da etapa C1)**
- `Game.update` passa a todos os inimigos as paredes próximas **do jogador** (`get_paredes_proximas(player.posicao)`). Um inimigo fora da caixa de ±500 px das paredes perto do jogador não colide com as paredes perto dele. Ainda não tem teste `xfail`: ele será escrito no início da C1.

**Fatos verificados que embasam o roteiro**
- Código morto: `atriox/{setup,states,attacks,vfx}.py`, `escharum/vfx.py` (usa `get_ticks`, mas não é importado) e `harbinger/states.py`.
- Volume e resolução não são salvos (não há leitura nem gravação em `windows/settings/`).
- O HUD aloca `Surface` SRCALPHA a cada frame; cada projétil cria a própria máscara.

**Decisões (roteiro §8):** A0 sim; `ruff` (regras `F`) sim; áudio no futuro (depois de H2); nível máximo por raridade (comum 25, incomum 20, rara 15, épica 10, lendária 5) com a raridade passando a ter efeito real, na nova etapa **E6**; memória do boss reseta a cada luta.

**Etapa A0 concluída:** o trabalho pendente da sessão anterior + estes docs foram commitados como linha de base, com a tag `base-reformulacao`. O `promptgoat.md` (prompt pessoal na raiz) ficou de fora.

**Pendências:** os pesos de sorteio por raridade e as bordas da E6 (item `upgrade` e level-up sem opções; ver roteiro §8). Próxima etapa: **A1**.

## 2026-11-21 | Correção de todos os bugs conhecidos + plano de bosses
**O que foi feito**
- **Granada no jogador (crash na fase 4):** `GrenadeBase._checar_colisao` usa `isinstance(AbstractGroup)` em vez de `hasattr('sprites')`.
- **Crawler/Soldier:** `opcoes_cooldown`, removido na refatoração `b6145f3`, foi trocado por `novo_cooldown(...)` com as mesmas faixas do `__init__`.
- **MRO:** `GravemindAnimation` e `DidactAI` foram movidos para antes de `BaseEnemy`. Antes, nenhum outro nome se sobrepunha, então só esses dois métodos mudam.
- **Armas:**
  - `brick.cooldown` ganhou `min_val=1000`;
  - `carabin.burst_count` mudou de `[1,2,3,4]` para `[2,3,4]`, o que não muda a jogabilidade porque o nível 1 era inalcançável;
  - a Shotgun agora lê `spread`;
  - as 5 armas de rajada só começam a rajada se houver alvo (constante `RAIO_ALVO` por arma).
- **Fuel Rod:**
  - estava recebendo `items_grupo` como alvo (grupos fora de ordem em `ARMAS_REGISTRO`), ou seja, **mirava nos itens**;
  - agora `dot` e `duracao` viram DoT, via o novo campo `ArtilhariaConfig.impacto_com_dot`, que por padrão é `False` (as presets antigas não mudam);
  - `quique` virou `FuelRodGrenade`: se a carga cair sem grudar, quica até N vezes rumo ao inimigo mais próximo do ponto de queda, num raio de 350;
  - ganhou descrição própria.
- **Pelican:** usa `VEHICLES_DATA['pelican']` e o nome "Pelican".
- **Warden:**
  - drop em `pos_drop`;
  - checagem de `manager` corrigida;
  - `update` passa os grupos para o `morrer`;
  - a consciência só morre quando nenhum corpo segue vivo (antes podia morrer antes do último corpo e dropar no lugar errado; o teste encontrou isso).
- **Outros:**
  - SuperWatcher repassa a `variante`;
  - EMP usa `max(0, r - largura)`;
  - `get_player_spawn_pos` usa `is not None`;
  - Jega volta a ter `vida_base=5000` (o valor original de `1a7f664`, que tinha virado 10 em `a4763a1`).
- **Ranking:** no executável grava em `%APPDATA%/ProjectHalo/ranking.json`; rodando o `.py`, usa `path('assets','data','ranking.json')`. Ver `caminho_padrao_ranking()`.
- **Testes:** `tests/unit/test_regressoes.py` tem um teste por correção e um teste genérico de MRO para todos os inimigos. Os `xfail` foram removidos. Resultado: **347 passando**.
- **Plano:** `docs/plano_bosses.md` (proposta, aguardando aprovação).
- **Convenção:** mensagens de commit em português.

**Decisões e motivos**
- Quique interpretado como uma "segunda chance" ao errar o alvo. É barato e legível, mas é uma decisão de design: confirmar se é isso que você imaginava.
- Brick com piso de 1000 ms: 50% do valor base, a mesma proporção das outras armas com `min_val`.
- Ranking em `%APPDATA%` porque o cwd do executável varia e a pasta do jogo pode ser somente leitura. No executável, o ranking começa vazio (o `ranking.json` do repo é de desenvolvimento).

**Medição de desempenho (base para o plano)**
- Bosses sozinhos custam de 2,9 a 6,8 ms/frame.
- Uma horda de 150 inimigos custa **31 ms/frame**. Cerca de 70% disso é `aplicar_colisao_mapa`: cada inimigo testa todas as paredes próximas *do jogador*.

**Pendências**
- Aprovar ou ajustar `docs/plano_bosses.md`. São 3 perguntas no fim do arquivo.
- Não existe nível máximo de arma: com `min_val` não quebra mais, mas é uma decisão de design em aberto.
- O Gravemind agora roda a própria `animar()`, que faz `mask.from_surface` a cada frame. Está dentro do orçamento hoje; a otimização fica na etapa 2 do plano.

## 2026-11-21 | Documentação base + infraestrutura de testes
- Criados `CLAUDE.md`, `docs/` (organization, architecture, conventions, testing, log), `requirements*.txt` e `pytest.ini`, mais a suíte `tests/` (unit + smoke de mapas, inimigos, bosses e armas). O pytest foi instalado no `.venv`.
- **Estado do projeto naquele momento:**
  - último commit `7d157d0`;
  - Arbiter reescrito sem commit (`config.py`, rotinas geradoras, `movement.py`, `arsenal.py`), assim como o `cone_strike` e o `PlasmaGrenade(preset=)`;
  - 9 mapas (fases 0–8); `PHASE_BOSSES` vai até 14 e `PHASE_POOLS` até 9; o portal da fase 8 chama `finalizar_campanha()`.
- Os bugs encontrados nessa sessão foram todos corrigidos na entrada acima.

**Dívidas técnicas que continuam abertas**
- `source/docs/BOSS_CREATION.md` descreve módulos inexistentes (`BossBase`, `enemy_routines`, `sim_harness`...). Será substituído pelo `docs/plano_bosses.md`.
- Atriox importa os mixins do Tartarus, então os próprios são código morto. Escharum também é uma cópia do Tartarus. O `states.py` do Harbinger não é usado.
- `feats/assets.py` carrega cerca de 120 MB no import (13 s) e acopla todo módulo ao display.
- Sem linter/formatter; imports `*` espalhados.
- 10 armas, companions e veículos não têm ícone (o HUD usa um placeholder).
- O PyInstaller não está no `.venv` (o `build.bat` usa o global, versão 6.19.0).
