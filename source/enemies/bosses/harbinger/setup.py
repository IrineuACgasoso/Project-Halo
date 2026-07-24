# source/enemies/bosses/harbinger/setup.py
import pygame

class HarbingerSetup:
    def inicializar_harbinger(self):
        """Configura os timers, recargas e estados iniciais do arsenal da Rainha Endless."""
        # Habilidades (Carabina)
        self.cooldown_carabin = 5000
        self.intervalo_carabina = 250
        self.cronometro_carabina = 0
        self.ultima_carabina = 0
        self.carabina_restante = 0
        self.contagem_carabina = 3

        # Teleporte
        self.ultimo_tp = 0
        self.tp_cooldown = 3000
        self.teleportando = False
        self.tempo_inicio_tp = 0
        self.duracao_invisivel = 400
        self.is_invulneravel = False

        # EMP
        # OBS: a onda EMP não é disparada aleatoriamente durante o combate —
        # ela só ocorre uma vez por marco de recarga (60% e 25%), veja
        # _entrar_em_recarga em ia.py.
        self.ultimo_emp = 0
        self.cooldown_emp = 5000

        # === Máquina de Estados Principal ===
        # 'idle' | 'recharging'
        self.estado_boss = 'idle'

        # === Recharging: dois marcos, cada um ativado uma única vez ===
        self.marcos_recarga_pendentes = [0.98, 0.95]  # % de vida restante
        self.estagio_recarga = 0  # 0 = nenhum marco ainda, 1 = pós-60%, 2 = pós-25%
        self.recharge_ativado = False
        self.permitir_spawns_normais = False  # libera o Spawner durante a recarga
        self.energy_aura_ref = None
        self.duracao_spawner_recarga = 7000  # ms que o Spawner fica liberado por marco
        self.recharge_spawn_timer_inicio = 0
        self.recharge_spawn_liberado = False

        # === Energy Blast ("Carabin Maior") — segue um teleporte defensivo ===
        self.energy_blast_ativo = False
        self.energy_blast_restante = 0
        self.contagem_energy_blast = 4
        self.energy_blast_intervalo = 450
        self.energy_blast_cronometro = 0

        # === Teleporte em Cadeia (múltiplas cargas por acionamento) ===
        # A cada marco de recarga superado, ela ganha +1 carga — vale tanto
        # para o teleporte OFENSIVO quanto para o DEFENSIVO: usa a
        # primeira, ataca, espera um breve intervalo VULNERÁVEL, e teleporta
        # de novo (repetindo o ataque) até esgotar as cargas do estágio.
        self.teleporte_cargas = 1
        self.teleporte_em_cadeia = False
        self.teleporte_cargas_restantes = 0
        self.teleporte_cadeia_ofensivo = True
        self.teleporte_cadeia_ab = (0, 0)
        self.teleporte_aguardando_proximo = False
        self.teleporte_intervalo_cadeia = 300  # ms vulnerável entre teleportes da cadeia
        self.teleporte_cadeia_cronometro = 0

        # Cooldown extra só após o teleporte OFENSIVO terminar de vez (toda
        # a cadeia), dando ao jogador uma janela de reação/desvio antes que
        # ela possa iniciar qualquer outra ação.
        self.cooldown_pos_teleporte_ofensivo = 900  # ms

        # === Buffs cumulativos concedidos ao sair de cada recarga ===
        self.buff_ofensivo_mult = 1.0  # multiplicador de velocidade de carabina/energy blast

        # === Wait genérico (evita que habilidades se atropelem, igual ao
        # padrão usado pelo Arbiter em states.py/attacks.py) ===
        self.wait = 0