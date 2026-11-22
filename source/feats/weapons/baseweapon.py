import pygame
from source.systems.gameclock import relogio
import math
from abc import ABC, abstractmethod
from source.windows.settings import *
from source.feats.assets import ASSETS
from source.data.weapon_data import *
from source.utils.vetores import direcao_segura
from source.systems.entitymanager import entity_manager

# Fusão dos dicionários de Dataclasses
ALL_DATA = {**WEAPON_DATA, **COMPANION_DATA, **VEHICLES_DATA}


class Arma(ABC):
    def __init__(self, jogador, nivel_maximo=None, **kwargs):
        self.jogador = jogador
        self.nivel = 1
        self.nivel_maximo = nivel_maximo   # da raridade (ArmaInfo.criar, roteiro E6); None = sem teto
        self.dano = 0
        self.velocidade = 0
        self.cooldown = 0
        self.ultimo_tiro = 0
        self._proxima_busca = 0   # throttle da busca de alvo quando não há inimigo no alcance
        self.nome = ""
        self.descricao = ""

    # ── Grupos de sprite (roteiro E4) ───────────────────────────────────────────
    # A arma lê os grupos do entity_manager pelo nome: não há lista posicional para errar
    # (era assim que o Fuel Rod recebia items_grupo no lugar de inimigos_grupo).

    @property
    def all_sprites(self):
        return entity_manager.all_sprites

    @property
    def inimigos_grupo(self):
        return entity_manager.inimigos_grupo

    @property
    def items_grupo(self):
        return entity_manager.items_grupo

    @property
    def auras_grupo(self):
        return entity_manager.auras_grupo

    # ── Core ────────────────────────────────────────────────────────────────────

    @staticmethod
    def _deve_melhorar(range_val, nivel):
        """
        0 / None  → nunca
        int       → a cada N níveis  (nivel % N == 0)
        list      → só nos níveis da lista
        """
        if not range_val:
            return False
        if isinstance(range_val, list):
            return nivel in range_val
        return nivel % range_val == 0
    
    # ── Genéricos (weapon ou companion) ─────────────────────────────────────────

    def aplicar_upgrades(self, nivel: int, nome_asset: str, target=None):
        targets = target if isinstance(target, list) else ([target] if target else [self])
        profile = ALL_DATA.get(nome_asset)
        if not profile: return
        
        stats = profile.stats

        for attr, meta in stats.items():
            if not meta.increase or not meta.label:
                continue
            if not self._deve_melhorar(meta.range_val, nivel):
                continue
                
            # Tratamos o nome real do atributo exatamente como no método de visualização
            attr_real = attr[1:] if attr.startswith('_') else attr
                
            for t in targets:
                atual = getattr(t, attr_real, meta.value)
                # Garante que se 'atual' for None, tratamos como 0 por segurança
                base_calculo = atual if atual is not None else 0
                novo = base_calculo + meta.increase
                
                if hasattr(meta, 'min_val') and meta.min_val is not None:
                    novo = max(meta.min_val, novo)
                setattr(t, attr_real, novo) # Modifica o atributo real (ex: 'cooldown' em vez de '_cooldown')


    def ver_proximos_upgrades(self, nivel_proximo: int, nome_asset: str, target=None) -> dict:
        """
        Retorna {attr: {label, atual, proximo}} sintonizado com as Dataclasses.
        """
        t = target if target and not isinstance(target, list) else (target[0] if target else self)
        profile = ALL_DATA.get(nome_asset)
        if not profile:
            return {}
        
        stats = profile.stats
        resultado = {}

        for attr, meta in stats.items():
            if not meta.label:
                continue

            attr_real = attr[1:] if attr.startswith('_') else attr
            atual = getattr(t, attr_real, meta.value)

            if self._deve_melhorar(meta.range_val, nivel_proximo): # Ajustado para range_val
                if atual is None:
                    # Se o objeto não tem esse atributo em tempo de execução (ex: atributos com '_'),
                    # usamos o valor base original da Dataclass. Se nem ele existir, assumimos 0.
                    base_calculo = meta.value if meta.value is not None else 0
                else:
                    base_calculo = atual

                # Segurança extra: se o aumento do upgrade for None, consideramos 0
                incremento = meta.increase if meta.increase is not None else 0

                proximo = base_calculo + incremento
                
                if hasattr(meta, 'min_val') and meta.min_val is not None: # Ajustado para min_val
                    proximo = max(meta.min_val, proximo)
            else:
                proximo = atual

            resultado[attr] = {'label': meta.label, 'atual': atual, 'proximo': proximo}

        return resultado

    def get_estatisticas_para_exibir(self, nivel_proximo: int, nome_asset: str, target=None) -> list[str]:
        """
        Formata apenas as estatísticas modificadas para exibição na interface gráfica.
        """
        proximos = self.ver_proximos_upgrades(nivel_proximo, nome_asset, target)
        linhas = []
        
        fmt = lambda v: "0" if v is None else (f"{v:.1f}" if isinstance(v, float) and v % 1 != 0 and v != float('inf') else str(int(v)))        
        for info in proximos.values():
            if info['atual'] == info['proximo']:
                continue
            linhas.append(f"{info['label']}: {fmt(info['atual'])} -> {fmt(info['proximo'])}")
        return linhas
    
    # ── Inicializar atributos a partir do data ───────────────────────────────────

    def inicializar_stats(self, nome_asset: str, target=None):
        """
        Lê os valores iniciais (.value) da Dataclass e injeta na arma instanciada.
        """
        t = target or self
        profile = ALL_DATA.get(nome_asset)
        if not profile:
            return
        
        stats = profile.stats
        for attr, meta in stats.items():
            if not attr.startswith('_') and meta.value is not None:
                setattr(t, attr, meta.value)

    # ── Interface obrigatória ────────────────────────────────────────────────────

    def direcao_para(self, alvo):
        """Direção unitária jogador -> alvo. Centraliza a conta que 11 armas repetiam e que
        lançava ValueError (crash) quando inimigo e jogador ocupavam o mesmo ponto."""
        return direcao_segura(self.jogador.posicao, alvo.posicao)

    def encontrar_inimigo_mais_proximo(self, grupo_inimigos, raio_maximo=2000):
        if not grupo_inimigos: 
            return None
        
        menor_dist_sq = raio_maximo ** 2
        inimigo_mais_proximo = None

        for inimigo in grupo_inimigos:
            if not inimigo.alvejavel:
                continue

            dist_sq = self.jogador.posicao.distance_squared_to(inimigo.posicao)
            if dist_sq < menor_dist_sq:
                menor_dist_sq = dist_sq
                inimigo_mais_proximo = inimigo
        return inimigo_mais_proximo

    def encontrar_inimigo_mais_forte(self, grupo_inimigos, raio_maximo=2000):
        """Busca, dentro do raio, o inimigo com maior vida atual — ideal
        para armas de precisão/execução como o Spartan Laser, que não
        fazem sentido perseguindo o alvo mais próximo."""
        if not grupo_inimigos:
            return None

        raio_maximo_sq = raio_maximo ** 2
        alvo_mais_forte = None
        maior_vida = -1

        for inimigo in grupo_inimigos:
            if not inimigo.alvejavel:
                continue

            dist_sq = self.jogador.posicao.distance_squared_to(inimigo.posicao)
            if dist_sq > raio_maximo_sq:
                continue

            if inimigo.vida > maior_vida:
                maior_vida = inimigo.vida
                alvo_mais_forte = inimigo

        return alvo_mais_forte
    
    def update(self, delta_time):
        """Lógica de cadência baseada no tick rate do pygame"""
        agora = relogio.agora()
        # Sem alvo, disparar() varria TODOS os inimigos a cada frame (por arma). Agora só a cada 100 ms.
        if agora < getattr(self, '_proxima_busca', 0):
            return
        # Buff de cadência (systems/status): sem efeito, mult_cooldown é exatamente 1.0
        if agora - self.ultimo_tiro > self.cooldown * self.jogador.status.mult_cooldown:
            if self.disparar():
                self.ultimo_tiro = agora
            else:
                self._proxima_busca = agora + 100
    
    @abstractmethod
    def disparar(self) -> bool:
        """Deve retornar True se o disparo foi realizado com sucesso para resetar o cooldown"""
        pass
    
    @property
    def no_maximo(self) -> bool:
        return self.nivel_maximo is not None and self.nivel >= self.nivel_maximo

    def upgrade(self) -> bool:
        """Sobe 1 nível e aplica os ganhos dele. No nível máximo não faz nada e devolve False
        (o sorteio já não oferece a arma; isto é a defesa em profundidade da E6)."""
        if self.no_maximo:
            return False
        self.nivel += 1
        self.aplicar_nivel()
        return True

    def aplicar_nivel(self):
        """Ganhos do nível recém-alcançado (`self.nivel`). Padrão: os stats do perfil na própria arma.
        Quem guarda os stats em outro sprite (companheiro, veículo) ou tem efeito extra sobrescreve."""
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)

    def equipar(self): 
        pass


