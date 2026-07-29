from .projetil import ProjetilUniversal

class ProjetilNeedler(ProjetilUniversal):
    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, alvo):
        super().__init__(
            posicao_inicial=posicao_inicial, 
            grupos=grupos, 
            game=game, 
            dono=dono,  
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
        if self.alvo_atual and self.alvo_atual.alive():
            desejado = (self.alvo_atual.posicao - self.posicao).normalize()
            self.direcao = (self.direcao + desejado * self.forca_curva).normalize()
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
        alvo.receber_dano(self.dano)

        if alvo.agulhas_presas >= 7:
            # Efeito de explosão (Dano massivo)
            ArtilhariaAviso(
                posicao             = alvo.posicao,
                grupos              = self.game.all_sprites,
                game                = self.game, 
                dono                = self.dono,
                preset='needler_supercombine'
                )
            alvo.agulhas_presas = 0
            # spawn_explosion_effect(alvo.posicao) # Dica para o futuro

        self.kill()