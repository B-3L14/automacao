"""
anuncios.py - le o texto copiado da grade, classifica cada anuncio (SKU ou 1SKU),
decide o que precisa ser feito e confere o resultado das alteracoes.

A classificacao e SEMPRE pelo texto do SKU, nunca pela posicao da linha
(a ordem das linhas na grade nao e fixa).
"""

import unicodedata
from dataclasses import dataclass

import config
from erros import (
    ErroAnuncioNaoConfere,
    ErroCenarioInvalido,
    ErroDoisAnunciosIguais,
    ErroSkuDiferente,
    ErroTelaNaoIdentificada,
)

TIPO_SKU = "SKU"
TIPO_1SKU = "1SKU"
TIPOS = (TIPO_SKU, TIPO_1SKU)

NOMES_CENARIO = {0: "grade vazia", 1: "1 anuncio", 2: "2 anuncios"}

AVISO_NAO_GRAVADO = "o Gravar verde nao foi apertado; feche a [0526] com Cancelar para descartar"


def _norm(texto):
    return unicodedata.normalize("NFC", texto).strip().casefold()


@dataclass(frozen=True)
class LinhaGrade:
    sku: str
    regra: str
    percentual: float


@dataclass(frozen=True)
class Item:
    tipo: str
    linha: LinhaGrade
    motivo_erro: str  # vazio = correto

    @property
    def correto(self):
        return not self.motivo_erro


@dataclass(frozen=True)
class Avaliacao:
    cenario: str
    itens: tuple

    @property
    def alterar(self):
        """
        O anuncio a ALTERAR no lugar (sem excluir): so existe quando o produto tem
        exatamente 1 anuncio e ele esta errado. Devolve o Item, ou None.
        """
        if len(self.itens) == 1 and not self.itens[0].correto:
            return self.itens[0]
        return None

    @property
    def excluir(self):
        """Anuncios errados que precisam ser excluidos (o que sera alterado no lugar nao entra)."""
        if self.alterar is not None:
            return []
        return [item for item in self.itens if not item.correto]

    @property
    def incluir(self):
        """Tipos que precisam ser criados: os que faltam ou que serao excluidos."""
        mantidos = {item.tipo for item in self.itens if item.correto}
        if self.alterar is not None:
            mantidos.add(self.alterar.tipo)   # esse sera corrigido no lugar
        return [tipo for tipo in TIPOS if tipo not in mantidos]

    @property
    def tudo_correto(self):
        return self.alterar is None and not self.excluir and not self.incluir


def regra_para_criar(tipo):
    """Devolve (regra, percentual) usados ao CRIAR um anuncio do tipo dado."""
    if tipo == TIPO_SKU:
        return config.REGRA_SKU_MANTER, None
    return config.REGRA_1SKU, config.PERCENTUAL_1SKU


