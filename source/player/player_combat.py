from source.systems.gameclock import relogio
from source.systems.dano import Dano, CONTATO
from source.systems.eventos import eventos, DANO_CAUSADO
from source.systems.status import multiplicador_de_dano

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

        agora = relogio.agora()
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

    def receber_dano(self, dano):
        """Contrato de dano do jogador (roteiro E1): i-frames, veículo, escudo e vida, nessa ordem."""
        # Invencibilidade
        if self.invencivel and not dano.ignora_iframes:
            return
        # Ativa iframe
        if not dano.ignora_iframes:
            self.invencivel = True
            self.tempo_ultimo_dano = relogio.agora()

        # Interrompe Regeneração de Escudo
        self.ultimo_dano_sofrido = relogio.agora()
        self.regenerando_escudo = False

        valor = dano.valor * multiplicador_de_dano(dano, self)   # buff de quem causa × fraqueza
        # ===== VEÍCULO =====
        if self.in_veicule and self.vida_veiculo_atual > 0:
            self.vida_veiculo_atual -= valor
            if self.vida_veiculo_atual <= 0:
                self.vida_veiculo_atual = 0
                # O veículo absorve todo o dano (sem transbordo para escudo/vida).
                # A destruição em si é responsabilidade do Vehicle, que também
                # cuida do cooldown até poder ser chamado de novo.
                if self.veiculo_atual is not None:
                    self.veiculo_atual.destruir()

        # ===== ESCUDO =====
        elif self.escudo_atual > 0:
            self.escudo_atual -= valor
            # Sobrou dano
            if self.escudo_atual < 0:
                dano_restante = abs(self.escudo_atual)

                self.escudo_atual = 0
                self.vida_atual -= dano_restante
        # ===== VIDA =====
        else:
            self.vida_atual -= valor
        # Clamp
        if self.vida_atual < 0:
            self.vida_atual = 0
        # Morte
        if self.vida_atual <= 0:
            self.kill()
        eventos.emitir(DANO_CAUSADO, alvo=self, dano=dano, valor=valor)

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
        agora = relogio.agora()
        if agora - self.ultimo_espinho_carregado >= self.espinho_cooldown * self.status.mult_cooldown:
            self.espinho_disponivel = True


    def contra_atacar_com_espinhos(self, inimigo):
        """Chamado pelo CollisionManager quando um inimigo encosta (mesmo durante os i-frames).
        Consome o espinho disponível (se houver) causando dano de volta ao inimigo."""
        if self.dano_espinhos <= 0 or not self.espinho_disponivel or self.status.atordoado:
            return
        inimigo.receber_dano(Dano(self.dano_espinhos, CONTATO, self))
        self._spawnar_faiscas_espinhos()
        self.espinho_disponivel = False
        self.ultimo_espinho_carregado = relogio.agora()


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

    def receber_cura(self, quantidade):
        """Só pelo sistema de status (`aplicar(alvo, Cura(...))`), que já descontou a queimadura."""
        self.vida_atual = min(self.vida_atual + quantidade, self.vida_maxima)

    def receber_escudo(self, quantidade):
        """Só pelo sistema de status (`aplicar(alvo, Escudo(...))`): até o escudo máximo."""
        if self.escudo_maximo > 0:
            self.escudo_atual = min(self.escudo_atual + quantidade, self.escudo_maximo)

    def atualizar_invencibilidade(self):
        if self.invencivel:
            agora = relogio.agora()
            if agora - self.tempo_ultimo_dano > self.duracao_invencibilidade:
                self.invencivel = False
                
            # Pisca player
            alpha = 255 if int(relogio.agora() / 50) % 2 == 0 else 0
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)