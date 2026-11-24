# Log entre sessões

Entradas curtas, a mais recente no topo. Quando o arquivo passar de cerca de 300 linhas, comprima as entradas antigas num resumo.

## 2026-11-24 | Scarab reformulado, zoom da câmera e knockback (muda o jogo, pedido do usuário)
- Sobre a `BossBase` (adianta o Scarab da F5): `config.py` (todos os números), `corpo` (desenho em camadas), `recortes`, `patas` (dano por ângulo), `movement` (passos, virar), `armas` (feixe, torreta, desembarque), `feixe`, `states`, `attacks` (stomp, sísmica, queda, colapso), `vfx`. Vida 5000 (era 15000 + 5000 de escudo, com ×5/×10).
- **Patas:** 3 ângulos a partir do centro do chão (frente ±38°, central ±26°, traseira ±26°), cada pata com 300 de vida (escala com a dele). Fora deles, 4% passa pela carapaça. Pata zerada → desaba, núcleo aberto por 7 s (dano ×4 de quem está atrás, ±75°; ×1 fora) → se ergue, regenera **só** a pata quebrada. A pata alcançável pulsa em vermelho e cada uma tem barra no pé.
- **Por baixo:** sem dano de contato; `y_desenho` (novo no `Renderer`) faz ele cobrir o jogador. Com o jogador a ≤ 320 px do centro do chão ele repousa: não anda, não vira, não anima. Passa por cima das paredes (decisão minha: era onde prendia), só não sai do mapa.
- **Golpes:** passo (2 artilharias presas aos pés, mesma duração da pata no ar: pousa no frame do estouro), body stomp (peso 10 × 2 de esperar, senta no estouro), sísmica (2,2 s colado numa pata; a artilharia persegue a 330 px/s e trava nos últimos 250 ms).
- **Armas autônomas** (só a queda e a morte desligam): feixe verde em camadas com barreira mínima de 320 px (quem está por baixo não leva dano), torreta igual à antiga, desembarque de 3–5 (teto 12, 18% de orbe de vida). **Decisão minha:** o canhão de cima virou camada própria e gira sozinho para o lado do alvo; o feixe sai da ponta fina do cano.
- Fase crítica (30%): fumaça, arcos, torreta 2×, feixe mais rápido. Morte: `morrer` adia 2,5 s de explosões em cadeia e detona (artilharia de 820 px com aviso).
- **Arte:** 93 recortes em `scarab/partes/` derivados dos sprites do usuário (o de pé remonta o original pixel a pixel, há teste): patas danificadas, caído com núcleo e sentado, nas 3 variantes. Os sprites inteiros antigos saíram do manifesto (os PNGs continuam na pasta). `assets.json` regravado por isso.
- **Câmera:** `definir_zoom(alvo, ms)`, `visao`, `restaurar_zoom` (fase e partida nova). O mundo é desenhado numa superfície maior e reduzido (`utils/reducao.py`, vizinho mais próximo). O tijolo passou a rebater na borda do que aparece. Scarab: 0,5625 (2276×1280).
- **Artilharia:** `knockback` (False ou px) sobre `systems/empurrao.py` (novo: jogador e comuns, sem atravessar parede; boss não se move).
- O `contar_alocacoes` deixou de contar `scale`/`smoothscale` com superfície de destino (não criam nada), com teste.
- Testes: `test_scarab.py` (136), `test_camera.py`, `test_empurrao.py`; 18 mutações conferidas. Saíram 3 casos do Scarab antigo de `test_dano` (mudança de especificação). `test_validacao` lê o `increase` da Energy Sword em vez de +200 (balanceamento do usuário). 4 exceções saíram do `ruff.toml`. **Suíte: 1953 verdes + 1 xfail.** Goldens da fase 0 e do Arbiter e catraca inalterados.
- Desempenho (na tomada, A/B alternado com o HEAD, 2 rodadas): boss_scarab 2,24/1,83 × 5,13/5,43 ms/frame (p95 3,2/2,7 × 6,4/7,3: é o zoom; `smoothscale` daria ~11); fase 0 1,37/1,47 × 1,31/1,33; arbiter 1,34/1,37 × 1,48/1,30; horda 4,83/4,64 × 7,39/4,87 (a 1ª foi ruído: update sem mudança).
- **Bots** (3 arsenais de nível 14–20): 70–195 s, 4–8 quedas. **Não validado:** a luta na tela real (sensação, legibilidade com o zoom, tremores). Conferi por capturas headless.

## 2026-11-24 | Armas: Energy Sword, Fuel Rod, ícones e balanceamento do usuário (muda o jogo)
- **Energy Sword (bug do dano infinito, corrigido):** a lâmina perfura infinito e não lembrava quem já acertou, então batia no mesmo alvo **a cada frame** (60×/s por lâmina). Agora cada lâmina acerta cada inimigo 1× por volta (`GRAUS_ENTRE_ACERTOS`). Medido num alvo parado, por ativação: nível 1, 350 → 10; nível 5, 11300 → 350; nível 10, 26800 → 1000. Também: o rect e a máscara ficavam na orientação do spawn; agora giram com a arte. Invulnerável não gasta o acerto da volta.
- **Fuel Rod:** projétil e área próprios (eram os da granada de plasma). `FuelRodGrenade` herda de `GrenadeBase`: gota achatada de plasma que acompanha a curva do voo, halo pulsando e rastro. `PocaDePlasma` (`artilharia/poca_plasma.py`): clarão, respingo e poça fervendo (8 quadros, por baixo dos sprites), vapor e esfriamento; some o projétil quando explode. Preset `fuel_rod`. **Números e mecânica iguais** (raio 150, 1,5 s grudada, arco, quique): só o visual mudou.
- **Ícones:** toda arma do registro tem um (há teste). `light_rifle.png` já existia e só não estava no manifesto; os outros 9 (tijolo, sniper, pistola, metralhadora, punho, dizimator, fuel rod, jipe e aeronave) são pixel art **original** 64×64, não cópias de imagens do Halo.
- **Balanceamento do usuário:** armas (`weapon_data.py`), flood elite e carry, pools das fases 2 e 3, Guilty (vida 800, contato 20, fases em 80% e 30%: a fase 2 pede 10 acertos da luz).
- **Conferência dos dados:** o Assault Rifle (−20) passava do piso 320 e travava: `min_val` 260. O `duracao` da Energy Sword (+200, `range_val=0`) nunca subia: `range_val=1`. Regra nova em `validar_armas`: label + increase com `range_val` vazio é erro.
- Goldens: `inimigos.json` (só flood elite e carry) e `assets.json` (só entradas novas) regravados; `fase0.json` e `arbiter.json` inalterados. Testes do Guilty leem `FASES`/`CFG`. 1 exceção saiu do `ruff.toml`.
- Testes: `test_energy_sword.py` (16) e `test_fuel_rod.py` (18). **Suíte: 1750 verdes + 1 xfail.** Catraca inalterada.
- **Não validado:** a sensação no jogo (a espada ficou ~30× mais fraca: talvez o dano precise subir). A Shotgun chega a 84 projéteis por disparo no nível 20 (+4 por nível); não medi o custo. Conferi o visual por capturas headless.

