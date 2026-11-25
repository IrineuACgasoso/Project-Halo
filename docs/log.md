# Log entre sessões

Entradas curtas (3 a 8 linhas), a mais recente no topo. O detalhe de cada entrega antiga está no git (`git log -p docs/log.md`).

## Pendências e bugs conhecidos
- `xfail`: fim de campanha e morte no mesmo update pontuam em dobro (`test_sistemas`).
- Granada e morteiro inimigos encostando no jogador dão `receber_dano(0)` (i-frames e regeneração do escudo).
- Golpe letal do Tartarus é absorvido pelo veículo. "Invulnerável" ainda não faz parte do contrato de dano (decisão do usuário).
- Elipse/ponto em `Colisoes` viram retângulo/degenerado. Hunter pode prender em parede. `OndaEMP.draw` sem deslocamento chama método que não existe (ramo morto).
- Árbitro companheiro no nível 1 nunca acerta alvo parado (orbita a 64 px, golpe exige < 60).
- Veículo é atualizado 2× por passo (hoje inofensivo). `shake` é "o último ganha".
- Sem indicador de status no HUD. `perf_base.json` precisa ser regravado numa sessão fria.
- Partida com cheats entra no ranking sem marca.
- `xfail`: o atirador do Warden escolhe um ponto atrás da parede e fica preso em `reposicionando`, sem atirar (`test_sistemas`).
- O Tartarus ainda tem o salto próprio; a skill `salto` generaliza o dele (migrar na F5).
- Corpo invulnerável ainda é `alvejavel`: as armas gastam tiros na consciência do Warden e na Harbinger em recarga se for o alvo mais perto.

## Decisões que valem até hoje
- Balanceamento é do usuário: números "estranhos" são propositais (Hunter 120 de vida, Zealot 100, Guilty, Scarab, Energy Sword).
- `min_val` bate exato no nível máximo; raridade define máximo (25/20/15/10/5) e peso (40/25/20/10/5).
- Invisível nunca é mirado, mas é atingível. Guilty com barreira não é alvejável. Scarab atravessa paredes.
- "Spawn dentro da navegação" e "portal obrigatório" não viram regra. Sem `GradeEntidades`; grade de paredes com margem de 128 px.
- Medição: só na tomada e por A/B alternado com o commit anterior (ruído de até 70%). Depois do bloco C: ~4 ms/frame nos piores casos.

## Estado do roteiro (`docs/roteiro_reformulacao.md`)
Feitos A–E, F1 (BossBase), F2 (Animador), F3 (IA de utilidade + memória, só o Arbiter usa) e F4 (bot e métricas); Hunter, Zealot, Guilty, Scarab e Arbiter reformulados (adiantam a F5). **Próxima: F5** (migração, um commit por boss; começa por Tartarus).
O Hunter ainda não está na `BossBase`. **Não validado na tela real:** as lutas reformuladas, HUD/culling (C4), o executável (D3) e a pausa da troca de fase (D2).

---

## 2026-11-25 | Arbiter: combo cadenciado, recuo com escolta e VFX de plasma
- **Combo:** sem o dash "simples"; os 4 golpes são artilharia, cone para trás (agora o da investida, `arbiter_combo_reverso` saiu), cruz e o corte frontal do salto, sem repetir o anterior. Cada dash prepara (220–320 ms), a cruz sai quando ele passa pelo meio do caminho e ele fica na pose até o golpe estourar.
- **Dashes mais lentos** (alcance mantido): combo 600 (~870 com a Fúria), investida 720, esquiva 900.
- **Escudo:** volta após 3,5 s sem dano, com faíscas, pisque azul enquanto enche e clarão ao encher. **Recuo:** melhor rumo com chão num leque, puxado para os Elites, ×1,3; esquiva na diagonal para trás. **IA:** escolta viva soma até 0,6 à nota de recuo.
- **VFX:** tiros do Phantom caindo em cada ponto do bombardeio (`purge_grid/disparo.py`); explosão da granada de plasma em camadas com plasma estourando, para jogador e inimigos (`artilharia/plasma.py`); carabina como gota girada (acerto continua o círculo antigo). Tudo visual no grupo das partículas.
- Balanceamento do usuário mantido (Phantom, cruz 90 px, frontal 180×450, flanco). Golden do Arbiter regravado (mudança declarada). `lutas --boss arbiter`: 25 s, 2,3 vidas/min.
- **Não validado:** a luta e os VFX na tela real (só capturas headless), áudio, balanceamento.

