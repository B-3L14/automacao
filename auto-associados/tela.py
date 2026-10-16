"""
tela.py - tudo que mexe na tela: clicar, copiar com Ctrl+C, abrir e fechar a [0526].

Como o codigo sabe em que tela esta (sem imagens de referencia):
  - Titulo da janela ativa: antes de qualquer tecla ou clique, confere se o Sysemp
    esta em primeiro plano. Assim nunca digita no VS Code ou em outro programa.
  - Ctrl+C: antes de copiar, poe um texto-marcador na area de transferencia.
    Se o marcador continua la depois, nao copiou nada -> tela inesperada.
  - Fotos de regioes: tira foto de um pedaco da tela e compara. Serve para saber
    qual tela esta aberta ([0667] ou [0526]) e em que estado ela esta.
"""

import logging
import re
import time

import pyautogui
import pyperclip
from PIL import ImageChops, ImageStat

import config
import cursor
from erros import ErroConfiguracao, ErroTelaNaoIdentificada

log = logging.getLogger("auto")


# ---------------------------------------------------------------
# Preparacao
# ---------------------------------------------------------------
def configurar():
    pyautogui.PAUSE = config.PAUSA_ENTRE_ACOES
    pyautogui.FAILSAFE = True  # mouse no canto da tela = para tudo

    tamanho = tuple(pyautogui.size())
    if tamanho != config.TELA_ESPERADA:
        raise ErroConfiguracao(
            f"a tela e {tamanho[0]}x{tamanho[1]}, mas as coordenadas foram feitas para "
            f"{config.TELA_ESPERADA[0]}x{config.TELA_ESPERADA[1]}"
        )


def mover_mouse_neutro():
    pyautogui.moveTo(*config.POSICAO_MOUSE_NEUTRA)
    time.sleep(0.2)


# ---------------------------------------------------------------
# Conferir que o Sysemp esta em primeiro plano
# ---------------------------------------------------------------
def titulo_janela_ativa():
    try:
        return pyautogui.getActiveWindowTitle() or ""
    except Exception as erro:
        raise ErroConfiguracao(
            f"nao consegui ler o titulo da janela ativa ({erro}). Rode: pip install pygetwindow"
        )


def sysemp_em_primeiro_plano():
    titulo = titulo_janela_ativa().strip().casefold()
    return any(titulo.startswith(prefixo.casefold()) for prefixo in config.TITULOS_JANELA_SYSEMP)


def garantir_sysemp(contexto=""):
    """Para a automacao se a janela ativa nao for o Sysemp."""
    if sysemp_em_primeiro_plano():
        return
    onde = f" ({contexto})" if contexto else ""
    raise ErroTelaNaoIdentificada(
        f"o Sysemp nao esta em primeiro plano{onde}. Janela ativa: {titulo_janela_ativa()!r}. "
        "Se o clique na barra de tarefas nao trouxe o Sysemp, ajuste CLIQUE_FOCO_SYSEMP no config.py"
    )


def focar_sysemp():
    """
    Passo 1: leva o Sysemp para o primeiro plano.
    - Se ele ja esta em primeiro plano, NAO clica na barra de tarefas
      (clicar de novo no icone minimizaria a janela).
    - Senao, clica no icone da barra de tarefas e espera o Sysemp aparecer.
    - Por fim, confere que o cursor no ponto neutro e a seta padrao (Sysemp livre).
      Se nao for, para depressa: assim a espera por "Sysemp ocupado" nao fica enganada.
    """
    if not sysemp_em_primeiro_plano():
        pyautogui.click(*config.CLIQUE_FOCO_SYSEMP)
        limite = time.time() + config.TIMEOUT_FOCO_SYSEMP
        while time.time() < limite and not sysemp_em_primeiro_plano():
            time.sleep(config.INTERVALO_VERIFICACAO)

    time.sleep(1.0)
    mover_mouse_neutro()
    garantir_sysemp("depois do clique na barra de tarefas")
    cursor.esperar_sysemp_livre("no inicio da rodada", maximo=config.CURSOR_ESPERA_MAXIMA_INICIO)


