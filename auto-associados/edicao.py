"""
edicao.py - acoes que ALTERAM dados na grade de Anuncios Associados: incluir, alterar e excluir.
(Gravar o produto no verde fica em tela.py, junto com o Cancelar, porque os dois fecham a [0526].)
"""

import logging
import time

import pyautogui
import pyperclip

import anuncios
import config
import tela
from erros import ErroConfiguracao, ErroTelaNaoIdentificada

log = logging.getLogger("auto")


# ---------------------------------------------------------------
# Apoio
# ---------------------------------------------------------------
def _colar_no_campo(clique, texto):
    """Clica no campo, apaga o que tem e cola o texto (colar e mais seguro que digitar)."""
    pyautogui.click(*clique)
    time.sleep(config.ESPERA_CAMPO)
    pyautogui.hotkey("ctrl", "a")
    pyperclip.copy(texto)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(config.ESPERA_CAMPO)


def _escolher_regra(regra):
    """Abre a lista de regras e clica na regra pedida."""
    clique_item = config.CLIQUES_ITENS_REGRA.get(regra)
    if clique_item is None:
        raise ErroConfiguracao(
            f"nao sei onde clicar para escolher a regra {regra!r} (veja CLIQUES_ITENS_REGRA no config.py)"
        )
    pyautogui.click(*config.CLIQUE_COMBO_REGRA)
    time.sleep(0.6)
    pyautogui.click(*clique_item)
    time.sleep(config.ESPERA_CAMPO)


def _digitar_percentual(percentual):
    """Digita o percentual no campo % (ele so fica ativo depois de escolher a regra)."""
    texto = f"{percentual:g}".replace(".", ",")
    pyautogui.click(*config.CLIQUE_CAMPO_PERCENTUAL)
    time.sleep(config.ESPERA_CAMPO)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.write(texto, interval=0.1)
    pyautogui.press("tab")  # sai do campo para o Sysemp registrar o valor
    time.sleep(config.ESPERA_CAMPO)


def _selecionar_linha_da_grade(indice):
    """Clica na 1a linha da grade e desce com a seta para baixo ate a linha pedida (0 = 1a)."""
    pyautogui.click(*config.CLIQUE_GRADE_ANUNCIOS)
    time.sleep(0.4)
    for _ in range(indice):
        pyautogui.press("down")
        time.sleep(0.25)


def _conferir_linha_selecionada(sku_esperado):
    """Copia a linha selecionada na grade e confere se e o anuncio esperado."""
    texto = tela.copiar_texto()
    if texto is None:
        raise ErroTelaNaoIdentificada("a linha selecionada na grade nao copiou nada com Ctrl+C")
    selecionadas = anuncios.interpretar_grade(texto)
    if len(selecionadas) != 1 or selecionadas[0].sku != sku_esperado:
        raise ErroTelaNaoIdentificada(
            f"a linha selecionada na grade nao e a esperada ({sku_esperado!r}). Copiado: {texto!r}"
        )


# ---------------------------------------------------------------
# Incluir
# ---------------------------------------------------------------
def incluir_anuncio(sku_texto, regra, percentual):
    """
    [0526] > Anuncios Associados: Incluir Anuncio, preenche, e Gravar retangular.
    O Gravar verde do produto NAO e apertado aqui.
    """
    tela.garantir_sysemp("antes de incluir anuncio")
    referencia = tela.foto(config.REGIAO_GRAVAR_VERDE)  # colorido = nao esta editando

    pyautogui.click(*config.CLIQUE_INCLUIR_ANUNCIO)
    tela.esperar_regiao(
        config.REGIAO_GRAVAR_VERDE, referencia, mudou=True,
        erro="o formulario de inclusao nao abriu (o Gravar verde de cima nao ficou cinza)",
    )
    time.sleep(0.4)

    _colar_no_campo(config.CLIQUE_CAMPO_SKU, sku_texto)

    if regra != config.REGRA_SKU_MANTER:   # "Manter o Preco Atual" ja vem marcada
        _escolher_regra(regra)
    if percentual is not None:
        _digitar_percentual(percentual)

    tela.garantir_sysemp("antes de clicar no Gravar da grade")
    pyautogui.click(*config.CLIQUE_GRAVAR_GRADE)
    tela.mover_mouse_neutro()
    tela.esperar_regiao(
        config.REGIAO_GRAVAR_VERDE, referencia, mudou=False,
        erro="o Gravar da grade nao concluiu (o Gravar verde de cima nao voltou ao normal). "
             "Pode ter aparecido algum aviso",
    )
    time.sleep(0.6)


