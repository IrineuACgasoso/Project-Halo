# Roteiro de reformulação

**Status:** aprovado (2026-11-21). Decisões na §8. Etapa atual: blocos A, B, C e D, a E1, o sistema de status (§7.1), a E2, a E3, a E4, a E5, a E6, a F1 e a F2 concluídos; próximo: F3 (IA de utilidade).
Este é o roteiro mestre: ele define a **ordem** e o **critério de pronto** de cada etapa. O desenho detalhado dos bosses continua em `docs/plano_bosses.md`; as etapas dele foram encaixadas aqui (ver §7).

## 1. Pilares (como cada um é medido)
| Pilar | Significa | Medida |
|---|---|---|
| **Integridade** | o jogo nunca quebra nem perde estado, e os dados são válidos | suíte verde; `validar_tudo()` sem erros; nenhum shim esquecido; golden master estável |
| **Desempenho** | 60 FPS com horda cheia e boss na tela | ms/frame por cenário (`tools/perf.py`); alocações por frame (catraca) |
| **Qualidade** | código simples, um contrato por conceito, dados fora da lógica | uma API de dano, um registro por tela, sem código morto, sem `hasattr` para descobrir contrato |

## 2. Regras de transição (valem para toda etapa)
1. **Estrangulamento:** o novo nasce ao lado do velho, os consumidores migram, e o velho só é apagado quando nada mais o usa. O jogo roda em todos os passos intermediários.
2. **Uma etapa = um commit revertível.** Começa verde e termina verde. `git revert` da etapa devolve o jogo ao estado anterior funcionando. Etapas marcadas com `.x` (ex.: F5.x) são um commit por item.
3. **Shim com prazo:** todo adaptador temporário leva o comentário `# SHIM(<etapa que remove>)`. `tests/unit/test_shims.py` lista os shims permitidos; a etapa H2 exige zero.
4. **Refatoração prova equivalência:** etapa "sem mudança de comportamento" passa no golden master **sem regerá-lo**, ou tem um teste de equivalência velho × novo.
5. **Mudança de comportamento é declarada:** a etapa diz o que muda, regenera o golden de propósito e registra o motivo em `docs/log.md`.
6. **Não misturar:** refatoração, otimização e recurso novo nunca vão no mesmo commit.
7. **Medir antes de otimizar:** etapa de desempenho só entra se o perfil mostrar o custo, e só termina com o número novo registrado.

## 3. Portão de qualidade (definição de pronto de toda etapa)
- [ ] Suíte **completa** verde (`.venv\Scripts\python.exe -m pytest`), sem `xfail` novo sem registro no log.
- [ ] Golden master: inalterado, ou regenerado com justificativa (regra 5).
- [ ] `tools/perf.py`: nenhum cenário piora mais de 10% **e** mais de 1 ms em relação à base, com a piora confirmada numa segunda medição (o script faz isso sozinho; ruído medido na A1).
- [ ] Catraca de alocação: o teto não sobe (só pode descer).
- [ ] Testes novos da etapa: caminho feliz, bordas e erro.
- [ ] O que não dá para validar automaticamente (visual, áudio, sensação de jogo) está listado como **não validado** na entrega.
- [ ] Entrada em `docs/log.md`; `docs/organization.md` atualizado se a estrutura mudou; commit em português.