def selecionar_primeira_linha_visivel():
    """
    [0667]: clica na celula 'Codigo Interno' da 1a linha visivel da lista.
    Isso devolve o foco do teclado para a lista (o clique na barra de tarefas
    tira o foco dela) e define o produto inicial: o da 1a linha visivel.
    """
    garantir_sysemp("antes de clicar na lista de produtos")
    pyautogui.click(*config.CLIQUE_PRIMEIRA_LINHA_PRODUTOS)
    time.sleep(0.6)
    mover_mouse_neutro()


# ---------------------------------------------------------------
# Copiar texto (Ctrl+C)
# ---------------------------------------------------------------
def copiar_texto():
    """Aperta Ctrl+C e devolve o texto copiado, ou None se nada foi copiado."""
    garantir_sysemp("antes do Ctrl+C")
    for _ in range(config.TENTATIVAS_COPIA):
        cursor.esperar_sysemp_livre("antes do Ctrl+C")
        pyperclip.copy(config.MARCADOR_CLIPBOARD)
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(config.ESPERA_COPIA)
        texto = pyperclip.paste()
        if texto != config.MARCADOR_CLIPBOARD:
            return texto
    return None

def ler_codigo_interno_selecionado():
    """Na [0667]: copia a celula selecionada, que precisa ser a do Codigo Interno."""
    texto = copiar_texto()
    if texto is None:
        raise ErroTelaNaoIdentificada(
            "a lista de produtos [0667] nao copiou nada com Ctrl+C (ela esta em foco?)"
        )

    codigo = texto.strip()
    if not re.fullmatch(r"\d+", codigo):
        raise ErroTelaNaoIdentificada(
            f"esperava o Codigo Interno (so numeros) e o Ctrl+C trouxe {codigo!r}. "
            "Confira se o cursor esta na coluna 'Codigo Interno'"
        )
    return codigo


# ---------------------------------------------------------------
# Fotos de regioes da tela
# ---------------------------------------------------------------
def foto(regiao):
    """Foto em tons de cinza de uma regiao (x, y, largura, altura)."""
    return pyautogui.screenshot(region=regiao).convert("L")


def _diferenca(foto_a, foto_b):
    return ImageStat.Stat(ImageChops.difference(foto_a, foto_b)).mean[0]


def esperar_regiao(regiao, referencia, mudou, erro):
    """
    mudou=True : espera a regiao ficar DIFERENTE da foto de referencia.
    mudou=False: espera a regiao ficar IGUAL a foto de referencia.
    Se nao acontecer dentro do tempo limite, para com a mensagem 'erro'.
    """
    limite = time.time() + config.TIMEOUT_TELA
    diferenca = 0.0
    while time.time() < limite:
        diferenca = _diferenca(referencia, foto(regiao))
        log.debug("regiao %s: diferenca = %.1f", regiao, diferenca)

        if mudou and diferenca >= config.LIMIAR_BARRA_MUDOU:
            return
        if not mudou and diferenca <= config.LIMIAR_BARRA_IGUAL:
            return
        time.sleep(config.INTERVALO_VERIFICACAO)

    if mudou:
        esperado = f"minimo esperado: {config.LIMIAR_BARRA_MUDOU}"
    else:
        esperado = f"maximo esperado: {config.LIMIAR_BARRA_IGUAL}"
    raise ErroTelaNaoIdentificada(
        f"{erro} (em {config.TIMEOUT_TELA}s; diferenca medida: {diferenca:.1f}, {esperado})"
    )


def _foto_da_barra():
    return foto(config.REGIAO_BARRA_FERRAMENTAS)