## 2026-11-24 | Zealot: balanceamento do usuário (muda o jogo)
- Vida 100 (era 250), escudo 300 (500), velocidade 120 (130); cooldowns do combo 4–7 s e do furtivo 6,5–9 s; pausa do combo 0,6–0,85 s e recuperação 0,7 s; fuga a 540 e depois 360 px/s, distância ideal 800 e gatilho do contra-ataque 520 px (260). Dash 550 px/s × 700 ms (1300 × 600) e bote 700 × 800 (1600 × 400).
- **Decisão do usuário:** os números são propositais. O dash alcança no máximo 385 px, então pode parar antes do alvo; parado, ele ainda está no alcance do cone do contra-ataque (480). `VIDA_MINIMA_BOSS['zealot']` 200 → 100 (o mesmo piso do Hunter).
- Testes: os 2 do dash esperavam chegar sempre ao alvo; agora a chegada sai do preset (dentro e fora do alcance) e o cone do contra-ataque precisa alcançar quem ficou parado. Comentários de velocidade dos `config.py` corrigidos. **Suíte: 1710 verdes + 1 xfail.** Goldens e catraca inalterados.
- **Não validado:** a luta na tela real. Pela conta (não simulado): quem perseguir o Zealot logo na quebra do escudo fica a menos de 520 px, e o contra-ataque sai no mínimo de 1,5 s, com ~19% do escudo regenerado.

## 2026-11-24 | Guilty Spark reformulado (muda o jogo, pedido do usuário)
- Sobre a `BossBase` (adianta o Guilty da F5): `config.py` (todos os números), `barreira`, `movement` (ronda e teleporte), `states` (fases e decisão), `attacks` (feixes), `invocacoes`, `armadilha`, `luz_visivel`, `vfx`. Vida 2000 (igual).
- **Barreira:** `EnergyAura` impenetrável + `is_invulneravel` + `ajustar_dano_recebido` (nada entra, nem explosão). `EnergyAura` ganhou `bloqueia_tiros` (tiros morrem na borda; lâmina, tijolo e granada passam) e `empurrao_max` (espremer contra uma parede jogava o jogador para o outro lado). Com a barreira ele **não é alvejável**: as armas miram nas sentinelas (decisão minha, fácil de reverter em `GuiltyBarreira.alvejavel`).
- **Fase 1:** ronda por caminhos que passam a até 170 px do jogador; chuva de sentinelas (até 900 px do jogador, teto de 18 vivas), armadilha (esferas não são inimigos) e feixe de proximidade (≤ 215 px, 250 de dano em 500 ms). 40 sentinelas derrotadas (qualquer uma, contador no HUD) derrubam a barreira e religam o spawner.
- **Fase 2 (60%):** pesos passear 6 × luz 2,5 × laser 1,5; super sentinelas em triângulo (430 px), infestação (5 floods, lentidão de 50% por 3 s) e luz visível (4 em cadeia). Cada acerto da luz nele = 5% da vida máxima; **aos 20% de vida** (8 acertos) a barreira cai e começa a fase 3 (foi a leitura do "limite de 20%").
- **Fase 3:** teleporte → 500 ms parado → laser aprimorado, até morrer. Um golpe nunca pula fase (piso de vida no limiar).
- **Sprites:** azul; vermelha só nos feixes; destruídas na fase 3. A azul destruída não existia: `guilty7.png` foi gerada da `guilty4.png` (vermelhos → azul). Terminal, `guilty_hell_*` do PurgeGrid e os quadros antigos do teleporte saíram do código e do manifesto (os PNGs continuam na pasta). `assets.json` regravado por isso.
- **Materialização:** `materializar()` (preset `materializacao`) para quem nasce invisível. Achado e corrigido: o alpha de uma Sentinel valia para todas (quadro do cache compartilhado).
- **Spawner com boss vivo (correção):** o `Game` nunca lia `permitir_spawns_normais` (só o `Spawner`, que nem era chamado). Agora lê; a recarga do Harbinger passa a religar o spawner como o código dela pretendia (fase 13, sem mapa). O timer continua parado e nunca nasce um 2º boss.
- Testes: `test_guilty.py` (104) no lugar do caso antigo de `test_dano` (mudança de especificação); 16 mutações conferidas. Golden da fase 0 e do Arbiter e catraca inalterados.
- Desempenho (A/B alternado com o HEAD, 2 rodadas): boss_guilty 1,61/1,71 × 3,58/3,15 ms/frame (p95 2,2/2,7 × 6,1/5,1: até 18 sentinelas, feixes e distorção); horda 5,65/7,48 × 5,50/5,84.
- **Não validado:** a luta na tela real (sensação, dificuldade de 40 sentinelas e de acertar a luz). Conferi por capturas headless e bots simples.