## 4. Ponto de partida (verificado em 2026-11-21)
| Área | Fato | Onde |
|---|---|---|
| Base | 347 testes verdes em 74 s. 32 arquivos modificados e vários novos **sem commit** desde `7d157d0` | `git status` |
| Desempenho | horda de 150 = 31 ms/frame; ~70% em `aplicar_colisao_mapa` | log de 2026-11-21 |
| Colisão | todos os inimigos recebem as paredes próximas **do jogador**: inimigo longe dele atravessa paredes (bug, ver log) | `game.py::update` |
| Assets | 251 `pygame.image.load` literais; 93 MB de imagens; os 9 mapas JPG são decodificados no import, junto com `pygame.init` e uma janela oculta | `feats/assets.py` |
| Alocação | o HUD cria `Surface` SRCALPHA a cada frame (barras, slots, placar); cada projétil cria a própria máscara | `hud/hud_draw.py`, `projetil/projetil.py` |
| Contratos | dano tem 3 APIs (`receber_dano`, `tomar_dano`, `tomar_dano_direto`) e 4 overrides em bosses; o projétil escolhe por `hasattr` | `player_combat.py`, `enemy_combat.py` |
| Acoplamento | 213 `hasattr/getattr`, 41 `import *`, 13 usos dos aliases `game.<grupo>`, `estado_do_jogo` atribuído em 17 lugares sem validação | `source/` |
| Entrada | o teclado é lido dentro de `Player.update`: não há como plugar bot nem replay | `player_input.py` |
| Dados | stats de inimigos fixos nas classes; `data/enemy_data.py` vazio | `enemies/standard/` |
| Código morto | `atriox/{setup,states,attacks,vfx}.py`, `escharum/vfx.py` e `harbinger/states.py` não são importados | `enemies/bosses/` |
| Configurações | volume e resolução não são salvos. A resolução chama `set_mode(res)`, mas o jogo desenha com 1280×720 fixos (efeito real: TODO: confirmar) | `windows/settings/settings.py` |

## 5. Mapa das etapas
Ordem recomendada = ordem da tabela. "Depende de" é o mínimo obrigatório.

| Bloco | Etapas | Depende de |
|---|---|---|
| **A. Rede de segurança** (sem mudar o jogo) | A0 base · A1 perf · A2 catraca · A3 golden · A4 higiene | — |
| **B. Núcleo** | B1 passo fixo · B2 estados · B3 sessão · B4 eventos | A |
| **C. Mundo e desempenho** | C1 grade de paredes · C2 broadphase · C3 alocações · C4 render | A (C1 pode vir logo após A) |
| **D. Assets e dados** | D1 manifesto · D2 mapas sob demanda · D3 import limpo · D4 dados de inimigos · D5 validação | A; D3 depois de D1 |
| **E. Entidades** | E1 dano · E2 alvo · E3 entrada · E4 armas · E5 troca de fase · E6 raridade | B4 (E1), C2 (E4), D5 (E6) |
| **F. Bosses** | F1 BossBase · F2 Animador · F3 IA · F4 bot · F5.x migração · F6 comuns · F7 guia | C1, E1, E3 (F4) |
| **G. Interface e configuração** | G1 resolução · G2 config salva · G3 telas · G4 áudio (adiado) | B2; G4 depois de H2 |
| **H. Entrega** | H1 smoke do exe · H2 limpeza final | D3; tudo (H2) |

## 6. Etapas

### A. Rede de segurança
**A0 · Linha de base versionada** (risco: nenhum)
- Muda: commit do trabalho pendente da sessão anterior e tag `base-reformulacao`.
- Pronto quando: árvore limpa, 347 verdes, tag criada.

**A1 · Medição de desempenho** (risco: nenhum)
- Muda: `tools/perf.py` roda cenários headless (horda de 150, fase 0 por 60 s, cada boss por 20 s, troca de fase) e grava ms/frame (média e p95) em `tools/perf_base.json`. Também mede o tempo de import dos assets e a memória.
- Testes: smoke do próprio script (1 cenário curto). Tempo não vira teste, porque varia por máquina; vira número registrado no log.
- Pronto quando: a tabela de base está no log.

**A2 · Catraca de alocação** (risco: nenhum)
- Muda: `tests/helpers.py::contar_alocacoes()` envolve `pygame.Surface`, `mask.from_surface`, `transform.*` e `font.Font` via `monkeypatch`. `tests/perf/test_catraca.py` simula cenários fixos e afirma `alocações_por_frame <= TETO`, com os tetos de hoje.
- Por quê: contagem é determinística (diferente de tempo) e impede regressão silenciosa.
- Pronto quando: os tetos atuais estão gravados e o teste é verde.

