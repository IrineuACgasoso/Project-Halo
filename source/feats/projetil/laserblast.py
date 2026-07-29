import pygame
from .projetil import ProjetilUniversal

class LaserBlast(ProjetilUniversal):
    """Feixe do Spartan Laser: núcleo branco-quente, envolto por um glow
    vermelho contínuo, com leve alargamento/flare na ponta de impacto."""

    def __init__(self, posicao_inicial, grupos, jogador, game, dono, tamanho, dano, velocidade, direcao_spread, piercing=1):
        super().__init__(
            posicao_inicial=posicao_inicial,
            grupos=grupos,
            game=game,
            dono=dono,
            sprite_key='spartan_laser',
            tamanho=tamanho,     # ex: (260, 16) — comprido e fino
            dano=dano,
            velocidade=velocidade,
            duracao=1200,
            direcao_custom=direcao_spread,
            piercing=piercing,
            rotacionar=True
        )

    def obter_imagem_base(self, sprite_key, tamanho):
        base_key = f"base_{sprite_key}_{tamanho[0]}x{tamanho[1]}"
        if base_key not in ProjetilUniversal.GLOBAL_CACHE:
            w, h = tamanho
            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            centro_y = h / 2

            # 1. Glow externo: halo vermelho difuso, largo e suave
            for frac, alpha in [(1.0, 35), (0.75, 55), (0.55, 90)]:
                espessura = max(1, h * frac)
                pygame.draw.rect(
                    surf, (255, 20, 10, alpha),
                    (0, centro_y - espessura / 2, w, espessura)
                )
            # 2. Corpo do feixe: vermelho vivo e contínuo
            corpo_h = max(3, h * 0.4)
            pygame.draw.rect(
                surf, (255, 40, 20, 255),
                (0, centro_y - corpo_h / 2, w, corpo_h)
            )
            # 3. Núcleo: linha branco-quente central (o "olho" do laser)
            nucleo_h = max(1.5, h * 0.14)
            pygame.draw.rect(
                surf, (255, 235, 220, 255),
                (0, centro_y - nucleo_h / 2, w, nucleo_h)
            )
            # 4. Fade suave nas duas pontas, pra não cortar reto e feio
            fade_len = max(6, int(w * 0.08))
            fade = pygame.Surface((fade_len, h), pygame.SRCALPHA)
            for x in range(fade_len):
                alpha = int(255 * (x / fade_len))
                pygame.draw.line(fade, (255, 255, 255, alpha), (x, 0), (x, h))
            surf.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(pygame.transform.flip(fade, True, False), (w - fade_len, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # 5. Flare de impacto: clarão alaranjado na ponta do feixe,
            flare_raio = int(h * 1.4)
            flare = pygame.Surface((flare_raio * 2, flare_raio * 2), pygame.SRCALPHA)
            centro_flare = (flare_raio, flare_raio)
            pygame.draw.circle(flare, (255, 90, 20, 70), centro_flare, flare_raio)
            pygame.draw.circle(flare, (255, 255, 240, 200), centro_flare, int(flare_raio * 0.4))
            surf.blit(flare, (w - flare_raio, centro_y - flare_raio), special_flags=pygame.BLEND_RGBA_ADD)

            ProjetilUniversal.GLOBAL_CACHE[base_key] = surf
        return ProjetilUniversal.GLOBAL_CACHE[base_key]

    def ao_atingir_alvo(self, alvo):
        from source.feats.skills.artilharia import ArtilhariaAviso

        if getattr(alvo, 'invulneravel', False):
            return

        if hasattr(alvo, 'receber_dano'):
            alvo.receber_dano(self.dano)
        elif hasattr(alvo, 'tomar_dano'):
            alvo.tomar_dano(self)

        ArtilhariaAviso(
            posicao=alvo.posicao,
            grupos=(self.game.all_sprites,),
            game=self.game,
            dono=self.dono,
            preset='spartan_laser'
        )

        if self.piercing <= 1:
            self.kill()
        else:
            self.piercing -= 1