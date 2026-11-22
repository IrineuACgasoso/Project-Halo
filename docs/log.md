# Log entre sessões

Entradas curtas, a mais recente no topo. Quando o arquivo passar de cerca de 300 linhas, comprima as entradas antigas num resumo.

## 2026-11-22 | Cheats pelo menu de pausa (recurso novo, pedido do usuário)
- A pausa ganhou o botão **ATIVAR CHEATS** (entre RESUME e EXIT TO MENU). Ele alterna `Teclado.cheats` (`Game.alternar_cheats`); o rótulo vira DESATIVAR CHEATS e, ligado, a pausa mostra as teclas (L: subir de nível, P: portal, B: boss). Vale até fechar o jogo (sobrevive a voltar ao menu). `MCE_DEBUG=1` continua abrindo com os cheats ligados (e só ele liga o overlay de paredes e a validação na abertura).
- `Teclado(debug=)` virou `Teclado(cheats=)`; `Game.teclado` guarda a fonte padrão (os testes trocam `Game.entrada` por um `Roteiro` sem perder o estado dos cheats).
- Testes (`test_entrada.py`): começa desligado; o botão liga e desliga e a tela continua na pausa; do botão até o efeito (L sobe o nível só depois de ligar); desenho com a dica. Suíte: **1098 verdes + 1 xfail**. Golden inalterado.
- **Atenção:** partida com cheats entra no ranking como qualquer outra (não há marca). **Não validado:** o botão e a dica na tela real.

## 2026-11-22 | Etapa E4: armas pegam os grupos do entity_manager (refatoração: golden inalterado)
- `Arma` ganhou as propriedades `all_sprites`, `inimigos_grupo`, `items_grupo` e `auras_grupo`, lidas do `entity_manager` (só leitura). Saíram `ArmaInfo.grupos`, o parâmetro `grupos` dos 22 construtores (armas, companheiros, veículos) e o desempacotamento posicional: a classe de bug do Fuel Rod mirando nos itens não existe mais. O construtor é `classe(jogador, game)`. Os nomes soltos (`grupo_inimigos`, `auras_grupos`, `item_grupo`) viraram os do `entity_manager`; o `projeteis_grupo` guardado e nunca usado saiu.
- `ArmaDeRajada` (`baseweapon.py`): a lógica de rajada copiada em Needler, Carabin, Dizimator, Machine Gun e Light Rifle. A subclasse só implementa `atirar(alvo)`; o Light Rifle troca `buscar_alvo()` (o mais forte). O Light Rifle buscava o alvo 2× por tiro; agora 1× (mesmo resultado no mesmo passo).
- `validar_armas` perdeu a regra de grupo (o campo não existe); os 2 casos dela saíram do `test_validacao` junto com o campo. 6 exceções do `ruff.toml` saíram (imports mortos nas rajadas e no `constants.py`).
- **Difere do roteiro:** sem helper de spread (só a Shotgun espalha; um helper para um uso seria abstração sem ganho) e sem busca de alvo pela broadphase (a C2 decidiu: a busca custa 0,04 ms/frame).
- Testes (`test_levelup_e_armas.py`): ninguém recebe `grupos`; grupo da arma não pode ser trocado; rajada dispara `burst_count` tiros espaçados, não reinicia no meio, para quando o alvo some e não atira fora do alcance; Light Rifle mira no mais forte; cada rajada real cria 1 projétil por tiro. A regressão dos grupos (`test_regressoes`) confere os 4 grupos de todas as armas. **Suíte: 1094 verdes + 1 xfail em 79 s.** Golden inalterado.
- Desempenho (na tomada, A/B alternado com o HEAD em worktree, 2 rodadas): horda 5,94/4,25 (HEAD) × 5,75/4,20 ms/frame; fase 0 2,33/1,59 × 2,11/1,45. Sem piora.
- Próxima etapa: **E5** (persistência entre fases explícita). Pendências da E1/status continuam.

