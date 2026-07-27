"""
ranking_data.py

Responsável exclusivamente por PERSISTIR o ranking em disco.
Não sabe nada de pygame, desenho ou input — só carrega e salva uma lista
de scores em JSON, de forma defensiva (arquivo ausente, corrompido,
diretório sem permissão, etc nunca devem derrubar o jogo).
"""

import json
import os
import shutil
from datetime import datetime


class RankingData:
    """
    Formato salvo em disco:
    {
        "version": 1,
        "scores": [
            {"name": "OPERADOR", "score": 1234},
            ...
        ]
    }
    """

    VERSION = 1
    MAX_ENTRADAS = 10

    def __init__(self, caminho_arquivo=None):
        if caminho_arquivo is None:
            caminho_arquivo = os.path.join('assets', 'data', 'ranking.json')
        self.caminho = caminho_arquivo

    # ------------------------------------------------------------------ #
    # LEITURA
    # ------------------------------------------------------------------ #
    def carregar(self):
        """Retorna uma lista de dicts {'name': str, 'score': int}.
        Nunca lança exceção — em qualquer falha, retorna lista vazia
        (e tenta preservar o arquivo problemático como backup).
        """
        if not os.path.exists(self.caminho):
            return []

        try:
            with open(self.caminho, 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
            print(f"[RankingData] Falha ao ler '{self.caminho}': {e}")
            self._backup_arquivo_corrompido()
            return []

        scores = self._extrair_scores(conteudo)
        return self._sanitizar(scores)

    def _extrair_scores(self, conteudo):
        # Aceita tanto o formato novo ({"version":..,"scores":[...]})
        # quanto uma lista "crua" antiga, por compatibilidade.
        if isinstance(conteudo, dict):
            return conteudo.get('scores', [])
        if isinstance(conteudo, list):
            return conteudo
        print(f"[RankingData] Formato inesperado em '{self.caminho}', ignorando.")
        return []

    def _sanitizar(self, scores):
        """Garante que cada entrada tem 'name' (str) e 'score' (int),
        descartando silenciosamente qualquer entrada malformada."""
        limpos = []
        if not isinstance(scores, list):
            return limpos

        for item in scores:
            try:
                nome = str(item.get('name', 'OPERADOR')).strip().upper()[:16] or "OPERADOR"
                score = int(item.get('score', 0))
                if score < 0:
                    score = 0
                limpos.append({'name': nome, 'score': score})
            except (AttributeError, TypeError, ValueError):
                continue

        limpos.sort(key=lambda x: x['score'], reverse=True)
        return limpos[: self.MAX_ENTRADAS]

    def _backup_arquivo_corrompido(self):
        try:
            destino = f"{self.caminho}.corrompido.{datetime.now():%Y%m%d%H%M%S}.bak"
            shutil.copy2(self.caminho, destino)
            print(f"[RankingData] Backup do arquivo corrompido salvo em '{destino}'")
        except OSError:
            pass

    # ------------------------------------------------------------------ #
    # ESCRITA
    # ------------------------------------------------------------------ #
    def salvar(self, scores):
        """Salva a lista de scores de forma atômica (escreve em arquivo
        temporário e só então substitui o original), para nunca deixar
        o arquivo de ranking pela metade se o jogo travar no meio do save.
        Retorna True/False indicando sucesso, mas nunca lança exceção.
        """
        scores_limpos = self._sanitizar(scores)

        payload = {
            'version': self.VERSION,
            'scores': scores_limpos,
        }

        try:
            pasta = os.path.dirname(self.caminho)
            if pasta:
                os.makedirs(pasta, exist_ok=True)

            caminho_tmp = f"{self.caminho}.tmp"
            with open(caminho_tmp, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            os.replace(caminho_tmp, self.caminho)
            return True
        except OSError as e:
            print(f"[RankingData] Falha ao salvar '{self.caminho}': {e}")
            return False