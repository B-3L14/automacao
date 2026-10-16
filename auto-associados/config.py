"""
config.py - todos os numeros e textos que podem precisar de ajuste ficam aqui.
Se uma coordenada ou um tempo estiver errado na sua tela, o ajuste e SO neste arquivo.
"""

from pathlib import Path

PASTA = Path(__file__).resolve().parent

# ---------------------------------------------------------------
# Arquivos
# ---------------------------------------------------------------
CAMINHO_PLANILHA = PASTA / "0667_manutencao_de_produtos_do_e-commerce_20261013081249.xlsx"
CAMINHO_LOG = PASTA / "log_automacao.txt"

# Nomes das colunas na planilha
COL_CODIGO_INTERNO = "Código Interno"
COL_SKU = "Código Auxiliar"
COL_DESCRICAO = "Descrição do Produto"

# ---------------------------------------------------------------
# Regras de negocio
# ---------------------------------------------------------------
PREFIXO_1SKU = "1"

REGRA_SKU_MANTER = "Manter o Preço Atual"   # usada ao CRIAR um SKU
REGRA_SKU_FIXO = "Preço Fixo"
REGRAS_SKU_ACEITAS = (REGRA_SKU_FIXO, REGRA_SKU_MANTER)

REGRA_1SKU = "% Acima do Preço Atual"
PERCENTUAL_1SKU = 12.0

# Colunas que o cabecalho copiado da grade precisa ter (confere que e a grade certa)
COLUNAS_CABECALHO_GRADE = ("SKU", "Regra", "%", "R$ Adicional")

# ---------------------------------------------------------------
# Tela (coordenadas lidas das suas fotos de 1366x768)
# ---------------------------------------------------------------
TELA_ESPERADA = (1366, 768)

CLIQUE_FOCO_SYSEMP = (548, 745)              # o clique do passo 1
CLIQUE_PRIMEIRA_LINHA_PRODUTOS = (665, 336)  # coluna Codigo Interno, 1a linha visivel da lista [0667]
CLIQUE_ALTERAR = (488, 60)                   # botao amarelo com lapis [0667]
CLIQUE_ABA_ANUNCIOS_ASSOCIADOS = (257, 325)  # ultima aba do menu lateral [0526] (posicao com o menu normal)

# O menu lateral da [0526] tem 6 abas, ou 7 quando o produto tem a aba "Produtos Filhos"
# (ai "Anuncios Associados" desce de y=325 para y=368). O codigo acha a ultima aba olhando
# as cores do menu, em vez de clicar sempre no mesmo ponto.
ABA_CLIQUE_X = 257                                       # x do clique na aba (o y e calculado)
ABAS_X_AMOSTRA = 176                                     # coluna de pixels examinada (borda esquerda das abas)
ABAS_Y_PROCURA = (95, 520)                               # faixa de y examinada
ABAS_CORES_CORPO = ((223, 225, 229), (250, 250, 250))    # cor de uma aba normal e da aba selecionada
ABAS_TOLERANCIA = 4
ABAS_CENTRO_ACIMA_DA_BASE = 19                           # o centro da aba fica 19 px acima da ultima linha dela
ABAS_ULTIMO_Y_MIN_MAX = (330, 480)                       # fora disso o menu e desconhecido: para a automacao
CLIQUE_GRADE_ANUNCIOS = (390, 169)           # coluna SKU, 1a linha da grade [0526]
CLIQUE_CANCELAR_PRODUTO = (208, 52)          # X vermelho "Cancelar" de cima [0526]
POSICAO_MOUSE_NEUTRA = (20, 400)             # canto sem nada, so para tirar o mouse do caminho

# Titulos de janela aceitos como "Sysemp em primeiro plano" (o titulo comeca com um destes).
# Antes de qualquer Ctrl+C ou clique, o codigo confere isso, para nunca digitar fora do Sysemp.
TITULOS_JANELA_SYSEMP = ("ERP SYSEMP", "[0667]", "[0526]")
TIMEOUT_FOCO_SYSEMP = 6
# Faixa da barra de botoes (x, y, largura, altura). Ela e muito diferente na [0667]
# (Pesquisar, Produtos...) e na [0526] (Cancelar, Gravar). O codigo compara a foto
# dessa faixa para saber se a tela mudou, sem precisar de imagens de referencia.
REGIAO_BARRA_FERRAMENTAS = (180, 35, 150, 55)
LIMIAR_BARRA_MUDOU = 8.0   # diferenca minima para considerar que a [0526] abriu
LIMIAR_BARRA_IGUAL = 3.0   # diferenca maxima para considerar que a [0667] voltou

