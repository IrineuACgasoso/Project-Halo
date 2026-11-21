# Criação de Bosses

Este é o padrão oficial para criar chefes no projeto. Ele substitui o antigo `docs/BOSS_GUIDE.md`.

Exemplos de referência:
- **Arbiter** (pasta `arbi/`): chefe completo, com 3 fases, 6 habilidades, camuflagem e invocação.
- **`boss_template.py`**: chefe mínimo e funcional (~50 linhas), para copiar e adaptar.

---

## 1. Ideia central

Um boss é um conjunto de **rotinas**. Uma rotina é um método que descreve uma habilidade em ordem cronológica, e cada `yield` significa **"espere o próximo frame"**.

```python
def rotina_golpe(self):
    cfg = self._lancar_cone('cleave_knight', self._dir_jogador())   # telegraph + dano
    yield from self._esperar(cfg.duracao + 150)                     # fica parado até o cone explodir
    yield from self._esperar(400)                                   # recuperação
    self._agendar('golpe')                                          # reagenda o cooldown
    self.wait = 500                                                 # respiro antes de decidir de novo
```

O motor (na base) cuida de todo o resto: **quando** usar cada habilidade, cooldowns, fases, movimento entre habilidades, detecção de travamento. Você só escreve o conteúdo de cada habilidade e as regras de decisão.

### O que acontece a cada frame

`BossBase.update` → `executar_estados`:

1. Atualiza percepção (velocidade estimada do jogador, troca de lado do strafe) e checa mudança de fase.
2. Avança a camuflagem (se ativa).
3. **Reseta o movimento** para o padrão "perseguir o jogador na velocidade da fase".
4. Se **não há rotina ativa**, o boss *pensa*, nesta ordem:
   1. `comportamento_idle`: como se move enquanto está livre.
   2. Anti-stuck: preso e longe do jogador? → `rotina_antistuck`.
   3. `wait` > 0? → espera.
   4. Mudança de fase pendente? → `rotina_transicao`.
   5. `habilidade_prioritaria` e depois sorteio por `pesos_habilidades`.
5. Se há rotina, executa **um passo** dela (`next`). Quando termina, volta ao `idle`.

> Consequência importante: **o boss nunca é interrompido pela IA no meio de uma habilidade.** Mudança de fase, por exemplo, só ocorre quando ele termina o que está fazendo.

---

## 2. Estrutura de pastas

```
source/enemies/<categoria>/<nome_do_boss>/
├── __init__.py     # from .core import BossNome
├── core.py         # a classe: configuração do motor, __init__, morrer()
├── config.py       # FASES + todos os números do boss (balanceamento)
├── states.py       # DECISÕES: pesos_habilidades, comportamento_idle, ...
├── attacks.py      # rotinas das habilidades (podem ser divididas em vários arquivos)
└── arsenal.py      # (opcional) outro grupo de habilidades
```

Divida os arquivos por assunto. Os que contêm métodos do boss são **mixins** (classes simples, sem `__init__`).

---

## 3. Passo a passo

### 3.1 Fases e números (`config.py`)

```python
from dataclasses import dataclass
from source.enemies.base.enemy_phases import FaseBoss

@dataclass(frozen=True)
class FaseWarden(FaseBoss):
    # herda: nome, limiar_vida, mult_cooldown, mult_velocidade, escudo_transicao
    golpes: int                      # campos que variam por fase, só deste boss

FASES = (
    FaseWarden(nome='Normal',  limiar_vida=1.0, mult_cooldown=1.0, mult_velocidade=1.0, escudo_transicao=0,   golpes=1),
    FaseWarden(nome='Furioso', limiar_vida=0.5, mult_cooldown=0.7, mult_velocidade=1.2, escudo_transicao=200, golpes=2),
)
```

Regras:
- A **primeira fase deve ter `limiar_vida=1.0`**. As demais entram quando `vida / vida_maxima <= limiar`.
- Sempre construa fases com **argumentos nomeados** (a herança de dataclass não aceita bem posicionais).
- `mult_cooldown` < 1 = habilidades voltam mais rápido. `mult_velocidade` > 1 = anda mais rápido.
- Fases só sobem, nunca descem (cura não faz o boss voltar de fase).