# ---------------------------------------------------------------
# Ler o texto copiado
# ---------------------------------------------------------------
def _ler_percentual(texto):
    limpo = texto.strip().replace("%", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        raise ErroTelaNaoIdentificada(f"percentual ilegivel na grade: {texto!r}")


def interpretar_grade(texto):
    """
    Transforma o texto copiado (cabecalho + 1 linha por anuncio, colunas separadas
    por tab) em uma lista de LinhaGrade. Grade vazia = so o cabecalho = lista vazia.
    """
    linhas = [linha for linha in texto.splitlines() if linha.strip()]
    if not linhas:
        raise ErroTelaNaoIdentificada("a grade copiada veio vazia (nem o cabecalho)")

    cabecalho = [_norm(coluna) for coluna in linhas[0].split("\t")]
    indices = {}
    for nome in config.COLUNAS_CABECALHO_GRADE:
        if _norm(nome) not in cabecalho:
            raise ErroTelaNaoIdentificada(
                f"o cabecalho copiado nao e o da grade de Anuncios Associados: {linhas[0]!r}"
            )
        indices[nome] = cabecalho.index(_norm(nome))

    resultado = []
    for linha in linhas[1:]:
        colunas = linha.split("\t")
        if len(colunas) <= max(indices.values()):
            raise ErroTelaNaoIdentificada(f"linha da grade com colunas faltando: {linha!r}")

        resultado.append(
            LinhaGrade(
                sku=colunas[indices["SKU"]].strip(),
                regra=colunas[indices["Regra"]].strip(),
                percentual=_ler_percentual(colunas[indices["%"]]),
            )
        )
    return resultado


# ---------------------------------------------------------------
# Decidir
# ---------------------------------------------------------------
def _motivo_de_erro(tipo, linha):
    """Devolve o motivo pelo qual o anuncio esta errado, ou '' se estiver correto."""
    if tipo == TIPO_SKU:
        regras_ok = [_norm(regra) for regra in config.REGRAS_SKU_ACEITAS]
        if _norm(linha.regra) in regras_ok:
            return ""
        return f"regra '{linha.regra}' (o SKU aceita: {' ou '.join(config.REGRAS_SKU_ACEITAS)})"

    motivos = []
    if _norm(linha.regra) != _norm(config.REGRA_1SKU):
        motivos.append(f"regra '{linha.regra}' em vez de '{config.REGRA_1SKU}'")
    if abs(linha.percentual - config.PERCENTUAL_1SKU) > 1e-9:
        motivos.append(f"{linha.percentual:g}% em vez de {config.PERCENTUAL_1SKU:g}%")
    return "; ".join(motivos)


def avaliar(produto, linhas):
    """
    Decide o cenario. Para a automacao (levanta erro) se:
      - tiver 3 ou mais anuncios                     -> cenario invalido
      - algum anuncio nao for o SKU nem o 1SKU       -> sku diferente do esperado
      - tiver 2 anuncios do mesmo tipo               -> 2 anuncios iguais
    """
    if len(linhas) > 2:
        raise ErroCenarioInvalido(f"{len(linhas)} anuncios na grade (o esperado e 0, 1 ou 2)")

    itens = []
    for linha in linhas:
        if linha.sku == produto.sku:
            tipo = TIPO_SKU
        elif linha.sku == produto.sku_afiliado:
            tipo = TIPO_1SKU
        else:
            raise ErroSkuDiferente(
                f"o anuncio '{linha.sku}' nao e nem '{produto.sku}' nem '{produto.sku_afiliado}'"
            )
        itens.append(Item(tipo=tipo, linha=linha, motivo_erro=_motivo_de_erro(tipo, linha)))

    tipos = [item.tipo for item in itens]
    if len(tipos) != len(set(tipos)):
        raise ErroDoisAnunciosIguais(f"a grade tem 2 anuncios do tipo {tipos[0]}: {linhas[0].sku}")

    return Avaliacao(cenario=NOMES_CENARIO[len(itens)], itens=tuple(itens))


def descrever(avaliacao, escrever=False):
    """Linhas de texto com o que foi lido e o que a automacao vai fazer (ou faria, no modo leitura)."""
    acao = "vai" if escrever else "faria"
    texto = [f"cenario: {avaliacao.cenario}"]

    for item in avaliacao.itens:
        situacao = "ok" if item.correto else f"ERRADO ({item.motivo_erro})"
        texto.append(
            f"  {item.tipo}: {item.linha.sku} | {item.linha.regra} | "
            f"{item.linha.percentual:g}% -> {situacao}"
        )

    if avaliacao.tudo_correto:
        texto.append("  nada a corrigir")
        return texto

    if avaliacao.alterar is not None:
        item = avaliacao.alterar
        regra, percentual = regra_para_criar(item.tipo)
        extra = f", {percentual:g}%" if percentual is not None else ""
        texto.append(f"  {acao}: ALTERAR {item.tipo} {item.linha.sku} para ({regra}{extra})")

    for item in avaliacao.excluir:
        texto.append(f"  {acao}: EXCLUIR {item.tipo} {item.linha.sku}")
    for tipo in avaliacao.incluir:
        regra, percentual = regra_para_criar(tipo)
        extra = f", {percentual:g}%" if percentual is not None else ""
        texto.append(f"  {acao}: INCLUIR {tipo} ({regra}{extra})")

    if escrever and avaliacao.excluir and avaliacao.incluir:
        texto.append(
            "  (as inclusoes ficam para a proxima passagem: depois de excluir, grava no verde e entra de novo)"
        )
    return texto


# ---------------------------------------------------------------
# Conferir o resultado das alteracoes (antes de gravar no verde)
# ---------------------------------------------------------------
def indice_do_sku(linhas, sku):
    """Posicao (0 = primeira linha) do anuncio com esse SKU na grade."""
    for indice, linha in enumerate(linhas):
        if linha.sku == sku:
            return indice
    raise ErroAnuncioNaoConfere(f"o anuncio {sku} nao esta na grade ({AVISO_NAO_GRAVADO})")


def conferir_exclusao(linhas, sku):
    if any(linha.sku == sku for linha in linhas):
        raise ErroAnuncioNaoConfere(
            f"o anuncio {sku} continua na grade depois de excluir ({AVISO_NAO_GRAVADO})"
        )


def conferir_inclusao(produto, linhas, tipo, acao="incluido"):
    """Confere se o anuncio do tipo dado aparece na grade e esta correto (acao: 'incluido' ou 'alterado')."""
    avaliacao = avaliar(produto, linhas)
    for item in avaliacao.itens:
        if item.tipo != tipo:
            continue
        if item.correto:
            return
        raise ErroAnuncioNaoConfere(
            f"o {tipo} {acao} ficou errado na grade: {item.linha.sku} | {item.linha.regra} | "
            f"{item.linha.percentual:g}% ({item.motivo_erro}). {AVISO_NAO_GRAVADO}"
        )
    raise ErroAnuncioNaoConfere(
        f"o {tipo} {acao} nao apareceu na grade depois de gravar ({AVISO_NAO_GRAVADO})"
    )