class ArmaDeRajada(Arma):
    """Uma ativação (cooldown) dispara `burst_count` tiros, um a cada `burst_interval` ms (stats do
    perfil). A rajada só começa com alvo no alcance e para se o alvo sumir: sem alvo, o cooldown
    não é gasto. A subclasse diz como achar o alvo (`buscar_alvo`) e como atirar (`atirar`)."""

    def __init__(self, jogador, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.tiros_restantes = 0
        self.ultimo_tiro_burst = 0

    def buscar_alvo(self):
        return self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=self.raio_maximo)

    @abstractmethod
    def atirar(self, alvo):
        """Cria o projétil de um tiro da rajada contra `alvo`."""

    def disparar(self) -> bool:
        if self.tiros_restantes > 0 or self.buscar_alvo() is None:
            return False
        self.tiros_restantes = self.burst_count
        return True

    def update(self, delta_time):
        super().update(delta_time)
        if self.tiros_restantes <= 0:
            return
        agora = relogio.agora()
        if agora - self.ultimo_tiro_burst > self.burst_interval:
            alvo = self.buscar_alvo()
            if alvo is None:
                self.tiros_restantes = 0
                return
            self.atirar(alvo)
            self.tiros_restantes -= 1
            self.ultimo_tiro_burst = agora
