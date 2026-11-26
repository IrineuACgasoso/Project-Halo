import pygame
from source.systems.gameclock import relogio, AcumuladorPassoFixo
# WINDOWS
from source.windows.settings import *
from source.windows.menu import *
from source.windows.colaboradores import TelaColaboradores
from source.windows.ranking import Ranking 
# SYSTEMS
from source.systems.mapmanager import Mapa
from source.systems.camera import Camera
from source.systems.hud import HUD
from source.systems.collision import CollisionManager 
from source.systems.stagemanager import StageManager
from source.systems.spawner import Spawner
from source.systems.entitymanager import entity_manager
from source.systems.eventmanager import EventManager
from source.systems.renderer import Renderer
from source.systems.estados import (ESTADOS, TRANSICOES, Tela, TransicaoInvalida, transicao_valida,
                                    MENU_PRINCIPAL, JOGANDO, PAUSA, LEVEL_UP, CONFIGURACOES,
                                    COLABORADORES, RANKING, GAME_OVER)
from source.systems.sessao import SessaoJogo
from source.systems.eventos import eventos, BOSS_DERROTADO
from source.systems.status import atualizar_status, limpar_status
from source.systems.empurrao import atualizar_empurroes, limpar_empurroes
from source.systems.entrada import Teclado
from source.debug import DEBUG
# FEATS
from source.feats.buddies import *
from source.feats.weapons import *
from source.feats.vehicles import *
from source.feats.effects import Portal
from source.feats.assets import path
from source.data.manifesto_assets import MANIFESTO
# PLAYER
from source.systems.levelup import *
from source.player.player import Player 