Coloque também em `config.py` todo número de habilidade (telegraph, dano, alcance, intervalos). Assim o balanceamento não exige mexer na lógica.

### 3.2 A classe (`core.py`)

```python
from source.enemies.base.boss_base import BossBase
from .config import FASES
from .states import WardenAI
from .attacks import WardenAttacks

class BossWarden(WardenAI, WardenAttacks, BossBase):     # mixins do boss ANTES de BossBase!
    FASES = FASES
    COOLDOWNS = {'golpe': (3000, 5000), 'investida': (6000, 9000)}   # (mín, máx) ms, sorteado
    COOLDOWN_INICIAL = {'golpe': 2000, 'investida': 5000}            # 1º uso após o spawn
    DIST_MIN, DIST_MAX = 150, 350                                    # banda de distância ao ficar livre

    def __init__(self, posicao, game, **kwargs):
        super().__init__(posicao, vida_base=3000, dano_base=60, velocidade_base=80,
                         game=game, sprite_key='warden', flip_sprite=True)
        self.titulo = "Nome do Boss"
        self.setup_animation(estado_inicial='right', velocidade_animacao=200)
        # hitbox personalizada, se precisar (BossBase atualiza hitbox.center sozinho)

    def morrer(self, grupos=None):
        Items.spawn_drop(...)
        self.kill()
```

> **A regra de ouro da herança.** Os mixins do boss **sempre vêm antes** de `BossBase`.
> Se vierem depois, os métodos padrão da base (`pesos_habilidades`, `rotina_transicao`, ...) vencem na ordem de resolução do Python e os seus **nunca são chamados — sem nenhum erro**. É o bug mais traiçoeiro desse padrão.

### 3.3 Decisões (`states.py`)

```python
class WardenAI:
    def pesos_habilidades(self, agora, dist):
        # peso 0 = não faz sentido agora. A base já filtra cooldown e penaliza repetir a última.
        return {
            'golpe':     5 if dist < 260 else 0,
            'investida': 3 if dist > 300 else 0,
        }

    # opcionais:
    def habilidade_prioritaria(self, agora, dist):
        return 'invocacao' if len(self.invocados) < 2 else None   # passa na frente do sorteio (se pronta)

    def comportamento_idle(self, dist, agora):
        ...   # default: banda DIST_MIN..DIST_MAX com strafe; sobrescreva para personalizar
```

Pense em `pesos_habilidades` como: *"dado onde o jogador está, quais habilidades fariam sentido?"* O sorteio ponderado deixa o boss imprevisível sem ser aleatório demais.

### 3.4 Habilidades (`attacks.py`)

Siga sempre este esqueleto:

```python
def rotina_nome(self):
    # 1. TELEGRAPH   (o jogador precisa de um aviso legível)
    # 2. EXECUÇÃO    (dano / projétil / movimento)
    # 3. RECUPERAÇÃO (janela de punição)
    self._agendar('nome')     # 4. SEMPRE reagenda o cooldown no fim
    self.wait = 500           # 5. respiro opcional
```

Padrões prontos:

**Investida** (movimento forçado):
```python
def rotina_investida(self):
    yield from self._esperar(400)               # telegraph: parado
    direcao = self._dir_jogador()               # trava a direção
    fim = self._agora + 450
    while self._agora < fim:
        self._ir(direcao, 5.0)                  # 5× a velocidade, naquela direção
        yield                                   # ← todo laço PRECISA de yield
    self._agendar('investida'); self.wait = 600
```

**Combo que cresce com a fase:**
```python
for i in range(self.fase_cfg.golpes):
    cfg = self._lancar_cone('preset', self._dir_jogador(), duracao_mult=0.82 ** i)  # cada golpe mais rápido
    yield from self._esperar(cfg.duracao + 150)
```

**Projétil com mira antecipada:**
```python
base = self._direcao_antecipada(vel_projetil=550, fator=0.55)   # 0 = onde está; 1 = mira perfeita no futuro
```

**Camuflagem** (a máquina de alpha é da base):
```python
self.adicionar_escudo(250)
self.iniciar_invisibilidade(alpha_alvo=0, fade_out=1000, fade_in=600, duracao=3500, flashing=False)
while self.invis_phase is not None:          # 'fade_out' → 'hold' → 'fade_in' → None
    ...
    yield
```
Use `self._revelar(ms, bônus_alpha)` quando ele atacar camuflado. Por padrão, enquanto revelado ele **pode tomar dano** (janela de contra-ataque; desligue com `VULNERAVEL_AO_REVELAR = False`).