## 2026-11-25 | Arbiter reformulado e skill de salto
- **Skill `salto`** (`feats/skills/salto/`): arco com alvo jogador/ponto/aleatório, altura, duração, recuo e invulnerável opcional; no ar é `no_ar` (não alvejável, `alvejavel` lê), inofensivo e passa por cima das paredes; pousa sempre em chão válido. Base: `no_ar`/`altura_z` nos inimigos. `ConeStrikeAviso(seguir=...)` e modo `linha_jogador` no Purge Grid.
- **Arbiter:** escudo regenerativo (4 s sem dano); 2 fases (40%: sem carabina nem invocação, +20% de velocidade, recua menos, aura). Rotinas: carabina (6 tiros 40 px), granada (`arbiter_plasma_grenade` 120/230), lâmina, investida com cone que viaja junto e costas expostas (×2) no atordoamento, salto + corte frontal (também o anti-stuck), emboscada no flanco. Reações: combo da quebra de escudo (grito + 5 dashes sorteados + Fúria) e esquiva lateral com spray camuflado (45%). Fora da rotina: Phantom (linha roxa no jogador) e 2 Elites camuflados.
- **IA:** a vida do jogador puxa para a espada e encurta a faixa; sem escudo, a postura avanço/recuo vem de vida dele + jogador longe − jogador fraco (com histerese).
- **Decisão minha:** os dashes do Arbiter não dão dano de contato (o corpo de 250 px encostava a 150 px: o combo dava 20 golpes por luta); quem fere é a espada.
- **Golden do Arbiter regravado** (mudança declarada) e sem contar partículas (só visuais, sorteio próprio: deixavam o golden instável). `lutas --boss arbiter`: 24 s, 2,7 vidas/min do bot (era 1,1).
- **Não validado:** a luta na tela real (só capturas headless), áudio, balanceamento de todos os números novos.

## 2026-11-25 | F4: bot jogador e métricas das lutas
- **`tests/bot.py`:** `FonteEntrada` que mantém distância e esquiva; só vê a tela, reage em 200 ms, decide a cada 100 ms, sem sorteio (mesma seed, mesma luta: conferido no Arbiter e no Gravemind). Não esquiva feixe, EMP nem efeito próprio de boss e não planeja caminho.
- **`tools/lutas.py`:** arsenal e nível fixos por fase, jogador blindado; golpe letal encerra a luta. `--boss` dá o uso das habilidades; `--parado` é a referência. Fora da BossBase, "uso" = entrada num estado.
- **Base (3 seeds; tempo · vidas de 500/min do bot × parado · tiros que acertam o bot):** hunter 42 s · 2,7×6,9 · 4% | zealot 44 · 7,3×16,8 | guilty 152 · 5,8×12,6 · 18% | scarab 31 · 1,7×4,0 · 18% | arbiter 24 · 1,1×34,9 · 0% | tartarus 26 · 4,8×68 · 90% | gravemind 67 · 2,3×29 (parado morre) · 0% | knight 2 · 0×0 | didact 42 · 10,8 (parado morre no void) · 100% | warden 14 · 5,4×55 · 33% | guardian 2 · 2,6×1,7 | jega 13 · 1,1×13 · 0% | escharum 11 · 0×55 | harbinger 55 (2 de 3) · 0,9×0,5 · 0% | atriox 10 · 4,1×63 · 33%.
- **Uso de habilidades (por luta):** arbiter granada 2 (83% ferem), carabina 1,7, furtivo 1, invocação 1; tartarus hammer_run 3,7, salto 3, brutes 2; hunter burst 5,3, cannon 4, run 3; didact laser 9, crypt 1; os demais: rode a ferramenta.
- **Achados (para o usuário):** Knight e Guardian caem em 2 s, o Knight sem atacar; Jega, Escharum e Atriox em 10 a 13 s: a vida deles não acompanha o arsenal da fase na régua. O laser do Didact acerta sempre. Harbinger: grunts da recarga presos atrás de parede travam o fim da recarga (o bot não vai buscá-los). Bug do atirador do Warden: ver pendências.
- **Não validado:** se a régua parece uma partida real; nenhum código do jogo mudou.

