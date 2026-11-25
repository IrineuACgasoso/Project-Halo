from .projetil import ProjetilUniversal
from source.systems.entitymanager import entity_manager
from source.utils.vetores import direcao_segura
from source.systems.dano import Dano, PROJETIL

class ProjetilNeedler(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, alvo, fonte=None):
        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono,
            fonte=fonte,
            sprite_key='needler', 
            tamanho=tamanho, 
            dano=dano, 
            velocidade=velocidade, 
            duracao=3000, 
            direcao_custom=direcao_spread, 
            rotacionar=True
            )
        self.alvo_atual = alvo
        self.forca_curva = 0.18

    def update(self, delta_time):
        # Alvo que some (invisível) é perdido de vez: a agulha segue reto
        if self.alvo_atual and not (self.alvo_atual.alive() and self.alvo_atual.alvejavel):
            self.alvo_atual = None
        if self.alvo_atual:
            desejado = direcao_segura(self.posicao, self.alvo_atual.posicao, padrao=self.direcao)
            nova = self.direcao + desejado * self.forca_curva
            if nova.length_squared() > 0:
                self.direcao = nova.normalize()
            if self.rotacionar:
                self.image = self.renderizar_com_rotacao()
                self.rect = self.image.get_rect(center=self.rect.center)
        super().update(delta_time)


    def ao_atingir_alvo(self, alvo):
        # Import Local
        from source.feats.skills.artilharia import ArtilhariaAviso
        # 1. Checa invulnerabilidade antes de tudo
        if getattr(alvo, 'invulneravel', False):
            return # Atravessa sem contar agulha e sem morrer

        # 2. Lógica de Supercombine (Só executa se for vulnerável)
        if not hasattr(alvo, 'agulhas_presas'):
            alvo.agulhas_presas = 0
        
        alvo.agulhas_presas += 1
        alvo.receber_dano(Dano(self.dano, PROJETIL, self.fonte, habilidade=self.habilidade))

        if alvo.agulhas_presas >= 7:
            # Efeito de explosão (Dano massivo)
            ArtilhariaAviso(
                posicao             = alvo.posicao,
                grupos              = entity_manager.all_sprites,
                game                = self.game, 
                dono                = self.dono, fonte=self.fonte, habilidade=self.habilidade,
                preset='needler_supercombine'
                )
            alvo.agulhas_presas = 0
            # spawn_explosion_effect(alvo.posicao) # Dica para o futuro

        self.kill()