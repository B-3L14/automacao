"""
fluxo.py - o que fazer com UM produto: entrar, ler, corrigir, gravar e conferir.

Regra de ouro: so sai do produto quando ele esta 100% correto.

Cada "passagem" = entrar na [0526], ler a grade e fazer o que o cenario pede:
  - tudo certo             -> fecha e termina
  - 1 anuncio e ele errado -> ALTERA esse anuncio no lugar (sem excluir), cria o que falta
                              e grava no verde
  - 2 anuncios, algum errado -> exclui os errados e grava no verde. A inclusao fica para a
                              proxima passagem, porque a plataforma bloqueia incluir um SKU
                              que acabou de ser excluido
  - so falta anuncio       -> inclui o que falta e grava no verde
Depois do Gravar verde o produto fecha; o codigo entra de novo e confere.

Se um anuncio excluido reaparecer na passagem seguinte, o codigo avisa com "ATENCAO"
no log (a exclusao nao persistiu) e simplesmente exclui de novo.
"""

import logging

import anuncios
import config
import edicao
import tela
from erros import ErroProdutoNaoFicouCorreto, ErroTelaNaoIdentificada

log = logging.getLogger("auto")

RESULTADO_JA_CORRETO = "ja correto"
RESULTADO_PRECISA_AJUSTE = "precisa de ajuste"   # so aparece no modo leitura
RESULTADO_CORRIGIDO = "corrigido"


def processar_produto(produto, escrever):
    """
    Devolve (resultado, cenario_inicial) quando o produto esta 100% correto
    (ou, no modo leitura, depois de ler uma vez).
    """
    cenario_inicial = None
    alterou = False
    excluidos_antes = []   # SKUs excluidos na passagem anterior (para saber se reapareceram)

    for passagem in range(1, config.MAX_PASSAGENS + 1):
        if passagem > 1:
            log.info("  passagem %d: entrando de novo no produto", passagem)

        referencia = tela.abrir_anuncios_associados()
        linhas = anuncios.interpretar_grade(tela.ler_grade_anuncios())
        avaliacao = anuncios.avaliar(produto, linhas)
        _avisar_se_voltaram(excluidos_antes, linhas)
        for texto in anuncios.descrever(avaliacao, escrever):
            log.info(texto)
        if cenario_inicial is None:
            cenario_inicial = avaliacao.cenario

        # --- modo leitura: so olha e fecha ---
        if not escrever:
            tela.fechar_sem_gravar(referencia)
            _conferir_produto_selecionado(produto)
            if avaliacao.tudo_correto:
                return RESULTADO_JA_CORRETO, cenario_inicial
            return RESULTADO_PRECISA_AJUSTE, cenario_inicial

        # --- modo escrita ---
        if avaliacao.tudo_correto:
            if config.GRAVAR_QUANDO_JA_CORRETO:
                tela.fechar_gravando(referencia)
            else:
                tela.fechar_sem_gravar(referencia)
            _conferir_produto_selecionado(produto)
            return (RESULTADO_CORRIGIDO if alterou else RESULTADO_JA_CORRETO), cenario_inicial

        if avaliacao.alterar is not None:
            excluidos_antes = []
            _alterar_e_incluir(produto, avaliacao)
        elif avaliacao.excluir:
            excluidos_antes = _excluir_errados(avaliacao)
        else:
            excluidos_antes = []
            _incluir_faltantes(produto, avaliacao)

        tela.fechar_gravando(referencia)
        _conferir_produto_selecionado(produto)
        alterou = True

    raise ErroProdutoNaoFicouCorreto(
        f"o produto {produto.codigo_interno} (SKU {produto.sku}) ainda nao esta correto "
        f"depois de {config.MAX_PASSAGENS} passagens"
    )


def _avisar_se_voltaram(excluidos, linhas):
    """Se um anuncio excluido na passagem anterior reapareceu na grade, avisa no log."""
    for linha in linhas:
        if linha.sku in excluidos:
            log.warning(
                "  ATENCAO: o anuncio %s voltou depois de excluir e gravar (a exclusao nao persistiu)",
                linha.sku,
            )


def _alterar_e_incluir(produto, avaliacao):
    """Produto com 1 anuncio errado: altera esse anuncio no lugar e depois cria o que falta."""
    item = avaliacao.alterar
    regra, percentual = anuncios.regra_para_criar(item.tipo)
    extra = f", {percentual:g}%" if percentual is not None else ""
    log.info("  alterando %s: %s (%s%s)", item.tipo, item.linha.sku, regra, extra)

    # Le a grade de novo para achar a posicao exata da linha
    linhas = anuncios.interpretar_grade(tela.ler_grade_anuncios())
    indice = anuncios.indice_do_sku(linhas, item.linha.sku)

    edicao.alterar_anuncio(indice, item.linha.sku, regra, percentual)

    linhas = anuncios.interpretar_grade(tela.ler_grade_anuncios())
    anuncios.conferir_inclusao(produto, linhas, item.tipo, acao="alterado")

    # Depois de alterado, o que falta e o outro tipo (avaliacao.incluir ja considera isso)
    _incluir_faltantes(produto, avaliacao)


def _excluir_errados(avaliacao):
    """Exclui os anuncios errados e devolve a lista de SKUs excluidos."""
    excluidos = []
    for sku in [item.linha.sku for item in avaliacao.excluir]:
        # Le a grade de novo antes de cada exclusao: depois de excluir, as linhas mudam de posicao
        linhas = anuncios.interpretar_grade(tela.ler_grade_anuncios())
        indice = anuncios.indice_do_sku(linhas, sku)
        log.info("  excluindo %s (linha %d da grade)", sku, indice + 1)

        edicao.excluir_anuncio(indice, sku)

        linhas = anuncios.interpretar_grade(tela.ler_grade_anuncios())
        anuncios.conferir_exclusao(linhas, sku)
        excluidos.append(sku)
    return excluidos


def _incluir_faltantes(produto, avaliacao):
    for tipo in avaliacao.incluir:
        sku_texto = produto.sku if tipo == anuncios.TIPO_SKU else produto.sku_afiliado
        regra, percentual = anuncios.regra_para_criar(tipo)
        extra = f", {percentual:g}%" if percentual is not None else ""
        log.info("  incluindo %s: %s (%s%s)", tipo, sku_texto, regra, extra)

        edicao.incluir_anuncio(sku_texto, regra, percentual)

        linhas = anuncios.interpretar_grade(tela.ler_grade_anuncios())
        anuncios.conferir_inclusao(produto, linhas, tipo)


def _conferir_produto_selecionado(produto):
    """Depois de fechar a [0526], o cursor precisa continuar no mesmo produto."""
    codigo = tela.ler_codigo_interno_selecionado()
    if codigo != produto.codigo_interno:
        raise ErroTelaNaoIdentificada(
            f"depois de fechar a [0526], o Ctrl+C trouxe {codigo!r} "
            f"em vez de {produto.codigo_interno!r}"
        )