import pygame

class PlayerCombat:
    def adicionar_escudo(self, valor):
        self.escudo_maximo = valor
        self.escudo_atual = valor

    def atualizar_escudo(self, delta_time):
        # Não possui shield
        if self.escudo_maximo <= 0:
            return
        # Shield já cheio
        if self.escudo_atual >= self.escudo_maximo:
            return

        agora = pygame.time.get_ticks()
        tempo_sem_dano = (agora - self.ultimo_dano_sofrido)
        # Começou Regeneração
        if tempo_sem_dano >= self.shield_regen:
            self.regenerando_escudo = True
        # Regenera
        if self.regenerando_escudo:

            self.escudo_atual += (
                self.velocidade_regen_escudo * delta_time
            )
            # Clamp
            if self.escudo_atual >= self.escudo_maximo:

                self.escudo_atual = self.escudo_maximo
                self.regenerando_escudo = False


    def receber_dano(self, dano, ignorar_invencibilidade=False):
        """
        Sistema central de dano do player.
        """
        # Invencibilidade
        if self.invencivel and not ignorar_invencibilidade:
            return
        # Ativa iframe
        if not ignorar_invencibilidade:
            self.invencivel = True
            self.tempo_ultimo_dano = pygame.time.get_ticks()

        # Interrompe Regeneração de Escudo
        self.ultimo_dano_sofrido = pygame.time.get_ticks()
        self.regenerando_escudo = False

        # ===== ESCUDO =====
        if self.escudo_atual > 0:
            self.escudo_atual -= dano
            # Sobrou dano
            if self.escudo_atual < 0:
                dano_restante = abs(self.escudo_atual)

                self.escudo_atual = 0
                self.vida_atual -= dano_restante
        # ===== VIDA =====
        else:
            self.vida_atual -= dano
        # Clamp
        if self.vida_atual < 0:
            self.vida_atual = 0
        # Morte
        if self.vida_atual <= 0:
            self.kill()

    def tomar_dano(self, inimigo):
        """
        Compatibilidade com projéteis/inimigos antigos.
        """
        self.receber_dano(inimigo.dano)


    def tomar_dano_direto(self, dano):
        """
        Compatibilidade com código antigo.
        Ignora invencibilidade.
        """
        self.receber_dano(dano, ignorar_invencibilidade=True)
                
    def curar(self, quantidade):
        self.vida_atual = min(self.vida_atual + quantidade, self.vida_maxima)

    def atualizar_invencibilidade(self):
        if self.invencivel:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_ultimo_dano > self.duracao_invencibilidade:
                self.invencivel = False
                
            # Pisca player
            alpha = 255 if int(pygame.time.get_ticks() / 50) % 2 == 0 else 0
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)