**A3 · Golden master** (risco: nenhum)
- Muda: `tests/integration/test_golden.py` simula 60 s da fase 0 com seed fixa e jogador blindado, e compara métricas por segundo (inimigos vivos, vida, XP, nível, posição, projéteis) com `tests/golden/fase0.json`. Regerar exige `--atualizar-golden`.
- Testes: rodar 2× seguidas dá o mesmo resultado (prova de determinismo).

**A4 · Higiene** (risco: baixo)
- Muda: apaga o código morto da §4. Cria `tests/unit/test_imports.py`, que importa todos os módulos de `source/` (pega import quebrado e nome indefinido em módulo que nenhum teste toca).
- Linter (aprovado): `ruff` em `requirements-dev.txt`, só com as regras `F` (nomes indefinidos, imports não usados, `import *`), configurado em `ruff.toml`. As violações atuais entram numa lista de exceções que só pode encolher; `CLAUDE.md` ganha o comando. Justificativa: 41 `import *` escondem nomes indefinidos que só quebram em jogo.

### B. Núcleo
**B1 · Passo fixo de simulação** (risco: baixo)
- Muda: `Game.run` usa um acumulador: `update(1/60)` quantas vezes couber (no máximo 5 por frame) e um `draw` por frame. A assinatura de `update(dt)` não muda.
- Ganho: a física fica igual em qualquer FPS e o jogo fica igual aos testes (que já usam 1/60). Substitui o teto de 0,05 s.
- Testes: acumulador com relógio falso (frame lento → até 5 passos; nunca entra em espiral). Golden inalterado.

**B2 · Estados formalizados** (risco: médio)
- Muda: `systems/estados.py` com constantes, a tabela `TRANSICOES` e `game.mudar_estado(novo)`, que valida (lança exceção em teste/debug, loga 1× no jogo). As 17 atribuições migram. `EventManager` e `Renderer` passam a ler um registro único `TELAS[estado] = (handler, draw)`.
- Testes: toda transição usada no código está na tabela; transição inválida lança exceção em teste; o registro cobre todos os estados.

**B3 · Sessão separada do Game** (risco: médio)
- Muda: `SessaoJogo` (dataclass: `timer_jogo`, `fase_atual`, `boss_atual`, portal, contadores do Gravemind) nasce em `iniciar_novo_jogo`. O `Game` expõe propriedades `# SHIM(B3)` durante a migração. Os 13 usos de `game.<grupo>` passam para `entity_manager`, e os aliases são removidos.
- Ganho: o restart vira "objeto novo", então é impossível sobrar estado de uma partida na outra.
- Testes: dois `iniciar_novo_jogo` seguidos geram sessões sem nenhum atributo compartilhado; golden inalterado.

**B4 · Ordem de update explícita + eventos de jogo** (risco: baixo)
- Muda: `Game.update` vira passos nomeados (`_atualizar_portal`, `_atualizar_spawner`, `_atualizar_entidades`...). `systems/eventos.py` é um barramento síncrono mínimo (`assinar`, `emitir`, limpo no reset), com os eventos `inimigo_morreu`, `dano_causado`, `boss_derrotado` e `fase_trocada`.
- Justificativa da abstração: a memória adaptativa dos bosses (F3) precisa de "dano por habilidade", o áudio (G4) precisa de gatilhos e a pontuação hoje é recalculada no fim. Sem isso, cada um acoplaria no `CollisionManager`.
- Testes: unidade do barramento; contagem de eventos numa simulação bate com as mortes reais; golden inalterado.