## 2026-11-22 | Etapa E3: entrada desacoplada (refatoração: golden inalterado)
- `source/systems/entrada.py`: `ComandoJogador` (frozen e validado: `direcao` + `veiculo`, `hack_nivel`, `hack_portal`, `hack_boss`), `FonteEntrada` com `Teclado` (WASD, V; L/P/B só com debug) e `Roteiro` (replay por segmentos `(passos, comando)`, parado no fim). `Game.entrada` (padrão `Teclado`) é lida 1× por passo em `_atualizar_entidades` e vira `player.comando`.
- O jogador (`aplicar_direcao_do_comando`, `executar_hacks`) e o Warthog/Pelican (tecla V) leem o comando; só `entrada.py` chama `get_pressed` (teste). O comando diz o que está **pressionado**: a borda do V continua no veículo, então nada muda no jogo. Saiu o `hasattr(game, 'spawner')` do hack B.
- Testes: `test_entrada.py` (48) e, no `test_golden.py`, um roteiro de 20 s tocado 2× dá a mesma partida. O teste do jogador atordoado (`test_status`) passou a usar um `Roteiro` em vez de sobrescrever o `input`. **Suíte: 1081 verdes + 1 xfail em 62 s.** Golden inalterado.
- Desempenho (na tomada): horda 4,95 ms/frame (−5% da base), fase 0 1,5 (−10%).
- **Não validado:** WASD, V e os hacks L/P/B no jogo real (cobertos só com teclado falso).
- Próxima etapa: **E4** (armas pegam os grupos do `entity_manager`). Pendências da E1/status continuam (abaixo).

## 2026-11-22 | Etapa E2: estado de alvo unificado + balanceamento do usuário (golden regravado)
- `BaseEnemy.vivo` (`vida > 0`) e `alvejavel` (vivo e não `invisivel`). As buscas de alvo das armas (`encontrar_inimigo_mais_proximo`/`_mais_forte`) e a checagem de morte do `CollisionManager` usam as propriedades; os `getattr` de alpha/`invis_phase` e a mistura `vida_atual`/`vida` saíram (só `BaseEnemy` entra em `inimigos_grupo`). Sozinha, a E2 deixa o golden inalterado (conferido com o balanceamento fora).
- **Balanceamento do usuário (muda o jogo, golden regravado por ele):** AR (velocidade do tiro 2400, alcance 600 +25/nível), Sidekick (alcance 450 +25), Sniper (alcance +50/nível), Machine Gun (alcance 550 +50), Light Rifle (alcance 700), Spartan Laser (+25/nível), Hunter (vida 800, costas ×8). O ×8 virou `Hunter.MULT_COSTAS`, e os testes leem a constante.
- **Suíte mais barata (pedido do usuário):** equivalências que já provaram a refatoração rodam com amostra menor: grade de paredes 10 mil → 1500 posições, broadphase 3000 → 1000 sondas, cone 1 direção por preset (as 3 formas alternadas). **Suíte: 1031 verdes + 1 xfail em 66 s** (antes, 94 s). Log comprimido (484 → ~130 linhas).
- Desempenho: horda 3,5 ms/frame (p95 4,8). Só a horda foi medida (a E2 só mexe na busca de alvo). **Não validado:** a sensação do balanceamento no jogo.
- Próxima etapa: **E3** (entrada desacoplada). Pendências da sessão anterior continuam (ver abaixo).

## 2026-11-21 | Alcance de todas as armas no weapon_data (refatoração: golden inalterado)
- As 9 armas que tinham o alcance no código (número solto no `disparar` ou `RAIO_ALVO` na classe) ganharam o stat `raio_maximo` no perfil, com o mesmo valor e sem upgrade (`label=None`, `increase=0`): Assault Rifle 700, Sidekick 600, Shotgun 500, Sniper 1200, Brick 1200, Needler 500, Dizimator 550, Carabin 650, Machine Gun 850. As classes leem `self.raio_maximo`; `RAIO_ALVO` saiu. Para o alcance subir por nível, basta dar `label` e `increase` no perfil.
- Testes (`test_regressoes.py`): toda arma cujo código procura alvo (13) tem `raio_maximo` no perfil; mudar o stat muda o alcance de verdade (as 13); o upgrade soma o `increase` (as 4 com upgrade). Suíte: 1016 verdes + 1 xfail; as mesmas 3 falhas do Hunter da entrada abaixo (mudança local, fora do commit).