## 2026-11-25 | F3: IA de utilidade e memória adaptativa dos bosses
- **`base/boss/decisao.py`:** boss com `HABILIDADES` (nome → `Habilidade`) escolhe por nota: peso × distância × `pontuar_<nome>(ctx)` × repetição × memória. Uma claramente melhor vence; entre as próximas, sorteio. Nota fraca espera até 2 s.
- **Memória:** dano por uso de cada habilidade nesta luta (fator 0,6 a 1,5, com esquecimento). `Dano.habilidade`: tiro e área guardam a da criação, e o que explode depois (granada, morteiro) a herda. Contato não conta.
- **Contexto:** `parado_ms` e `afastamento`. `eventos.cancelar`: o boss solta o barramento no `kill`.
- **Arbiter** usa notas: granada em quem para, tiro e emboscada em quem foge, invocação conforme a escolta (antes, prioridade absoluta). Zealot, Guilty e Scarab seguem com os pesos próprios.
- **Golden do Arbiter regravado** (mudança declarada). Uso em 60 s parecido com o de antes; fases iguais.
- **Fora desta entrega** (plano §3.1): histograma de esquiva e esquiva reativa, para quando um boss da F5 precisar.
- **Não validado:** a sensação da luta na tela real e os pesos (do usuário: `HABILIDADES` em `arbiter/config.py`).

## 2026-11-24 | Fuel Rod incendiário, fogo, quebra de escudo, soco; suíte e docs podados (pedido do usuário)
- **Fuel Rod:** a poça não dá mais dano direto: aplica `Queimadura` (dps = `dot`, renovada a cada 250 ms, 2,5 s depois de sair; `queimadura_ms` no preset). Poças sobrepostas não somam; invulnerável não pega fogo. O impacto continua.
- **Quique:** só quando o alvo morre antes do impacto; aí quica até grudar ou acabarem os quiques (inimigo a ≤ 350 px, senão segue 180 px em frente). Alvo vivo que só fugiu: explode onde caiu. Gota desenhada no código (PNG e entrada do manifesto removidos).
- **Status (correção):** renovar a queimadura antes do tick apagava o dano acumulado (renovada por frame, nunca feria).
- **Fogo** (`status/fogo.py`): pisque laranja/amarelo + chamas sobre o corpo em todo alvo com `Queimadura` (jogador, veículo, inimigos, bosses); camuflado não mostra.
- **Quebra de escudo** (`effects.quebra_de_escudo`): fagulhas azuis e amarelas que caem; jogador (dano e EMP), todo inimigo, escudo físico do Jackal e barreira do Guilty. O Zealot trocou as faíscas próprias pelo padrão (mantém o tremor).
- **Soco Spartan:** o efeito antigo **nunca aparecia** (lia `game.all_sprites`, que não existe). Agora clarão + 68 faíscas no ponto do impacto. `Particula` ganhou `gravidade`; efeito só visual usa sorteio próprio (goldens inalterados).
- **Balanceamento do usuário** (shotgun, sniper, Scarab 2800, cura de level-up = metade). O `min_val` do sniper foi de 9775 para 9750 (a conta exata; 28 testes falhavam por isso).
- **Suíte:** 1953 → 720 testes, 125 → ~40 s na mesma máquina; saíram equivalências, aparência, config inválida, `test_perf_tool`, `test_shims` e os goldens `assets`/`inimigos`. **Contexto por sessão:** CLAUDE.md + docs de ~70 KB para ~5 KB (nada é importado sozinho); `.ignore` para buscas; `BOSS_CREATION.md` apagado.
- Custo do fogo: 3–4 ms/frame com 150 alvos queimando na tela (pior caso irreal; ~0,03 ms por alvo).
- **Não validado:** a sensação na tela real (conferi por capturas headless) e o balanceamento da queimadura.