def _esperar_barra(referencia, mudou, depois_de="o Cancelar"):
    """Espera a [0526] abrir (mudou=True) ou a [0667] voltar (mudou=False)."""
    if mudou:
        erro = "a tela [0526] nao abriu"
    else:
        erro = f"a tela [0667] nao voltou depois d{depois_de}. Pode ter aparecido algum aviso"
    esperar_regiao(config.REGIAO_BARRA_FERRAMENTAS, referencia, mudou, erro)


# ---------------------------------------------------------------
# Acoes na [0667] e na [0526]
# ---------------------------------------------------------------
def _y_da_ultima_linha_de_aba():
    """
    Menu lateral da [0526]: acha a ultima linha (y) que tem a cor de fundo de uma aba.
    Tira uma foto de uma faixa fina do menu e olha de cima para baixo.
    Devolve None se nao achar nenhuma.
    """
    y_ini, y_fim = config.ABAS_Y_PROCURA
    faixa = pyautogui.screenshot(
        region=(config.ABAS_X_AMOSTRA - 1, y_ini, 3, y_fim - y_ini + 1)
    ).convert("RGB")

    ultimo = None
    for i in range(faixa.height):
        cor = faixa.getpixel((1, i))
        for alvo in config.ABAS_CORES_CORPO:
            if all(abs(a - b) <= config.ABAS_TOLERANCIA for a, b in zip(cor, alvo)):
                ultimo = y_ini + i
                break
    return ultimo


def _y_da_aba_anuncios_associados():
    """
    O menu lateral da [0526] tem 6 abas, ou 7 quando o produto tem a aba 'Produtos Filhos'.
    'Anuncios Associados' e SEMPRE a ultima, entao o codigo acha onde o menu termina.
    Espera dar o mesmo resultado 2 vezes seguidas, para ter certeza de que o menu terminou de aparecer.
    """
    anterior = None
    limite = time.time() + config.TIMEOUT_TELA
    while time.time() < limite:
        ultimo = _y_da_ultima_linha_de_aba()
        if ultimo is not None and ultimo == anterior:
            minimo, maximo = config.ABAS_ULTIMO_Y_MIN_MAX
            if not minimo <= ultimo <= maximo:
                raise ErroTelaNaoIdentificada(
                    f"o menu lateral da [0526] termina em y={ultimo}, fora do esperado "
                    f"({minimo} a {maximo}). Pode ter aparecido algum aviso por cima"
                )
            return ultimo - config.ABAS_CENTRO_ACIMA_DA_BASE
        anterior = ultimo
        time.sleep(0.3)
    raise ErroTelaNaoIdentificada(
        "nao consegui achar o menu lateral da [0526] (as cores das abas nao foram encontradas). "
        "Confira ABAS_X_AMOSTRA e ABAS_CORES_CORPO no config.py"
    )


def abrir_anuncios_associados():
    """
    [0667]: clica em Alterar, espera a [0526] abrir e clica em Anuncios Associados.
    Devolve a foto da barra da [0667], usada depois para saber que ela voltou.
    """
    garantir_sysemp("antes de clicar em Alterar")
    mover_mouse_neutro()
    referencia = _foto_da_barra()

    pyautogui.click(*config.CLIQUE_ALTERAR)
    mover_mouse_neutro()
    _esperar_barra(referencia, mudou=True)
    time.sleep(config.ESPERA_APOS_ABRIR)

    garantir_sysemp("antes de clicar em Anuncios Associados")
    y_aba = _y_da_aba_anuncios_associados()
    log.debug("  aba Anuncios Associados em y=%d", y_aba)
    if abs(y_aba - config.CLIQUE_ABA_ANUNCIOS_ASSOCIADOS[1]) > 3:
        log.info("  menu com aba(s) a mais: Anuncios Associados esta em y=%d", y_aba)
    pyautogui.click(config.ABA_CLIQUE_X, y_aba)
    time.sleep(config.ESPERA_APOS_ABA)
    return referencia