## 2026-11-23 | Zealot reformulado (muda o jogo, pedido do usuário)
- Sobre a `BossBase` (adianta o Zealot da F5): `config.py` (todos os números), `setup`, `states` (decisão), `movement` (dash, perseguição, fuga), `attacks` (rotinas), `vfx`. Escudo 500 e vida 250 (antes: 750 de vida, sem escudo), escalados juntos pelo nível do jogador. Vida mínima própria (200) em `test_boss_tem_vida_de_boss`.
- **Com escudo** (pesos por distância): perto (≤ 250 px) só o combo; média (≤ 600) combo 7 × furtivo 2; longe, furtivo 8 × só perseguir 2 (nunca o combo).
  - **Combo:** dash puro → dash + estocada (retângulo 70×460, 350 ms, 220 de dano) → dash + varredura (cone azul de 150°). Todo golpe sai **no vetor do dash**. Pausa de 0,5–1 s entre um dash e o próximo; 0,9 s de recuperação no fim. Parado entre dashes ele é inofensivo (para em cima do jogador: o contato bateria a cada 100 ms).
  - **Furtivo:** invisível a 442 px/s (buff de 240%; o jogador começa com 500). A 200 px, reaparece por 150 ms e dá um bote de 1600 px/s que passa reto. Contorna paredes.
- **Sem escudo:** ao ficar livre (nunca no meio de um golpe), foge invisível: 1,8 s a 650 px/s e depois 416 px/s, sorteando rumos perto da distância ideal (700 px). Regenera tudo em 8 s. Jogador a 260 px (depois de 1,5 s): dash + cone fino e longo, e volta ao ataque com o escudo que tiver; sem escudo no fim do golpe, foge de novo. Escudo cheio: só reaparece.
- **Achado e corrigido:** a arte do Zealot aponta para a esquerda e ele era espelhado ao contrário (`flip_sprite=True`).
- `BossBase` ganhou `mover`/`_ir`/`_dir_mov` (vinham do Arbiter) e `_paredes`; `particulas.emitir_leque` (a poeira do Hunter usa). Golden do Arbiter inalterado nesta parte. A exceção do `zealot/__init__.py` saiu do `ruff.toml`.
- VFX: rastro azul do dash (silhuetas em cache), faíscas nos golpes e na quebra do escudo, camera shake.
- Testes: `test_zealot.py` (61); 8 mutações conferidas (estocada no jogador, sem fuga, sem regeneração, buff preso...). **Suíte: 1600 verdes + 1 xfail.** Catraca inalterada.
- Desempenho (na tomada, A/B alternado com a F2, 2 rodadas): boss_zealot 1,05/1,09 × 1,36/1,32 ms/frame (p95 1,37/1,34 × 2,25/2,26: distorção, rastro e cones); arbiter, jega, hunter e horda iguais.
- **Não validado:** a luta na tela real (sensação da velocidade, se a distorção dá tempo de reagir, balanceamento de escudo × DPS do jogador). Conferi por capturas de tela headless.

## 2026-11-23 | Skills: ataque retangular e dash em subpassos
- `feats/skills/rect_strike/`: `RectStrikeAviso(posicao, direcao, ..., preset)`; `RectStrikeConfig` (dano, `largura` = espessura, `altura` = alcance, duração do aviso, 4 cores). Fundo claro, borda escura e preenchimento escuro que avança **do dono até a ponta**. Atinge quem tem a posição dentro (como cone e artilharia). `no_retangulo` em `utils/vetores`.
- `Dash`: com paredes, anda em pedaços de até 60% do raio de colisão. Um passo ≥ 15 px (900 px/s) caía do outro lado da linha. O dash do Hunter (8 px por passo) não muda.

## 2026-11-23 | Invisibilidade: skill única e regra do jogo (muda o jogo, pedido do usuário)
- **Skill** `feats/skills/invisibilidade/`: `fade_out_ms`, `duracao_ms` (sem contar os fades; `None` = até `encerrar()`), `fade_in_ms`. A máquina `invis_*` da `EnemyCombat` saiu; Elite, Arbiter, Jega e Harbinger migraram para presets com os mesmos tempos. Goldens inalterados nesta parte.
- **Regra:** invisível (fade out e oculto) **nunca é mirado**. Furos fechados: companheiros (inclusive o alvo que some no meio do ataque), veículos, agulha teleguiada do Needler e quique do Fuel Rod. E **não é invulnerável**: tiro perdido, aura e explosão acertam, e ele dá dano de contato.
- `em_teleporte` (novo): Knight e Warden viajando usavam `alpha_atual = 0` como "fora do mundo" e ficariam vulneráveis; seguem como antes.
- Saíram a exceção do Arbiter (`vulneravel_ao_revelar`) e a do Jega (invulnerável na órbita e na ilusão; agora só `inofensivo`, porque atravessa o mapa). O teleporte do Harbinger segue invulnerável (é teleporte, não camuflagem).
- **Distorção:** o `Renderer` recola o cenário ondulando na silhueta de todo camuflado, com um véu claro (senão some em chão liso). 0,08 ms por Elite, 0,16 no Zealot, zero alocação. `silhueta_de` em `utils/superficies`.
- **Golden do Arbiter regravado** (declarado): a 1ª divergência é o contato camuflado. Golden da fase 0 inalterado.
- Testes: `test_invisibilidade.py` (toda arma, companheiro e veículo do registro entra sozinho).
- **Achado (não corrigido):** o Árbitro companheiro no nível 1 nunca acerta alvo parado: estabiliza orbitando a 64 px e o golpe exige < 60 px.