## 2026-11-21 | Correção: upgrade de alcance do Light Rifle não fazia efeito
- O perfil `light_rifle` tem `raio_maximo` ("Alcance", +50 por nível), mas a classe mirava com a constante `RAIO_ALVO = 1000`: o card mostrava o alcance subindo e no jogo ele ficava em 1000. Agora usa `self.raio_maximo` (nível 1 = 1000: sem mudança até o 1º upgrade). **Muda o jogo:** o alcance cresce com o nível.
- Regressão em `test_regressoes.py::test_upgrade_de_alcance_muda_o_alcance_de_verdade`, para toda arma com `raio_maximo` no perfil (Fuel Rod, Grenade Launcher, Light Rifle, Spartan Laser; só o Light Rifle falhou antes). As outras armas têm o alcance fixo no código, sem stat (Assault Rifle, Sidekick, Shotgun, Sniper, Brick e o `RAIO_ALVO` de Needler, Dizimator, Carabin e Machine Gun).
- Suíte: 1003 verdes + 1 xfail; as 3 falhas restantes (`test_hunter_pelas_costas`, `test_fraqueza_e_a_regra_das_costas_do_hunter_se_somam`) vêm de uma mudança local não commitada em `hunter/core.py` (costas ×4 → ×8), fora deste commit. Não validado no jogo real.

## 2026-11-21 | Sistema de status (S3): bônus da Cortana como buff (muda o jogo)
- Antes: cada upgrade da Cortana fazia `jogador.velocidade += 10`, com o número fixo no código. O stat `jogador_speed_bonus` (+10/nível) só aparecia no card de upgrade e não era lido.
- Agora o stat manda: `jogador_speed_bonus` em **pontos percentuais** (+2 por nível, label "(%)"), e a Cortana aplica `BuffVelocidade(bonus / 100)` sem fim, com `chave=self` (reaplicar só atualiza). A velocidade-base do jogador não muda mais.
- **Muda o jogo (declarado):** +2% equivale a +10 na velocidade inicial (500). Como o level-up também soma +10 na velocidade-base, o bônus da Cortana agora cresce junto: no nível 20 do jogador (690), cada +2% vale +13,8.
- Teste em `test_status.py` (nível 1 sem bônus, +2% por nível, um lugar só, velocidade-base intacta). Suíte: **1001 verdes + 1 xfail**. Golden inalterado (a fase 0 do golden não tem Cortana). **Não validado:** a sensação no jogo.

**Pendências da sessão (E1 + status):**
- Decisões suas: "invulnerável" centralizado no contrato de dano (ver E1); indicador de status no HUD e feedback visual no alvo (ver S1).
- Ainda nenhuma arma nem inimigo aplica lentidão, atordoamento, queimadura, fraqueza, cegueira ou buff de dano: o sistema está pronto para o conteúdo.
- Bug do Hunter preso nas paredes (diagnóstico na E1). Bug do fim de campanha (xfail, B4). Regravar `perf_base.json` na tomada, numa sessão fria.
- Próxima etapa do roteiro: **E2** (estado de alvo unificado).