def ler_grade_anuncios():
    """[0526]: seleciona a grade inteira (Ctrl+A) e copia. Devolve o texto copiado."""
    garantir_sysemp("antes de ler a grade de anuncios")
    pyautogui.click(*config.CLIQUE_GRADE_ANUNCIOS)
    time.sleep(0.4)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.4)

    texto = copiar_texto()
    if texto is None:
        raise ErroTelaNaoIdentificada("a grade de Anuncios Associados nao copiou nada com Ctrl+C")
    return texto


def _fechar(referencia, clique, botao, espera):
    garantir_sysemp(f"antes de clicar em {botao}")
    pyautogui.click(*clique)
    mover_mouse_neutro()
    _esperar_barra(referencia, mudou=False, depois_de=f"o {botao}")
    time.sleep(espera)
    cursor.esperar_sysemp_livre(f"depois do {botao}")


def fechar_sem_gravar(referencia):
    """[0526]: clica em Cancelar (X vermelho) e espera a [0667] voltar."""
    _fechar(referencia, config.CLIQUE_CANCELAR_PRODUTO, "Cancelar", config.ESPERA_APOS_FECHAR)


def fechar_gravando(referencia):
    """[0526]: clica no Gravar verde (o mesmo que F12) e espera a [0667] voltar."""
    _fechar(referencia, config.CLIQUE_GRAVAR_PRODUTO, "Gravar verde", config.ESPERA_APOS_GRAVAR)


def ir_para_proximo_produto():
    """[0667]: seta para baixo (o cursor precisa estar na lista)."""
    garantir_sysemp("antes de apertar a seta para baixo")
    pyautogui.press("down")
    time.sleep(config.ESPERA_APOS_SETA)


# ---------------------------------------------------------------
# Recuperacao depois de um erro (modo "continuar")
# ---------------------------------------------------------------
_referencia_lista = None


def memorizar_lista():
    """Guarda a foto da barra de botoes da [0667]. Chamar uma vez, com a [0667] aberta e normal."""
    global _referencia_lista
    mover_mouse_neutro()
    _referencia_lista = _foto_da_barra()


def na_lista_de_produtos():
    """True se a tela [0667] esta aberta (a barra de botoes igual a foto guardada)."""
    if _referencia_lista is None:
        raise ErroConfiguracao("a foto de referencia da [0667] nao foi guardada (memorizar_lista)")
    return _diferenca(_referencia_lista, _foto_da_barra()) <= config.LIMIAR_BARRA_IGUAL


def _aguardar_lista(segundos):
    limite = time.time() + segundos
    while time.time() < limite:
        if na_lista_de_produtos():
            return True
        time.sleep(config.INTERVALO_VERIFICACAO)
    return False


def voltar_para_lista():
    """
    Depois de um erro: tenta voltar para a [0667] DESCARTANDO o que estiver aberto na
    [0526] (Cancelar). Nao grava nada. Devolve True se a lista voltou, False se nao conseguiu.
    Se houver uma janela desconhecida aberta, os cliques nao fazem efeito e a funcao devolve False.
    """
    garantir_sysemp("para voltar para a lista depois de um erro")
    mover_mouse_neutro()
    if na_lista_de_produtos():
        return True

    # 1) fecha a [0526] sem gravar (Cancelar de cima)
    pyautogui.click(*config.CLIQUE_CANCELAR_PRODUTO)
    mover_mouse_neutro()
    if _aguardar_lista(4):
        time.sleep(config.ESPERA_APOS_FECHAR)
        return True

    # 2) se estava editando um anuncio, o Cancelar de cima fica cinza:
    #    cancela a edicao (Cancelar da grade) e tenta o de cima de novo
    garantir_sysemp("na recuperacao (Cancelar da grade)")
    pyautogui.click(*config.CLIQUE_CANCELAR_GRADE)
    time.sleep(1.0)
    pyautogui.click(*config.CLIQUE_CANCELAR_PRODUTO)
    mover_mouse_neutro()
    if _aguardar_lista(6):
        time.sleep(config.ESPERA_APOS_FECHAR)
        return True
    return False