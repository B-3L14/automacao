"""
cursor.py - descobre se o Sysemp esta OCUPADO (carregando) olhando o cursor do mouse.

Regra: o Sysemp esta LIVRE quando o cursor, no ponto neutro (config.POSICAO_MOUSE_NEUTRA),
e a seta padrao do Windows. Qualquer outro cursor ali conta como ocupado (a ampulheta do
Sysemp e um cursor proprio, que muda de numero a cada vez que ele e aberto; so a seta
padrao tem um numero que da para reconhecer sempre).
"""

import ctypes
import logging
import sys
import time
from ctypes import wintypes

import pyautogui

import config
from erros import ErroConfiguracao, ErroTelaNaoIdentificada

log = logging.getLogger("auto")

IDC_ARROW = 32512


class _CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),
        ("ptScreenPos", wintypes.POINT),
    ]


_user32 = None
_cursor_seta = None


def _preparar():
    """Carrega as funcoes do Windows uma vez e descobre o 'numero' da seta padrao."""
    global _user32, _cursor_seta
    if _user32 is not None:
        return
    if sys.platform != "win32":
        raise ErroConfiguracao("a leitura do cursor so funciona no Windows")

    user32 = ctypes.windll.user32
    user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
    user32.LoadCursorW.restype = wintypes.HANDLE
    user32.GetCursorInfo.argtypes = [ctypes.POINTER(_CURSORINFO)]
    user32.GetCursorInfo.restype = wintypes.BOOL

    seta = user32.LoadCursorW(None, IDC_ARROW)
    if not seta:
        raise ErroConfiguracao("nao consegui descobrir qual e o cursor de seta padrao do Windows")
    _user32 = user32
    _cursor_seta = seta


def _numero_do_cursor():
    """Numero do cursor que esta na tela agora (0 se estiver oculto, None se nao deu para ler)."""
    info = _CURSORINFO()
    info.cbSize = ctypes.sizeof(_CURSORINFO)
    if not _user32.GetCursorInfo(ctypes.byref(info)):
        return None
    return info.hCursor or 0


def _formatar(numero):
    return "nao consegui ler" if numero is None else f"{numero:#x}"


def _mouse_no_ponto_neutro():
    destino = tuple(config.POSICAO_MOUSE_NEUTRA)
    if tuple(pyautogui.position()) != destino:
        pyautogui.moveTo(*destino)
        time.sleep(0.15)


def esperar_sysemp_livre(contexto="", maximo=None):
    """
    Espera o Sysemp terminar de carregar. Devolve quantos segundos ficou ocupado (0 se nao ficou).

    - Leva o mouse ao ponto neutro (o cursor so conta ali).
    - Considera livre depois de config.CURSOR_LEITURAS_SEGUIDAS leituras seguidas com a seta.
    - Escreve no log quando ficou ocupado por mais de config.CURSOR_AVISAR_ACIMA segundos.
    - Se passar de 'maximo' segundos, para com ErroTelaNaoIdentificada.
    """
    _preparar()
    if maximo is None:
        maximo = config.CURSOR_ESPERA_MAXIMA
    onde = f" ({contexto})" if contexto else ""

    _mouse_no_ponto_neutro()

    inicio = time.time()
    inicio_ocupado = None   # quando apareceu o primeiro cursor que nao e a seta
    inicio_seta = None      # quando comecou a sequencia atual de leituras com a seta
    seguidas = 0

    while True:
        agora = time.time()
        numero = _numero_do_cursor()

        if numero == _cursor_seta:
            if seguidas == 0:
                inicio_seta = agora
            seguidas += 1
            if seguidas >= config.CURSOR_LEITURAS_SEGUIDAS:
                break
        else:
            if inicio_ocupado is None:
                inicio_ocupado = agora
                log.debug("  cursor diferente da seta: %s", _formatar(numero))
            seguidas = 0

        if agora - inicio > maximo:
            raise ErroTelaNaoIdentificada(
                f"o cursor do mouse no ponto {tuple(config.POSICAO_MOUSE_NEUTRA)} nao voltou a ser a "
                f"seta padrao em {maximo:g} s (cursor atual: {_formatar(numero)}){onde}. "
                "Ou o Sysemp continua ocupado, ou o cursor do Sysemp nesse ponto nao e a seta "
                "(ajuste POSICAO_MOUSE_NEUTRA no config.py)"
            )
        time.sleep(config.CURSOR_INTERVALO)

    if inicio_ocupado is None:
        return 0.0

    ocupado = inicio_seta - inicio_ocupado
    if ocupado > config.CURSOR_AVISAR_ACIMA:
        log.info("  Sysemp ocupado: esperei %.1f s%s", ocupado, onde)
    return ocupado