## 2026-11-22 | Etapa F2: Animador (refatoração: golden inalterado)
- `enemies/base/boss/animador.py`:
  - `Clip(ms_por_quadro, quadros=None, loop=True, eventos={})`: frozen e validado; `eventos` = passo do clip -> nome (hit frame);
  - `Animador`: copia cada quadro **no spawn** (o alpha da camuflagem é de cada instância) e usa a máscara do original no cache. Por frame, só escolhe uma dessas superfícies (antes: `Surface.copy` a cada troca de quadro ou de lado).
- **Regras de tempo** (as do `animar` antigo): o quadro troca com **mais** de `ms_por_quadro`. Pedir um clip com a mesma sequência só muda o ritmo, sem reiniciar o passo; sequência diferente ou `tocar(..., reiniciar=True)` recomeçam do 1º quadro, e trocar de clip zera o `terminou`. O evento vale no `atualizar` em que o quadro entra.
- `BossBase`: `CLIPS`/`CLIP_INICIAL` (padrão: todos os quadros a 200 ms), `animar` e `set_sprite_direction` pelo animador (o lado vale no `animar` do fim do frame) e a sub-rotina `_tocar(clip, ate_evento, limite_ms)`. A rotina vê o evento 1 frame depois (o `animar` roda depois dela) e desiste no limite, sem travar a luta.
- Arbiter: os `velocidade_animacao = N` viraram clips no `config.py` (`andar` 200, `parado` 300, `investida` 80, `furtivo` 100, `reaparecer` 80). Nenhum ataque dele tem quadro próprio: o hit frame fica sem consumidor até a F5 (Didact, Gravemind, Jega).
- **Equivalência:** o golden do Arbiter ganhou `quadro`, `lado` e `alpha` da imagem, regravado com o código **antigo** (sem os 3 campos, idêntico ao anterior) e inalterado depois. Mutações conferidas: ritmo do `parado` 300 → 260 e alpha sem passar de um quadro ao outro quebram o golden.
- "Zero alocação no update": a catraca não vê `Surface.copy` (método em C), então o teste é de identidade. Em 20 s de luta, toda imagem e máscara do Arbiter são as do spawn (voltar a copiar quebra o teste).
- `validar_motor_de_bosses`: `CLIPS` = dict não vazio de `Clip` e `CLIP_INICIAL` dentro dele. Os índices dos quadros o `Animador` confere no spawn (a classe não declara o `sprite_key`).
- Testes: `test_animador.py` (45) e 6 casos novos em `test_validacao.py`. **Suíte: 1425 verdes + 1 xfail.** Catraca inalterada.
- Achado na revisão, antes do commit: sair de um clip sem loop já terminado para outro com a mesma sequência (golpe → andar) deixava a animação congelada. Corrigido (trocar de clip zera o `terminou`), com teste.
- Desempenho (na tomada, A/B alternado com o HEAD em worktree, 2 rodadas): boss_arbiter 1,34/1,49 (HEAD) × 1,42/1,52 ms/frame (p95 1,91/2,04 × 1,92/2,19). Igual.
- Nos bosses da `BossBase`, `frame_atual`, `estado_animacao` e `velocidade_animacao` (do `EnemyAnimation`) só valem no spawn; quem lê o quadro usa o `animador`.
- **Não validado:** nada muda na tela (refatoração); o Arbiter na tela real não foi aberto.
- Próxima: **F3** (IA de utilidade + memória).

## 2026-11-22 | Etapa F1: BossBase + ContextoCombate (refatoração: golden inalterado)
- `source/enemies/base/boss/`, extraído do Arbiter:
  - `BossBase(BaseEnemy)`: ciclo do frame (perceber → fase → pensar/avançar a rotina → orientar → mover → animar), rotina ativa (`iniciar`, `finalizar_rotina` e `interromper_rotina`, nova, que fecha o gerador), cooldowns (`cd`, `pronto`, `agendar` com o `mult_cooldown` da fase), `wait`, decisão padrão (anti-stuck > wait > transição > `escolher_habilidade`), `hitbox` padrão (cópia do `rect`), imunidades de chefe e `is_boss`;
  - `ContextoCombate` (1× por frame: distância, velocidade suavizada do jogador, % de vida), `FaseBoss` (frozen, validada; a `FaseArbiter` herda), `ConfigTravamento` + `DetectorTravamento` (o anti-stuck por caminho).
- O boss declara `FASES`, `COOLDOWNS`, `COOLDOWN_INICIAL`, `ESTADOS` (com `rotina_<nome>` para cada um) e `ANTISTUCK`, e implementa `escolher_habilidade`. O Arbiter ficou só com o que é dele (strafe, camuflagem, rotinas, pesos); os mixins vêm **antes** da `BossBase` (o teste de MRO agora considera as duas bases).
- **Equivalência:** golden novo `tests/golden/arbiter.json` (60 s na fase 4, as 3 fases, 5 habilidades), gravado com o código antigo **antes** da extração, e inalterado depois. Ele pega até 0,01 na suavização da mira (mutação conferida). Golden da fase 0 e catraca inalterados.
- `validar_motor_de_bosses` (em `validar_tudo`): fases começando em 1,0 com limiares decrescentes, faixas de cooldown `(min, max)` inteiras e cooldown inicial com faixa. Casos que falham em `test_validacao.py`.
- Testes: `test_boss_base.py` (56) e `test_golden_arbiter.py` (3). A exceção `F401` do `arbiter/movement.py` saiu do `ruff.toml` (o import morto foi junto). **Suíte: 1373 verdes + 1 xfail.**
- Desempenho (na tomada, A/B alternado com o HEAD em worktree, 2 rodadas): boss_arbiter 1,48/1,48 × 1,45/1,40 ms/frame (p95 2,03/2,15 × 2,04/1,90). Igual.
- **Não validado:** nada muda na tela (refatoração); o Arbiter na tela real não foi aberto.
- Próxima: **F2** (Animador). O Hunter e os outros bosses migram na F5.