### C. Mundo e desempenho
**C1 · Grade espacial de paredes** (= etapa 0 do plano de bosses; risco: médio)
- Muda: ao carregar o mapa, os segmentos viram tuplas de float numa grade de células de 128 px. Cada entidade consulta as células **ao redor dela**. A projeção deixa de alocar `Vector2`.
- Muda o comportamento (declarado): inimigo longe do jogador passa a colidir com as paredes perto dele (corrige o bug da §4). Golden regenerado.
- Testes: equivalência (10 mil posições aleatórias: empurrão novo == antigo quando a parede relevante está na lista); o teste do bug, escrito como `xfail(strict=True)` antes da mudança, passa e perde a marca.
- Pronto quando: horda de 150 com **≤ 10 ms/frame**.

**C2 · Broadphase de entidades** (risco: médio; só entra se o perfil pedir)
- Gatilho: depois de C1, `CollisionManager.update` + busca de alvo das armas > 2 ms/frame com 250 inimigos.
- Muda: `GradeEntidades` reconstruída 1× por frame; usada por projétil × inimigo, contato e `encontrar_inimigo_mais_proximo`/`_mais_forte`.
- Testes: equivalência com a força bruta (mesmo conjunto de acertos em cenários aleatórios); golden inalterado.
- Feito (2026-11-21): gatilho disparou (5,6 ms/frame com 5 armas). Saiu como filtro `Rect.collidelistall` (`BroadphaseInimigos`), não grade; a busca de alvo ficou de fora (0,04 ms). Ver log.

**C3 · Projéteis e efeitos sem alocação** (risco: baixo)
- Muda: a máscara do projétil vai para o `GLOBAL_CACHE` por (sprite, tamanho, ângulo). Fim das `Surface` por frame em `ArtilhariaAviso.draw`, `PlasmaGrenade.update`, `cone_strike`, `onda_emp`, auras e efeitos. Partículas vêm de um pool com teto global.
- Testes: a catraca desce para o novo teto (meta: zero no `update`).
- Feito (2026-11-21): horda 20,0 → 8,0 alocações/frame (o grosso era a máscara da animação dos inimigos comuns). Sobra no `update` só aquecimento de cache e o Gravemind (F2/F5). Ver log.

**C4 · Render** (risco: baixo)
- Muda: culling pela câmera (só ordena e desenha o que intersecta a tela + margem). HUD com camadas estáticas pré-renderizadas, uma `Surface` reutilizada por barra e cache de texto que só renderiza quando o valor muda.
- Testes: sprite fora da tela não recebe `draw`; catraca do `draw` em `jogando` = 0 sem mudança de valor; `renderer._erros_logados` vazio.
- Não validado automaticamente: aparência do HUD (conferir no jogo).
- Feito (2026-11-21): catraca da fase 0 em 0,0/frame; sem camadas estáticas (o HUD custa ~0,2 ms/frame). Ver log.

### D. Assets e dados
**D1 · Manifesto de assets** (risco: médio)
- Muda: as 251 linhas literais viram uma tabela (`chave → arquivo, escala, flip, alpha`) e um carregador `carregar_assets()` idempotente. O formato de `ASSETS` não muda. Arquivo ausente gera placeholder magenta + log, em vez de crash.
- Testes: todo arquivo do manifesto existe; as chaves de `ASSETS` e os tamanhos das superfícies são idênticos aos de antes (equivalência gravada antes da troca).
- Feito (2026-11-21): `data/manifesto_assets.py`; as 248 superfícies saíram idênticas pixel a pixel (`tests/golden/assets.json`, gravado com o código antigo). Ver log.

**D2 · Mapas sob demanda** (risco: baixo)
- Muda: `ASSETS['maps']` vira um mapeamento preguiçoso (carrega no primeiro acesso, mantém só os 2 mais recentes). `existe_proxima_fase()` consulta o manifesto, não a imagem.
- Testes: só o mapa usado é decodificado; troca de fase e fim de campanha continuam verdes. O ganho de import e memória entra no log (medido com A1).
- Feito (2026-11-21): import −42%, pico de memória −183 MB; a troca de fase passou a custar ~130 ms (decodificação, com a tela preta). Ver log.