## 2026-11-21 | Sistema de status (S2): curas e escudos pelo sistema
**O que foi feito** (refatoração: golden inalterado)
- Orbe de vida e cura do level-up → `aplicar(alvo, Cura(...))`; escudo cheio do level-up e regeneração do MK2 → `aplicar(alvo, Escudo(...))`; transferência do Watcher → `aplicar(aliado, Escudo(t), fonte=watcher)`. Agora a queimadura corta essas curas (teste).
- `curar` saiu (a guarda de "jogador fora do mundo" da correção anterior está no próprio `aplicar`). Nenhuma cura nem ganho de escudo direto sobrou em `source/` (grep).
- O buff de cooldown antigo saiu: `adicionar_tempo_buff`, `atualizar_buff`, `buff_timer` e `buff_cooldown_ativo` **não tinham chamador** (o item "café" não tem efeito em `_aplicar_efeito`), e ele mexia em `arma.cooldown` com uma flag por arma. A cadência agora é o `BuffCadencia`. Os 2 testes dele viraram testes do `BuffCadencia` (mudança de especificação: o mecanismo foi trocado, não enfraquecido).
- **Equivalência:** os valores são os mesmos, porque `Escudo`/`Cura` fazem `min(atual + v, máximo)`, igual ao `+=` seguido do clamp de antes. Única diferença possível: o Watcher somava sem clamp e podia passar do máximo por 1 ulp de float; agora para no máximo.
- Testes: +5 (`test_player`: level-up cura 1/4 e enche o escudo; `test_status`: Watcher pelo sistema, sem passar do máximo, queimadura cortando o orbe de vida). Suíte: **1000 verdes + 1 xfail**. Golden e catraca inalterados.

**Fica para depois (não migrado):** os buffs internos dos bosses (velocidade temporária do Warden, `buff_ofensivo_mult` do Harbinger) e o "derrete escudo" do EMP são mecânicas do próprio boss, com movimento e ataques próprios; entram na F5 (`BossBase`).

## 2026-11-21 | Correção: cura não ressuscita o jogador morto no mesmo frame
- A coleta de itens (passo 4 do `CollisionManager`) vem depois do dano (passos 2 e 3). Morrer e, no mesmo frame, pegar um orbe de vida ou subir de nível com XP devolvia a vida a um jogador que já tinha saído dos grupos de sprite (`kill`): sem game over, a partida seguia com ele invisível. Agora `curar` não age em jogador fora do mundo. Achado ao planejar as migrações do sistema de status; commit próprio (roteiro §2, regra 6).
- Regressão em `test_regressoes.py` (orbe de vida e level-up; os dois falharam antes da correção). Suíte: **996 verdes + 1 xfail**. Golden inalterado.

## 2026-11-21 | Sistema de status (S1): núcleo de buffs e debuffs
**O que foi feito** (recurso novo pedido nesta sessão; decisões no roteiro §8, itens 8–11)
- `source/systems/status/`: `aplicar(alvo, efeito, fonte=None, chave=None)` é o ponto único, para jogador e inimigos; `remover` tira um buff sem fim.
  - **Debuffs:** `Lentidao`, `Atordoamento`, `Queimadura` (DPS + `reducao_cura`), `Fraqueza` (+% de dano recebido, pedido nesta sessão) e `Cegueira` (só no jogador).
  - **Buffs:** `BuffDano`, `BuffVelocidade` (com duração ou sem fim) e `BuffCadencia` (só no jogador).
  - **Instantâneos:** `Escudo` (até o máximo) e `Cura` (até o máximo, menos o corte da queimadura).
- **Validação:** dataclasses frozen. Porcentagem é fração (teto de 10 = 1000%, para pegar quem passa 30 querendo dizer 30%). Duração em ms; só os buffs aceitam `None`. Efeito exclusivo do jogador num inimigo, `fonte` que não é entidade e efeito desconhecido lançam exceção.
- **`fonte` × `chave`:** `fonte` é a entidade que causa (como em `Dano.fonte`: a queimadura dá o dano em nome dela). `chave` é o lugar de acúmulo (padrão: a fonte). Ex.: duas armas do jogador com chaves próprias acumulam queimadura, e o crédito continua sendo do jogador.
- **Acúmulo (item 9):** o mesmo lugar reaplicando substitui valores e duração. Entre lugares: lentidão = a mais forte; queimadura, fraqueza e buffs de dano/velocidade somam; cadência multiplica; atordoamento e cegueira valem enquanto houver um (cegueira: o menor raio).
- **Componente `status`** no jogador e em todo inimigo. Os modificadores são recalculados só quando um efeito entra ou sai, e só as entidades com efeito ativo são atualizadas (`Game._atualizar_status`, passo novo antes de `_atualizar_entidades`). A lista é limpa a cada partida.
- **Onde cada efeito age:** tabela em `docs/architecture.md`.
  - Atordoamento: o `Game` não chama o `update` do inimigo nem as armas do jogador; o jogador ignora o input; `inofensivo`; espinhos, aura do MK2, veículo e aura de energia do dono param.
  - Queimadura: dano `STATUS` (tipo novo do `Dano`) a cada 0,25 s, ignorando os i-frames sem ligá-los.
