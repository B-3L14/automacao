"""
explorar_leitura_tela.py

Script de EXPLORACAO: nao grava nada no Sysemp.
Serve so para descobrir qual a melhor forma de o codigo "enxergar" a tela.

Uso:
    python explorar_leitura_tela.py 1   -> Ctrl+C na grade de Anuncios Associados [0526]
    python explorar_leitura_tela.py 2   -> OCR (leitor de texto em imagem) na grade [0526]
    python explorar_leitura_tela.py 3   -> Seta para baixo na lista de produtos [0667]
"""

import os
import sys
import time
from datetime import datetime

import pyautogui
import pyperclip
from PIL import Image, ImageChops, ImageOps, ImageStat

# ---------------------------------------------------------------
# AJUSTES (coordenadas lidas das suas fotos de 1366x768)
# ---------------------------------------------------------------
TELA_ESPERADA = (1366, 768)
CLIQUE_FOCO_SYSEMP = (548, 745)   # o mesmo clique do passo 1 da automacao
ESPERA_INICIAL = 5                # segundos para voce se preparar

# Grade de Anuncios Associados [0526]
GRADE_X = 333                     # borda esquerda da grade
GRADE_LARGURA = 857               # ate a borda direita (x = 1190)
LINHA1_Y = 160                    # topo da 1a linha de dados
ALTURA_LINHA = 20
QTD_LINHAS_LER = 4
COLUNAS = {                       # (x_inicio, x_fim) de cada coluna
    "SKU": (335, 447),
    "Regra": (810, 993),
    "%": (993, 1058),
}
WHITELIST = {                     # caracteres permitidos no OCR de cada coluna
    "SKU": "0123456789.ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "Regra": None,
    "%": "0123456789,.",
}
CLIQUE_LINHA_ANUNCIO = (680, 168)  # coluna Descricao, 1a linha (segura)

# Lista de produtos [0667]
CLIQUE_LINHA_PRODUTO = (665, 336)  # coluna Codigo Interno (NAO clicar em "Selecionar")
REGIAO_LISTA_PRODUTOS = (406, 295, 770, 345)  # x, y, largura, altura

PASTA_SAIDA = "saida_exploracao"
SEM_COPIA = "@@SEM_COPIA@@"


# ---------------------------------------------------------------
# Funcoes de apoio
# ---------------------------------------------------------------
def conferir_tamanho_da_tela():
    largura, altura = pyautogui.size()
    print(f"Tamanho da tela vista pelo Python: {largura}x{altura}")
    if (largura, altura) != TELA_ESPERADA:
        print(
            f"  ATENCAO: as coordenadas foram lidas de fotos {TELA_ESPERADA[0]}x{TELA_ESPERADA[1]}. "
            "Se a tela for diferente, os cliques podem cair no lugar errado. Me avise."
        )


def ir_para_sysemp():
    print(f"Va ate o Sysemp na tela certa. Comecando em {ESPERA_INICIAL}s (nao mexa no mouse depois).")
    for i in range(ESPERA_INICIAL, 0, -1):
        print(f"  {i}...", end="\r")
        time.sleep(1)
    print(" " * 20, end="\r")
    pyautogui.click(*CLIQUE_FOCO_SYSEMP)
    time.sleep(1.5)


def copiar_e_ler(teclas):
    """Poe um texto-marcador na area de transferencia, aperta as teclas e devolve o que foi copiado."""
    pyperclip.copy(SEM_COPIA)
    time.sleep(0.2)
    pyautogui.hotkey(*teclas)
    time.sleep(0.6)
    texto = pyperclip.paste()
    return None if texto == SEM_COPIA else texto


def mostrar_copia(titulo, texto):
    print(f"\n--- {titulo} ---")
    if texto is None:
        print("  NAO copiou nada.")
        return
    print(f"  copiou {len(texto)} caracteres, {len(texto.splitlines())} linha(s)")
    print(f"  conteudo (repr): {texto!r}")


# ---------------------------------------------------------------
# TESTE 1: Ctrl+C na grade de Anuncios Associados [0526]
# ---------------------------------------------------------------
def teste_1_copiar_grade_anuncios():
    print("\n=== TESTE 1: Ctrl+C na grade de Anuncios Associados ===")
    ir_para_sysemp()

    pyautogui.click(*CLIQUE_LINHA_ANUNCIO)
    time.sleep(0.5)
    mostrar_copia("a) clicar na 1a linha + Ctrl+C", copiar_e_ler(("ctrl", "c")))

    pyautogui.click(*CLIQUE_LINHA_ANUNCIO)
    time.sleep(0.5)
    mostrar_copia("b) clicar na 1a linha + Ctrl+Insert", copiar_e_ler(("ctrl", "insert")))

    pyautogui.click(*CLIQUE_LINHA_ANUNCIO)
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.5)
    mostrar_copia("c) clicar + Ctrl+A + Ctrl+C (todas as linhas)", copiar_e_ler(("ctrl", "c")))

    pyautogui.click(*CLIQUE_LINHA_ANUNCIO)  # tira a selecao de "todas"


