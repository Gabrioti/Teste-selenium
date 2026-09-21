import cv2
import os

# 1. Definimos os caminhos das pastas
pasta_entrada = '1imagem/TRABALHO'
pasta_saida = '3final'

# 2. Usamos os.listdir para pegar todos os arquivos dentro da pasta 1imagem
arquivos_na_pasta = os.listdir(pasta_entrada)

# 3. O laço 'for' agora vai passar por CADA imagem encontrada na pasta
for nome_arquivo in arquivos_na_pasta:
    
    # Monta o caminho completo. Ex: "1imagem/image1.png"
    caminho_completo_entrada = os.path.join(pasta_entrada, nome_arquivo)
    
    # Lê a imagem
    imagem = cv2.imread(caminho_completo_entrada)
    
    if imagem is None:
        print(f"Ignorando '{nome_arquivo}' (Não é uma imagem válida ou não foi encontrada).")
        continue # Pula para o próximo arquivo do laço
        
    # Converte para escala de cinza
    imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    
    # Aplica o método de tratamento
    _, imagem_final = cv2.threshold(imagem_cinza, 126, 255, cv2.THRESH_BINARY)
    
    # 4. O SEGREDO ESTÁ AQUI: Criamos um nome dinâmico para salvar!
    # Ex: vai salvar como "3final/tratada_image1.png"
    nome_arquivo_saida = f"tratada_{nome_arquivo}"
    caminho_completo_saida = os.path.join(pasta_saida, nome_arquivo_saida)
    
    # Salva a imagem final sem sobrescrever as outras
    cv2.imwrite(caminho_completo_saida, imagem_final)
    
    print(f"Sucesso: {nome_arquivo} tratada e salva como {nome_arquivo_saida}!")

print("\nTodo o lote de imagens foi processado!")