# Log entre sessões

Entradas curtas, a mais recente no topo. Quando o arquivo passar de cerca de 300 linhas, comprima as entradas antigas num resumo.

## 2026-11-21 | Etapa C3: projéteis e efeitos sem alocação
**Onde o frame alocava (medido por sítio, cenários da catraca):** na horda, 11,8 das 20 alocações/frame eram `mask.from_surface` da **animação dos inimigos comuns** (a A2 tinha atribuído aos projéteis); Guilty e Didact criavam 1 máscara/frame; no `draw`, artilharia, cone, onda EMP e aviso de laser criavam uma `Surface` por efeito por frame (Warden 2,6/frame).

**O que foi feito**
- `utils/superficies.py`: `mascara_de` (cache com chave fraca por superfície), `camada_alpha` (buffer SRCALPHA do tamanho da tela, limpo e recortado na caixa do efeito), `rascunho` (SRCALPHA local por tamanho) e `SUPERFICIE_VAZIA`.
- Máscaras do cache: inimigos comuns (`mostrar_frame_atual` substitui `get_current_sprite`: a cópia continua, porque o alpha é por inimigo, mas a máscara vem do frame original), Sentinel, Guilty, Didact, Hunter, Guardian e projéteis (`ProjetilUniversal`).
- `draw` sem `Surface`: artilharia, onda EMP e aviso de laser pela `camada_alpha`; o cone pelo `rascunho` (o `draw.polygon` recortado pela borda da tela muda pixels da aresta; os raios vêm de presets, então há poucos tamanhos). `RaioEscudo` (Watcher) criava uma `Surface` por frame no `update`; agora tem `draw` próprio e só atualiza a caixa.
- Granada de plasma: a composta (sprite + auréola) fica em cache por nível de alpha (passo 10). Itens: o frame com brilho pulsante fica em cache por nível de alpha (passo 5; antes eram 2 cópias por item por frame).
- `feats/particulas.py`: `Particula` (imagem base em cache + 16 variantes de alpha, guardadas na partícula) e `emitir`, com **teto global** `TETO_PARTICULAS = 2000` em `entity_manager.particulas_grupo` (novo, zerado a cada partida). Substitui `DustParticle` (`emitir_poeira`), `ItemParticulaColeta` e o rastro do teleporte Promethean (que copiava uma `Surface` por partícula). O núcleo do teleporte fica em cache por tamanho. A ordem dos sorteios é a mesma de antes, inclusive quando o teto descarta.
- Picos medidos de partículas vivas: Warden 1504, Knight 781, Gravemind 30, hordas das fases 0–8 ≤ 12; a horda do pool da fase 9 (sem mapa) passa de 2500. O teto não corta nenhum caso jogável de hoje.
- Testes: `test_sem_alocacao.py` (50), com **equivalência de pixels** (cópia literal do código antigo) para artilharia, cone (todos os presets, 3 direções), onda EMP e aviso de laser em 8 posições × 2 offsets, inclusive cortados pela borda e fora da tela; composta da granada idêntica à antiga. Mais: máscaras do cache, update da horda sem `mask.from_surface`, partículas (teto, fade, sorteios, reset por partida), `draw` dos efeitos sem alocar. Suíte: **785 verdes + 1 xfail**. Golden inalterado.

**Catraca (alocações/frame):** horda 20,0 → **8,0**; fase 0 8,2 → 8,0; bosses 9,1–12,0 → 8,6–10,0. O que sobra é o HUD (~8/frame: C4). No `update`, só aquecimento de cache (ângulo novo de projétil, base nova de partícula), criação de boss e o Gravemind (máscara por frame da animação de respawn: F2/F5, como já previsto no roteiro §7). Tetos baixados.

**Desempenho** (na tomada; a rodada completa contra a base):
| Cenário | Média | p95 |
|---|---|---|
| horda_150 | 5,2 → 4,6 | 14,5 → **6,2** |
| boss_guardian | 8,6 → **3,4** | 25,6 → 4,7 |
| boss_tartarus / atriox / didact | −29% a −33% | −21% a −36% |
- Acusados: Knight e Warden (p95). A/B alternado com a C2 (worktree), 3 rodadas: Warden média 4,6–4,7 → 3,7–3,8, p95 igual; Knight média igual, p95 4,0–4,2 → 4,2–4,8 (abaixo do piso de 1 ms). A 1ª versão da partícula consultava o cache de variantes a cada frame e custava 2× no profiler; agora a lista fica na partícula.