## 2026-11-22 | Hunter: camera shake nos ataques + balanceamento do usuário (muda o jogo)
- Tremores pelo `camera.shake` existente, intensidades em `HunterConfig` (`shake_burst/slam/canhao`):
  - **burst:** 1, renovado a cada tiro com a duração do intervalo (cobre a rajada e para junto com ela);
  - **slam:** 3, no golpe;
  - **canhão:** 5, na explosão (mesmo com o Hunter morto).
- Os ganchos `ao_explodir` viraram `impacto_do_canhao`/`impacto_do_slam` (`vfx.py`): poeira + tremor.
- **Balanceamento do usuário:** vida 120 (era 800), dano de contato 50, velocidade 65, costas ±40° (era 30°), cooldowns do canhão (6–10 s), do burst (3–7 s) e do dash (7–10 s), intervalo do burst 130 ms.
- **Decisão do usuário:** a vida 120 é proposital. O Hunter virou exceção declarada em `test_boss_tem_vida_de_boss`, com piso próprio de 100. O teste das costas agora lê `CFG.costas_graus` (1° dentro e 1° fora da borda), em vez de 30° fixos.
- Testes: +3 em `test_hunter.py` (o burst treme do 1º ao último tiro e depois para; o slam só treme no golpe; o canhão treme com o Hunter morto). **Suíte: 1292 verdes + 1 xfail.** Golden inalterado.
- **Limite conhecido:** o `shake` antigo vale "o último ganha". Se o morteiro explodir durante uma rajada, o próximo tiro corta o tremor 5 para 1 (no máximo 130 ms depois).
- **Não validado:** a sensação dos tremores e do balanceamento na tela real.

## 2026-11-22 | Hunter reformulado (muda o jogo, pedido do usuário)
- Padrão novo (como o Arbiter, ainda sem `BossBase`): `config.py` (`HunterConfig` frozen: todos os números), `setup.py`, `states.py` (IA, orientação, vulnerabilidade, movimento), `attacks.py` (rotinas geradoras) e `vfx.py`. Adianta o Hunter da F5: falta só migrar para a `BossBase` quando ela existir.
- **Armadura:** `Defesa(90%)` sem fim; **vulnerável** = jogador nas costas, dentro de ±30° do eixo x (`no_cone`, só multiplicações). Vulnerável tira a Defesa e acende o brilho vermelho; sair devolve as duas coisas. **Decisões do usuário:** "vulnerável" = tirar a Defesa (sem debuff novo); o `MULT_COSTAS ×8` saiu (de costas = dano normal, de frente = 10%; vida continua 800).
- **Virar com atraso:** jogador do outro lado inicia um timer de 1,5 s que **não reinicia** com spam; no vencimento ele olha para o lado do jogador naquele instante. Depois do dash, 2,5 s. No dash ele olha para o lado da corrida.
- **IA (sorteio por pesos, nunca determinista):** longe (> 450 px) canhão 5, burst 5, dash 1; perto, canhão 1, burst 1, dash 6, slam 8. Cooldowns sorteados no fim da habilidade + 1 s de pausa entre ataques. Fora do dash, do slam e da recuperação ele anda: avança ou anda de lado (perpendicular, lado sorteado), trocando a cada 1–2,5 s, **inclusive enquanto atira**.
- **Dash:** skill `dash`, preset `hunter` (500 px/s por 2 s, até o fim do tempo), com poeira lateral. Depois, **parado o tempo todo** (decisão do usuário), inofensivo e com a animação congelada durante os 2,5 s do atraso de virar.
- **Shield slam (novo):** jogador a ≤ 230 px e na frente (±45°) → cone de 90° no eixo de frente (preset `hunter_shield_slam`: 150 de dano, raio 300, carga de 1000 ms), parado; poeira na área do cone (`ao_explodir`).
- **Canhão e burst:** os mesmos ataques; a explosão do morteiro solta um anel de poeira (`ao_explodir`).
- **VFX:** silhueta vermelha por frame (4 no total, criadas no spawn), desenhada em `draw_extras` com alpha pulsando (35–105, período de 600 ms). Zero alocação por frame (teste). Poeira em padrões (leque, área do cone) sobre `particulas.emitir`.
- Saíram o `HunterMortarProjectile` (morto: o canhão usa o `CanhaoParabolico`), o `ajustar_dano_recebido` do Hunter e 2 exceções do `ruff.toml`. O `mascara_de(self.image)` do `__init__` (uma cópia entrava no cache de máscaras; a base já pega a máscara do original) também saiu, e a imagem do spawn agora acompanha o lado (antes, ficava no lado da base até o 1º `animar`).
- **Mudança de especificação:** `test_hunter_pelas_costas` (`test_dano`) e `test_fraqueza_e_a_regra_das_costas_do_hunter_se_somam` (`test_status`) testavam o ×8 no stun; viraram os testes de Defesa × costas em `test_hunter.py` (35 testes). `test_mascara_sai_do_cache_com_a_superficie` coleta o lixo antes de medir: o ciclo inimigo ↔ rotina geradora de outro teste era coletado junto e o cache encolhia mais de 1.
- **Suíte: 1288 verdes + 1 xfail.** Golden e catraca inalterados. Desempenho (na tomada, A/B alternado com o HEAD, 2 rodadas): boss_hunter 1,45/1,17 × 1,26/1,26 ms/frame. Igual.
- **Não validado:** sensação e balanceamento (de frente o Hunter aguenta ~10× mais; velocidade 40 mantida, talvez lenta para o andar de lado), o brilho e a poeira na tela real. O bug do Hunter preso nas paredes (E1) continua e pode aparecer mais com o dash.

