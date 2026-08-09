import pygame
from source.feats.assets import ASSETS
from source.data.weapon_data import VEHICLES_DATA
from source.feats.buddies import Companheiro


class Vehicle(Companheiro):
    """
    Classe base para veículos.

    Herda de Companheiro para reaproveitar posição, animação e a busca de
    inimigos mais próximos, mas troca completamente a "IA": o veículo não
    tem comportamento autônomo (SEGUINDO/ATACANDO/COLETANDO). Ele fica
    parado até ser chamado; quando embarcado, sua posição gruda na do
    jogador, ele atira sozinho em inimigos próximos e pode atropelar quem
    tocar.

    Subclasses (ex: VehicleWarhog) devem sobrescrever apenas
    `decidir_disparo_veiculo` para definir a arma do veículo, e podem
    ajustar `atropelar` se precisarem de um comportamento de colisão
    diferente do padrão (dano por contato + cooldown por inimigo).
    """

    # ---- Dados/atributos ---------------------------------------------------
    def configurar_atributos(self):
        config = VEHICLES_DATA.get(self.nome_asset, VEHICLES_DATA['warhog'])
        self.tipo = config.tipo

        for attr, meta in config.stats.items():
            if not attr.startswith('_') and meta.value is not None:
                setattr(self, attr, meta.value)

        # Estado herdado de Companheiro que não se aplica ao veículo,
        # mas alguns métodos base (animar, etc.) esperam que exista.
        self.estado_logico = 'PARADO'
        self.alvo = None
        self.direcao_movimento = pygame.math.Vector2()
        self.frame_atual = 0
        self.ultimo_update_anim = pygame.time.get_ticks()

        # Estado próprio do veículo
        self.embarcado = False
        self.destruido = False
        self.tempo_destruicao = 0
        self.ultimo_tiro_burst = 0
        self._ultimo_hit_atropelamento = {}

    def carregar_assets(self):
        """Busca sprites em ASSETS['vehicles'][nome_asset]; se não existir
        ainda (sprite não pronto), usa um placeholder retangular simples."""
        veiculos_assets = ASSETS.get('vehicles', {}) if isinstance(ASSETS, dict) else {}
        frames = veiculos_assets.get(self.nome_asset)

        if not frames:
            frames = [self._criar_placeholder()]

        self.sprites = {
            'right': frames,
            'left': [pygame.transform.flip(s, True, False) for s in frames]
        }
        self.estado_animacao = 'right'
        self.image = self.sprites[self.estado_animacao][self.frame_atual]

    def _criar_placeholder(self):
        largura, altura = 96, 56
        surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(surf, (90, 110, 70), (0, 0, largura, altura), border_radius=10)
        pygame.draw.rect(surf, (35, 45, 25), (0, 0, largura, altura), width=3, border_radius=10)
        # "canhão" traseiro, só pra dar uma pista visual até ter sprite de verdade
        pygame.draw.rect(surf, (20, 20, 20), (int(largura * 0.62), int(altura * 0.15), int(largura * 0.3), int(altura * 0.2)))
        return surf

    # ---- Entrada / saída / destruição --------------------------------------
    def pode_ser_chamado(self):
        """True se o veículo está livre pra ser convocado (não destruído, ou
        já cumpriu o cooldown pós-destruição)."""
        if not self.destruido:
            return True
        agora = pygame.time.get_ticks()
        return agora - self.tempo_destruicao >= self.cooldown_destruicao

    def entrar(self):
        if self.destruido or self.embarcado:
            return False
        self.embarcado = True
        self.posicao = self.jogador.posicao.copy()
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.jogador.entrar_veiculo(self, self.vida_maxima)
        return True

    def sair(self):
        if not self.embarcado:
            return False
        self.embarcado = False
        self.posicao = self.jogador.posicao.copy()
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))
        self.jogador.sair_veiculo()
        return True

    def destruir(self):
        """Chamado pelo player quando a vida do veículo chega a zero."""
        if self.destruido:
            return
        self.embarcado = False
        self.destruido = True
        self.tempo_destruicao = pygame.time.get_ticks()
        self.jogador.sair_veiculo()

    # ---- Loop principal ------------------------------------------------------
    def update(self, delta_time):
        if not self.embarcado:
            return

        # Segurança extra: se por algum motivo a vida zerou sem passar pelo
        # receber_dano do player (ex: dano direto externo), destrói aqui também.
        if self.jogador.vida_veiculo_atual <= 0:
            self.destruir()
            return

        self.posicao = self.jogador.posicao.copy()
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        self.atropelar()

        agora = pygame.time.get_ticks()
        inimigo = self.encontrar_alvo_mais_proximo(self.inimigos_grupo, self.raio_deteccao_inimigo, precisa_dano=True)
        if inimigo:
            self.alvo = inimigo
            disparo = self.decidir_disparo_veiculo(agora)
            if disparo:
                self.atirar(**disparo)

        self.animar()

    def atropelar(self):
        """Dano de contato a inimigos tocados pelo veículo, com cooldown
        individual por inimigo (pra não explodir tudo em 1 frame)."""
        dano = getattr(self, 'dano_atropelamento', 0)
        if dano <= 0:
            return

        agora = pygame.time.get_ticks()
        raio_sq = self.raio_atropelamento ** 2

        for inimigo in self.inimigos_grupo:
            if not inimigo.alive() or not hasattr(inimigo, 'receber_dano'):
                continue
            if self.posicao.distance_squared_to(inimigo.posicao) >= raio_sq:
                continue

            ultimo_hit = self._ultimo_hit_atropelamento.get(id(inimigo), 0)
            if agora - ultimo_hit >= self.cooldown_atropelamento:
                inimigo.receber_dano(dano)
                self._ultimo_hit_atropelamento[id(inimigo)] = agora

    def decidir_disparo_veiculo(self, agora):
        """Hook: subclasses definem qual projétil/cadência o veículo usa.
        Retorna um dict de kwargs para atirar(), ou None."""
        return None