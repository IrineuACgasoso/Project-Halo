# source/enemies/bosses/harbinger/attacks.py
import pygame
import random
import math
from source.systems.entitymanager import entity_manager
from source.feats.projetil import Carabin
from .vfx import HarbingerTeleport, EnergyBlastShot, TeleportBurstShot


class HarbingerAttacks:
    def teleporte(self, a, b, ofensivo=True):
        """Executa a movimentação dimensional instantânea com invulnerabilidade e camuflagem nativas.

        O parâmetro `ofensivo` define a consequência do teleporte — este é o
        "Teleporte de Recomposição":
            - ofensivo=True  -> ela se aproxima do jogador e sai atirando de
              perto (TeleportBurstShot).
            - ofensivo=False -> ela se afasta bastante do jogador, congela e
              prepara a rajada de Energy Blast ("Carabin Maior").
        """
        self.teleportando = True
        self.is_invulneravel = True  # Proteção ativada contra qualquer projétil/ataque do jogador

        # Inicializa o motor de invisibilidade nativo do EnemyCombat
        self.iniciar_invisibilidade(
            alpha_alvo=0,            # Fica 100% invisível no ápice
            fade_out=60,             # Tempo sumindo (ms)
            fade_in=100,             # Tempo reaparecendo (ms)
            duracao=self.duracao_invisivel, # Tempo total (400ms)
            flashing=False
        )
        
        angulo = random.uniform(0, 2 * math.pi)
        distancia_teleporte = random.uniform(a, b)

        # Efeito visual de saída
        HarbingerTeleport(self.posicao, ordem=1)

        # Reposicionamento dimensional
        nova_posicao_x = self.jogador.posicao.x + distancia_teleporte * math.cos(angulo)
        nova_posicao_y = self.jogador.posicao.y + distancia_teleporte * math.sin(angulo)

        self.posicao.x = nova_posicao_x
        self.posicao.y = nova_posicao_y
        self.rect.center = (round(self.posicao.x), round(self.posicao.y))

        # Efeito visual de chegada (invertido)
        HarbingerTeleport(self.posicao, ordem=-1)

        if ofensivo:
            # Ataque surpresa saindo da fenda, de perto — projétil dedicado
            self.iniciar_teleport_burst()
        else:
            # Fugiu para longe: prepara a rajada de Energy Blast
            self.iniciar_energy_blast()

    def iniciar_teleport_burst(self):
        """Ativa o estado de espera estratégica antes de desferir o TeleportBurstShot."""
        self.teleport_burst_ativo = True
        self.teleport_burst_liberacao = pygame.time.get_ticks() + 800

    def disparar_teleport_burst(self, dano=110, tamanho=(110, 110), velocidade=850):
        """Disparo de impacto do teleporte OFENSIVO ("Teleporte de
        Recomposição"). Projétil dedicado (ver vfx.py)."""
        direcao = self.jogador.posicao - self.posicao
        if direcao.length_squared() > 0:
            direcao = direcao.normalize()

        spread = pygame.math.Vector2(random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05))
        direcao_com_spread = direcao + spread
        if direcao_com_spread.length_squared() > 0:
            direcao_com_spread = direcao_com_spread.normalize()

        TeleportBurstShot(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono='INIMIGO',
            tamanho=tamanho,
            dano=dano,
            velocidade=velocidade * self.buff_ofensivo_mult,
            direcao_spread=direcao_com_spread,
        )

    def carabin(self, dano=30, tamanho=(28, 28), velocidade=400):
        """Dispara projéteis de Carabina com dispersão tática."""
        direcao = self.jogador.posicao - self.posicao
        if direcao.length_squared() > 0:
            direcao = direcao.normalize()
            
        spread = pygame.math.Vector2(random.uniform(-0.07, 0.07), random.uniform(-0.07, 0.07))
        direcao_com_spread = (direcao + spread)
        
        if direcao_com_spread.length_squared() > 0:
             direcao_com_spread = direcao_com_spread.normalize()
             
        Carabin(
            posicao_inicial=self.posicao,
            grupos=(entity_manager.all_sprites,),
            jogador=self.jogador,
            game=self.game,
            dono='INIMIGO',
            tamanho=tamanho,
            dano=dano,
            velocidade=velocidade * self.buff_ofensivo_mult,
            direcao_spread=direcao_com_spread
        )

    def executar_onda_emp(self):
        """Invoca uma onda EMP amarela massiva e ultra rápida que desativa escudos."""
        agora = pygame.time.get_ticks()
        
        from source.feats.skills.onda_emp import OndaEMP
        
        OndaEMP(
        posicao=self.posicao.copy(),
        grupos=self.game.all_sprites,
        game=self.game,
        atacante=self,
        preset='harbinger_zone'
        )
        
        self.ultimo_emp = agora
        self.cooldown_emp = random.randint(13000, 17000)

    # ------------------------------------------------------------------
    # ENERGY BLAST ("Carabin Maior") — consequência do teleporte defensivo
    # ------------------------------------------------------------------
    def iniciar_energy_blast(self):
        """Prepara a rajada intercalada de tiros pesados após fugir para longe do jogador."""
        self.energy_blast_ativo = True
        self.energy_blast_restante = self.contagem_energy_blast
        self.energy_blast_cronometro = self.energy_blast_intervalo

    def disparar_energy_blast(self):
        """Dispara um tiro de Energy Blast mirado na posição atual do jogador."""
        EnergyBlastShot(
            posicao_inicial=self.posicao,
            alvo=self.jogador.posicao,
            game=self.game,
            velocidade=750 * self.buff_ofensivo_mult,
        )

        self.energy_blast_restante -= 1
        if self.energy_blast_restante <= 0:
            self.energy_blast_ativo = False

    # ------------------------------------------------------------------
    # RECHARGING — EMP único + Energy Aura amarela impenetrável
    # ------------------------------------------------------------------
    def ativar_recarga(self):
        """Aos marcos de vida: dispara a onda EMP uma única vez, torna a
        boss diretamente invulnerável (a EnergyAura por si só só empurra e
        dá dano no jogador — ela não protegia a própria dona, por isso a
        Harbinger continuava tomando dano) e força o Spawner a gerar
        inimigos imediatamente, sem depender só da janela passiva de tempo
        do loop normal do Spawner (que nunca chegava a disparar)."""
        self.is_invulneravel = True

        self.executar_onda_emp()

        from source.feats.auras import EnergyAura
        self.energy_aura_ref = EnergyAura(
            owner=self,
            raio=225,
            dano_contato=35,
            game=self.game,
            cor_base=(255, 220, 0),  # Amarelo
            impenetravel=True,
        )

        # Força o Spawner a gerar inimigos AGORA
        spawner = getattr(self.game, 'spawner', None)
        if spawner is not None:
            qtd_forcada = 6 + (self.estagio_recarga - 1) * 2
            for _ in range(qtd_forcada):
                spawner.spawnar('normal')

    def desativar_recarga(self):
        """Encerra a recarga: remove a Energy Aura amarela e devolve a
        vulnerabilidade normal à boss."""
        if self.energy_aura_ref is not None and self.energy_aura_ref.alive():
            self.energy_aura_ref.kill()
        self.energy_aura_ref = None
        self.is_invulneravel = False