# ---------------------------------------------------------------
# Tempos (segundos)
# ---------------------------------------------------------------
PAUSA_ENTRE_ACOES = 0.5
ESPERA_INICIAL = 5
ESPERA_APOS_ABRIR = 1
ESPERA_APOS_ABA = 1
ESPERA_APOS_FECHAR = 1
ESPERA_APOS_SETA = 0.7
ESPERA_COPIA = 1
TENTATIVAS_COPIA = 3
TIMEOUT_TELA = 15
INTERVALO_VERIFICACAO = 0.4

# ---------------------------------------------------------------
# Espera do Sysemp ocupado (cursor de "carregando")
# O Sysemp esta LIVRE quando o cursor, no ponto neutro, e a seta padrao do Windows.
# ---------------------------------------------------------------
CURSOR_INTERVALO = 0.2             # de quanto em quanto tempo olha o cursor (s)
CURSOR_LEITURAS_SEGUIDAS = 3       # leituras seguidas com a seta para considerar livre
CURSOR_ESPERA_MAXIMA = 90          # se continuar ocupado por mais que isso (s), para com erro
CURSOR_ESPERA_MAXIMA_INICIO = 8    # no inicio da rodada, se o cursor nao for a seta: para depressa (s)
CURSOR_AVISAR_ACIMA = 0.5          # so escreve no log se ficou ocupado por mais que isso (s)

# Texto colocado na area de transferencia antes de cada Ctrl+C.
# Se depois do Ctrl+C ele continua la, nada foi copiado.
MARCADOR_CLIPBOARD = "@@SEM_COPIA@@"

# ---------------------------------------------------------------
# ETAPA 2 (escrita): botoes e campos da tela [0526]
# (coordenadas lidas das suas fotos de 1366x768; ajuste aqui se algum clique errar)
# ---------------------------------------------------------------
CLIQUE_INCLUIR_ANUNCIO = (397, 107)
CLIQUE_EXCLUIR_ANUNCIO = (644, 107)
CLIQUE_GRAVAR_GRADE = (766, 107)           # Gravar retangular (da grade)
CLIQUE_GRAVAR_PRODUTO = (279, 52)          # Gravar verde de cima (o mesmo que F12)
CLIQUE_CONFIRMAR_EXCLUSAO = (435, 478)     # botao "Sim" da janela de confirmacao

CLIQUE_CAMPO_SKU = (620, 545)
CLIQUE_COMBO_REGRA = (620, 618)
CLIQUE_CAMPO_PERCENTUAL = (510, 642)

# Onde clicar na lista de regras depois de aberta (ela abre para cima)
CLIQUES_ITENS_REGRA = {
    REGRA_SKU_MANTER: (520, 487),
    REGRA_1SKU: (520, 551),
    REGRA_SKU_FIXO: (520, 599),
}

# Regioes usadas para saber em que estado a tela esta (comparando fotos)
REGIAO_GRAVAR_VERDE = (268, 38, 22, 22)         # icone do Gravar verde: colorido = normal, cinza = editando
REGIAO_ICONE_CONFIRMACAO = (365, 283, 66, 66)   # icone "?" da janela "Confirma a exclusao"

ESPERA_APOS_GRAVAR = 1.5
ESPERA_CAMPO = 0.3
MAX_PASSAGENS = 6  # quantas vezes entra no mesmo produto antes de desistir

# Produto que ja esta 100% correto:
#   False = fecha com Cancelar (nao regrava nada)
#   True  = fecha com o Gravar verde mesmo assim
GRAVAR_QUANDO_JA_CORRETO = False

# ---------------------------------------------------------------
# ERROS: parar ou continuar (para deixar rodando sem ninguem olhando)
# ---------------------------------------------------------------
# True  = para no primeiro erro (modo vigiado: voce ve o erro e decide)
# False = registra o erro, volta para a lista de produtos e segue para o proximo produto
PARAR_A_CADA_ERRO = False

MAX_ERROS_SEGUIDOS = 5                          # no modo "continuar": para se N produtos seguidos derem erro
CAMINHO_ERROS = PASTA / "erros_automacao.csv"   # aqui ficam os produtos que deram erro

# ---------------------------------------------------------------
# Botoes novos da [0526] (coordenadas lidas das fotos; ajuste aqui se algum clique errar)
# ---------------------------------------------------------------
CLIQUE_ALTERAR_ANUNCIO = (520, 107)    # botao "Alterar Anuncio" da grade
CLIQUE_CANCELAR_GRADE = (889, 107)     # botao "Cancelar" retangular (da grade)