**Invocação:**
```python
nasceram = self._invocar_aliados(Elite, quantidade=2, max_vivos=4)   # 0 = não achou chão válido
```
A lista de vivos fica em `self.invocados`.

**Sub-rotinas:** reutilize trechos com `yield from self.outra_rotina()` (é assim que a emboscada do Arbiter chama a espada).

---

## 4. Referência rápida

### Atributos de classe

| Atributo | Padrão | Função |
|---|---|---|
| `FASES` | 1 fase única | tupla de `FaseBoss` |
| `COOLDOWNS` | `{}` | `{'hab': (mín_ms, máx_ms)}` |
| `COOLDOWN_INICIAL` | `{}` | 1º uso após o spawn (padrão = o mín. do cooldown) |
| `ESTADOS` | `{}` | nome público do estado (`estado_habilidade`); padrão = nome da habilidade |
| `DIST_MIN` / `DIST_MAX` | 250 / 450 | banda do `comportamento_idle` padrão |
| `PESO_REPETICAO` | 0.3 | multiplicador do peso da última habilidade usada |
| `DONO_SKILLS` | `'BOSS'` | `dono` repassado a cones e granadas |
| `VULNERAVEL_AO_REVELAR` | `True` | revelado = vulnerável |
| `STRAFE_TROCA_MS` | (1200, 2600) | de quanto em quanto tempo o strafe inverte |
| `ANTISTUCK_JANELA` / `_CAMINHO_MIN` / `_DIST_MIN_SQ` | 1500 / 40 / 40000 | detecção de travamento |

### Hooks (todos opcionais)

| Hook | Quando é chamado |
|---|---|
| `pesos_habilidades(agora, dist)` | toda vez que o boss decide |
| `habilidade_prioritaria(agora, dist)` | antes do sorteio |
| `comportamento_idle(dist, agora)` | todo frame em que está livre |
| `rotina_transicao()` | ao entrar numa fase nova (padrão: ganha o escudo da fase) |
| `rotina_antistuck()` | ao detectar travamento (padrão: teleporta) |
| `ao_interromper()` | quando `interromper_rotina()` corta uma habilidade |

### Dentro de uma rotina

| Categoria | Métodos |
|---|---|
| Tempo | `yield`, `yield from self._esperar(ms, strafe=0)`, `self._agora` |
| Cooldown | `self._agendar('hab')`, `self.cd['hab']`, `self.wait = ms` |
| Movimento | `_parar()`, `_ir(dir, fator)`, `_aproximar(f)`, `_recuar(f)`, `_strafe(f)` |
| Percepção | `_dir_jogador()`, `_dist_jogador()`, `_ponto_antecipado(v, f)`, `_direcao_antecipada(v, f)` |
| Posição | `realizar_teleporte()`, `encontrar_posicao_valida_ao_redor(...)`, `verificar_posicao_valida(p)` |
| Combate | `_lancar_cone(preset, dir, duracao_mult)`, `_invocar_aliados(...)`, `adicionar_escudo(v)` |
| Camuflagem | `iniciar_invisibilidade(...)`, `invis_phase`, `_revelar(ms, alpha)` |
| Estado | `self.fase`, `self.fase_cfg.<campo>`, `self.invocados`, `self.vida` |
| De fora | `boss.interromper_rotina()` (atordoar, por exemplo) |

### Unidades

- `self._agora`, `cd`, `wait`, durações: **milissegundos** (relógio do jogo).
- `delta_time`: **segundos**.
- Velocidades: pixels por segundo; `fator` é multiplicador da velocidade da fase.

---

## 5. Armadilhas comuns