**D3 · Import sem efeito colateral** (risco: médio)
- Muda: `pygame.init` e a janela oculta saem do import de `assets.py` e vão para `carregar_assets()`, chamado por `main.py` e pelo `conftest`.
- Pré-condição: nenhum módulo lê `ASSETS` durante o import. Fora de classes já não há nenhum; dentro de corpos de classe, TODO: confirmar no início da etapa.
- Testes: importar `source.game` não abre display; `test_imports` (A4) continua verde.
- Feito (2026-11-21): pré-condição confirmada por AST (nenhum módulo lê `ASSETS` nem chama pygame no import, fora o próprio `assets.py`). Ver log.

**D4 · Dados de inimigos** (risco: baixo; um commit por família)
- Muda: `data/enemy_data.py` com dataclasses frozen (`vida`, `dano`, `velocidade`, faixas de cooldown, tabela de drop). Os inimigos comuns leem dali.
- Testes: equivalência (cada classe instanciada tem os mesmos stats de antes); golden inalterado.
- Feito (2026-11-21): 3 commits (Covenant, Flood, Forerunner/Prometheans); `tests/golden/inimigos.json` gravado com os valores antigos (stats, faixas de cooldown e drops na ordem). Ver log.

**D5 · Validação central de dados** (risco: nenhum)
- Muda: `data/validacao.py::validar_tudo()` devolve a lista de erros de `weapon_data`, `ARMAS_REGISTRO`, pools, os 3 dicts de bosses, perfis de inimigos, manifesto e mapas (camadas obrigatórias, spawn dentro da navegação, portal). Roda nos testes (lista vazia) e na abertura do jogo com `MCE_DEBUG=1`.
- Testes: cada regra tem um caso que falha de propósito. Os testes de integridade espalhados hoje passam a chamar a validação.
- Feito (2026-11-21): dados reais sem erros. **Difere do roteiro:** "spawn dentro da navegação" e "portal" obrigatório não entraram: os mapas reais não seguem essas regras e o código não as exige (ver log; decisão pendente).

### E. Entidades
**E1 · Contrato de dano único** (risco: alto)
- Muda: `Dano` (dataclass: valor, fonte, tipo `projetil|contato|aura|void|direto`, `ignora_iframes`) e `receber_dano(dano)` em jogador e inimigos. As APIs antigas viram `# SHIM(E1)` finos e somem no fim da etapa. Os 4 overrides (Guilty, Warden, Hunter, Scarab) migram. Emite `dano_causado`.
- Testes: matriz escudo × i-frames × invulnerável × transbordo, para jogador e inimigo; um teste por override; golden inalterado.
- Feito (2026-11-21): golden inalterado. Tipos: os 5 + `area` (explosão, cone, onda, puxão, feixe). Migração completa no mesmo commit, sem shims (como na B3). O inimigo ganhou 2 ganchos: `ajustar_dano_recebido` (a regra do alvo) e `absorver_dano` (só o Scarab sobrescreve). `fonte` em projéteis, granadas e habilidades (39 ataques inimigos passam `fonte=self`). **Difere do roteiro:** "invulnerável" não entrou no contrato: hoje só projéteis e auras o respeitam, e centralizar mudaria o jogo (ver log).

**E2 · Estado de alvo unificado** (risco: baixo)
- Muda: propriedades `alvejavel` e `vivo` substituem as checagens repetidas de alpha/`invis_phase` nas armas e a mistura `vida`/`vida_atual`.
- Testes: inimigo invisível nunca é alvo; o mais forte é escolhido por `vida`.
- Feito (2026-11-22): `vivo` (`vida > 0`) e `alvejavel` (`vivo` e não `invisivel`) no `BaseEnemy` (só ele entra em `inimigos_grupo`); as 2 buscas de alvo das armas e a checagem de morte do `CollisionManager` usam as propriedades. Golden inalterado pela E2. `invulneravel` continua separado (a granada que quica e os projéteis o usam).

