"""
main.py - Automacao dos Anuncios Associados do Sysemp (telas [0667] e [0526])

Sem --escrever : MODO LEITURA. Le a grade, diz o que FARIA e fecha com Cancelar.
                 Nao grava nada.
Com --escrever : MODO ESCRITA. Corrige os anuncios (altera, exclui, inclui, grava) e
                 so passa para o proximo produto quando ele esta 100% correto.

Quando um produto da erro (config.PARAR_A_CADA_ERRO):
  True  -> para na hora (modo vigiado)
  False -> registra o erro em erros_automacao.csv, volta para a lista de produtos
           (Cancelar, sem gravar) e segue para o proximo produto.
           Erros de configuracao, produto diferente da planilha, falha ao voltar para a
           lista e muitos erros seguidos SEMPRE param a automacao.

Uso:
    python main.py --limite 3 --detalhe              (leitura, 3 produtos)
    python main.py --escrever --limite 1 --detalhe   (escrita, 1 produto)
    python main.py --escrever                        (escrita, todos)
"""

import argparse
import logging
import sys
import time
from collections import Counter

import pyautogui

import config
import fluxo
import planilha
import tela
from erros import (
    ErroAutomacao,
    ErroConfiguracao,
    ErroMuitosErrosSeguidos,
    ErroProdutoDiferente,
    ErroRecuperacaoFalhou,
)
from registro_erros import RegistroDeErros

log = logging.getLogger("auto")

RESULTADO_ERRO = "com erro"

# Estes erros param a automacao mesmo no modo "continuar": nao da para confiar no que veio depois
ERROS_FATAIS = (ErroConfiguracao, ErroProdutoDiferente)


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Automacao dos Anuncios Associados do Sysemp")
    parser.add_argument(
        "--escrever",
        action="store_true",
        help="GRAVA de verdade no Sysemp (sem isso, so le e diz o que faria)",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="quantos produtos processar a partir da primeira linha visivel da lista (padrao: todos)",
    )
    parser.add_argument(
        "--detalhe",
        action="store_true",
        help="mostra mais detalhes no terminal (ex.: diferencas medidas nas fotos da tela)",
    )
    args = parser.parse_args()
    if args.limite is not None and args.limite < 1:
        parser.error("--limite precisa ser 1 ou mais")
    return args


def confirmar_escrita():
    print()
    print("ATENCAO: com --escrever a automacao GRAVA de verdade no Sysemp")
    print("(altera, exclui, inclui e grava anuncios associados).")
    resposta = input("Digite GRAVAR e aperte Enter para continuar (qualquer outra coisa cancela): ")
    return resposta.strip() == "GRAVAR"


def configurar_log(detalhe):
    log.setLevel(logging.DEBUG if detalhe else logging.INFO)
    formato = logging.Formatter("%(asctime)s | %(message)s", "%H:%M:%S")
    destinos = (
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.CAMINHO_LOG, encoding="utf-8"),
    )
    for destino in destinos:
        destino.setFormatter(formato)
        log.addHandler(destino)


def mostrar_resumo(resumo, registro):
    log.info("-" * 50)
    log.info("RESUMO: %d produto(s) concluido(s) sem erro", resumo["concluidos"])
    for chave in sorted(chave for chave in resumo if chave != "concluidos"):
        log.info("  %s: %d", chave, resumo[chave])

    if registro.itens:
        log.info("-" * 50)
        log.info(
            "PRODUTOS COM ERRO: %d (lista completa em %s)", len(registro.itens), config.CAMINHO_ERROS
        )
        for linha, codigo, sku, erro in registro.itens:
            log.info("  linha %d | Codigo Interno %s | SKU %s | %s", linha, codigo, sku, erro)


def voltar_para_o_produto(produto):
    """Depois de um erro: volta para a [0667] (sem gravar) e confere que o cursor esta no mesmo produto."""
    if not tela.voltar_para_lista():
        raise ErroRecuperacaoFalhou(
            f"a tela [0667] nao voltou depois do erro no produto {produto.codigo_interno}"
        )
    codigo = tela.ler_codigo_interno_selecionado()
    if codigo != produto.codigo_interno:
        raise ErroRecuperacaoFalhou(
            f"depois do erro, a lista mostra o Codigo Interno {codigo!r} "
            f"em vez de {produto.codigo_interno!r}"
        )