**Achados (não corrigidos)**
- `OndaEMP.draw` sem deslocamento chama `camera.aplicar_posicao`, que não existe (o método é `apply_pos`). O `Renderer` sempre passa o deslocamento, então o ramo não roda.
- `Sentinel.animar` passa o frame do cache sem copiar para `set_image`, que aplica `set_alpha` nele: o alpha de um Sentinel vale para todos que mostram o mesmo frame.

**Não validado:** a aparência das partículas (alpha em 16 níveis), do brilho dos itens e da granada (níveis de alpha) e do raio do Watcher (agora desenhado em coordenadas de tela) no jogo real.

## 2026-11-21 | Etapa C2: broadphase de inimigos
**Gatilho (§6) medido:** 250 inimigos da fase 0, 10 s, na tomada. Só com a AR: colisão 0,35 ms/frame. Com 5 armas no nível 10 (needler, carabin, shotgun, sniper, machine gun): **colisão 5,6 ms/frame** (passa dos 2 ms); com spartan laser, light rifle, sniper, needler e dizimator: 2,3 ms. A busca de alvo das armas custou **0,04 ms/frame**. Script fora do repo (cronometra `CollisionManager.update` e `encontrar_inimigo_*`).

**O que foi feito**
- `collision.py::BroadphaseInimigos`: os retângulos de colisão dos inimigos são lidos 1× por frame (`reconstruir`, no início do `CollisionManager.update`), e cada consulta filtra os candidatos com `Rect.collidelistall` (laço em C), na ordem do grupo. A decisão final continua com `custom_collision`. Usada por projétil × inimigo e no contato do jogador (`colidindo_com_inimigos`). Inimigo com `usar_circulo` (Scarab) é candidato de toda consulta, porque o círculo passa da borda do rect.
- `rect_de_colisao(sprite)` concentra a regra collision_rect > hitbox > rect (antes repetida no `custom_collision`).
- **Decisão (difere do roteiro):** filtro por `collidelistall` em vez de uma `GradeEntidades`. É mais simples, mantém a ordem do grupo de graça (a ordem decide o desempate do "mais próximo primeiro") e mediu o bastante: colisão de **5,6 → 0,3 ms/frame** no cenário do gatilho. A busca de alvo **não** entrou (0,04 ms/frame: a regra 7 não justifica); fica para a E4, se o perfil pedir.
- **Limite declarado:** inimigo que surge ou se move *durante* a passada de colisão (ex.: teleporte ao tomar dano) só é visto pelos projéteis no frame seguinte. Na força bruta seria no mesmo frame. O teste quadro a quadro (abaixo) não pegou nenhum caso em 4 s de combate.
- Testes: `test_broadphase.py` (11): equivalência com `spritecollide` (mesma lista, mesma ordem) em 3000 sondas aleatórias numa horda com Scarab, Didact e Jega; para o jogador; e **quadro a quadro** em 4 s de combate com 4 armas de projétil (cada consulta conferida com a força bruta no próprio frame). Bordas: grupo vazio, inimigo que saiu do grupo, inimigo circular, reconstrução, consulta inválida. Suíte: **733 verdes + 1 xfail**. Golden inalterado; catraca inalterada.

**Desempenho:** a rodada completa acusou piora em quase tudo, inclusive no `draw`, que a C2 não toca (mesmo ruído da B2–B4). A/B alternado com o HEAD (worktree), na tomada: horda (½ escala, ordem invertida) C2 4,6–5,2 × HEAD 5,3–5,6; Warden 4,6–4,7 × 4,7–4,9. Sem piora. Base não regravada.

