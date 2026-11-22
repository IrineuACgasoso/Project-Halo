# Log entre sessões

Entradas curtas, a mais recente no topo. Quando o arquivo passar de cerca de 300 linhas, comprima as entradas antigas num resumo.

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

## 2026-11-21 | Etapa D5: validação central de dados (bloco D concluído)
**O que foi feito**
- `source/data/validacao.py::validar_tudo()` devolve a lista de erros (vazia nos dados reais; 0,03 s; não inicia o pygame nem decodifica imagem). Cada validador recebe os dados como parâmetro (padrão: os do jogo):
  - `validar_armas`: nome repetido entre armas/companheiros/veículos; stat que não é `WeaponStats`; stat que diminui por nível sem `min_val`; no `ARMAS_REGISTRO`: id × chave, raridade, grupos que existem no `entity_manager`, `NOME_ASSET` com perfil.
  - `validar_spawner`: pools (classes × pesos, peso > 0, classe é `BaseEnemy`, inclusive o `DEFAULT_POOL`); boss nos **3** dicts; horário > 0; cronograma na ordem das fases.
  - `validar_inimigos`: vida > 0, dano >= 0, velocidade > 0; cooldown (mín, máx) inteiros com 0 < mín <= máx (`random.randint`); drop de item conhecido e no formato que `Items.spawn_drop` entende (ele ignora em silêncio o que não entende).
  - `validar_manifesto`: folha que não é `Imagem`, caminho com `\` ou absoluto, arquivo ausente, escala inválida.
  - `validar_mapas`: `.tmj` legível (lido pelo `MapLoader` do jogo, sem a imagem), camadas `Colisoes` e `SpawnPoints` com objetos, spawn do jogador, portal e pontos de spawn dentro do mapa, fase com pool e boss.
- `main.py`: com `MCE_DEBUG=1`, imprime cada erro e o total na abertura.
- Os testes de integridade espalhados saíram (`test_levelup_e_armas.py`: registro, perfil, nomes, `min_val`; `test_sistemas.py`: bosses, cronograma, pools, fase com mapa; `test_assets.py`: arquivos e escalas do manifesto): as regras deles estão na validação, que roda nos dados reais. O smoke de mapas (com o `Mapa` real) continua.
- Testes: `test_validacao.py` (64): dados reais sem erros, validar sem iniciar o pygame, **um caso que falha de propósito por regra** (mapas com `.tmj` sintético em `tmp_path`) e a abertura com e sem `MCE_DEBUG`. Suíte: **858 verdes + 1 xfail**. Golden e catraca inalterados; nada no loop do jogo mudou.

**Desempenho do bloco D (D3–D5)** (na tomada): a rodada completa do `perf.py` acusou horda, Gravemind, Knight, Warden e Scarab, mas também o `draw` dos bosses e a troca de fase (206 ms; 115 ms na D3, na mesma sessão), que D3–D5 não tocam: o mesmo ruído da B2–C4. A/B alternado com a D2 (`4b059f1`, worktree), 2 rodadas, média em ms/frame:
| Cenário | D2 | HEAD (D4.3 = loop da D5) |
|---|---|---|
| horda_150 | 3,8–6,4 | 4,1–4,3 |
| boss_gravemind | 3,3–3,9 | 3,7–4,0 |
| boss_knight | 1,5–1,6 | 1,45–1,6 |
| boss_warden | 3,0–4,1 (p95 8,0–12,0) | 3,2–4,7 (p95 9,1–14,3) |
| boss_scarab | 1,5–1,6 | 1,4–1,5 |
- Sem piora confirmada. O Warden mediu um pouco acima nas 2 rodadas, mas o código dele não usa nada da D4 (só ganha `tabela_drop` ao nascer) e o HEAD sempre rodou depois da D2 em cada rodada. **`perf_base.json` segue sem regravar** (pendência desde a C4).

**Difere do roteiro (decisão pendente, sua):** "spawn dentro da navegação" e "portal obrigatório" **não** viraram regra. Medido nos `.tmj`:
- Pontos de spawn de inimigo fora das zonas `Navigation`: mapa 0 34/35, 1 25/31, 2 25/25, 3 19/41, 4 7/23, 5 5/22, 6 14/28, 7 5/27 (o 8 tem a camada vazia: tudo vale).
- Spawn do jogador fora da navegação no mapa 2; portal fora dela no mapa 7. Os mapas 1, 6 e 8 não têm `SpawnPlayer` nem `Portal`: o jogo usa o centro do mapa, que está na navegação (1 e 6) ou num mapa sem navegação (8).
- No código, `Navigation` só decide onde o Knight e o Zealot podem teleportar/invocar (`verificar_posicao_valida`); o spawn de inimigos não a consulta. Exigir as regras faria `validar_tudo()` acusar os mapas reais. Se a intenção é que valham, é preciso editar os mapas no Tiled (conteúdo) e então ligar as regras.

**Pendências:** a decisão acima (navegação/portal nos mapas); regravar `perf_base.json` (na tomada, sessão fria; absorve a troca de fase da D2); o bug do fim de campanha (xfail, B4); o TODO do Hunter preso nas paredes (C1). Próxima etapa: **E1** (contrato de dano único).

## 2026-11-21 | Etapa D4: dados de inimigos (um commit por família)
**O que foi feito**
- `source/data/enemy_data.py`: `PerfilInimigo` (dataclass frozen: `vida`, `dano` de contato, `velocidade`, `cooldowns` nome → (mín, máx) ms e `drops` no formato dos kwargs de `Items.spawn_drop`) e `INIMIGOS` (nome → perfil). As tabelas são `MappingProxyType` (só leitura). Valores de nível 0; a escala por nível continua em `EnemyScaling`.
- `EnemySetup.setup_core` cria `tabela_drop = DROP_PADRAO`, e `EnemyCombat.morrer` usa `**self.tabela_drop`. Os inimigos comuns trocam a tabela e guardam `self.perfil`. Bosses e minibosses sem `morrer()` próprio continuam com a tabela de sempre (teste).
- **D4.1 Covenant** (Grunt ×3, Jackal, JackalSniper, Elite ×3, Brute): os `morrer()` de Elite e Brute eram cópias do da base com outra tabela e saíram; com isso o `F405` de `brute.py` e `elite.py` saiu do `ruff.toml`. A linha solta `self.game` (sem efeito) do Brute saiu.
- **Fica na classe:** sprite, variante, velocidade de animação, projéteis (dano e velocidade do tiro), IA e os primeiros cooldowns fixos (Brute 3000 ms, Elite 4000 ms, FloodMarine 2500 ms): trocá-los por uma faixa mudaria a sequência aleatória.
- **Equivalência:** `tests/golden/inimigos.json`, gravado com os valores antigos antes da troca. Para cada uma das 19 classes comuns: stats logo depois de criada, as faixas pedidas a `novo_cooldown` em 30 s de update perto do jogador e os drops da morte **na ordem** (`spawn_drop` sorteia item por item). Regravar só com `--atualizar-golden`.
- Testes: `test_dados_inimigos.py`: equivalência, perfil imutável, cada classe usa o seu perfil, mudar o perfil muda o inimigo (prova que não sobrou número na classe), perfil sem o cooldown que a classe usa falha ao criar, inimigo sem perfil usa o drop padrão. Suíte: 844 verdes + 1 xfail na D4.1 e **855 + 1 xfail** no fim da D4. Golden e catraca inalterados.

- **D4.2 Flood** (Infection, FloodElite, FloodCarry, FloodMarine): o `morrer()` do `FloodForm` era cópia do da base e saiu; o do FloodCarry continua (solta os Infection) e usa a tabela do perfil.
- **D4.3 Forerunner e Prometheans** (Sentinel, SentinelMajor, Crawler, Soldier, Watcher, SuperWatcher): o `Watcher` recebe `perfil=` no lugar de `vida_base=`/`velocidade_base=` (o SuperWatcher passa o dele). Com isso as 19 classes comuns têm perfil, e não sobrou perfil sem classe (teste).

**Desempenho:** horda 4,1 ms/frame (p95 5,6), na tomada.

## 2026-11-21 | Etapa D3: import sem efeito colateral
**O que foi feito**
- Pré-condição verificada por AST (script fora do repo): fora o próprio `assets.py`, nenhum módulo de `source/` lê `ASSETS` nem chama pygame no import (nível do módulo, corpo de classe, valor padrão de argumento e decorador). A única chamada é `SUPERFICIE_VAZIA` (`utils/superficies.py`), uma `Surface` 1×1 que não precisa de display.
- `feats/assets.py`: saíram `pygame.init()`, a janela oculta e a chamada de `carregar_assets()` do import. `ASSETS` nasce vazio. `carregar_assets()` chama `_preparar_display()`: inicia o pygame se preciso e só abre uma janela oculta (1280×720; sem modo oculto, uma comum) se ainda não houver janela. A global `screen` saiu (ninguém a usava).
- Quem carrega: `main.py` (depois do `set_mode`, então o jogo não abre mais a janela oculta extra), o `conftest` (antes da coleta: `test_smoke_simulacao` lê `ASSETS['maps']` no nível do módulo) e o `tools/perf.py` ("import dos assets" = import + `carregar_assets()`, comparável com as medidas antigas).
- Testes (+5 em `test_assets.py`): num processo novo, importar os 226 módulos de `source/` deixa o pygame e o display sem iniciar e `ASSETS` vazio (o teste falha no código da D2, conferido); carregar sem janela abre uma oculta; carregar com a janela do jogo aberta não troca a janela; driver sem modo oculto cai na janela comum; com janela existente não chama `set_mode`. `main.main()` rodado no driver dummy (com `Game.run` trocado) chega ao menu. Suíte: **828 verdes + 1 xfail**. Golden e catraca inalterados.

**Desempenho** (na tomada): import dos assets 1,3 s (D2: 1,5 s na bateria); pico 379 MB. O `update` e o `draw` não mudaram. `troca_de_fase` segue acusada contra a base, como desde a D2.

**Não validado:** o `main.py` no Windows de verdade (com janela): a ordem nova é janela → assets → `Game`; o executável (PyInstaller) não foi gerado.

## 2026-11-21 | Etapa D2: mapas sob demanda
**O que foi feito**
- `feats/assets.py::MapasSobDemanda` (um `Mapping`): `ASSETS['maps']` decodifica o fundo de uma fase no 1º acesso e guarda só os 2 mais recentes (LRU). `in`, `len` e a iteração consultam o manifesto, sem decodificar; chave inexistente dá `KeyError`, como num dict. Arquivo ausente vira o placeholder da D1.
- `Game.existe_proxima_fase()` lê `MANIFESTO['maps']`, não a imagem.
- Nada desenha sobre o fundo do mapa (verificado por grep), então a superfície do cache pode ser reaproveitada entre partidas.
- Testes: +10 em `test_assets.py`: consultar chaves não decodifica, 1º acesso decodifica e reaproveita, LRU (inclusive o acesso que renova a recência), limite 1, limite inválido, `KeyError`, mapa ausente, e uma partida real (nova partida decodifica só o mapa 0; `existe_proxima_fase` não decodifica; 2 trocas de fase deixam só os mapas 1 e 2). A equivalência da D1 continua verde (os fundos decodificados sob demanda saem iguais). Suíte: **823 verdes + 1 xfail**. Golden inalterado; catraca inalterada.

**Desempenho** (A/B alternado com a D1, worktree, `perf.py --cenario troca_de_fase`, 2 rodadas; **na bateria**)
| | D1 | D2 |
|---|---|---|
| import dos assets | 2,5–2,6 s | **1,5 s** |
| pico de memória (só a troca de fase) | 562 MB | **379 MB** |
| troca de fase | 1,6–1,9 ms | **120–140 ms** (máx 200) |
- A troca de fase ficou mais cara de propósito: a decodificação saiu do import e foi para ela (56–185 ms por mapa; o JPG de 4608×3072 é o mais lento). Ela roda com a tela toda preta (`fade_alpha == 255`), e o passo fixo absorve o quadro longo (no máximo 5 passos de recuperação). O `perf.py` acusa `troca_de_fase` contra a base (1,56 ms): **esperado**, até a base ser regravada.
- Os outros cenários não foram medidos: a D2 não toca o `update` nem o `draw` (o mapa é criado fora do cronômetro), e na bateria a medida não vale.
- Suíte na bateria: 130 s, contra 64 s na rodada da D1 (energia não registrada). `test_grade_paredes.py` levou o mesmo tempo nos dois commits (A/B: 14,5–15,6 s), então a diferença é a energia, não a D2.

**Não validado:** a sensação da troca de fase no jogo real (a pausa cai no quadro preto) e o início de uma nova partida depois de um game over numa fase alta (o mapa 0 pode ter saído do cache: +~185 ms ao começar).

**Pendências:** regravar `perf_base.json` (na tomada, sessão fria) — agora também para absorver a troca de fase nova; o bug do fim de campanha (xfail, B4); o TODO do Hunter preso nas paredes (C1). Próxima etapa: **D3** (import sem efeito colateral).

## 2026-11-21 | Etapa D1: manifesto de assets
**O que foi feito**
- `source/data/manifesto_assets.py`: `MANIFESTO`, com o mesmo formato de `ASSETS` (dicts e listas) e uma `Imagem(arquivo, escala, alpha, espelhar)` em cada folha. Ajudantes `quadros(pasta, nomes, escala)` e `numerados(prefixo, fim, inicio)` para as sequências de quadros; os nomes fora de padrão (`guilty.png`, `clone2/clone/clone3`, `super.png` 2×, Hunter com 2 escalas) ficam explícitos. Módulo só de dados (sem pygame).
- `feats/assets.py`: as 251 linhas literais viraram `carregar_imagem(imagem)` e `carregar_assets()`, que preenche **o mesmo dict** `ASSETS` (os `from ... import ASSETS` continuam valendo) e é idempotente. Ainda roda no import (a D3 tira). Arquivo ausente ou ilegível vira um placeholder magenta do tamanho pedido (64×64 sem escala) e um aviso no console, uma vez por arquivo.
- O jogador espelhado (`player.left`) agora é `espelhar=True` no manifesto (antes, `flip` da lista da direita). `player_right_frames` saiu (ninguém o importava). A exceção `F405` do `assets.py` saiu do `ruff.toml`.
- **Equivalência:** `tests/golden/assets.json` foi gravado **com o código antigo**, antes da troca: cada superfície vira `LxA bits alpha|opaco crc32-dos-pixels`. As 248 superfícies saíram idênticas pixel a pixel. Regravar só com `--atualizar-golden`, quando a arte mudar de propósito.
- Testes: `test_assets.py` (14): equivalência, todo arquivo do manifesto existe, a estrutura de `ASSETS` espelha o manifesto, idempotência (zero `image.load` na 2ª chamada), espelhar, opaco sem alpha, ausente (com e sem alpha, log uma vez) e ilegível viram placeholder. Suíte: **813 verdes + 1 xfail**. Golden inalterado; catraca inalterada.

**Desempenho:** o jogo em execução usa as mesmas superfícies (pixels idênticos), então só o import foi medido. A/B alternado com o HEAD (worktree), 3 rodadas: HEAD 3,4–4,6 s × D1 3,0–4,7 s. Sem diferença.

## 2026-11-21 | Etapa C4: render (bloco C concluído)
**O que foi feito**
- **Culling** (`Renderer._sprites_visiveis`): só ordena e desenha o sprite de imagem cuja imagem toca a tela (caixa da imagem, não do rect, com folga de 2 px para o arredondamento do blit). Sprite com `draw` próprio sempre entra: o rect dele nem sempre cobre o que desenha (artilharia e aviso de laser têm rect 1×1), e esses efeitos já se recortam sozinhos desde a C3. Sprite quebrado continua entrando, para o erro ser logado como antes.
- **HUD** (`hud_draw.py`): uma `Surface` reaproveitada por barra (`_camada_barra`), redesenhada só quando a largura ou a cor muda; fundo dos slots (um por cor) e do placar em cache (`_FUNDOS`); texto renderizado só quando muda (`_texto`, por lugar do HUD: nível, XP, timer, placar, nível de cada slot, nome do boss). A variável morta `fill_rect` saiu, e com ela a exceção `F841` do `hud_draw.py` no `ruff.toml`.
- **Decisão (difere do roteiro):** sem camadas estáticas pré-renderizadas. O HUD inteiro custa ~0,2 ms/frame (profiler), e o fundo e a borda das barras ficam um abaixo e o outro acima do preenchimento: seriam 2 camadas para ganhar centésimos de ms (regra 7).
- **Equivalência:** (1) teste permanente: o mundo desenhado com e sem culling é idêntico pixel a pixel numa horda de 150 com tremor de câmera (12 quadros, mais de 100 sprites cortados); (2) checagem única (script fora do repo): o HUD antigo (`git HEAD`) e o novo saíram idênticos em 1200 estados aleatórios (vida, escudo, XP, veículo, timer, placar, armas e níveis, barra e escudo de Hunter, Guardian e Warden), com o cache frio e quente.
- Testes: `test_render.py` (13): culling (fora, borda, imagem maior que o rect, `draw` próprio, sem imagem), equivalência do culling, **draw parado = zero `Surface` e zero `Font.render`** (com e sem boss), texto renderizado de novo só quando o valor muda, barra reaproveitada, `_erros_logados` vazio. Suíte: **798 verdes + 1 xfail**. Golden inalterado.

**Catraca (alocações/frame):** fase 0 8,0 → **0,0**; horda 8,0 → 0,02; bosses ≤ 0,06, menos o Gravemind (0,64: máscara da animação de respawn, F2/F5). Tetos em 0,1 (o mínimo pela regra de arredondamento) e 0,7 no Gravemind. O aviso "baixe o teto" só dispara se o teto puder mesmo descer. **Esperado:** na suíte completa o Gravemind mede 0,48 (caches de partícula já quentes) e dá o aviso; isolado mede 0,64, então o teto fica em 0,7.

**Desempenho:** a rodada completa acusou Knight e Warden (p95) e saiu ruidosa (o `update`, que a C4 não toca, subiu até 16%). A/B alternado com a C3 (worktree): `draw` 0,1 a 0,3 ms menor em todos (Zealot 1,05 → 0,91; Guilty 1,28 → 1,14; Warden 2,7 → 2,4); Warden em 5 pares: média 3,4–3,7 × 3,4–4,1, p95 9,8–10,8 × 8,1–10,7 (sem piora confirmada); Knight dentro do ruído.

**Bloco C × base da A1** (rodadas completas desta sessão, na tomada): horda 33,2 → **4,4–4,6** ms/frame (p95 46,5 → 6,2–6,6); Guardian 11,5 → 3,4–4,0 (p95 34,1 → 4,7–6,4); fase 0 5,3 → 1,6–1,8; alocações da horda 20,0 → 0,02/frame.

**`perf_base.json` não regravado:** a máquina esteve ruidosa a sessão toda (B2–C4). A base atual esconde regressões de até ~50% na horda e no Guardian (o p95 caiu mais que isso). **Pendência:** regravar com `--gravar-base` numa sessão fria, na tomada, antes da próxima etapa de desempenho.

**Não validado:** a aparência do HUD e do culling no jogo real (a equivalência de pixels cobre a lógica, não a tela de verdade).

**Pendências:** regravar a base do perf (acima); o bug do fim de campanha (xfail, B4); o TODO do Hunter preso nas paredes (C1). Próxima etapa: **D1** (manifesto de assets).

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
