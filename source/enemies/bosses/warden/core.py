import pygame
import random
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.auras import EnergyAura
from source.feats.items import Items
from source.systems.entitymanager import entity_manager

# Importações das Mixins locais
from .setup import WardenSetup
from .states import WardenAI
from .functions import WardenFunctions
from .attacks import WardenAttacks

class BaseWarden(BaseEnemy, WardenSetup, WardenAI, WardenAttacks, WardenFunctions):
    """Corpo físico individual do Warden Eternal com função fixa e imutável."""
    def __init__(self, posicao, game, jogador, variante, vida, velocidade, funcao_atual, manager):
        super().__init__(
            posicao, 
            vida_base=vida, 
            dano_base=90, 
            velocidade_base=velocidade, 
            game=game, 
            sprite_key='warden', 
            flip_sprite=True,
            variante=variante
        )
        self.jogador = jogador if jogador else entity_manager.player
        self.setup_animation(estado_inicial='right', velocidade_animacao=300)
        
        # Hitbox estruturada
        self.hitbox = pygame.Rect(0, 0, self.rect.width * 0.4, self.rect.height * 0.8)
        self.hitbox.center = self.rect.center
        
        self.is_invulneravel = False # Sem escudos automáticos de troca de fase
        self.aura = None
        
        self.inicializar_habilidades()
        
        # Injeção das configurações da Lore Accurate Fight
        self.funcao_atual = funcao_atual  # FIXO: Definido no nascimento e nunca muda
        self.manager = manager
        self.is_boss = False # Apenas o DomainConsciousness reportará como Boss para a UI

    def update(self, delta_time, paredes=None):
        agora = pygame.time.get_ticks()
        
        # Gerenciamento de Aura (Apenas se receber algum escudo externo por itens/mixins)
        precisa_de_aura = getattr(self, 'escudo_atual', 0) > 0
        
        if precisa_de_aura:
            if self.aura is None or not self.aura.alive():
                self.aura = EnergyAura(
                    owner=self, 
                    raio=280, 
                    dano_contato=0, 
                    game=self.game, 
                    cor_base=(255, 215, 0), # Amarelo Dourado
                    impenetravel=True
                )
        else:
            if self.aura and self.aura.alive():
                self.aura.kill()
                self.aura = None

        # Executa IA e movimentação
        self.executar_estados(agora, delta_time)
        direcao_x = self.jogador.posicao.x - self.posicao.x 

        if self.estado_habilidade == 'bruiser_leap':
            self.processar_bruiser_leap(agora, delta_time)
        else:
            super().update(delta_time, paredes)
            self.set_sprite_direction(direcao_x)      
        
        self.animar()
        self.hitbox.center = self.rect.center

    def morrer(self, grupos=None):
        if self.aura and self.aura.alive():
            self.aura.kill()
        
        # Remove a si mesmo do rastreio do manager antes de sumir
        if self in self.manager.wardens_vivos:
            self.manager.wardens_vivos.remove(self)
            
        self.kill()


class DomainConsciousness(BaseEnemy):
    """Mente abstrata do Domínio. Serve como o Manager invisível e oficial da Boss Fight."""
    def __init__(self, posicao, game, jogador=None):
        # Inicializa o esqueleto básico do BaseEnemy
        super().__init__(
            posicao, 
            vida_base=4500, # O valor vai direto para o atributo real da classe mãe
            dano_base=0, 
            velocidade_base=0, 
            game=game, 
            sprite_key='warden', 
            flip_sprite=False,
            variante='default'
        )
        self.jogador = jogador if jogador else entity_manager.player
        self.is_boss = True # SÓ ELE tem a tag de Boss para travar o HUD e invocar portais
        self.titulo = "WARDEN ETERNAL, O Guardião do Domínio"
        
        # Transforma este objeto em uma entidade 100% invisível e sem colisão física
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=posicao)
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.is_invulneravel = True 
        
        self.wardens_vivos = []
        self.spawnar_corpos_do_warden()

    def spawnar_corpos_do_warden(self):
        """Materializa os 3 corpos estáveis espalhados simultaneamente na arena."""
        funcoes = ['COMBATENTE', 'ATIRADOR', 'ASSASSINO']
        
        # Offsets calculados a partir do centro do spawn para não nascerem colados
        offsets = [
            pygame.math.Vector2(-200, 40),   # Esquerda -> Combatente
            pygame.math.Vector2(0, -120),    # Recuado/Centro -> Atirador
            pygame.math.Vector2(200, 40)     # Direita -> Assassino
        ]
        
        for i, funcao in enumerate(funcoes):
            pos_corpo = self.posicao + offsets[i]
            
            corpo = BaseWarden(
                posicao=pos_corpo,
                game=self.game,
                jogador=self.jogador,
                variante='default' if funcao == 'COMBATENTE' else 'clone', # Diferenciação visual se houver
                vida=1500,
                velocidade=85 if funcao != 'ASSASSINO' else 105,
                funcao_atual=funcao,
                manager=self
            )
            self.wardens_vivos.append(corpo)

    @property
    def vida(self):
        """A vida exibida no HUD do Boss é a soma exata dos corpos físicos restantes!"""
        if hasattr(self, 'wardens_vivos') and self.wardens_vivos:
            return sum(w.vida for w in self.wardens_vivos if w.alive())
        return 0

    @vida.setter
    def vida(self, valor):
        """Permite que o construtor da classe mãe configure a vida inicial sem quebrar."""
        pass

    def receber_dano(self, quantidade):
        # A mente do domínio não pode ser atingida diretamente por tiros
        pass

    def update(self, delta_time, paredes=None):
        # O manager apenas monitora se a presença física do Warden foi eliminada
        if not self.wardens_vivos:
            self.morrer()

    def morrer(self, grupos=None):
        # Quando todos os corpos caem, a Consciência gera a recompensa unificada
        Items.spawn_drop(self.posicao, grupos, 'big_shard', 12, 100)
        Items.spawn_drop(self.posicao, grupos, 'life_orb', 2, 100)
        Items.spawn_drop(self.posicao, grupos, 'cafe', 1, 5)
        
        # self.kill() desativa o status de is_boss, liberando o portal da fase
        self.kill()