## 2026-11-21 | Etapa B4: ordem de update explícita + eventos (bloco B concluído)
**O que foi feito**
- `Game.update` virou passos nomeados: `_atualizar_portal`, `_checar_boss_derrotado`, `_checar_portal_tocado`, `_atualizar_spawner`, `_atualizar_entidades`, colisão, fase, `_checar_game_over`. A ordem e as condições não mudaram.
- `systems/eventos.py`: barramento síncrono `eventos` (`assinar`, `emitir`, `limpar`), limpo a cada partida. Eventos: `inimigo_morreu` (`CollisionManager`, só quando `morrer()` tirou o inimigo do mundo: a consciência do Warden adia a morte), `boss_derrotado` (boss, fase), `fase_trocada` (fase nova). `dano_causado` está definido, mas só é emitido a partir da **E1**: hoje há 3 APIs de dano e 4 overrides, e emitir em só parte delas daria dados errados para a F3.
- Ainda não há assinantes no jogo (F3, G4 e a pontuação vêm depois).
- Testes: `test_eventos.py` (16), incluindo a ordem dos passos e a contagem: em 60 s da fase 0, cada inimigo que saiu do mundo gerou exatamente um `inimigo_morreu`. Suíte: **722 verdes + 1 xfail**. Golden inalterado; catraca inalterada.

**Bug novo (não corrigido; xfail):** tocar o portal da **última** fase e morrer no mesmo update chama `_encerrar_partida` duas vezes (`finalizar_campanha` e `_checar_game_over`): a pontuação final é somada em dobro (o teste deu 14 em vez de 7). Com `estados_estritos`, a 2ª ida a `game_over` vira exceção. `test_sistemas.py::test_fim_de_campanha_e_morte_no_mesmo_update_pontua_uma_vez` é `xfail(strict=True)`. Correção sugerida: `_checar_game_over` só age se o estado ainda for `jogando` (1 linha, commit próprio).

**Desempenho:** rodada completa acusou horda e Guilty; lado a lado com o HEAD (B3), alternando: horda 8,8–9,3 × 8,9; Guilty 1,5–1,6 × 1,4–1,5; Warden 4,5–4,6 × 4,6 (uma rodada isolada deu 5,7, que não se repetiu); Guardian 9,3–9,4 × 9,3. Sem piora.

**Ruído de medição (B2–B4):** nesta sessão a máquina mediu até 70% acima da base **no próprio HEAD**, na tomada. Por isso as 3 etapas foram validadas por A/B alternado contra o commit anterior (worktree), não contra `perf_base.json`. Base não regravada: convém medir de novo numa sessão "fria" antes da próxima etapa de desempenho.

**Pendências:** o bug acima (xfail). TODO do Hunter preso nas paredes (ver C1). Próxima etapa: **C2** (só se o gatilho da §6 disparar) ou **C3**.

## 2026-11-21 | Etapa B3: sessão separada do Game
**O que foi feito**
- `systems/sessao.py::SessaoJogo` (dataclass): `timer_jogo`, `fase_atual`, `boss_atual`, `portal_atual`, `spawnar_portal_em_breve`, `timer_portal`, `tela_de_upgrade_ativa`, `gravemind_reborns`. Nasce em `_resetar_estado_jogo`; todos os consumidores (spawner, stage manager, HUD, game over, player, Gravemind, testes) passaram a `game.sessao.<campo>`. Migração completa no mesmo commit: os shims de propriedade previstos no roteiro não foram necessários.
- `invocacao_protogravemind` foi apagado: era atribuído e nunca lido.
- **Bug da A3 corrigido:** `relogio.reiniciar()` no início de cada partida, antes de criar qualquer objeto. O HUD, que guardava `_ultimo_check_boss` da partida anterior, agora é recriado com a sessão. `test_nova_partida_zera_o_relogio` perdeu o `xfail`, e o `# SHIM(B3)` do golden (que zerava o relógio à mão) foi apagado.
- Os aliases `game.<grupo>` saíram; os 11 usos foram para `entity_manager.<grupo>`. 3 arquivos (`companion.py`, `laserblast.py`, `needler.py`) não importavam o `entity_manager`: adicionado (o ruff não pegaria no `companion.py`, que tem `import *` com exceção F405).
- Testes: `test_sessao.py` (6) e `test_shims.py` (2; a regra 3 do roteiro previa o arquivo e ele não existia). `PERMITIDOS` está vazio: zero shims no repo. Suíte: **705 verdes, nenhum xfail**.