# ---------------------------------------------------------------
# TESTE 2: OCR na grade de Anuncios Associados [0526]
# ---------------------------------------------------------------
def _configurar_tesseract():
    try:
        import pytesseract
    except ImportError:
        print("Falta instalar o pytesseract:  pip install pytesseract")
        return False

    caminhos = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for caminho in caminhos:
        if os.path.exists(caminho):
            pytesseract.pytesseract.tesseract_cmd = caminho
            break

    try:
        pytesseract.get_tesseract_version()
    except Exception:
        print("O programa Tesseract nao foi encontrado. Instale-o e rode de novo.")
        return False
    return True


def _ocr_celula(celula, whitelist=None):
    import pytesseract

    img = ImageOps.grayscale(celula)
    img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
    img = ImageOps.autocontrast(img)
    config = "--psm 7"
    if whitelist:
        config += f" -c tessedit_char_whitelist={whitelist}"
    return pytesseract.image_to_string(img, config=config).strip()


def teste_2_ocr_grade_anuncios():
    print("\n=== TESTE 2: OCR na grade de Anuncios Associados ===")
    if not _configurar_tesseract():
        return
    ir_para_sysemp()

    cabecalho = 22
    altura_total = cabecalho + ALTURA_LINHA * QTD_LINHAS_LER
    grade = pyautogui.screenshot(
        region=(GRADE_X, LINHA1_Y - cabecalho, GRADE_LARGURA, altura_total)
    )
    caminho_foto = os.path.join(PASTA_SAIDA, f"grade_{datetime.now():%H%M%S}.png")
    grade.save(caminho_foto)
    print(f"  foto da grade salva em: {caminho_foto}")

    print(f"\n  {'linha':<7}{'SKU':<26}{'Regra':<30}{'%':<8}variacao")
    for i in range(QTD_LINHAS_LER):
        topo = cabecalho + i * ALTURA_LINHA
        linha = grade.crop((0, topo, GRADE_LARGURA, topo + ALTURA_LINHA))
        variacao = ImageStat.Stat(ImageOps.grayscale(linha)).stddev[0]

        valores = {}
        for nome, (x0, x1) in COLUNAS.items():
            celula = grade.crop((x0 - GRADE_X, topo, x1 - GRADE_X, topo + ALTURA_LINHA))
            valores[nome] = _ocr_celula(celula, WHITELIST[nome])

        print(
            f"  {i + 1:<7}{valores['SKU']:<26}{valores['Regra']:<30}{valores['%']:<8}{variacao:.1f}"
        )

    print("\n  Obs.: 'variacao' perto de 0 = linha em branco (grade sem anuncio naquela linha).")
    print("  Obs.: se o SKU vier sem o '.001' no fim, a coluna esta estreita demais na tela.")


# ---------------------------------------------------------------
# TESTE 3: seta para baixo na lista de produtos [0667]
# ---------------------------------------------------------------
def teste_3_seta_para_baixo_lista_produtos():
    print("\n=== TESTE 3: seta para baixo na lista de produtos ===")
    ir_para_sysemp()

    pyautogui.click(*CLIQUE_LINHA_PRODUTO)
    time.sleep(0.6)
    antes = pyautogui.screenshot(region=REGIAO_LISTA_PRODUTOS)
    antes.save(os.path.join(PASTA_SAIDA, "lista_antes.png"))
    mostrar_copia("linha selecionada ANTES (Ctrl+C)", copiar_e_ler(("ctrl", "c")))

    pyautogui.press("down")
    time.sleep(0.6)
    depois = pyautogui.screenshot(region=REGIAO_LISTA_PRODUTOS)
    depois.save(os.path.join(PASTA_SAIDA, "lista_depois.png"))
    mostrar_copia("linha selecionada DEPOIS (Ctrl+C)", copiar_e_ler(("ctrl", "c")))

    diferenca = ImageChops.difference(antes.convert("RGB"), depois.convert("RGB")).convert("L")
    marcados = diferenca.point(lambda p: 255 if p > 30 else 0)
    pixels_diferentes = marcados.histogram()[255]
    percentual = 100 * pixels_diferentes / (diferenca.width * diferenca.height)

    print(f"\n  Pixels diferentes entre antes e depois: {percentual:.1f}%")
    if percentual > 5:
        print("  Parece que a selecao MUDOU de linha (a seta para baixo funcionou).")
    else:
        print("  Quase nada mudou: a seta pode NAO ter funcionado. Veja lista_antes.png e lista_depois.png.")

    pyautogui.press("up")  # volta para a linha original


# ---------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------
TESTES = {
    "1": teste_1_copiar_grade_anuncios,
    "2": teste_2_ocr_grade_anuncios,
    "3": teste_3_seta_para_baixo_lista_produtos,
}


def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    pyautogui.PAUSE = 0.3

    if len(sys.argv) > 1:
        escolha = sys.argv[1]
    else:
        escolha = input("Qual teste rodar? (1, 2 ou 3): ").strip()

    if escolha not in TESTES:
        print("Escolha 1, 2 ou 3.")
        return

    conferir_tamanho_da_tela()
    try:
        TESTES[escolha]()
    except pyautogui.FailSafeException:
        print("\nInterrompido: o mouse foi para o canto da tela (trava de seguranca).")
    print("\nPronto. Copie tudo o que apareceu aqui e me mande.")


if __name__ == "__main__":
    main()