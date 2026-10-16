import pandas as pd
import pyautogui

# ==============================
# CONFIGURAÇÕES
# ==============================
CAMINHO_PLANILHA = r"planilhas\0667_manutencao_de_produtos_do_e-commerce_20261013081249.xlsx"
COLUNA_CODIGO_INTERNO = "Código Interno"
COLUNA_SKU = "Código Auxiliar"

pyautogui.PAUSE = 1

def ler_planilha(caminho):
    """Lê a planilha e devolve só as linhas que são produtos."""
    # dtype=str: mantém tudo como texto, para o Excel não transformar códigos em número
    df = pd.read_excel(caminho, dtype=str)

    # A última linha do arquivo é um rodapé do ERP (só traz o total), não é produto.
    # Ela não tem Código Interno, por isso é removida aqui.
    df = df.dropna(subset=[COLUNA_CODIGO_INTERNO])
    return df.reset_index(drop=True)


def executar_cliques(sku):
    
    pyautogui.click(488, 59)
    pyautogui.sleep(5)
    pyautogui.click(247, 321)
    pyautogui.click(400, 105)
    pyautogui.write(sku)
    pyautogui.click(771, 616)

    pyautogui.hotkey("enter")

    pyautogui.click(766, 105)
    pyautogui.hotkey("f12")
    pyautogui.hotkey("down")
    

def excluir(sku):
    
    pyautogui.click(488, 59)
    pyautogui.sleep(5)
    pyautogui.click(247, 321)
    pyautogui.click(644, 105)
    pyautogui.hotkey("left")
    pyautogui.hotkey("enter")
    pyautogui.click(644, 105)
    pyautogui.hotkey("left")
    pyautogui.hotkey("enter")
    pyautogui.hotkey("f12")
    pyautogui.sleep(3)
    pyautogui.hotkey("down")


def main():
    df = ler_planilha(CAMINHO_PLANILHA)
    total = len(df)
    print(f"{total} produtos encontrados na planilha.")

    pulados = []

    # O for repete o bloco abaixo 1 vez para cada produto da planilha
    for posicao, (_, linha) in enumerate(df.iterrows(), start=1):
        sku = linha[COLUNA_SKU]

        # Produto sem SKU: não tem o que digitar na tela, então pula e anota
        if pd.isna(sku) or not str(sku).strip():
            pulados.append(linha[COLUNA_CODIGO_INTERNO])
            print(f"[{posicao}/{total}] Código Interno {linha[COLUNA_CODIGO_INTERNO]} sem SKU - pulado")
            continue

        sku = str(sku).strip()  # <- o SKU fica guardado nesta variável
        print(f"[{posicao}/{total}] SKU: {sku}")

        pyautogui.click(548, 745)

        executar_cliques(sku)

    print(f"Finalizado. Processados: {total - len(pulados)} | Pulados: {len(pulados)}")
    if pulados:
        print("Códigos Internos pulados (sem SKU):", pulados)


if __name__ == "__main__":
    main()