## 2026-11-22 | Skills: dash, cone sem trigonometria e gancho ao_explodir (base do Hunter novo)
- `feats/skills/dash/`: `Dash(inimigo, alvo, preset|config)` trava a posição do alvo e a direção no início e anda `velocidade × mult_velocidade × dt` por `atualizar(dt, paredes)` (devolve se acabou). `ate_o_alvo=True` para no ponto travado, medido ao longo da direção (deslizar numa parede não teleporta); `False` corre até o fim do tempo. Presets `padrao` e `hunter` (500 px/s, 2000 ms; a run antiga era 500 e 2500).
- `utils/vetores.py::no_cone(origem, eixo, ponto, cos_meio_angulo)`: ponto dentro de um cone só com multiplicações (sem `acos`, `atan2` nem raiz). Teste de equivalência com o ângulo calculado (7 aberturas, 500 pontos cada). O `ConeStrikeAviso` continua com o `acos` dele (não troquei de passagem).
- `ao_explodir` (callback opcional, chamado 1× com o aviso) em `ArtilhariaAviso`, `ConeStrikeAviso` e `CanhaoParabolico` (repassa para a artilharia do impacto). Sem ele, nada muda.
- Testes: `test_skills.py` (13) e `test_core_utils.py` (no_cone). **Suíte: 1255 verdes + 1 xfail** (o lint, que falhou na rodada completa por falta de `__all__` no pacote novo, foi rodado de novo depois da correção). Golden inalterado.

## 2026-11-22 | Sistema de status: buff Defesa (recurso novo, pedido do usuário)
- `Defesa(porcentagem, duracao_ms=None)`: o alvo recebe `porcentagem` a menos de dano de todas as fontes (inclusive queimadura). Entra em `mult_dano_recebido` junto da fraqueza: `(1 + fraqueza) × Π(1 − defesa)`.
- **Decisão do usuário:** entre fontes diferentes, multiplica (como a cadência): 2 × 50% = 75%, e nunca chega a 100% (porcentagem < 1). Base da reformulação do Hunter (Defesa de 90% fora das costas).
- Testes em `test_status.py` (validação, jogador e inimigo, acúmulo, com fraqueza e buff de dano, duração e sem fim, queimadura). **Suíte: 1222 verdes + 1 xfail.** Golden inalterado (ninguém aplica ainda).

## 2026-11-22 | Balanceamento: todo min_val bate exato no nível máximo (muda o jogo, decisão do usuário)
- O commit anterior só garantia "alcançável": 7 dos 13 ajustados passavam do piso, e o limite (`max(min_val, ...)`) segurava (ex.: Energy Sword 7000 − 9×225 = 4975 com piso 5000; o último nível dava só 175). As 11 comuns, incomuns e raras passavam muito e travavam por volta do nível 11 (Mjolnir 1500 − 24×100 = −900). O usuário notou.
- **Decisão do usuário:** todos os 18 exatos, com `increase` redondo e o `min_val` trocado pelo ponto final real. Agora valor + subidas × increase == min_val nos 24 stats com piso (o Assault Rifle chega no nível 24, porque o cooldown só sobe nos níveis pares).
  - Comuns e incomuns (curva mais lenta, ganho até o fim): Assault Rifle −15/320, Mjolnir −40/540, MK2 regen −100/2600, Sidekick −12/912, Needler −25/1525, Shotgun −50/2050, Dizimator −125/2625, Warthog tiro −8/148 e reuso −500/40500.
  - Raras e épicas: Carabin −70/2520, Marine −35/510, Grenade Launcher −150/5900, Energy Sword −225/4975, Árbitro −60/460, Sniper −350/8850, Fuel Rod −450/7950, Pelican tiro −17/147 e reuso −1200/39200.
- A regra do `validar_armas` virou "bate exato": acusa "nunca chega a ele" e "passa dele e trava antes do fim", com a conta na mensagem. Com os dados do commit anterior: 18 erros. Casos novos em `test_validacao.py` (os dois lados, exato, `range_val` a cada 2 níveis, máximo da raridade diferente). **Suíte: 1209 verdes + 1 xfail.** Golden inalterado.
- **Não validado:** a sensação das comuns e incomuns, que agora ficam mais lentas no meio do jogo (antes chegavam ao piso no nível 11).

## 2026-11-22 | Balanceamento: nenhum min_val de mentira (muda o jogo, decisão do usuário)
- Com o teto da E6, 13 cooldowns nunca chegavam ao `min_val` (ex.: Spartan Laser parava em 9000 com piso 7500; sniper do Noble, em 9800 com piso 5000). **Decisão do usuário:** manter o piso (o alvo desenhado) e aumentar o `increase` só desses 13, para chegar ao piso no nível máximo da raridade. As comuns e incomuns, que já chegavam ao piso por volta do nível 11, não mudaram.
- Novos `increase` (piso alcançado no nível máximo): Brick −250, Spartan Laser −625, Light Rifle −625, Machine Gun −1250, Noble rifle −125 e sniper −1250 (nível 5); Energy Sword −225, Sniper −350, Fuel Rod −450, Árbitro −60, Pelican tiro −17 e reuso −1200 (nível 10); Grenade Launcher −150 (nível 15).
- Regra nova em `validar_armas`: um stat que desce com `min_val` precisa alcançá-lo até o nível máximo da raridade (a mensagem diz o `increase` necessário). Casos em `test_validacao.py`; `test_no_maximo_todo_piso_e_alcancado` sobe cada arma real até o máximo e confere o piso onde ela guarda o stat (arma, companheiro ou veículo). Com os dados antigos: 35 falhas. **Suíte: 1207 verdes + 1 xfail.** Golden inalterado.
- **Não validado:** a sensação do balanceamento (as lendárias ganham cadência bem mais rápido por nível).

