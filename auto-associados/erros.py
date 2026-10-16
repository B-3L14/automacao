"""
erros.py - cada motivo de parada da automacao tem a sua propria classe.
"""


class ErroAutomacao(Exception):
    """Base: qualquer motivo para travar a automacao."""

    mensagem = "erro da automacao"

    def __init__(self, detalhe=""):
        self.detalhe = detalhe
        texto = f"{self.mensagem}: {detalhe}" if detalhe else self.mensagem
        super().__init__(texto)


class ErroDoisAnunciosIguais(ErroAutomacao):
    mensagem = "2 anuncios iguais"


class ErroCenarioInvalido(ErroAutomacao):
    mensagem = "cenario invalido"


class ErroTelaNaoIdentificada(ErroAutomacao):
    mensagem = "tela não identificada"


class ErroSkuDiferente(ErroAutomacao):
    """Um anuncio da grade nao e nem o SKU nem o 1SKU do produto da planilha."""

    mensagem = "sku diferente do esperado"


class ErroProdutoDiferente(ErroAutomacao):
    """O produto selecionado na tela nao e o que a planilha esperava."""

    mensagem = "produto diferente da planilha"


class ErroConfiguracao(ErroAutomacao):
    """Problema antes de comecar (planilha, resolucao da tela...)."""

    mensagem = "configuracao invalida"


class ErroAnuncioNaoConfere(ErroAutomacao):
    """Depois de excluir ou incluir, a grade nao ficou como deveria."""

    mensagem = "a grade nao confere com o esperado"


class ErroProdutoNaoFicouCorreto(ErroAutomacao):
    """Passou do limite de entradas no mesmo produto e ele ainda nao esta correto."""

    mensagem = "produto nao ficou correto"


class ErroRecuperacaoFalhou(ErroAutomacao):
    """Depois de um erro, nao deu para voltar com seguranca para a lista de produtos."""

    mensagem = "nao consegui voltar para a lista de produtos depois do erro"


class ErroMuitosErrosSeguidos(ErroAutomacao):
    """No modo 'continuar', varios produtos seguidos deram erro (provavel problema geral)."""

    mensagem = "muitos erros seguidos"