**E3 · Entrada desacoplada** (risco: médio)
- Muda: `ComandoJogador` (direção + ações) vem de uma `FonteEntrada`: `Teclado`, `Roteiro` (replay) ou `Bot` (F4). `Player.update` lê o comando; os hacks de debug viram comandos.
- Testes: replay de um roteiro gera o mesmo golden 2×; teclado mapeado corretamente.
- Feito (2026-11-22): `systems/entrada.py`; o `Game` lê `game.entrada` 1× por passo e entrega `player.comando`. O comando diz o que está **pressionado** (a borda do V continua no veículo). Os hacks só saem do `Teclado` com debug. Golden inalterado; só `entrada.py` chama `get_pressed` (teste).

**E4 · Armas** (risco: médio)
- Muda: as armas pegam os grupos do `entity_manager`; `ArmaInfo.grupos` e o desempacotamento posicional somem, eliminando a classe de bug que fez o Fuel Rod mirar nos itens. Helpers comuns para rajada e spread; busca de alvo via C2 (se existir). O nível máximo fica para E6 (é recurso novo, não refatoração).
- Testes: os atuais (cada arma até o nível 21, mira no grupo certo) + rajada/spread.

**E5 · Persistência entre fases explícita** (risco: baixo)
- Muda: a flag `sobrevive_troca_de_fase` nos sprites (player, companions, auras, veículos) substitui a cadeia de `hasattr` do `StageManager`.
- Testes: depois da troca, sobrevivem exatamente os sprites marcados (veículos inclusos: comportamento atual TODO: confirmar).
- Feito (2026-11-22): flag de classe em `Player`, `Companheiro` e `PlayerAura`; golden inalterado. Confirmado: hoje o veículo **não** sobrevive (some, mas continua ativo) e os companheiros vão para o spawn do mapa antigo; os dois são bugs (ver log), corrigidos em commits próprios.

**E6 · Raridade de fato** (recurso novo; pode ser antecipada logo após D5, porque não depende do resto de E)
- Hoje: `ArmaInfo.raridade` (4 comuns, 4 incomuns, 3 raras, 5 épicas, 6 lendárias, contando companions e veículos) só muda a cor no HUD e no level-up. O sorteio de `gerar_opcoes_aleatorias` é uniforme e não há nível máximo.
- Muda (dados em `systems/levelup/constants.py`, validados por D5):
  - `NIVEL_MAXIMO_POR_RARIDADE = {comum: 25, incomum: 20, rara: 15, epica: 10, lendaria: 5}` (decidido);
  - `PESO_SORTEIO_POR_RARIDADE = {comum: 40, incomum: 25, rara: 20, epica: 10, lendaria: 5}` para oferecer **armas novas** (decidido);
  - arma no nível máximo sai do sorteio de upgrade e mostra "MAX" no HUD e no card.
- Bordas que a etapa resolve:
  - item `upgrade` sorteia só entre armas abaixo do máximo. Se todas estiverem no máximo, **provisoriamente** mantém só os +200 pontos que já dá hoje e não abre tela;
  - level-up sem nenhuma opção válida (6 armas, todas no máximo) **provisoriamente** não abre tela (o nível sobe normalmente);
  - os dois casos provisórios ficam num ponto único (`recompensa_sem_upgrade()`), marcado `# TODO(itens temporários)`, para o recurso futuro plugar ali;
  - `upgrade()` acima do máximo não faz nada (defesa em profundidade).
- Testes: cada raridade para exatamente no seu máximo; sorteio respeita os pesos (seed fixa, 10 mil sorteios, tolerância); nenhuma tela vazia; item `upgrade` nunca escolhe arma no máximo. O teste atual que sobe toda arma até o nível 21 passa a subir até o máximo da raridade (é mudança de especificação, registrada no log, não enfraquecimento).
- Muda o comportamento (declarado): golden regenerado se o sorteio entrar na simulação.
- Feito (2026-11-22): `ArmaInfo.criar` passa o `nivel_maximo`; `Arma.upgrade()` é o único ponto de subida (as subclasses implementam `aplicar_nivel`). O sorteio não entra no golden (o jogador blindado não sobe de nível): golden inalterado. O upgrade forçado é revalidado ao sair da fila (a arma pode ter chegado ao máximo numa tela anterior).