- **Bosses e minibosses (item 8):** as 19 classes das pastas `bosses/` e `minibosses/` declaram `IMUNIDADES_CHEFE` (sem atordoamento e lentidão de fora); um teste varre as pastas. O stun próprio do Scarab e do Hunter não muda.
- **Cegueira:** buraco com degradê em cache por raio (no máximo 8 raios) + 4 `fill` pretos; desenhada no `_draw_mundo` (vale na pausa e no level-up), por baixo do HUD. Zero alocação por frame (teste).
- Testes: `test_status.py` (78); `test_eventos.py` ganhou o passo novo na ordem do update. Suíte: **994 verdes + 1 xfail**. Golden e catraca inalterados (sem efeito, todos os multiplicadores são exatamente 1.0).

**Desempenho** (na bateria): A/B alternado com o commit anterior, 2 rodadas: horda 4,1–6,1 × 4,2–4,3 ms/frame; Warden 3,4 × 3,5. Sem piora. Pior caso medido à parte: 150 inimigos com 4 efeitos cada (2 queimaduras) = **0,27 ms/frame** no `atualizar_status`.

**Não incluído (decisão sua, se quiser):** indicador de status no HUD e feedback visual no alvo (cor de queimadura, estrelas de stun). Buff de velocidade em boss não tem efeito: os bosses movem-se por código próprio (entra na F5, com a `BossBase`).

**Não validado:** a cegueira na tela real (o degradê e a sensação) e a sensação de jogo de cada efeito: ainda não há arma nem inimigo que os aplique (só as migrações dos próximos commits).

## 2026-11-21 | Correção: névoa do Gravemind pelo contrato de dano
- `MiasmaGas` (fora do raio seguro, 300 por segundo) fazia `vida_atual -= 300` direto: ignorava escudo e veículo, não interrompia a regeneração do escudo e não chamava `kill` (o game over vinha só do `_checar_game_over`). Agora é `receber_dano(Dano(300, AREA, boss, ignora_iframes=True))`: **muda o jogo** (o escudo e o veículo passam a absorver a névoa). Achado na E1; commit próprio (roteiro §2, regra 6).
- Regressão em `test_regressoes.py::test_nevoa_do_gravemind_passa_pelo_contrato_de_dano` (falhou antes da correção). Suíte: **912 verdes + 1 xfail**. Golden inalterado (a fase 0 não tem Gravemind). Não validado no jogo real.

## 2026-11-21 | Etapa E1: contrato de dano único
**Decisões do usuário (desta sessão):** as regras "spawn dentro da navegação" e "portal obrigatório" da D5 **não** serão adotadas (pendência fechada). Novo recurso aprovado: o **sistema de status** (buffs e debuffs), logo depois da E1; decisões no roteiro §8 (itens 8–11).