**Golden: inalterado**, agora sem zerar o relógio à mão. A 2ª partida no mesmo processo continua idêntica (`test_simulacao_e_deterministica`): é a prova de que nada vaza entre partidas na fase 0.

**Desempenho:** a rodada completa acusou horda, Warden, Guardian e Atriox, mas a máquina segue ruidosa (o HEAD anterior mediu de 6,3 a 9,2 ms na horda). Lado a lado e alternando com o HEAD: horda 6,1 × 6,3–9,2; Warden 4,7 × 4,6; Guardian 9,4–10,0 × 9,4–10,3; Atriox 3,3 × 3,4. Sem piora. Catraca inalterada.

**Não validado:** restart pelo menu no jogo real (o fluxo é testado pelos handlers).

## 2026-11-21 | Correção: tela de colaboradores não desenhava
- `TelaColaboradores.draw` usava `self.imagem`, mas o atributo é `self.image`: `AttributeError` a cada frame, que o `Renderer` engolia, mostrando "Erro ao renderizar" no lugar dos créditos. Achado na B2.
- Commit separado da B2 (roteiro §2, regra 6). Regressão em `test_regressoes.py::test_tela_de_colaboradores_desenha_sem_erro`. Suíte: **696 verdes + 1 xfail**. Não validado visualmente.

## 2026-11-21 | Etapa B2: estados formalizados
**O que foi feito**
- `systems/estados.py`: constantes dos 8 estados, `ESTADOS`, `TRANSICOES` (origem → destinos), `TransicaoInvalida` e `Tela(evento, desenhar)`.
- `Game.estado_do_jogo` virou propriedade só de leitura; a troca é `game.mudar_estado(CONSTANTE)`. Fora da tabela: com `estados_estritos` (testes e `MCE_DEBUG`) lança exceção; no jogo final loga 1× e aplica, para não prender o jogador numa tela. Estado inexistente é sempre recusado.
- As 17 atribuições migraram (`EventManager`, `Game`, `player_scaling`, `colaboradores`). A tela de colaboradores trocava o estado sozinha: agora devolve `'sair'`, como as outras.
- Registro único `game.telas[estado] = Tela(handler, desenho)` (`Game._registrar_telas`), lido pelo `EventManager` e pelo `Renderer`. Os dois `_dispatch` sumiram; os métodos viraram `tratar_<estado>` e `desenhar_<estado>`.
- Tabela tirada do código, inclusive um caso pouco óbvio: **`level_up → game_over`** (subir de nível e morrer no mesmo update; a partida acaba com a tela de upgrade aberta, como antes).
- Testes: `test_estados.py` (13): tabela coerente, registro cobre os estados, estrito × jogo final, nenhum estado escrito à mão em `source/`, e um teste que percorre os **fluxos reais** pelos handlers e exige que as transições feitas sejam exatamente a tabela. `helpers.voltar_ao_menu(game)` encerra partidas de teste em qualquer estado (usado pela fixture, golden e `perf.py`). Suíte: **694 verdes + 1 xfail**. Golden inalterado; catraca inalterada.

**Desempenho:** o `perf.py` acusou piora em quase tudo (horda 5,2 → 7,9 ms), inclusive no `draw` dos bosses e na troca de fase, que a B2 não toca. Na tomada. Medi o HEAD anterior (worktree) e a B2 alternados, nas mesmas condições: horda 6,3–6,7 (HEAD) × 6,3–6,6 (B2); Warden 4,5 × 4,8; Guardian 9,5 × 10,0; Gravemind 4,2 × 4,2. Diferença dentro do ruído; a máquina é que estava mais lenta que na base. Base não regravada.

**Não validado:** navegação real dos menus com teclado (os fluxos foram testados chamando os handlers).