### F. Bosses (detalhe em `docs/plano_bosses.md`)
| Etapa | Entrega | Pronto quando |
|---|---|---|
| **F1** BossBase + ContextoCombate | extraídos do Arbiter, sobre o contrato de dano de E1 | Arbiter igual (smoke + regressão); testes do motor (cooldown, fases, interrupção, anti-stuck). **Feito (2026-11-22):** golden próprio do Arbiter (`tests/golden/arbiter.json`, gravado antes) inalterado |
| **F2** Animador | clips declarativos, hit frames, cache de máscaras | update de boss com zero alocação (catraca). **Feito (2026-11-22):** o Arbiter migrou; golden dele (com quadro, lado e alpha) inalterado; teste de identidade das imagens no lugar da catraca, que não vê `Surface.copy` |
| **F3** IA de utilidade + memória | `decisao.py`, alimentada por `dano_causado` (B4) | teste determinístico: contexto X → habilidade Y |
| **F4** Bot jogador | `FonteEntrada` Bot (E3) que esquiva e kita | métricas por boss no log: tempo para matar, % de acerto, uso de cada habilidade |
| **F5.x** Migração | um commit por boss: Tartarus (+ Atriox e Escharum, que deixam de ser cópias), Harbinger, Jega, Guilty, Didact, Gravemind, Warden, Guardian; depois Hunter (adiantado em 2026-11-22 sem a `BossBase`: falta só migrar para ela), Zealot, Scarab, Knight | smoke + métricas do bot sem piora + catraca zero no update |
| **F6** Inimigos comuns no Animador | mesmo motor de animação para `enemies/standard/` | catraca; golden inalterado |
| **F7** Guia | `docs/bosses.md` + template; apaga `source/docs/BOSS_CREATION.md` | guia validado criando um boss de teste só pelo template |

### G. Interface e configuração
**G1 · Resolução independente** (risco: médio)
- Muda: o jogo desenha sempre em 1280×720 e a janela escala com `pygame.SCALED`. A troca de resolução só muda o tamanho da janela.
- Testes: trocar a resolução não muda `game.tela.get_size()`. Não validado: nitidez e fullscreen em monitor real.

**G2 · Configurações salvas** (risco: baixo)
- Muda: `persistencia_json.py` (gravação atômica + backup de corrompido, extraída do `RankingData`) é usada pelo ranking e por `config.json` (volume, resolução, fullscreen), no mesmo diretório do ranking.
- Testes: ida e volta, JSON corrompido, valor fora da faixa; sempre com `tmp_path`.

**G3 · Telas com contrato único** (risco: baixo)
- Muda: menus, ranking, game over, colaboradores e configurações seguem `handle_event → ação` e `draw`, com cache de texto.
- Testes: os fluxos de `handle_event` (hoje sem cobertura): navegação, digitar nome no ranking, restart.

**G4 · Áudio central** (aprovado para o futuro: entra depois de H2)
- Muda: `AudioManager` com efeitos disparados pelos eventos de B4, teto de canais e volume vindo de G2.
- Testes: com `SDL_AUDIODRIVER=dummy`, cada evento toca no máximo N sons por frame. Não validado: mixagem.

### H. Entrega
**H1 · Smoke do executável** (risco: baixo)
- Muda: `main.py --smoke 600` roda 600 frames de partida real em modo headless e sai com código 0/1. O `build.bat` roda esse smoke depois do PyInstaller; o PyInstaller 6.19.0 entra no `requirements-dev.txt`.
- Pronto quando: `build.bat` falha se o exe quebrar.

**H2 · Limpeza final** (risco: baixo)
- Muda: zero shims (`test_shims.py`), docs consolidados (`architecture.md` reescrito para a estrutura nova), `CLAUDE.md` revisado, log comprimido.
- Pronto quando: portão de qualidade completo + tabela final de desempenho × base de A1.