def executar(args):
    produtos = planilha.carregar_produtos(config.CAMINHO_PLANILHA)
    total = len(produtos)
    log.info("Planilha carregada: %d produtos", total)

    tela.configurar()

    if args.escrever:
        log.info("MODO ESCRITA: a automacao vai GRAVAR no Sysemp.")
    else:
        log.info("MODO LEITURA: nada sera gravado no Sysemp (use --escrever para gravar).")
    if config.PARAR_A_CADA_ERRO:
        log.info("ERROS: a automacao PARA no primeiro erro (PARAR_A_CADA_ERRO = True).")
    else:
        log.info(
            "ERROS: a automacao REGISTRA o erro em %s e CONTINUA no proximo produto "
            "(PARAR_A_CADA_ERRO = False).",
            config.CAMINHO_ERROS.name,
        )
    log.info("Confirme: tela [0667] aberta, com o produto inicial na PRIMEIRA LINHA VISIVEL da lista.")
    for restante in range(config.ESPERA_INICIAL, 0, -1):
        print(f"  comecando em {restante}s (nao mexa no mouse)...", end="\r")
        time.sleep(1)
    print(" " * 60, end="\r")

    tela.focar_sysemp()
    tela.selecionar_primeira_linha_visivel()
    tela.memorizar_lista()

    codigo_na_tela = tela.ler_codigo_interno_selecionado()
    posicao = planilha.posicao_do_codigo(produtos, codigo_na_tela)
    fim = total if args.limite is None else min(total, posicao + args.limite)
    log.info(
        "Comecando no produto %d de %d (Codigo Interno %s); vai ate o %d.",
        posicao + 1, total, codigo_na_tela, fim,
    )

    resumo = Counter()
    registro = RegistroDeErros()
    erros_seguidos = 0
    try:
        while posicao < fim:
            produto = produtos[posicao]
            if codigo_na_tela != produto.codigo_interno:
                raise ErroProdutoDiferente(
                    f"a tela mostra o Codigo Interno {codigo_na_tela}, mas a planilha "
                    f"esperava {produto.codigo_interno} (produto {posicao + 1} de {total})"
                )

            log.info(
                "[%d/%d] Codigo Interno %s | SKU %s",
                posicao + 1, total, produto.codigo_interno, produto.sku,
            )
            try:
                resultado, cenario = fluxo.processar_produto(produto, args.escrever)
            except ErroAutomacao as erro:
                registro.registrar(posicao + 1, produto, erro)
                if config.PARAR_A_CADA_ERRO or isinstance(erro, ERROS_FATAIS):
                    raise

                erros_seguidos += 1
                log.error("  ERRO no produto %s: %s", produto.codigo_interno, erro)
                if erros_seguidos >= config.MAX_ERROS_SEGUIDOS:
                    raise ErroMuitosErrosSeguidos(
                        f"{erros_seguidos} produtos seguidos deram erro; o ultimo foi "
                        f"{produto.codigo_interno} ({erro})"
                    )

                log.info("  voltando para a lista de produtos (sem gravar)...")
                voltar_para_o_produto(produto)
                log.info("  voltou; seguindo para o proximo produto")
                resumo[RESULTADO_ERRO] += 1
            else:
                erros_seguidos = 0
                log.info("  -> %s", resultado)
                resumo["concluidos"] += 1
                resumo[resultado] += 1
                resumo["cenario inicial: " + cenario] += 1

            posicao += 1
            if posicao < fim:
                tela.ir_para_proximo_produto()
                codigo_na_tela = tela.ler_codigo_interno_selecionado()
    finally:
        mostrar_resumo(resumo, registro)


def main():
    args = ler_argumentos()
    if args.escrever and not confirmar_escrita():
        print("Cancelado: nada foi feito.")
        return

    configurar_log(args.detalhe)
    try:
        executar(args)
    except ErroAutomacao as erro:
        log.error("AUTOMACAO TRAVADA -> %s", erro)
        pyautogui.alert(text=str(erro), title="Automação travada")
        if not isinstance(erro, ErroConfiguracao):
            log.error("A tela foi deixada como esta. Confira o que aparece nela antes de continuar.")
        sys.exit(1)
    except pyautogui.FailSafeException:
        log.error("Interrompido: o mouse foi para o canto da tela (trava de seguranca).")
        sys.exit(1)


if __name__ == "__main__":
    main()