## 2026-11-21 | Etapa C1: grade espacial de paredes
**O que foi feito**
- `mapmanager/grade_paredes.py::GradeParedes`: os segmentos viram tuplas de float `(indice, x1, y1, x2, y2)`, e cada um entra nas células de 128 px que a sua caixa, inflada de `MARGEM_GRADE` (128 px), toca. A célula da entidade traz todo segmento a menos de 128 px dela, na ordem do mapa (a ordem importa: os empurrões são sequenciais). Consulta = um acesso a dict, sem alocar. Raio maior que a margem (ex.: hitbox de veículo) junta células. A grade é montada no fim de `carregar_json`.
- `collision_utils.py`: `empurrao_do_segmento` (float, mesma ordem de contas do `Vector2` antigo) e `sair_das_paredes(posicao, raio, grade, iteracoes)`, usados pelo inimigo (`aplicar_colisao_mapa`) e pelo jogador (`mover_com_colisao`). O `Game.update` passa a grade no lugar da lista; as ~30 assinaturas `update(dt, paredes)` não mudaram.
- Removidos (sem uso): `get_paredes_proximas` e `projetar_fora_da_linha`. Os testes deles migraram para as funções novas; o cache de bbox (ainda usado por `caminho_livre`) passou a ser testado por ele.
- **Bug corrigido:** inimigo longe do jogador colide com as paredes perto dele. O teste (`test_regressoes.py`) foi escrito antes como `xfail(strict=True)`, falhou no código antigo (inimigo parado a 6 px da parede, raio 15) e perdeu a marca.
- Testes: `test_grade_paredes.py` (19), com a **equivalência** contra uma cópia literal do código antigo em 10 mil posições do mapa 0 (inimigo e jogador): resultado idêntico bit a bit. Suíte: **681 verdes + 1 xfail em 40 s** (antes, 75 s).

**Golden: inalterado (não foi regerado).** O roteiro previa regerar, mas a mudança não aparece nesse cenário. Verificado em 2 passos: (1) a grade nova consultada à moda antiga (paredes perto do jogador) reproduz o golden bit a bit, o que prova a matemática e a ordem; (2) a consulta nova (perto de cada entidade) também dá o golden idêntico: com o jogador parado na fase 0, nenhum inimigo chega a uma parede fora da lista antiga. O bug fica coberto pelo teste de regressão.

**Decisão:** a margem começou em 64 px. A equivalência falhou para o jogador (raio 48, folga de só 16 px): num canto fundo os empurrões o deslocaram 56 px, até paredes que a consulta não trouxe. Com 128 px a folga é de 80 px (jogador) e 113 px (inimigo), ao custo de 4,7 segmentos por célula em média no mapa 0 (eram 3,2).

**Desempenho** (na tomada; ms/frame, média × base da A1)
| Cenário | Antes | Depois | p95 depois |
|---|---|---|---|
| horda_150 | 33,2 | **5,2 a 6,3** | 14,5 a 17,5 |
| fase0_60s | 5,3 | 1,7 a 2,2 | 2,3 a 4,2 |
| bosses | 2,0 a 11,5 | 1,2 a 8,7 (−7% a −47%) | |
| troca_de_fase | 1,2 | 1,6 (+0,4 ms: montar a grade; abaixo do piso de 1 ms) | |
- Meta da C1 (horda ≤ 10 ms) cumprida. Parte da queda dos bosses é ruído: o `draw`, que a C1 não toca, também caiu entre as 2 rodadas. O Guardian segue o mais caro (draw ~8 ms, alvo da C4/F5).
- **`tools/perf_base.json` regravado** com a 2ª rodada: sem isso, a base antiga esconderia uma regressão de até 80% na horda. Os números da A1 continuam na entrada dela, para a tabela final da H2.
- Catraca: sem mudança (o `Vector2` antigo não era contado).

**Não validado:** a sensação de colisão no jogo real (deslizar em parede e cantos). A equivalência prova o mesmo empurrão; não foi jogado.

**Jogado depois (relato do usuário):** a colisão ficou boa. Numa rodada o **Hunter ficou preso nas paredes centrais**: a hitbox dele é grande e o spawn caiu muito perto da parede. **TODO (futuro):** tratar no próprio mapa, com paredes "sólidas" de verdade (área bloqueada, não só segmentos que empurram), para impedir que uma entidade nasça ou entre dentro delas. Sem etapa no roteiro ainda.

**Pendências:** o bug do relógio (B3). Próxima etapa: **B2** (ou C2, se o perfil pedir: gatilho na §6).

