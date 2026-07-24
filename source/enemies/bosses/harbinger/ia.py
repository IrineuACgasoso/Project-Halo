# source/enemies/bosses/harbinger/ia.py
import pygame
import random
from source.systems.entitymanager import entity_manager


class HarbingerIA:
    """Gerencia a máquina de estados tática da Rainha Endless.

    Estados principais (self.estado_boss):
        - 'idle'        : comportamento padrão, todas as habilidades liberadas.
        - 'recharging'  : ativado nos marcos de 60% e 25% de vida (cada um
                          UMA única vez). Dispara a onda EMP uma vez só,
                          fica diretamente invulnerável, ergue a Energy
                          Aura amarela e força o Spawner a gerar inimigos.
                          Quando todos eles (menos ela) morrem, ela volta
                          ao combate já mais forte. A animação fica
                          congelada durante esse estado.

    Teleporte em Cadeia:
        A cada marco de recarga superado ela ganha +1 carga de teleporte
        (self.teleporte_cargas) — vale IGUALMENTE para o teleporte
        ofensivo e o defensivo. Ao acionar um teleporte, ela consome todas
        as cargas em sequência: teleporta, executa o ataque correspondente
        até ele terminar por completo (inclusive a rajada de Energy Blast
        do defensivo, se for o caso), espera um breve intervalo
        VULNERÁVEL, e teleporta de novo.

    self.wait:
        Cooldown genérico (mesmo padrão usado pelo Arbiter) para evitar
        que as habilidades se atropelem umas nas outras. É setado ao fim
        de uma rajada de carabina, ao sair da recarga, e — com um valor
        maior — ao final de uma cadeia de teleportes OFENSIVOS, dando ao
        jogador uma janela de reação para desviar.
    """

    # ------------------------------------------------------------------
    # LOOP PRINCIPAL
    # ------------------------------------------------------------------
    def executar_ia_harbinger(self, agora, delta_time, paredes=None):
        direcao = (self.jogador.posicao - self.posicao)

        # 1. Motor nativo de camuflagem sempre atualiza (independe de estado)
        self.atualizar_invisibilidade(delta_time * 1000)

        # 2. Transição para RECHARGING nos marcos de 60% e 25% de vida
        if (not self.recharge_ativado and self.marcos_recarga_pendentes
                and self.vida <= self.marcos_recarga_pendentes[0] * self.vida_maxima):
            self._entrar_em_recarga()

        # 3. Estado RECHARGING trava todas as outras habilidades e a animação
        if self.estado_boss == 'recharging':
            self._executar_recharging(agora)
            return

        # 4. Gerenciamento do ciclo nativo de teleporte/invulnerabilidade
        if self.teleportando:
            if self.invis_phase is not None:
                return  # ainda no meio do fade nativo
            self.teleportando = False
            self.is_invulneravel = False
            self.hitbox.center = self.rect.center

            if self.teleporte_em_cadeia and self.teleporte_cargas_restantes > 0:
                # Ainda há cargas: mas só marcamos a espera aqui; se um
                # Energy Blast tiver sido iniciado por este salto (teleporte
                # defensivo), o passo 5 abaixo tem prioridade e represa o
                # avanço da cadeia até a rajada terminar por completo.
                self.teleporte_aguardando_proximo = True
                self.teleporte_cadeia_cronometro = 0
            else:
                self._finalizar_cadeia_teleporte()

        # 5. Energy Blast tem PRIORIDADE sobre o avanço da cadeia — garante
        # que, no teleporte defensivo, cada salto realize sua rajada
        # completa antes de pular para o próximo (isso é o que fazia as
        # cargas parecerem só funcionar no ofensivo).
        if self.energy_blast_ativo:
            self._executar_energy_blast(delta_time)
            self._flip_visual(direcao)
            return
        
        if getattr(self, 'teleport_burst_ativo', False):
            if agora >= getattr(self, 'teleport_burst_liberacao', 0):
                self.teleport_burst_ativo = False
                self.disparar_teleport_burst()

        # 6. Intervalo breve e VULNERÁVEL entre teleportes da mesma cadeia
        if self.teleporte_aguardando_proximo:
            self.teleporte_cadeia_cronometro += delta_time * 1000
            if self.teleporte_cadeia_cronometro >= self.teleporte_intervalo_cadeia:
                self.teleporte_aguardando_proximo = False
                a, b = self.teleporte_cadeia_ab
                self.teleporte_cargas_restantes -= 1
                self.teleporte(a, b, ofensivo=self.teleporte_cadeia_ofensivo)
            self._flip_visual(direcao)
            return

        # 7. Teleporte de Recomposição — decide ofensivo/defensivo pela distância
        if (self.wait <= 0 and agora - self.ultimo_tp > self.tp_cooldown
                and not self.teleporte_em_cadeia):
            if direcao.length_squared() > 1170 ** 2:
                # Longe demais: cadeia OFENSIVA, aproxima e ataca de perto
                self._iniciar_cadeia_teleporte(400, 440, ofensivo=True)
                self.ultimo_tp = agora
                return
            elif direcao.length_squared() < 300 ** 2:
                # Encurralada: cadeia DEFENSIVA, foge e prepara Energy Blast
                self._iniciar_cadeia_teleporte(500, 580, ofensivo=False)
                self.ultimo_tp = agora
                return

        # 8. Consome o wait genérico (não bloqueia o movimento, só novas ações)
        if self.wait > 0:
            self.wait = max(0, self.wait - delta_time * 1000)

        # 9. Movimentação de perseguição padrão
        if direcao.length_squared() > 0:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * delta_time
            if paredes:
                self.aplicar_colisao_mapa(paredes)
            self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # 10. Sequenciador padrão de disparos de Carabina (estado idle)
        if self.wait <= 0:
            if agora - self.ultima_carabina >= self.cooldown_carabin:
                self.carabina_restante = self.contagem_carabina
                self.cooldown_carabin = random.choice([6000, 8000, 10000, 11000])
                self.ultima_carabina = agora

            if self.carabina_restante > 0:
                self.cronometro_carabina += delta_time * 1000
                if self.cronometro_carabina >= self.intervalo_carabina:
                    self.cronometro_carabina = 0
                    self.carabina_restante -= 1
                    self.carabin()
                    if self.carabina_restante <= 0:
                        # Rajada encerrada: pequeno respiro antes da próxima ação
                        self.wait = max(self.wait, 350)

        self._flip_visual(direcao)

    # ------------------------------------------------------------------
    # TELEPORTE EM CADEIA (múltiplas cargas por acionamento — ofensivo E defensivo)
    # ------------------------------------------------------------------
    def _iniciar_cadeia_teleporte(self, a, b, ofensivo):
        """Dispara a primeira carga da cadeia. As cargas restantes
        (self.teleporte_cargas, que sobe a cada marco de recarga superado)
        são consumidas automaticamente pelo loop principal — cada uma com
        um breve intervalo VULNERÁVEL entre si."""
        self.teleporte_em_cadeia = True
        self.teleporte_cargas_restantes = self.teleporte_cargas - 1
        self.teleporte_cadeia_ofensivo = ofensivo
        self.teleporte_cadeia_ab = (a, b)
        self.teleporte(a, b, ofensivo=ofensivo)

    def _finalizar_cadeia_teleporte(self):
        """Encerra a cadeia (todas as cargas consumidas). Se a cadeia foi
        OFENSIVA, aplica um cooldown extra (self.wait) para dar ao jogador
        uma janela de reação antes da próxima ação da boss."""
        era_ofensiva = self.teleporte_cadeia_ofensivo
        self.teleporte_em_cadeia = False
        if era_ofensiva:
            self.wait = max(self.wait, self.cooldown_pos_teleporte_ofensivo)

    # ------------------------------------------------------------------
    # ESTADO: RECHARGING
    # ------------------------------------------------------------------
    def _entrar_em_recarga(self):
        """Nos marcos de 60% e 25% de vida: dispara a onda EMP uma única
        vez, fica invulnerável, ergue a Energy Aura amarela e força o
        Spawner a gerar inimigos que o jogador precisa limpar."""
        self.marcos_recarga_pendentes.pop(0)
        self.estagio_recarga += 1

        self.recharge_ativado = True
        self.estado_boss = 'recharging'
        self.permitir_spawns_normais = True
        self.recharge_spawn_liberado = True
        self.recharge_spawn_timer_inicio = pygame.time.get_ticks()

        # Cancela qualquer coisa em andamento para não sobrepor com a recarga
        self.energy_blast_ativo = False
        self.teleportando = False
        self.teleporte_em_cadeia = False
        self.teleporte_aguardando_proximo = False
        self.wait = 0

        self.ativar_recarga()  # definido em attacks.py: EMP único, invulnerabilidade,
                                # EnergyAura amarela e spawn forçado de inimigos

    def _executar_recharging(self, agora):
        """Fase 1: spawner liberado por `duracao_spawner_recarga` ms para
        gerar inimigos. Fase 2: spawner travado de novo, aguardando todos
        os inimigos convocados (menos ela) morrerem para sair da recarga.
        A animação da boss fica congelada nesse estado (ver core.py)."""
        if self.recharge_spawn_liberado:
            if agora - self.recharge_spawn_timer_inicio >= self.duracao_spawner_recarga:
                self.recharge_spawn_liberado = False
                self.permitir_spawns_normais = False
            else:
                return  # ainda no período de geração de inimigos

        inimigos_vivos = [i for i in entity_manager.inimigos_grupo.sprites() if i is not self]
        if len(inimigos_vivos) == 0:
            self._sair_da_recarga()

    def _sair_da_recarga(self):
        self.estado_boss = 'idle'
        self.recharge_ativado = False
        self.permitir_spawns_normais = False
        self.wait = 500  # pequeno respiro antes de voltar a agir
        self.desativar_recarga()  # remove a EnergyAura e a invulnerabilidade
        self._aplicar_buffs_pos_recarga()

    def _aplicar_buffs_pos_recarga(self):
        """Buffs cumulativos concedidos ao sobreviver a cada marco de
        recarga (60% e 25%): mais tiros por rajada, projéteis mais rápidos
        e mais uma carga de teleporte em cadeia (ofensivo E defensivo)."""
        self.contagem_carabina += 1
        self.contagem_energy_blast += 1
        self.teleporte_cargas += 1

        self.buff_ofensivo_mult += 0.15  # velocidade de carabina/energy blast
        self.intervalo_carabina = max(80, int(self.intervalo_carabina * 0.85))
        self.energy_blast_intervalo = max(150, int(self.energy_blast_intervalo * 0.85))

    # ------------------------------------------------------------------
    # ENERGY BLAST ("Carabin Maior") — pós teleporte defensivo
    # ------------------------------------------------------------------
    def _executar_energy_blast(self, delta_time):
        """Enquanto ativo, a Harbinger congela no lugar e intercala os disparos."""
        self.energy_blast_cronometro += delta_time * 1000
        if self.energy_blast_cronometro >= self.energy_blast_intervalo:
            self.energy_blast_cronometro = 0
            self.disparar_energy_blast()

    # ------------------------------------------------------------------
    def _flip_visual(self, direcao):
        if direcao.x < 0:
            self.estado_animacao = 'left'
        elif direcao.x > 0:
            self.estado_animacao = 'right'