## 2026-11-22 | Etapa E6: raridade de fato (recurso novo: muda o jogo)
- `constants.py`: `NIVEL_MAXIMO_POR_RARIDADE` (comum 25, incomum 20, rara 15, épica 10, lendária 5) e `PESO_SORTEIO_POR_RARIDADE` (40/25/20/10/5, por arma). `ArmaInfo.criar(jogador, game)` cria a arma com o `nivel_maximo` (o `Game` e o `EventManager` criam por ele; arma criada fora do registro não tem teto).
- `Arma.upgrade()` é o único ponto de subida: no máximo devolve `False` e não muda nada. As subclasses implementam o gancho `aplicar_nivel()`; as 14 armas que só aplicavam o perfil perderam o `upgrade` copiado (o padrão da base faz isso).
- Sorteio (`gerar_opcoes`): até 2 upgrades entre as armas **abaixo do máximo**, armas novas com peso por raridade (`sortear_armas_novas`, sem reposição), e mais upgrades se faltar. Sem opção nenhuma não abre tela: `recompensa_sem_upgrade()` (provisório, `TODO(itens temporários)`; o nível sobe normalmente). O item `upgrade` só mira arma abaixo do máximo; com tudo no máximo, dá só os +200 pontos. O upgrade forçado é revalidado ao sair da fila (a arma pode ter chegado ao máximo numa tela anterior).
- HUD: "MAX" na cor da raridade no lugar de `L<n>`; card: "(Nv. MAX)" no upgrade que leva ao máximo. `validar_armas` confere que toda raridade tem máximo (inteiro >= 1) e peso (> 0, finito).
- Testes: cada arma para exatamente no máximo e `upgrade()` acima dele não muda nada; pesos (10 mil sorteios, seed fixa); sem tela vazia (level-up, vários níveis, item, fila); MAX no card e no HUD; 11 casos da validação. **Mudança de especificação:** "sobe cada arma até o nível 21" (unit) e "cada arma no nível 10 em combate" (integração) viraram "até o máximo da raridade" (o `while < 10` travava a suíte com a lendária parada no 5). **Suíte: 1182 verdes + 1 xfail em 83 s.** Golden inalterado (o jogador blindado não sobe de nível).
- Desempenho: não medido (fora do laço quente; o HUD lê 1 propriedade por slot).
- **Não validado:** a sensação do teto e dos pesos no jogo, o "MAX" na tela real.

## 2026-11-22 | Correção: veículo sobrevive à troca de fase
- O Warthog e o Pelican saíam dos grupos na troca de fase, mas a arma continuava atualizando o sprite: invisível, o veículo seguia atirando e atropelando, e o jogador continuava "no veículo". O `Vehicle` deixou de recusar a flag (herda `sobrevive_troca_de_fase = True` do `Companheiro`) e, como companheiro, vai para o spawn novo junto do jogador (estacionado ou destruído; embarcado, ele já gruda no jogador). **Muda o jogo:** o veículo continua visível e utilizável nas fases seguintes. Achado na E5; commit próprio.
- Regressão em `test_regressoes.py::test_veiculo_sobrevive_a_troca_de_fase` (Warthog e Pelican, embarcado e estacionado; os 4 falharam antes); o teste do conjunto de sobreviventes da E5 passou a incluir os veículos. Suíte: **1108 verdes + 1 xfail**. Golden inalterado.
- **Achado (não corrigido):** o veículo é atualizado 2× por passo (pela arma e pelo laço do `all_sprites` em `Game._atualizar_entidades`), como já acontecia na fase 0. Hoje é inofensivo (tiro, atropelamento e animação usam cooldown pelo relógio, e a posição só gruda no jogador), mas um efeito por chamada no `Vehicle.update` contaria em dobro.
- **Não validado:** o veículo depois da troca na tela real (estacionado ao lado do spawn, embarcado, destruído).

## 2026-11-22 | Correção: companheiros no spawn do mapa novo
- O `StageManager` lia `get_player_spawn_pos()` **antes** de trocar o mapa: os companheiros iam para o spawn do mapa antigo e cruzavam o mapa voando até o jogador. Agora o reposicionamento vem depois do mapa novo, com a mesma posição do jogador (cópia própria do `Vector2`). **Muda o jogo:** os companheiros começam a fase ao lado do jogador. Achado na E5; commit próprio (roteiro §2, regra 6).
- Regressão em `test_regressoes.py::test_companheiros_vao_para_o_spawn_do_mapa_novo` (falhou antes da correção); `test_troca_de_fase.py` confere que o companheiro não divide o `Vector2` do spawn. Suíte: **1104 verdes + 3 xfail**. Golden inalterado (a fase 0 não troca de fase). **Não validado:** a troca de fase na tela real.

## 2026-11-22 | Etapa E5: persistência entre fases explícita (refatoração: golden inalterado)
- Na troca de fase sobrevive quem declara `sobrevive_troca_de_fase = True` na classe: `Player`, `Companheiro` (Árbitro, Cortana, Marines, Noble) e `PlayerAura` (MK2). O `StageManager` não conhece mais arma nem dono: os 4 `hasattr` (`companions`, `sprite_companion`, `area_de_dano`) saíram. O reposicionamento usa `isinstance(sprite, Companheiro)`.
- **Equivalência:** o teste do conjunto de sobreviventes (todas as armas do registro, inimigo, item e portal) passa igual no código antigo; `Vehicle` declara `False` de propósito para manter o comportamento de hoje (ver o 1º achado).
- Testes (`test_troca_de_fase.py`): sobrevivem exatamente jogador, 4 companheiros e aura; todos os Marines; a flag decide sozinha (sprite solto marcado fica, a instância pode recusar); a aura continua no `auras_grupo`. **Suíte: 1102 verdes + 4 xfail** (3 novos, abaixo). Golden inalterado.
- Desempenho: só a troca de fase (na tomada, A/B alternado com o HEAD, 2 rodadas): 238/234 × 236/236 ms. Igual. O `perf.py` acusa +15000% contra a base antiga (1,56 ms), esperado desde a D2 (decodifica o mapa); a base continua para regravar.
- **Achados (bugs, `xfail(strict=True)` em `test_troca_de_fase.py`):**
  - **Veículo some na troca de fase:** o Warthog e o Pelican saem dos grupos (`kill`), mas a arma continua atualizando o sprite: invisível, ele segue atirando e atropelando, e o jogador continua "no veículo".
  - **Companheiros vão para o spawn do mapa antigo:** a posição é lida antes de trocar o mapa (na fase 0→1: companheiro em (2302, 2048), jogador em (1536, 1024)), e eles cruzam o mapa voando até o jogador.
