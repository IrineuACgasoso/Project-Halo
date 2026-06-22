import pygame
from source.enemies.base.enemy_base import BaseEnemy
from source.feats.effects import RaioEscudo
from source.feats.auras import EnergyAura
from source.systems.entitymanager import entity_manager

class Watcher(BaseEnemy):
    def __init__(self, posicao, game, vida_base=25, velocidade_base=180, intervalo=2000, porcentagem=0.05, min_esc=15, max_esc=40, cor_raio=(255, 120, 0), sprite_key='watcher', variante='default'):
        # MUDANÇA: dano_base=0 para que ele SÓ dê escudo (sem dano por contato físico)
        super().__init__(posicao, vida_base=vida_base, dano_base=0, velocidade_base=velocidade_base, game=game, sprite_key=sprite_key)
        
        self.setup_animation(estado_inicial='left', velocidade_animacao=300)

        self.alvo_protegido = None
        self.distancia_ideal = 120 
        
        self.ultimo_escudo = pygame.time.get_ticks()
        self.intervalo_escudo = intervalo    
        self.porcentagem_escudo = porcentagem  
        self.min_escudo = min_esc            
        self.max_escudo = max_esc            
        self.cor_raio = cor_raio 

    def buscar_novo_alvo(self):
        """Procura o aliado mais próximo para orbitar (mesmo que o escudo esteja cheio)."""
        menor_distancia = float('inf')
        novo_alvo = None
        
        for inimigo in entity_manager.inimigos_grupo.sprites():
            if inimigo != self and not isinstance(inimigo, Watcher) and inimigo.alive():
                distancia = (inimigo.posicao - self.posicao).length()
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    novo_alvo = inimigo
                    
        self.alvo_protegido = novo_alvo

    def aplicar_escudo(self):
        """Dispara o raio apenas se o aliado tiver espaço no escudo."""
        agora = pygame.time.get_ticks()
        
        if self.alvo_protegido and agora - self.ultimo_escudo >= self.intervalo_escudo:
            distancia_atual = (self.alvo_protegido.posicao - self.posicao).length()
            if distancia_atual <= (self.distancia_ideal * 2):
                
                self.ultimo_escudo = agora
                
                # CORREÇÃO: Verifica se o alvo não tem escudo_maximo configurado ou se está zerado.
                # Isso resolve o problema com mixins do Knight que criavam 'escudo_atual = 0' mas ignoravam o máximo.
                if not hasattr(self.alvo_protegido, 'escudo_maximo') or self.alvo_protegido.escudo_maximo <= 0:
                    self.alvo_protegido.adicionar_escudo(self.alvo_protegido.vida_base)
                    self.alvo_protegido.escudo_atual = 0
                    
                # Só calcula e transfere SE o escudo atual for menor que o máximo
                if self.alvo_protegido.escudo_atual < self.alvo_protegido.escudo_maximo:
                    
                    valor_calculado = self.alvo_protegido.escudo_maximo * self.porcentagem_escudo
                    transferencia = max(self.min_escudo, min(valor_calculado, self.max_escudo))
                    
                    espaco_disponivel = self.alvo_protegido.escudo_maximo - self.alvo_protegido.escudo_atual
                    transferencia = min(transferencia, espaco_disponivel)
                    
                    self.alvo_protegido.escudo_atual += transferencia
                    
                    if transferencia > 0:
                        RaioEscudo(
                            fonte=self, 
                            alvo=self.alvo_protegido, 
                            grupos=(entity_manager.all_sprites,), 
                            cor=self.cor_raio 
                        )

    def update(self, delta_time, paredes=None):
        if self.alvo_protegido is None or not self.alvo_protegido.alive():
            self.buscar_novo_alvo()

        direcao_movimento = pygame.math.Vector2(0, 0)
        olhar_para_x = self.jogador.posicao.x

        if self.alvo_protegido:
            olhar_para_x = self.alvo_protegido.posicao.x
            vetor_para_alvo = self.alvo_protegido.posicao - self.posicao
            distancia = vetor_para_alvo.length()
            
            if distancia > 0:
                direcao_alvo = vetor_para_alvo.normalize()
                if distancia > self.distancia_ideal + 15:
                    direcao_movimento = direcao_alvo
                elif distancia < self.distancia_ideal - 15:
                    direcao_movimento = -direcao_alvo
                    
        else:
            vetor_fuga = self.posicao - self.jogador.posicao
            if vetor_fuga.length() > 0:
                direcao_movimento = vetor_fuga.normalize()

        if direcao_movimento.length() > 0:
            direcao_movimento = direcao_movimento.normalize()
            self.posicao += direcao_movimento * self.velocidade * delta_time
            
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        direcao_x = olhar_para_x - self.posicao.x
        self.set_sprite_direction(direcao_x)
        
        self.aplicar_escudo()
        self.animar()


class SuperWatcher(Watcher):
    def __init__(self, posicao, game):
        super().__init__(
            posicao=posicao, 
            game=game,
            vida_base=75,             
            velocidade_base=300,      
            intervalo=2000,           
            porcentagem=0.10,         
            min_esc=20,               
            max_esc=60,              
            cor_raio=(255, 120, 0),   
            sprite_key='watcher',
            variante='omega'
        )
        
        self.velocidade = self.velocidade_base
        self.titulo = "ÔMEGA WATCHER"
        
        self.adicionar_escudo(self.vida_base * 2)
        
        self.aura = EnergyAura(
            owner=self, 
            raio=60,               
            dano_contato=0, 
            game=self.game, 
            cor_base=(255, 100, 0), 
            impenetravel=False,
        )

    def update(self, delta_time, paredes=None):
        super().update(delta_time, paredes)

        # Gerenciamento dinâmico da aura visual do SuperWatcher baseado no escudo
        if hasattr(self, 'escudo_atual') and self.escudo_atual > 0:
            if self.aura is None or not self.aura.alive():
                self.aura = EnergyAura(
                    owner=self, 
                    raio=60,               
                    dano_contato=0, 
                    game=self.game, 
                    cor_base=(255, 100, 0), 
                    impenetravel=False,
                )
        elif hasattr(self, 'escudo_atual') and self.escudo_atual <= 0:
            if self.aura and self.aura.alive():
                self.aura.kill()