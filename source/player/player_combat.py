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

    def atualizar_veiculo(self, delta_time):
        """Compatibilidade: o controle de entrada/saída/vida do veículo agora é
        feito via entrar_veiculo()/sair_veiculo(), chamados pelo próprio Vehicle.
        Este método não faz mais nada sozinho — pode ser removido do loop principal."""
        pass

    def entrar_veiculo(self, veiculo, vida_maxima):
        """Chamado pelo Vehicle quando o jogador embarca. A partir daqui,
        todo dano recebido é absorvido pelo veículo em vez do player."""
        self.veiculo_atual = veiculo
        self.vida_veiculo_maxima = vida_maxima
        self.vida_veiculo_atual = vida_maxima
        self.in_veicule = True
        self.has_entered = True

    def sair_veiculo(self):
        """Chamado pelo Vehicle quando o jogador desembarca (por escolha ou destruição)."""
        self.veiculo_atual = None
        self.in_veicule = False
        self.has_entered = False
        self.vida_veiculo_atual = 0

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
        
        # ===== VEÍCULO =====
        if self.in_veicule and self.vida_veiculo_atual > 0:
            self.vida_veiculo_atual -= dano
            if self.vida_veiculo_atual <= 0:
                self.vida_veiculo_atual = 0
                # O veículo absorve todo o dano (sem transbordo para escudo/vida).
                # A destruição em si é responsabilidade do Vehicle, que também
                # cuida do cooldown até poder ser chamado de novo.
                if self.veiculo_atual is not None:
                    self.veiculo_atual.destruir()

        # ===== ESCUDO =====
        elif self.escudo_atual > 0:
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
            

    def tomar_dano(self, inimigo, colisao=False):
        """
        Compatibilidade com projéteis/inimigos antigos.
        """
        self.receber_dano(inimigo.dano)
        if colisao:
            self._contra_atacar_com_espinhos(inimigo)


    def tomar_dano_direto(self, dano):
        """
        Compatibilidade com código antigo.
        Ignora invencibilidade.
        """
        self.receber_dano(dano, ignorar_invencibilidade=True)

    # ===== ESPINHOS (contra-ataque, ex: Mjolnir Punch) =====
    def configurar_espinhos(self, dano, cooldown):
        """Chamado pela arma responsável (ex: MjolnirPunch) ao equipar/upgradar."""
        self.dano_espinhos = dano
        self.espinho_cooldown = cooldown

    def atualizar_espinhos(self):
        """Recarrega o espinho disponível respeitando o cooldown.
        Chamado a cada frame pela arma dona do sistema (ex: MjolnirPunch.update)."""
        if self.espinho_cooldown <= 0 or self.espinho_disponivel:
            return
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_espinho_carregado >= self.espinho_cooldown:
            self.espinho_disponivel = True


    def _contra_atacar_com_espinhos(self, inimigo):
        """Consome o espinho disponível (se houver) causando dano de volta ao inimigo."""
        if self.dano_espinhos <= 0 or not self.espinho_disponivel:
            return
        if hasattr(inimigo, 'receber_dano'):
            inimigo.receber_dano(self.dano_espinhos)
        self._spawnar_faiscas_espinhos()
        self.espinho_disponivel = False
        self.ultimo_espinho_carregado = pygame.time.get_ticks()


    def _spawnar_faiscas_espinhos(self):
        """Efeito visual rápido no momento do contra-ataque. Falha em
        silêncio se o player não tiver referência ao grupo de sprites."""
        grupo = getattr(getattr(self, 'game', None), 'all_sprites', None)
        if grupo is None:
            return
        from source.feats.effects import EfeitoFaiscas
        EfeitoFaiscas(posicao=self.posicao, grupos=(grupo,))
                
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