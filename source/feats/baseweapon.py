import pygame
import math
from source.windows.settings import *
from source.player.player import *
from source.feats.assets import ASSETS
from source.feats.data import *

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
        """
        Aplica os increases elegíveis do nivel atual.
        target=None  → aplica em self (arma)
        target=obj   → aplica no companion (ou lista de companions)
        """
        targets = target if isinstance(target, list) else ([target] if target else [self])
        stats = ALL_DATA[nome_asset]['stats']

        for attr, meta in stats.items():
            if attr.startswith('_') or not meta['increase'] or not meta['label']:
                continue
            if not self._deve_melhorar(meta['range'], nivel):
                continue
            for t in targets:
                atual = getattr(t, attr)
                novo  = atual + meta['increase']
                if 'min' in meta:
                    novo = max(meta['min'], novo)
                setattr(t, attr, novo)

    def ver_proximos_upgrades(self, nivel_proximo: int, nome_asset: str, target=None) -> dict:
        """
        Retorna {attr: {label, atual, proximo}} para todos os atributos com label.
        target=None → lê de self
        """
        t = target if target and not isinstance(target, list) else (target[0] if target else self)
        stats = ALL_DATA[nome_asset]['stats']
        resultado = {}

        for attr, meta in stats.items():
            if not meta['label']:
                continue
            if attr.startswith('_'):
                # atributo virtual — valor base do data, arma preenche depois
                resultado[attr] = {'label': meta['label'], 'atual': 0, 'proximo': 0}
                continue

            atual = getattr(t, attr, meta['value'])
            if self._deve_melhorar(meta['range'], nivel_proximo):
                proximo = atual + meta['increase']
                if 'min' in meta:
                    proximo = max(meta['min'], proximo)
            else:
                proximo = atual

            resultado[attr] = {'label': meta['label'], 'atual': atual, 'proximo': proximo}

        return resultado

    def get_estatisticas_para_exibir(self, nivel_proximo: int, nome_asset: str, target=None) -> list[str]:
        """
        Formata apenas o que muda no próximo nível.
        """
        proximos = self.ver_proximos_upgrades(nivel_proximo, nome_asset, target)
        linhas = []
        for info in proximos.values():
            if info['atual'] == info['proximo']:
                continue
            fmt = lambda v: str(int(v)) if isinstance(v, (int, float)) and v != float('inf') else str(v)
            linhas.append(f"{info['label']}: {fmt(info['atual'])} -> {fmt(info['proximo'])}")
        return linhas
    
    # ── Inicializar atributos a partir do data ───────────────────────────────────

    def inicializar_stats(self, nome_asset: str, target=None):
        """
        Lê os 'value' do data e seta os atributos no target (ou self).
        Chamado no __init__ de cada arma.
        """
        t = target or self
        stats = ALL_DATA[nome_asset]['stats']
        for attr, meta in stats.items():
            if not attr.startswith('_') and meta['value'] is not None:
                setattr(t, attr, meta['value'])

    # ── Interface obrigatória ────────────────────────────────────────────────────

    def encontrar_inimigo_mais_proximo(self, grupo_inimigos, raio_maximo=2000):
        if not grupo_inimigos: return None
        menor_dist_sq = raio_maximo ** 2
        inimigo_mais_proximo = None
        for inimigo in grupo_inimigos:
            dist_sq = self.jogador.posicao.distance_squared_to(inimigo.posicao)
            if dist_sq < menor_dist_sq:
                menor_dist_sq = dist_sq
                inimigo_mais_proximo = inimigo
        return inimigo_mais_proximo
    

    def update(self, delta_time):
        """Lógica de cooldown padronizada"""
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro > self.cooldown:
            # O disparar() agora pode retornar True/False se de fato atirou
            if self.disparar():
                self.ultimo_tiro = agora
    

    @abstractmethod
    def disparar(self) -> bool:
        """Deve retornar True se o disparo foi realizado com sucesso"""
        pass
    
    def upgrade(self): self.nivel += 1 

    def equipar(self): pass 