## 2026-11-21 | Etapa B1: passo fixo de simulação
**O que foi feito**
- `gameclock.py::AcumuladorPassoFixo`: soma o tempo real do frame e devolve quantos passos de `PASSO_FIXO` (1/60 s) cabem, no máximo `MAX_PASSOS_POR_FRAME` (5). Quando bate o teto, o atraso é descartado: o jogo desacelera em vez de entrar em espiral. dt zero ou negativo não gera passo; parâmetro inválido lança `ValueError`.
- `Game.run`: eventos 1× → `update(1/60)` × n → draw 1× por frame. Substitui o teto de 0,05 s. A assinatura de `update(dt)` não mudou.
- `tests/helpers.py::DT` agora é o próprio `PASSO_FIXO` (jogo e testes usam o mesmo passo por construção).
- 10 testes novos em `test_core_utils.py` (60/144 FPS, ticks em ms inteiros sem deriva, teto de 5, sem espiral, dt ≤ 0, parâmetros inválidos e o `Game.run` com relógio falso). Suíte: **660 verdes + 1 xfail**. Golden inalterado.
- `perf.py` e a catraca não foram refeitos: os dois chamam `update` direto com dt de 1/60, e só o `Game.run` mudou.

**Não validado:** sensação de jogo numa máquina que não segura 60 FPS (abaixo de 12 FPS o jogo passa a andar em câmera lenta, por causa do teto de 5 passos).

## 2026-11-21 | Etapa A4: higiene (bloco A concluído)
**O que foi feito**
- Código morto apagado (nada os importava, verificado por grep): `atriox/{setup,states,attacks,vfx}.py`, `escharum/vfx.py` e `harbinger/states.py`. O Atriox continua usando os mixins do Tartarus (identidade própria na F5).
- `tests/unit/test_imports.py`: importa cada um dos 226 módulos de `source/` (um teste por módulo, a lista sai de uma varredura da pasta). Todos importam sozinhos: nenhum import circular nem quebrado.
- `ruff==0.17.6` em `requirements-dev.txt`, com `ruff.toml` só nas regras `F`. As violações de hoje viraram exceções por arquivo × regra (108 arquivos, 139 pares): 168 `F401`, 117 `F405`, 42 `F403`, 5 `F841`, 1 `F811`. **Nenhum `F821`** (nome indefinido) no repo.
- `tests/unit/test_lint.py`: o repo passa no ruff; exceção que não é mais necessária falha (é isso que faz a lista encolher); a config pega `F821`/`F401`/`F403`. `CLAUDE.md` ganhou o comando.
- Suíte: **650 verdes + 1 xfail** (~100 s). Golden e catraca inalterados. `perf.py` não foi refeito: os arquivos apagados não eram importados, então o jogo em execução é o mesmo.

**Achados (não corrigidos, ficam na lista de exceções)**
- Os 5 `F841` e o `F811` são variáveis mortas inofensivas (`bruiser.py: agora`, `mortar.py: aviso`, `hud_draw.py: fill_rect` e o parâmetro `altura_tela` que sombreia o import, `ranking_draw.py: brilho`, `settings_draw.py: gap`). Nenhum esconde bug.
- **Limite:** a exceção é por arquivo × regra, então um 2º import não usado num arquivo que já tem `F401` passa. Corrigir os `F401`/`F403` exige cuidado com imports de efeito colateral (ex.: `assets`), por isso não entrou nesta etapa.

**Pendências:** o bug do relógio (B3). Próxima etapa: **B1** (ou C1).

## 2026-11-21 | Etapa A3: golden master
**O que foi feito**
- `tests/integration/test_golden.py`: 60 s da fase 0 (seed 1234, jogador blindado, só `update`), com uma amostra por segundo (inimigos, projéteis dos dois lados, itens, vida, escudo, XP, nível, pontuação, posição). Compara com `tests/golden/fase0.json` (uma amostra por linha, para o diff mostrar o segundo que mudou) e aponta a primeira divergência (`t=54 s, projeteis_inimigos: golden 5, agora 6`).
- Regerar exige `--atualizar-golden` (opção nova do `conftest.py`); o teste então é pulado com aviso para registrar o motivo no log.
- `test_simulacao_e_deterministica`: uma 2ª partida no mesmo processo dá o mesmo resultado. O golden gerado em dois processos diferentes também saiu idêntico.
- Suíte: **409 verdes + 1 xfail**, em ~92 s (o golden soma ~28 s, porque são 2 simulações de 60 s). Nenhum código de produção mudou, então o perf não foi refeito.