- Próxima: as 2 correções acima (feitas, entradas acima) e depois **E6** (raridade de fato).

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

## Resumo comprimido (2026-11-21): base, blocos A–D, E1, status e correções
Detalhes completos no histórico do git (`git log -p docs/log.md`).

**Feito**
- Base: docs (`CLAUDE.md`, `docs/`), suíte `tests/`, todos os bugs conhecidos de então corrigidos (granada, Crawler/Soldier, MRO de Gravemind/Didact, Fuel Rod mirando nos itens, Warden, ranking em `%APPDATA%` no exe), roteiro e tag `base-reformulacao` (A0).
- **A** (medição): `tools/perf.py` (A1), catraca de alocação (A2), golden master da fase 0 (A3), código morto apagado + `ruff` só regras F + teste de import de todo módulo (A4).
- **B** (núcleo): passo fixo 1/60 com teto de 5 passos (B1); estados com tabela `TRANSICOES` e registro único de telas (B2); `SessaoJogo` recriada a cada partida, relógio zerado por partida (B3); passos nomeados do `Game.update` + barramento `eventos` (B4).
- **C** (desempenho): `GradeParedes` de 128 px, que também corrigiu o bug do inimigo longe do jogador atravessar paredes (C1); broadphase por `collidelistall` (C2); máscaras em cache, `camada_alpha`/`rascunho`, partículas com teto de 2000 (C3); culling e HUD em cache (C4).
- **D** (dados): `MANIFESTO` de assets com equivalência de pixels (D1); fundos de fase sob demanda, LRU de 2 (D2); import sem efeito colateral, `carregar_assets()` explícito (D3); `INIMIGOS`/`PerfilInimigo` com golden de equivalência por classe (D4); `validar_tudo()` (D5).
- **E1** (2026-11-21): contrato de dano único (`Dano`, `receber_dano`, ganchos). **Status S1–S3:** `systems/status/`, curas e escudos por ele, bônus da Cortana como `BuffVelocidade`. **Correções:** névoa do Gravemind pelo contrato, cura não ressuscita o morto do mesmo frame, upgrade de alcance do Light Rifle, alcance de toda arma no `weapon_data`.
- Correções avulsas: HUD usava `get_ticks` (A2); tela de colaboradores (`self.imagem` → `self.image`).

**Base de desempenho da A1 (para a tabela final da H2)**, ms/frame na tomada: horda_150 33,2 (p95 46,5); fase0 5,3; Guardian 11,5 (p95 34,1; custo no draw); Warden 6,8; Gravemind 5,6; outros bosses 2,0–4,8; troca de fase 1,2; import 4,2 s; pico 781 MB. **Depois do bloco C:** horda 4,4–4,6 (p95 6,2–6,6); Guardian 3,4–4,0; fase0 1,6–1,8; alocações da horda 20 → 0,02/frame. **Depois da D2:** import 1,5 s, pico 379 MB, troca de fase 120–140 ms (decodifica o mapa; roda com a tela preta, esperado).

**Medição:** na bateria nada vale; na tomada o ruído entre sessões chegou a 70% no próprio HEAD (B2–C4). Etapas validadas por A/B alternado com o commit anterior (worktree).

**Decisões que valem até hoje**
- C1: margem da grade 128 px (64 falhou na equivalência do jogador). C2: sem `GradeEntidades`; a busca de alvo das armas custa 0,04 ms/frame. C4: sem camadas estáticas no HUD.
- D5: "spawn dentro da navegação" e "portal obrigatório" **não** viram regra (decisão do usuário na E1); `Navigation` só serve ao teleporte do Knight/Zealot.
- Catraca: Gravemind com teto 0,7 (máscara por frame da animação de respawn, F2/F5); na suíte completa mede 0,48 e avisa (esperado).

**Achados não corrigidos**
- E1: granada e morteiro inimigos encostando no jogador dão `receber_dano(0)` (i-frames e regeneração do escudo); golpe letal do Tartarus é absorvido pelo veículo; elipse/ponto em `Colisoes` viram retângulo/degenerado.
- Pendências: "invulnerável" no contrato de dano (decisão sua), indicador de status no HUD, regravar `perf_base.json` numa sessão fria, Hunter preso em parede (sem `xfail` ainda).
- `OndaEMP.draw` sem deslocamento chama `camera.aplicar_posicao` (não existe; o ramo não roda).
- `Sentinel.animar` passa o frame do cache sem copiar: o alpha de um Sentinel vale para todos no mesmo frame.
- Limite do ruff: exceção por arquivo × regra (um 2º `F401` num arquivo já listado passa).
- Catraca não conta métodos em C (`Surface.copy`, `convert_alpha`, `Font.render`).
- C2: inimigo que surge ou se move durante a passada de colisão só é visto pelos projéteis no frame seguinte.

**Não validado no jogo real (acumulado):** sensação abaixo de 12 FPS (câmera lenta pelo teto de passos), aparência de partículas/itens/granada/raio do Watcher (C3), HUD e culling (C4), pausa da troca de fase e 1ª partida depois de game over numa fase alta (D2), executável (D3), menus pelo teclado (B2).
