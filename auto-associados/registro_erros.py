"""
registro_erros.py - guarda os produtos que deram erro num arquivo CSV (abre no Excel).
Cada erro e gravado na hora, entao nada se perde se o programa for interrompido depois.
"""

import csv
from datetime import datetime

import config

CABECALHO = ["data_hora", "linha_planilha", "codigo_interno", "sku", "erro", "detalhe"]


class RegistroDeErros:
    def __init__(self, caminho=None):
        self.caminho = caminho or config.CAMINHO_ERROS
        self.itens = []   # (linha_planilha, codigo_interno, sku, erro) dos erros desta rodada

    def registrar(self, linha_planilha, produto, erro):
        arquivo_novo = not self.caminho.exists() or self.caminho.stat().st_size == 0
        detalhe = " ".join(str(erro.detalhe).split())   # tira quebras de linha

        with open(self.caminho, "a", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            if arquivo_novo:
                escritor.writerow(CABECALHO)
            escritor.writerow(
                [
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    linha_planilha,
                    produto.codigo_interno,
                    produto.sku,
                    erro.mensagem,
                    detalhe,
                ]
            )

        self.itens.append((linha_planilha, produto.codigo_interno, produto.sku, erro.mensagem))