# ---------------------------------------------------------------
# Alterar (no lugar, sem excluir)
# ---------------------------------------------------------------
def alterar_anuncio(indice, sku_esperado, regra, percentual):
    """
    [0526] > Anuncios Associados: seleciona a linha, confere o SKU dela, clica em
    Alterar Anuncio, troca a regra (e o %) e clica no Gravar retangular.
    O Gravar verde do produto NAO e apertado aqui.
    """
    tela.garantir_sysemp("antes de alterar anuncio")
    _selecionar_linha_da_grade(indice)
    _conferir_linha_selecionada(sku_esperado)

    referencia = tela.foto(config.REGIAO_GRAVAR_VERDE)  # colorido = nao esta editando
    pyautogui.click(*config.CLIQUE_ALTERAR_ANUNCIO)
    tela.esperar_regiao(
        config.REGIAO_GRAVAR_VERDE, referencia, mudou=True,
        erro="o formulario de alteracao nao abriu (o Gravar verde de cima nao ficou cinza)",
    )
    time.sleep(0.4)

    _escolher_regra(regra)
    if percentual is not None:
        _digitar_percentual(percentual)

    tela.garantir_sysemp("antes de clicar no Gravar da grade")
    pyautogui.click(*config.CLIQUE_GRAVAR_GRADE)
    tela.mover_mouse_neutro()
    tela.esperar_regiao(
        config.REGIAO_GRAVAR_VERDE, referencia, mudou=False,
        erro="o Gravar da grade nao concluiu depois de alterar (o Gravar verde de cima nao voltou "
             "ao normal). Pode ter aparecido algum aviso",
    )
    time.sleep(0.6)


# ---------------------------------------------------------------
# Excluir
# ---------------------------------------------------------------
def excluir_anuncio(indice, sku_esperado):
    """
    [0526] > Anuncios Associados: seleciona a linha, confere o SKU dela, clica em
    Excluir Anuncio e confirma com "Sim". O Gravar verde do produto NAO e apertado aqui.
    """
    tela.garantir_sysemp("antes de excluir anuncio")
    _selecionar_linha_da_grade(indice)
    _conferir_linha_selecionada(sku_esperado)

    referencia = tela.foto(config.REGIAO_ICONE_CONFIRMACAO)
    pyautogui.click(*config.CLIQUE_EXCLUIR_ANUNCIO)
    tela.esperar_regiao(
        config.REGIAO_ICONE_CONFIRMACAO, referencia, mudou=True,
        erro="a janela 'Confirma a exclusao desse SKU associado' nao apareceu",
    )
    time.sleep(0.4)

    pyautogui.click(*config.CLIQUE_CONFIRMAR_EXCLUSAO)  # botao "Sim"
    tela.mover_mouse_neutro()
    tela.esperar_regiao(
        config.REGIAO_ICONE_CONFIRMACAO, referencia, mudou=False,
        erro="a janela 'Confirma a exclusao' nao fechou depois do Sim",
    )
    time.sleep(0.6)

    # Gravar retangular: se estiver cinza (nada para gravar na grade), o clique nao faz nada.
    tela.garantir_sysemp("antes de clicar no Gravar da grade")
    pyautogui.click(*config.CLIQUE_GRAVAR_GRADE)
    time.sleep(0.6)