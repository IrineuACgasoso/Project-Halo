# Convenções

## Código
- **Idioma:** identificadores, comentários e docstrings em português (`vida_atual`, `receber_dano`, `inimigos_grupo`). Há exceções herdadas em inglês (`update`, `draw`, `handle_event`, `setup_*`). Mantenha o padrão do arquivo onde você está mexendo.
- **Nomes:** `snake_case` para funções e atributos, `PascalCase` para classes, `MAIUSCULAS` para constantes e configs de módulo (`MAX_ARMAS`, `PHASE_POOLS`, `CRONOGRAMA_BOSSES`).
- **Grupos de uma arma:** a ordem de `ArmaInfo.grupos` precisa bater com o desempacotamento no `__init__` da classe. Já houve uma troca que fez o Fuel Rod mirar nos itens; `test_arma_mira_no_grupo_de_inimigos` cobre isso.
- **Mixins em vez de herança profunda:** cada arquivo define uma classe sem `__init__` que manipula `self` (por exemplo, `PlayerCombat` e `EnemyCombat`). O `__init__` real chama os `setup_*` explicitamente.
  - **Boss:** `class X(BaseEnemy, XSetup, XAI, XAttacks)`. Quem vem antes na MRO vence. Para sobrescrever um método de `BaseEnemy`, o mixin precisa vir **antes** dela (como faz o Arbiter com `ArbiterMovement`).
- **Dados separados da lógica:** os números de balanceamento ficam em `data/weapon_data.py` ou em `config.py` (dataclasses frozen + dict de presets, como em `skills/*/config.py` e `bosses/arbiter/config.py`). Prefira esse padrão para código novo.
- **Registro por dict:** `ARMAS_REGISTRO`, `BOSS_CLASSES`, `PHASE_POOLS`, `ASSETS[...]` e os presets. Para adicionar algo, crie a entrada no dict; não espalhe `if tipo == ...`.
- **Tempo:** usa `relogio.agora()` (ms) e `delta_time` (s). Velocidades em px/s.
- **Robustez:** leituras opcionais via `getattr(obj, 'attr', padrao)`, um padrão muito usado em colisão e no renderer. Vetor nulo: use `direcao_segura()` em vez de `normalize()`.
- **Comentários:** explique o *porquê* (o projeto já documenta bugs antigos ao lado da correção). Evite comentários que só repetem o código.
- **Logs:** o projeto usa `print` com prefixo (`[RankingData]`, `[Renderer]`). Não há módulo de logging.

## Assets
- Sempre via `ASSETS[...]` (`feats/assets.py`) ou `path(...)` (`utils/paths.py`). Nunca use caminho absoluto nem `os.getcwd()` direto, porque o executável usa `sys._MEIPASS`.
- Fontes: `utils/fonts.carregar_fonte(...)`, que tem cache e fallback para SysFont.

## Segurança e dados
- O jogo é offline. A única entrada externa é `ranking.json`, que deve passar sempre por `RankingData`: nome sanitizado (maiúsculas, até 16 caracteres) e score inteiro maior ou igual a 0.
- Onde o ranking fica (`caminho_padrao_ranking()`): `assets/data/ranking.json` rodando o `.py`, e `%APPDATA%/ProjectHalo/ranking.json` no executável.
- O projeto não usa segredos nem variáveis sensíveis. Variáveis de ambiente usadas: `MCE_DEBUG`; nos testes, também `SDL_VIDEODRIVER`/`SDL_AUDIODRIVER=dummy`.

## Commits e branches
- **Estilo de mensagem:** em **português**. Título em MAIÚSCULAS e depois uma lista com `+`. Exemplo: `CORREÇÃO DE BUGS + Granada inimiga não derruba mais o jogo; + Fuel Rod mira nos inimigos;`. Os commits antigos misturam inglês e português.
- **Branches:** trabalho direto na `main` (não há outras branches nem CI).
- **Nunca versionar:** `dist/`, `build/`, `*.spec` ou `.venv/` (já estão no `.gitignore`).