**Bug novo (não corrigido; vai para a B3)**
- `iniciar_novo_jogo` não zera o `relogio`, e a simulação depende do valor **absoluto** dele: a 2ª partida com a mesma seed divergiu em t=54 s. Zerando o relógio antes de cada partida, 3 rodadas seguidas ficaram idênticas.
- Não foi corrigido porque zerar só o relógio quebraria objetos que duram a sessão: o `HUD._ultimo_check_boss`, por exemplo, guarda o tempo da partida anterior e veria o tempo voltar, congelando a barra do boss. É exatamente o escopo da B3 (sessão nova a cada partida).
- Até lá, o golden zera o relógio antes de simular (`# SHIM(B3)` em `simular_golden`). `test_nova_partida_zera_o_relogio` é `xfail(strict=True)`.

**Limite do golden:** o jogador não recebe input, então a posição só muda por empurrão (no cenário atual ela fica parada). O movimento entra no golden quando a E3 permitir plugar um bot.

**Pendências:** o bug do relógio (B3). Próxima etapa: **A4**.

## 2026-11-21 | Etapa A2: catraca de alocação
**O que foi feito**
- `tests/helpers.py::contar_alocacoes()` conta, por tipo, as chamadas a `pygame.Surface(...)`, `mask.from_surface`, `transform.*` (menos as que não alocam) e `font.Font`/`SysFont`. A `Surface` é trocada por uma metaclasse que conta e devolve uma `Surface` original, então o `isinstance(x, pygame.Surface)` de `enemy_sprites` e `items/draw` continua valendo. `contador.pausado()` (aninhável) tira um trecho da conta.
- `tests/perf/test_catraca.py`: 1 s de aquecimento fora da conta, depois update + draw por 3 s (horda de 150), 5 s (fase 0) ou 2 s (cada boss). Afirma `alocações/frame <= TETOS[cenário]`. Boss novo falha até ganhar teto; medida 10% abaixo do teto gera aviso para baixá-lo. Há um teste de ponta a ponta: uma Surface a mais por frame no HUD aparece como +1,0/frame.
- Suíte: **397 verdes** (~63 s; a catraca soma ~20 s, tudo marcado `integration`). `perf.py`: saída 0 (a 1ª passada acusou 9 cenários e nenhum se confirmou na nova medida).

**Tetos de hoje (alocações por frame)**
- O HUD cria ~8 `Surface` por frame em **todo** cenário (fase 0 = 8,2, quase só isso); a barra do boss soma ~1. É o alvo principal da C3.
- Horda de 150: 20,0 (12 `mask.from_surface` + 8 `Surface`): as máscaras são de projéteis criados (C3).
- Bosses: 9,1 a 10,3; Warden 12,0. Guilty, Didact e Escharum criam ~1 máscara a cada 1–2 frames.

**Achados**
- O HUD usava `get_ticks` (corrigido no commit anterior): sem a correção, a contagem dos bosses variava ±1/frame entre rodadas iguais.
- `test_perf_tool::test_confirmacao_mede_de_novo_e_descarta_ruido` oscilava desde a A1. A base de ~0 ms exigia que a troca de fase real passasse do piso de 1 ms, e ela mede ~1 ms. Agora a base é `-PISO_MS`. A ferramenta não mudou.
- A contagem tem uma sobra de até 2 chamadas em 180 frames, vinda de caches de módulo (mais frios na 1ª partida do processo). O teto cobre isso (medida truncada em 0,1 + 0,1).
- **Limite:** métodos de tipo em C (`Surface.copy`, `convert_alpha`, `subsurface`, `Font.render`) não são contados, porque o monkeypatch não os alcança. O texto do HUD renderizado por frame fica fora da catraca.