**O que foi feito**
- `source/systems/dano.py`: `Dano(valor, tipo, fonte, ignora_iframes)` (frozen; valor >= 0, infinito vale, NaN não; tipo conhecido). Tipos: `projetil`, `contato`, `aura`, `area` (novo: explosão, cone, onda, puxão, feixe), `void`, `direto`. `fonte_do_dono(dono, fonte)`: sem fonte explícita, o que é do jogador é dele.
- `receber_dano(dano)` no jogador (mesma ordem de antes: i-frames → veículo → escudo → vida) e nos inimigos, com 2 ganchos: `ajustar_dano_recebido(valor, dano)` (regra do alvo; `None` = ignora o golpe) e `absorver_dano(valor)` (escudo → vida). Os 4 overrides viraram ganchos: Guilty, Hunter, Scarab (que também sobrescreve `absorver_dano`: defensivo = só escudo) e a consciência do Warden.
- `tomar_dano`, `tomar_dano_direto` e `ignorar_invencibilidade` saíram; os espinhos viraram `contra_atacar_com_espinhos`, chamado pelo `CollisionManager` no contato (antes vinham dentro do `tomar_dano`). Os `hasattr(alvo, 'receber_dano'/'tomar_dano')` dos pontos migrados saíram. Migração completa no mesmo commit: sem shims.
- **Fonte:** projéteis, granadas, morteiro, artilharia e cone guardam `fonte`; os 39 ataques inimigos passam `fonte=self` (o projétil que vira artilharia repassa a sua). É o que vai permitir o buff de dano de quem ataca e a atribuição da F3.
- `dano_causado` (`alvo`, `dano`, `valor`) é emitido quando o golpe entra.
- O `import pygame` morto do `player_combat.py` saiu, e com ele a exceção `F401` do `ruff.toml`.
- Testes: `test_dano.py` (52): validação do `Dano`, a matriz escudo × i-frames × `ignora_iframes` × transbordo (jogador e inimigo), ganchos, evento, os 4 overrides, a fonte de projéteis e habilidades e **um teste por AST: todo ataque inimigo passa `fonte=`**. `test_player`/`test_sistemas` migrados para a API nova. Suíte: **911 verdes + 1 xfail**. Golden e catraca inalterados.

**Difere do roteiro:** "invulnerável" não entrou no contrato. Hoje quem respeita `invulneravel` (invisível, proteção de spawn) é quem causa o dano: projéteis e auras checam; **artilharia, cone, companheiro corpo a corpo, atropelamento do veículo e espinhos não** (acertam inimigo invisível). Centralizar mudaria o jogo: decisão sua.

**Achados (não corrigidos)**
- A névoa do Gravemind fazia `vida_atual -= 300` direto (sem escudo, veículo nem `kill`): corrigida no commit seguinte.
- Granada e morteiro inimigos (dano 0 no voo) que encostam no jogador chamam `receber_dano(0)`: ligam os i-frames (100 ms) e interrompem a regeneração do escudo. Verificado com um Spike.
- O golpe letal do Tartarus (`inf`) é absorvido pelo veículo (sem transbordo) e bloqueado pelos i-frames, se cair na janela de 100 ms.
- Loader de mapa: na camada `Colisoes`, elipse vira o retângulo em volta dela (8 no mapa 0) e ponto vira 4 segmentos de comprimento zero (4 no mapa 0).

**Desempenho** (**na bateria**): a rodada completa acusou Knight e Warden (p95) e a troca de fase (esperada desde a D2). A/B alternado com a D5 (worktree), 2 rodadas: Knight 1,65–1,81 × 1,64–2,06 ms/frame (p95 4,0–4,5 × 4,1–4,7; na 2ª rodada, iguais); Warden 3,5–3,6 × 3,6 (p95 8,5–9,0 × 8,8–9,1); horda 4,2–5,5 × **4,0–4,2**. Sem piora.

**Bug do Hunter preso (C1), diagnóstico desta sessão, não reproduzido:** a camada `Colisoes` já tem polígonos fechados, mas o código só usa as arestas (que empurram); o Hunter usa o raio padrão de colisão com o mapa (15 px), apesar do sprite enorme. Se o centro nascer dentro de um polígono, as arestas o empurram para dentro. Correção provável no código, sem editar o Tiled: "dentro do polígono → sai pela aresta mais próxima" + spawn longe das paredes. Fica para depois do sistema de status, com um teste `xfail` primeiro.

**Pendências:** a decisão sobre "invulnerável"; regravar `perf_base.json` (na tomada, sessão fria); o bug do fim de campanha (xfail, B4); o Hunter preso (acima). Próximo: correção da névoa do Gravemind e o **sistema de status**.

## Resumo comprimido (2026-11-21): base, blocos A–D e correções
Detalhes completos no histórico do git (`git log -p docs/log.md`).

