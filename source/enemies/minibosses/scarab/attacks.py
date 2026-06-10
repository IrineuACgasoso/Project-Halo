import pygame
from source.feats.projetil import PlasmaGun
from source.systems.entitymanager import entity_manager

class ScarabAttacks:
    def logica_laser(self, agora, delta_time):
        if self.estado_combate == 'MOVENDO':
            if agora - self.ultimo_laser > self.cooldown_laser:
                self.estado_combate = 'CARREGANDO'
                self.tempo_inicio_carga = agora
                # Reseta a mira do laser para a posição do Scarab antes de começar
                self.beam_principal.mira_atual = pygame.math.Vector2(self.posicao)
        
        elif self.estado_combate == 'CARREGANDO':
            self.game.camera.shake(intensidade=5 * self.intensidade_shake)
            if agora - self.tempo_inicio_carga > self.duracao_carga:
                self.estado_combate = 'DISPARANDO_LASER'
                self.tempo_inicio_laser = agora

        elif self.estado_combate == 'DISPARANDO_LASER':
            self.game.camera.shake(intensidade=10 * self.intensidade_shake)
            # O feixe persegue o jogador continuamente
            self.beam_principal.update(delta_time, self.jogador.posicao)
            
            if agora - getattr(self, 'tempo_inicio_laser', 0) > self.duracao_laser:
                self.estado_combate = 'MOVENDO'
                self.ultimo_laser = agora

    def draw_laser(self, superficie, deslocamento):
        if self.estado_combate == 'DISPARANDO_LASER':
            # Offset vertical para o canhão no sprite
            offset_canhao = pygame.math.Vector2(0, -360) 
            self.beam_principal.draw(superficie, deslocamento, origem_offset=offset_canhao)

    def gerenciar_rajada(self, agora):
        if self.tiros_restantes_rajada > 0:
            if agora - getattr(self, 'ultimo_tiro_rajada', 0) >= self.delay_entre_tiros:
                self.plasma_array()
                self.tiros_restantes_rajada -= 1
                self.ultimo_tiro_rajada = agora
        else:
            if agora - getattr(self, 'ultimo_tiro_plasma', 0) >= getattr(self, 'cooldown_plasma', 4000):
                self.tiros_restantes_rajada = self.pente_rajada 
                # Rolagem de cooldown corrigida para usar o sistema da BaseEnemy
                self.cooldown_plasma = self.novo_cooldown(4000, 8000)
                self.ultimo_tiro_plasma = agora

    def plasma_array(self):
        # Dispara de dois "canhões laterais" simulados por offsets
        offsets = [pygame.math.Vector2(160, -40), pygame.math.Vector2(-160, -40)]
        for off in offsets:
            p_pos = self.posicao + off
            
            # Cálculo seguro do vetor do tiro
            dir_vec = self.jogador.posicao - p_pos
            if dir_vec.length() > 0:
                dir_tiro = dir_vec.normalize()
            else:
                dir_tiro = pygame.math.Vector2(1, 0)
            
            PlasmaGun(
                posicao_inicial = p_pos,
                grupos          = (entity_manager.all_sprites,),
                jogador         = self.jogador,
                game            = self.game,
                dono            = 'INIMIGO',
                tamanho         = (96, 16), # Plasma "Heavy"
                dano            = 20,
                velocidade      = 750,
                direcao_spread  = dir_tiro,
                vai_rotacionar  = True
            )