**Pendências:** nenhuma. Próxima etapa: **A3**.

## 2026-11-21 | Correção: HUD usava o relógio de parede
- `HUD._atualizar_boss_foco` usava `pygame.time.get_ticks()` (viola a regra de tempo do `CLAUDE.md`). Agora usa `relogio.agora()`.
- Efeito: o foco da barra de vida do boss é reavaliado a cada 500 ms **de jogo**. Na simulação headless, a barra aparecia antes ou depois conforme a velocidade da máquina, e a contagem de alocações da A2 variava ±1 Surface/frame entre rodadas iguais (foi assim que o bug apareceu).
- Commit separado da A2 (roteiro §2, regra 6). Regressão em `test_regressoes.py::test_hud_foco_do_boss_usa_relogio_de_jogo`. Suíte: **372 verdes**.
- Não muda a simulação (só o desenho do HUD); não validado visualmente.

## 2026-11-21 | Etapa A1: medição de desempenho
**O que foi feito**
- `tools/perf.py`: cenários headless com o loop real (update + draw, dt 1/60), jogador blindado e seeds fixas: `horda_150` (reposta fora do cronômetro), `fase0_60s`, `boss_<nome>` (20 s, todos do `PHASE_BOSSES`) e `troca_de_fase` (0→8). Grava média/p95/update/draw em `tools/perf_base.json`, mede o import dos assets e o pico de memória e compara com a base.
- `ir_para_fase` saiu do smoke test para `tests/helpers.py` (o perf reusa).
- `tests/unit/test_perf_tool.py`: 24 testes. Suíte: **371 verdes em 36 s**. Nenhum código de produção mudou.

**Base (notebook na tomada, Windows 11, Python 3.13.5, pygame 2.6.1)**, em ms/frame (update + draw)
| Cenário | Média | p95 | Update | Draw |
|---|---|---|---|---|
| horda_150 | 33,2 | 46,5 | 30,4 | 2,8 |
| fase0_60s | 5,3 | 8,7 | 3,8 | 1,5 |
| boss_guardian | 11,5 | 34,1 | 1,2 | **10,3** |
| boss_warden | 6,8 | 13,9 | 3,3 | 3,5 |
| boss_gravemind | 5,6 | 7,3 | 3,7 | 1,9 |
| outros 12 bosses | 2,0 a 4,8 | 2,7 a 7,2 | 0,2 a 2,8 | 1,4 a 2,5 |
| troca_de_fase | 1,2 (máx 1,5) | | | |
- Import dos assets: 4,2 s (a doc dizia ~13 s; a diferença não foi investigada, TODO: confirmar a frio). Pico de memória: **781 MB**.
- Leitura: a horda é o único cenário fora dos 16,7 ms, e o update é 92% dela (alvo da C1/C2). O Guardian é o único boss caro, e o custo está no **draw** (alvo da C4/F5). A troca de fase é barata porque os mapas já estão decodificados no import; a D2 vai mudar isso, então é preciso medir de novo.

**Ruído (decisões de implementação)**
- **Na bateria** (4 rodadas): a horda variou de 32,7 a 45,9 ms, e numa rodada os bosses saíram 2× mais lentos. **Na tomada** (2 rodadas): as médias variaram até ±4% (Atriox +8%), e o p95 até 17%.
- Por isso: (1) a piora só conta se passar de 10% **e** de 1 ms; (2) o cenário acusado é medido de novo antes de reprovar (na 2ª rodada na tomada, o p95 do Atriox foi acusado e não se confirmou); (3) o relatório registra a fonte de energia, e `--gravar-base` é recusado na bateria. O §3 do roteiro foi atualizado.

**Pendências:** nenhuma. Próxima etapa: **A2** (catraca de alocação).

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

**Decisões da E6 (depois da A0):** pesos de sorteio comum 40, incomum 25, rara 20, épica 10, lendária 5. Item `upgrade` e level-up sem opções (tudo no máximo) ficam para o recurso futuro **itens temporários e boosts** (roteiro §7.1); até lá, a E6 usa um comportamento provisório (só os pontos / não abre tela).

**Pendências:** nenhuma decisão em aberto. Próxima etapa: **A1**.

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
