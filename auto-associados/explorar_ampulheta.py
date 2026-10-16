"""
explorar_ampulheta.py

Script de EXPLORACAO: so OBSERVA o cursor do mouse (nao clica, nao digita, nao mexe em nada).
Serve para descobrir se o Python consegue "ver" quando o Sysemp esta ocupado (cursor de ampulheta).

Uso:
    python explorar_ampulheta.py          (observa por 120 segundos)
    python explorar_ampulheta.py 180      (observa por 180 segundos)
"""

import ctypes
import sys
import time
from ctypes import wintypes

IDC_ARROW = 32512
IDC_IBEAM = 32513
IDC_WAIT = 32514
IDC_CROSS = 32515
IDC_NO = 32648
IDC_HAND = 32649
IDC_APPSTARTING = 32650

CURSORES_CONHECIDOS = [
    ("seta", IDC_ARROW),
    ("texto (I)", IDC_IBEAM),
    ("AMPULHETA (espera)", IDC_WAIT),
    ("SETA + AMPULHETA (iniciando)", IDC_APPSTARTING),
    ("mao", IDC_HAND),
    ("cruz", IDC_CROSS),
    ("proibido", IDC_NO),
]
OCUPADOS = ("AMPULHETA (espera)", "SETA + AMPULHETA (iniciando)")


class CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),
        ("ptScreenPos", wintypes.POINT),
    ]


def preparar_windows():
    user32 = ctypes.windll.user32
    user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
    user32.LoadCursorW.restype = wintypes.HANDLE
    user32.GetCursorInfo.argtypes = [ctypes.POINTER(CURSORINFO)]
    user32.GetCursorInfo.restype = wintypes.BOOL
    return user32


def montar_tabela(user32):
    """Descobre qual 'numero' o Windows da para cada cursor conhecido."""
    nomes_por_numero = {}
    for nome, id_cursor in CURSORES_CONHECIDOS:
        numero = user32.LoadCursorW(None, id_cursor) or 0
        if numero:
            nomes_por_numero.setdefault(numero, []).append(nome)
    return nomes_por_numero


def cursor_atual(user32):
    info = CURSORINFO()
    info.cbSize = ctypes.sizeof(CURSORINFO)
    if not user32.GetCursorInfo(ctypes.byref(info)):
        return None
    return info.hCursor or 0


def nome_do_cursor(numero, tabela):
    if numero is None:
        return "(nao consegui ler o cursor)"
    if numero in tabela:
        return " / ".join(tabela[numero])
    return f"OUTRO (numero {numero:#x}) <- cursor que eu nao conheco"


def eh_ocupado(numero, tabela):
    return any(nome in OCUPADOS for nome in tabela.get(numero, []))


def main():
    if sys.platform != "win32":
        print("Este script so funciona no Windows.")
        return

    segundos = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    user32 = preparar_windows()
    tabela = montar_tabela(user32)

    print("Cursores que o Windows conhece neste PC:")
    for numero, nomes in tabela.items():
        print(f"  {numero:#x} = {' / '.join(nomes)}")
    print()
    print(f"Observando por {segundos} s. Va para o Sysemp, deixe o mouse em cima da janela dele")
    print("e faca o que costuma demorar (abrir um produto com Alterar e fechar com Gravar [F12]).")
    print("Cada mudanca de cursor aparece abaixo. Nao precisa fazer mais nada neste terminal.")
    print("-" * 60)

    inicio = time.time()
    ultimo = object()
    inicio_ocupado = None
    vezes = 0
    total_ocupado = 0.0
    maior = 0.0

    while time.time() - inicio < segundos:
        atual = cursor_atual(user32)
        agora = time.time()

        if atual != ultimo:
            print(f"{agora - inicio:6.1f}s | cursor: {nome_do_cursor(atual, tabela)}")
            ultimo = atual

        ocupado = eh_ocupado(atual, tabela)
        if ocupado and inicio_ocupado is None:
            inicio_ocupado = agora
            vezes += 1
        elif not ocupado and inicio_ocupado is not None:
            duracao = agora - inicio_ocupado
            total_ocupado += duracao
            maior = max(maior, duracao)
            print(f"         (a ampulheta durou {duracao:.1f} s)")
            inicio_ocupado = None

        time.sleep(0.1)

    if inicio_ocupado is not None:
        duracao = time.time() - inicio_ocupado
        total_ocupado += duracao
        maior = max(maior, duracao)

    print("-" * 60)
    print(f"RESUMO: ampulheta vista {vezes} vez(es), {total_ocupado:.1f} s no total, a maior com {maior:.1f} s.")


if __name__ == "__main__":
    main()