## 7. Como o que já existe entra
| Item atual | Vira |
|---|---|
| `plano_bosses.md`, etapa 0 | C1 (+ C3 para as alocações citadas lá) |
| `plano_bosses.md`, etapas 1 a 6 | F1 a F7 |
| Pendência "nível máximo de arma" | E6 (máximo por raridade) |
| Pendência "Gravemind faz `mask.from_surface` por frame" | F2 + F5 (Gravemind) |
| Dívida "Atriox/Escharum são cópias do Tartarus" | A4 (apaga o morto) + F5 (identidade própria) |
| Dívida "`assets.py` carrega tudo no import" | D1 → D2 → D3 |
| Dívida "imports `*`, sem linter" | A4 (decisão do `ruff`) |
| Dívida "PyInstaller fora do `.venv`" | H1 |
| Dívida "10 armas/companions/veículos sem ícone" | conteúdo, fora do roteiro (o placeholder continua) |

## 7.1 Depois do roteiro (recursos aprovados para o futuro)
- **G4 · Áudio central** (descrito no bloco G).
- **Itens temporários e boosts do personagem:** substituem os casos provisórios da E6 (item `upgrade` e level-up sem opções quando tudo está no máximo). Usam os eventos de B4 e os dados validados de D5. Desenho: TODO, a definir quando começar.
- **Sistema de status (buffs e debuffs)** (pedido em 2026-11-21; entra logo depois da E1, antes da E2): um ponto único `aplicar(alvo, efeito)` para jogador e inimigos. Debuffs: lentidão, atordoamento, queimadura (DPS + corte na cura), fraqueza (+% de dano recebido), cegueira (só no jogador). Buffs: dano, velocidade, cadência (só no jogador), escudo e vida (instantâneos). Curas, escudos de aliados (Watcher), regeneração do MK2 e o bônus da Cortana passam por ele. Decisões na §8 (itens 8–11). Feito (2026-11-21): o núcleo (S1) e as migrações (S2: curas, escudos, buff de cadência antigo; S3: Cortana) em commits separados; ver o log.

## 8. Decisões tomadas (2026-11-21)
1. **A0:** commitar o trabalho pendente como linha de base: **sim** (feito).
2. **A4:** `ruff` com as regras `F`, só em dev: **sim**.
3. **G4:** áudio de efeitos: **sim, mas no futuro** (depois de H2).
4. **E6:** nível máximo **por raridade**: comum 25, incomum 20, rara 15, épica 10, lendária 5. A raridade também passa a ter efeito real (peso no sorteio).
5. **F3:** a memória adaptativa do boss **reseta a cada luta**.
6. **E6:** pesos de sorteio de arma nova: comum 40, incomum 25, rara 20, épica 10, lendária 5.
7. **E6:** item `upgrade` e level-up sem opções (tudo no máximo) serão resolvidos pelos **itens temporários e boosts** (§7.1). Até lá, o comportamento provisório da E6 vale.
8. **Status:** bosses e minibosses **não** podem ser atordoados por fora (o stun do Scarab e do Hunter é mecânica própria deles). Lentidão em bosses: também não, por ora (pode ser ligada na F5, com o movimento centralizado na `BossBase`).
9. **Status:** acúmulo **por tipo**: a mesma fonte só renova a duração; entre fontes diferentes, lentidão = a mais forte, queimadura = DPS soma, buffs de dano/velocidade e fraqueza = % somam, cadência = multiplica (nunca zera o cooldown), atordoamento e cegueira = a maior duração.
10. **Status:** o buff de escudo é **limitado ao escudo máximo** do alvo.
11. **Status:** fraqueza é incondicional; a regra "só pelas costas" do Scarab continua no gancho `ajustar_dano_recebido` do próprio boss. O Hunter (reformulado em 2026-11-22) usa `Defesa` em vez do gancho.
