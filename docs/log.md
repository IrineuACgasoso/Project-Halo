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

## Decisões que valem até hoje
- Balanceamento é do usuário: números "estranhos" são propositais (Hunter 120 de vida, Zealot 100, Guilty, Scarab, Energy Sword).
- `min_val` bate exato no nível máximo; raridade define máximo (25/20/15/10/5) e peso (40/25/20/10/5).
- Invisível nunca é mirado, mas é atingível. Guilty com barreira não é alvejável. Scarab atravessa paredes.
- "Spawn dentro da navegação" e "portal obrigatório" não viram regra. Sem `GradeEntidades`; grade de paredes com margem de 128 px.
- Medição: só na tomada e por A/B alternado com o commit anterior (ruído de até 70%). Depois do bloco C: ~4 ms/frame nos piores casos.

## Estado do roteiro (`docs/roteiro_reformulacao.md`)
Feitos A–E, F1 (BossBase), F2 (Animador) e F3 (IA de utilidade + memória, só o Arbiter usa); Hunter, Zealot, Guilty e Scarab reformulados (adiantam a F5). **Próxima: F4** (bot jogador).
O Hunter ainda não está na `BossBase`. **Não validado na tela real:** as lutas reformuladas, HUD/culling (C4), o executável (D3) e a pausa da troca de fase (D2).

---

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