**Feito**
- Base: docs (`CLAUDE.md`, `docs/`), suíte `tests/`, todos os bugs conhecidos de então corrigidos (granada, Crawler/Soldier, MRO de Gravemind/Didact, Fuel Rod mirando nos itens, Warden, ranking em `%APPDATA%` no exe), roteiro e tag `base-reformulacao` (A0).
- **A** (medição): `tools/perf.py` (A1), catraca de alocação (A2), golden master da fase 0 (A3), código morto apagado + `ruff` só regras F + teste de import de todo módulo (A4).
- **B** (núcleo): passo fixo 1/60 com teto de 5 passos (B1); estados com tabela `TRANSICOES` e registro único de telas (B2); `SessaoJogo` recriada a cada partida, relógio zerado por partida (B3); passos nomeados do `Game.update` + barramento `eventos` (B4).
- **C** (desempenho): `GradeParedes` de 128 px, que também corrigiu o bug do inimigo longe do jogador atravessar paredes (C1); broadphase por `collidelistall` (C2); máscaras em cache, `camada_alpha`/`rascunho`, partículas com teto de 2000 (C3); culling e HUD em cache (C4).
- **D** (dados): `MANIFESTO` de assets com equivalência de pixels (D1); fundos de fase sob demanda, LRU de 2 (D2); import sem efeito colateral, `carregar_assets()` explícito (D3); `INIMIGOS`/`PerfilInimigo` com golden de equivalência por classe (D4); `validar_tudo()` (D5).
- Correções avulsas: HUD usava `get_ticks` (A2); tela de colaboradores (`self.imagem` → `self.image`).

**Base de desempenho da A1 (para a tabela final da H2)**, ms/frame na tomada: horda_150 33,2 (p95 46,5); fase0 5,3; Guardian 11,5 (p95 34,1; custo no draw); Warden 6,8; Gravemind 5,6; outros bosses 2,0–4,8; troca de fase 1,2; import 4,2 s; pico 781 MB. **Depois do bloco C:** horda 4,4–4,6 (p95 6,2–6,6); Guardian 3,4–4,0; fase0 1,6–1,8; alocações da horda 20 → 0,02/frame. **Depois da D2:** import 1,5 s, pico 379 MB, troca de fase 120–140 ms (decodifica o mapa; roda com a tela preta, esperado).

**Medição:** na bateria nada vale; na tomada o ruído entre sessões chegou a 70% no próprio HEAD (B2–C4). Etapas validadas por A/B alternado com o commit anterior (worktree).

**Decisões que valem até hoje**
- C1: margem da grade 128 px (64 falhou na equivalência do jogador). C2: sem `GradeEntidades`; a busca de alvo das armas custa 0,04 ms/frame. C4: sem camadas estáticas no HUD.
- D5: "spawn dentro da navegação" e "portal obrigatório" **não** viram regra (decisão do usuário na E1); `Navigation` só serve ao teleporte do Knight/Zealot.
- Catraca: Gravemind com teto 0,7 (máscara por frame da animação de respawn, F2/F5); na suíte completa mede 0,48 e avisa (esperado).

**Achados não corrigidos**
- `OndaEMP.draw` sem deslocamento chama `camera.aplicar_posicao` (não existe; o ramo não roda).
- `Sentinel.animar` passa o frame do cache sem copiar: o alpha de um Sentinel vale para todos no mesmo frame.
- Limite do ruff: exceção por arquivo × regra (um 2º `F401` num arquivo já listado passa).
- Catraca não conta métodos em C (`Surface.copy`, `convert_alpha`, `Font.render`).
- C2: inimigo que surge ou se move durante a passada de colisão só é visto pelos projéteis no frame seguinte.

**Não validado no jogo real (acumulado):** sensação abaixo de 12 FPS (câmera lenta pelo teto de passos), aparência de partículas/itens/granada/raio do Watcher (C3), HUD e culling (C4), pausa da troca de fase e 1ª partida depois de game over numa fase alta (D2), executável (D3), menus pelo teclado (B2).