class Game:
    def __init__(self, tela):
        # Variaveis de controle de tempo e fase
        self.tela = tela
        self.running = True
        self.clock = pygame.time.Clock()

        # Estado: só muda por mudar_estado(), que confere a tabela TRANSICOES (roteiro B2)
        self._estado = MENU_PRINCIPAL
        self.estados_estritos = DEBUG      # True: transição inválida lança exceção (testes/debug)
        self._transicoes_invalidas_logadas = set()
        self.player = None
        self.sessao = None                 # SessaoJogo da partida atual (roteiro B3)
        self.hud = None                    # recriada a cada partida: guarda tempos da sessão
        self.teclado = Teclado()           # fonte padrão; guarda se os cheats L/P/B estão ligados
        self.entrada = self.teclado        # FonteEntrada lida 1x por passo (roteiro E3)

        # Sistemas que vivem para sempre (não resetam entre jogos)
        self._inicializar_sistemas_permanentes()

        # EventManager gerencia o estado da tela
        self.event_manager = EventManager(self)
        self.telas = self._registrar_telas()

    def _registrar_telas(self):
        """Registro único estado -> (handler de evento, desenho), lido pelo EventManager e
        pelo Renderer. Estado novo entra aqui, em ESTADOS e em TRANSICOES."""
        ev, r = self.event_manager, self.renderer
        return {
            MENU_PRINCIPAL: Tela(ev.tratar_menu_principal, r.desenhar_menu_principal),
            JOGANDO:        Tela(ev.tratar_jogando,        r.desenhar_jogando),
            PAUSA:          Tela(ev.tratar_pausa,          r.desenhar_pausa),
            LEVEL_UP:       Tela(ev.tratar_level_up,       r.desenhar_level_up),
            CONFIGURACOES:  Tela(ev.tratar_configuracoes,  r.desenhar_configuracoes),
            COLABORADORES:  Tela(ev.tratar_colaboradores,  r.desenhar_colaboradores),
            RANKING:        Tela(ev.tratar_ranking,        r.desenhar_ranking),
            GAME_OVER:      Tela(ev.tratar_game_over,      r.desenhar_game_over),
        }

    @property
    def cheats(self):
        return self.teclado.cheats

    def alternar_cheats(self):
        """Botão da pausa: liga/desliga os cheats L/P/B do teclado até fechar o jogo."""
        self.teclado.cheats = not self.teclado.cheats

    @property
    def estado_do_jogo(self):
        return self._estado

    def mudar_estado(self, novo):
        """Troca o estado conferindo TRANSICOES.

        Transição inválida lança `TransicaoInvalida` quando `estados_estritos` (testes e
        MCE_DEBUG). No jogo final ela é logada uma vez e aplicada, para não travar o jogador
        numa tela; o destino só é recusado se nem existir (não haveria tela para desenhar).
        """
        if transicao_valida(self._estado, novo):
            self._estado = novo
            return
        erro = TransicaoInvalida(f'{self._estado!r} -> {novo!r} (permitidas: '
                                 f'{sorted(TRANSICOES.get(self._estado, ()))})')
        if self.estados_estritos:
            raise erro
        chave = (self._estado, novo)
        if chave not in self._transicoes_invalidas_logadas:
            self._transicoes_invalidas_logadas.add(chave)
            print(f'[Game] Transição de estado inválida: {erro}')
        if novo in ESTADOS:
            self._estado = novo


    def _inicializar_sistemas_permanentes(self):
        """Sistemas que existem desde o início e nunca são recriados."""
        self.menu_principal     = MenuPrincipal(self)
        self.menu_pausa         = MenuPausa(self)
        self.tela_game_over     = TelaGameOver(self)
        self.tela_colaboradores = TelaColaboradores(self)
        self.ranking            = Ranking(self)
        self.tela_configuracoes = Settings(self)
        self.collision_manager  = CollisionManager(self)
        self.renderer           = Renderer(self)

        # Mapa inicial (fase 0) — só para o construtor não explodir
        caminho = path('assets', 'img', 'map', '0', 'm0.tmj')
        self.mapa   = Mapa(caminho, 0)
        self.camera = Camera(largura_tela, altura_tela, self.mapa)

    #=================== FUNÇÕES DE INÍCIO/REINÍCIO =======================================

    def _resetar_estado_jogo(self):
        """
        Zera TUDO que pertence a uma sessão de jogo.
        Chamado tanto na primeira partida quanto no restart.
        """
        # 1. Relógio primeiro: tudo que nasce abaixo guarda timestamps dele. A simulação depende
        #    do valor absoluto (cooldowns "prontos" no início), então toda partida começa igual.
        relogio.reiniciar()
        eventos.limpar()   # assinaturas valem por partida
        limpar_status()    # buffs e debuffs da partida anterior não contam mais
        limpar_empurroes()

        # 2. Limpa todos os grupos de sprite
        entity_manager.all_sprites.empty()
        entity_manager.inimigos_grupo.empty()
        entity_manager.items_grupo.empty()
        entity_manager.projeteis_jogador_grupo.empty()
        entity_manager.projeteis_inimigos_grupo.empty()
        entity_manager.auras_grupo.empty()
        entity_manager.particulas_grupo.empty()

        # 3. Estado da partida: objeto novo, nada sobra da anterior
        self.sessao = SessaoJogo()
        self.hud = HUD(self)


    def iniciar_novo_jogo(self):
        self._resetar_estado_jogo()

        # Mapa e câmera — recriados juntos (câmera depende do mapa)
        caminho = path('assets', 'img', 'map', '0', 'm0.tmj')
        self.mapa   = Mapa(caminho, 0, all_sprites=entity_manager.all_sprites)
        self.camera = Camera(largura_tela, altura_tela, self.mapa)  # ← estava faltando

        # Player
        pos_inicial = self.mapa.get_player_spawn_pos()
        self.player = Player(pos_inicial, entity_manager.all_sprites, self)
        entity_manager.player = self.player

        # Arma inicial
        self.player.armas['assault_rifle'] = ARMAS_REGISTRO['assault_rifle'].criar(self.player, self)

        # Spawner — depois do player para não explodir no primeiro spawn
        self.spawner      = Spawner(self)
        self.stage_manager = StageManager(self)

        self.mudar_estado(JOGANDO)

    #================= FUNÇÕES DO GAME ==========================================================
            
    def eventos(self):
        self.event_manager.processar()


    def update(self, delta_time):
        """Um passo de simulação. A ordem dos passos importa (ver docs/architecture.md)."""
        if self._estado != JOGANDO:
            return
        # O relógio de jogo só avança aqui: pausa/level-up/menus congelam todos os timers.
        relogio.avancar(delta_time)
        self._atualizar_portal()
        self._checar_boss_derrotado()
        self._checar_portal_tocado()
        self._atualizar_spawner(delta_time)
        self._atualizar_status(delta_time)
        self._atualizar_entidades(delta_time)
        self.collision_manager.update(delta_time)
        self.stage_manager.update(delta_time)
        self._checar_game_over()

    def _atualizar_portal(self):
        """O portal nasce 2000 ms (de jogo) depois que o boss morre."""
        s = self.sessao
        if s.spawnar_portal_em_breve and relogio.agora() - s.timer_portal >= 2000:
            s.portal_atual = Portal(self.mapa.portal_pos, entity_manager.all_sprites)
            s.spawnar_portal_em_breve = False

    def _checar_boss_derrotado(self):
        if self.sessao.boss_atual and not self.sessao.boss_atual.alive():
            self.boss_derrotado()

    def _checar_portal_tocado(self):
        portal = self.sessao.portal_atual
        if not portal:
            return
        ox = portal.rect.x - self.player.rect.x
        oy = portal.rect.y - self.player.rect.y
        if self.player.mask.overlap(portal.mask, (ox, oy)) and not self.stage_manager.transicao_ativa:
            self.stage_manager.iniciar_transicao()

    def _atualizar_spawner(self, delta_time):
        """Timer e spawner só rodam sem boss, portal nem transição. Um boss pode religar os inimigos
        comuns (`permitir_spawns_normais`); o timer, que agenda os bosses, continua parado."""
        s = self.sessao
        if self.stage_manager.transicao_ativa or s.spawnar_portal_em_breve or s.portal_atual:
            return
        if not s.boss_atual:
            s.timer_jogo += delta_time
        elif not getattr(s.boss_atual, 'permitir_spawns_normais', False):
            return
        self.spawner.update(delta_time)

    def _atualizar_status(self, delta_time):
        """Buffs e debuffs (systems/status): antes das entidades, para o atordoamento já valer neste passo."""
        atualizar_status(delta_time)

    def _atualizar_entidades(self, delta_time):
        """Player, câmera, armas e depois os outros sprites (inimigos recebem as paredes)."""
        if not self.player:
            return
        # Cada entidade consulta a grade na própria posição (roteiro C1)
        paredes = self.mapa.grade_paredes
        atualizar_empurroes(delta_time, paredes)
        self.player.comando = self.entrada.ler()   # antes das armas: os veículos leem a tecla V
        self.player.update(delta_time, paredes)
        self.camera.update(self.player.posicao)

        if not self.player.status.atordoado:   # atordoado não ataca
            for arma in self.player.armas.values():
                arma.update(delta_time)

        for sprite in entity_manager.all_sprites:
            if sprite == self.player:
                continue
            if sprite in entity_manager.inimigos_grupo:
                if not sprite.status.atordoado:   # atordoado: nem anda nem ataca
                    sprite.update(delta_time, paredes)
            else:
                sprite.update(delta_time)

    def _checar_game_over(self):
        if self.player.vida_atual <= 0:
            self._encerrar_partida()


    def perder_partida(self):
        """Derrota que não passa pela vida do jogador (ex.: o Halo disparou)."""
        if self._estado == JOGANDO:
            self._encerrar_partida()

    def _encerrar_partida(self):
        """Fecha a sessão (derrota ou fim da campanha) e vai para a tela final."""
        self._calcular_pontuacao_final()
        self.mudar_estado(GAME_OVER)
        pygame.mixer.music.pause()

    def existe_proxima_fase(self):
        """True se o manifesto tem mapa para a fase seguinte (evita KeyError no fim da campanha).
        Não decodifica a imagem (roteiro D2)."""
        return f'{self.sessao.fase_atual + 1}' in MANIFESTO['maps']

    def finalizar_campanha(self):
        """Portal da última fase disponível foi tocado: encerra a campanha."""
        print(f"Campanha concluída na fase {self.sessao.fase_atual}!")
        self._encerrar_partida()

    def _calcular_pontuacao_final(self):
        """Extraído do update para não poluir o loop principal."""
        p = self.player
        p.pontuacao += p.experiencia_atual
        pesos = {'exp_shard': 1, 'big_shard': 2, 'life_orb': 3, 'cafe': 10}
        for tipo, peso in pesos.items():
            p.pontuacao += p.coletaveis.get(tipo, 0) * peso


    def draw(self):
        self.renderer.draw()

    def boss_derrotado(self):
        s = self.sessao
        print(f"Boss da fase {s.fase_atual} derrotado!")
        boss, s.boss_atual = s.boss_atual, None
        s.spawnar_portal_em_breve = True
        s.timer_portal = relogio.agora()
        eventos.emitir(BOSS_DERROTADO, boss=boss, fase=s.fase_atual)

    def run(self):
        # Passo fixo: a simulação sempre avança de PASSO_FIXO em PASSO_FIXO, então um engasgo
        # (arrastar a janela, carregamento) nunca gera um dt enorme que atravessa paredes.
        acumulador = AcumuladorPassoFixo()
        while self.running:
            passos = acumulador.passos(self.clock.tick(fps) / 1000)
            self.eventos()
            for _ in range(passos):
                self.update(acumulador.passo)
            self.draw()