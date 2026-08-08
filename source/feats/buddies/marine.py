import math
from source.feats.weapons import Arma
from source.data.weapon_data import COMPANION_DATA
from .companion import Companheiro


class Marine(Arma):
    NOME_ASSET = 'marine'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.all_sprites, self.inimigos_grupo, self.item_grupo = grupos
        self.sprite_companion = None

        self.itens_reservados = set() # Itens que já têm um Marine indo buscar
        self.companions = [] # Lista para guardar todos os marines
        self.nome = "UNSC Marine"
        self.descricao = "Leal soldado que auxilia coletando itens e atacando inimigos."
        self.dano = 1

        if kwargs.get('criar_sprite', True):
            self.adicionar_soldado()

    def equipar(self):
        if not self.companions:
            self.adicionar_soldado()
            
    def adicionar_soldado(self):
        novo_marine = Companheiro(
            self.jogador, self.all_sprites, 
            self.inimigos_grupo, self.item_grupo, 
            'marine' 
        )
        novo_marine.arma_parent = self # Referência para gerenciar reservas
        novo_marine.pode_atirar = True
        novo_marine.dano = self.dano
        # Dá um offset para eles não ficarem um em cima do outro
        novo_marine.angulo_orbita = len(self.companions) * (math.pi / 2)

        # Sincroniza com o primeiro para não nascer desatualizado
        if self.companions:
            ref = self.companions[0]
            stats = COMPANION_DATA[self.NOME_ASSET].stats
            for attr in stats:
                if not attr.startswith('_') and hasattr(ref, attr):
                    setattr(novo_marine, attr, getattr(ref, attr))

        self.companions.append(novo_marine)
        if self.sprite_companion is None:
            self.sprite_companion = novo_marine

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET, target=self.companions)
        self.dano = self.companions[0].dano if self.companions else self.dano
        if self._deve_melhorar(
            COMPANION_DATA[self.NOME_ASSET].stats['_soldados'].range_val,
            self.nivel
        ):
            self.adicionar_soldado()            


    def ver_proximo_upgrade(self):
        proximos = self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET, target=self.companions)
        proximos['_soldados']['atual'] = len(self.companions)
        proximos['_soldados']['proximo'] = len(self.companions) + (
            1 if self._deve_melhorar(
                COMPANION_DATA[self.NOME_ASSET].stats['_soldados'].range_val,
                self.nivel + 1
            ) else 0
        )
        return proximos

    def get_estatisticas_para_exibir(self):
        # 1. Puxamos o dicionário completo de upgrades que você já tratou no método acima
        proximos = self.ver_proximo_upgrade()
        linhas = []
        
        # 2. Nossa função de formatação segura contra None
        fmt = lambda v: "0" if v is None else (f"{v:.1f}" if isinstance(v, float) and v % 1 != 0 and v != float('inf') else str(int(v)))
        
        # 3. Varremos os atributos gerando as linhas de texto para a tela
        for info in proximos.values():
            # Se o valor atual for igual ao próximo, não há motivo para mostrar na tela de upgrade
            if info['atual'] == info['proximo']:
                continue
            linhas.append(f"{info['label']}: {fmt(info['atual'])} -> {fmt(info['proximo'])}")
            
        return linhas
    
    def disparar(self): pass

    def update(self, delta_time): pass




