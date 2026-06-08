import pygame
import math
from abc import ABC, abstractmethod
from source.windows.settings import *
from source.feats.assets import ASSETS
from source.data.weapon_data import *

# Fusão dos dicionários de Dataclasses
ALL_DATA = {**WEAPON_DATA, **COMPANION_DATA}


class Arma(ABC):
    def __init__(self, jogador, **kwargs):
        self.jogador = jogador
        self.nivel = 1
        self.dano = 0
        self.velocidade = 0
        self.cooldown = 0
        self.ultimo_tiro = 0
        self.nome = ""
        self.descricao = ""

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

    def encontrar_inimigo_mais_proximo(self, grupo_inimigos, raio_maximo=2000):
        if not grupo_inimigos: 
            return None
        
        menor_dist_sq = raio_maximo ** 2
        inimigo_mais_proximo = None

        for inimigo in grupo_inimigos:
            # TRAVA COMPLETA: Se estiver totalmente invisível OU sumindo/escondido, ignora!
            alpha = getattr(inimigo, 'alpha_atual', 255)
            fase_invis = getattr(inimigo, 'invis_phase', 'none')
            
            if alpha == 0 or fase_invis in ['fade_out', 'hold']:
                continue

            dist_sq = self.jogador.posicao.distance_squared_to(inimigo.posicao)
            if dist_sq < menor_dist_sq:
                menor_dist_sq = dist_sq
                inimigo_mais_proximo = inimigo
        return inimigo_mais_proximo
    
    def update(self, delta_time):
        """Lógica de cadência baseada no tick rate do pygame"""
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro > self.cooldown:
            if self.disparar():
                self.ultimo_tiro = agora
    
    @abstractmethod
    def disparar(self) -> bool:
        """Deve retornar True se o disparo foi realizado com sucesso para resetar o cooldown"""
        pass
    
    def upgrade(self): 
        self.nivel += 1 

    def equipar(self): 
        pass