| Sintoma | Causa provável |
|---|---|
| A habilidade "não espera" | `self._esperar(300)` sem `yield from` (não dá erro, só não faz nada) |
| O jogo congela | um `while` dentro da rotina sem `yield` |
| O boss persegue o jogador no meio da habilidade | em algum frame a rotina não chamou `_parar/_ir/_strafe/_esperar` (o padrão é perseguir) |
| Seus hooks nunca são chamados | mixins do boss depois de `BossBase` na herança |
| Habilidade usada sem cooldown | esqueceu `self._agendar('hab')` no fim da rotina |
| Habilidade nunca é escolhida | nome diferente entre `COOLDOWNS`, `pesos_habilidades` e `rotina_<nome>` |
| `KeyError` em `cd` | habilidade em `pesos_habilidades` que não está em `COOLDOWNS` |
| Repetir uma habilidade | um gerador não reinicia; chame `self.rotina_x()` de novo (a base já faz isso) |
| Cooldown estranho | `cd['x']` é um **instante**, não uma duração; use `_agendar` |
| Tempo errado ao pausar | uso de `time`/`pygame.time` em vez de `self._agora` |
| Sobrescrever método de `BaseEnemy` não funciona | ele precisa estar no corpo de `BossBase` ou de classe que venha **antes** dele |

---

## 6. Boas práticas de design

- **Todo ataque tem telegraph legível.** O cone do `ConeStrike` já é o telegraph: crie-o no início e espere `cfg.duracao`.
- **Todo ataque tem janela de punição** (recuperação). Sem ela o boss é injusto.
- **Fases mudam o jogo, não só os números.** No Arbiter: combos maiores, rajada em leque, mais granadas, mais reforços.
- **Prefira poucas habilidades bem feitas** com variações por fase a muitas habilidades rasas.
- **Dano de cones e projéteis é fixo** (não escala com a dificuldade como `dano_base`). Se quiser escalar, crie o `custom_config` do cone com o dano multiplicado.
- Um cone novo se cria em `cone_strike/config.py` (um `ConeStrikeConfig` no dicionário `CONE_STRIKE_PRESETS`). Cones telegrafam a **direção travada na criação**, então o boss deve ficar parado enquanto o cone carrega.

---

## 7. Testando sem abrir o jogo

A pasta `tools/sim_harness/` simula lutas inteiras (jogador andando ou parado) com o seu código real.

```
python build.py --base ... --arbi <pasta_do_boss> --cone ... --grenades ... --template ...
cd sandbox
python run_sim.py                    # 10 lutas + 3 com jogador parado
python test_targeted.py
python test_base_and_template.py
```

Para o seu boss, copie a seção 2 de `test_base_and_template.py` trocando `BossExemplo` pelo seu.

O simulador pega: exceções, rotina presa, fase que não dispara, cooldown quebrado, aliados acima do teto, dano errado de combo. **Não** avalia visual, balanceamento nem performance.

---

## 8. Checklist de um boss novo

- [ ] `FASES` com a primeira em `limiar_vida=1.0`, fases nomeadas e construídas por argumentos nomeados
- [ ] `COOLDOWNS` e `COOLDOWN_INICIAL` cobrem **todas** as habilidades
- [ ] Mixins do boss antes de `BossBase`
- [ ] Cada `rotina_x` tem telegraph, execução, recuperação e termina com `_agendar('x')`
- [ ] Todo `while` em rotina tem `yield`; todo `_esperar` tem `yield from`
- [ ] `pesos_habilidades` só devolve nomes que existem em `COOLDOWNS`
- [ ] Sem `time`/`pygame.time`: só `self._agora`
- [ ] Números de balanceamento em `config.py`
- [ ] Simulador rodado: sem exceção, todas as habilidades usadas, fases disparadas
- [ ] Testado no jogo: telegraphs legíveis, dano justo, sem ficar preso em paredes

---

## 9. Onde fica cada coisa

| Arquivo | Conteúdo |
|---|---|
| `base/boss_base.py` | `BossBase`: `update`, vulnerabilidade ao se revelar, teleporte, cone, invocar |
| `base/enemy_routines.py` | motor: ciclo do frame, cooldowns, decisão, anti-stuck, interromper |
| `base/enemy_phases.py` | `FaseBoss` e a lógica de subir de fase |
| `base/enemy_perception.py` | velocidade do jogador, antecipação de mira, strafe |
| `base/enemy_movement.py` | `mover` com direção opcional; `_ir`, `_parar`, ... (inimigos comuns não mudam) |
| `base/enemy_collision.py` | `encontrar_posicao_valida_ao_redor` |
| `base/enemy_effects.py` | `_revelar` |