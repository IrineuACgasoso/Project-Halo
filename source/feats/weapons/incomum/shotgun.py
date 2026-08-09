from ..baseweapon import Arma
from ...projetil import ProjetilShotgun
import random

class Shotgun(Arma):
    NOME_ASSET = 'shotgun'

    def __init__(self, jogador, grupos, game, **kwargs):
        super().__init__(jogador=jogador, **kwargs)
        self.game = game
        self.nome = "Shotgun"
        self.descricao = "Dispara uma salva de estilhaços superaquecidos com leve dispersão."
        self.all_sprites, self.projeteis_grupo, self.inimigos_grupo = grupos
        self.inicializar_stats(self.NOME_ASSET)
        
    def disparar(self) -> bool:
        # Encontra alvos próximos (Shotguns operam melhor à queima-roupa)
        inimigo_alvo = self.encontrar_inimigo_mais_proximo(self.inimigos_grupo, raio_maximo=500)
        if inimigo_alvo and inimigo_alvo.alive():
            direcao_base = (inimigo_alvo.posicao - self.jogador.posicao).normalize()
            
            # Captura propriedades táticas seguras direto do dicionário de dados da arma
            qtd_estilhacos = getattr(self, 'projeteis_por_disparo', 6)
            angulo_espalhamento = getattr(self, 'espalhamento', 14)  # Limite angular do leque em graus
            vel_projetil = getattr(self, 'velocidade_projetil', getattr(self, 'velocidade', 750))
            
            for _ in range(qtd_estilhacos):
                # Rotaciona ligeiramente o vetor para criar o padrão fragmentado em leque
                variacao = random.uniform(-angulo_espalhamento, angulo_espalhamento)
                direcao_spread = direcao_base.rotate(variacao)
                
                ProjetilShotgun(
                    posicao_inicial = self.jogador.posicao,
                    grupos          = (self.all_sprites,), 
                    jogador         = self.jogador,
                    game            = self.game,
                    dono            = 'PLAYER',
                    tamanho         = (32, 14),  # Aspecto bem pontiagudo e fino
                    dano            = self.dano,
                    velocidade      = vel_projetil,
                    direcao_spread  = direcao_spread
                )
            return True
        return False

    def upgrade(self):
        super().upgrade()
        self.aplicar_upgrades(self.nivel, self.NOME_ASSET)

    def ver_proximo_upgrade(self):
        return self.ver_proximos_upgrades(self.nivel + 1, self.NOME_ASSET)

    def get_estatisticas_para_exibir(self):
        return super().get_estatisticas_para_exibir(self.nivel + 1, self.NOME_ASSET)

