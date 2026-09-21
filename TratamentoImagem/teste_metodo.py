import cv2

# 1. Lê a imagem (Certifique-se de que o caminho existe)
imagem = cv2.imread("1imagem/TRABALHO/teste.png")

if imagem is None:
    print("Erro: Imagem não encontrada. Verifique o caminho.")
else:
    # 2. Converte para escala de cinza (lembre-se: OpenCV usa BGR)
    imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    # 3. Testa os métodos de thresholding padrão
    metodos = [
        (cv2.THRESH_BINARY, "BINARY"),
        (cv2.THRESH_BINARY_INV, "BINARY_INV"),
        (cv2.THRESH_TRUNC, "TRUNC"),
        (cv2.THRESH_TOZERO, "TOZERO"),
        (cv2.THRESH_TOZERO_INV, "TOZERO_INV")
    ]

    for metodo, nome in metodos:
        # Usamos apenas o método aqui. Deixaremos o OTSU de fora neste teste base.
        _, imagem_tratada = cv2.threshold(imagem_cinza, 127, 255, metodo)
        cv2.imwrite(f'2resultado/imagem_tratada_{nome}.png', imagem_tratada)

    '''_, imagem_final = cv2.threshold(imagem_cinza, 126, 255, cv2.THRESH_BINARY)
    cv2.imwrite('3final/imagem_final.png', imagem_final)
    print("Tratamento concluído com sucesso!")'''
