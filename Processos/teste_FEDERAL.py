import time
import os
import sys
import webbrowser # NOVA: Biblioteca nativa para abrir sites com segurança
import pyautogui as ad
import pygetwindow as gw
from Gerenciadores import gerenciador_cnpj

# Cores para o terminal
COR_FEDERAL = "\033[38;2;51;153;255m"  # Azul (#3399FF)
COR_ERRO = "\033[31m"
COR_RESET = "\033[0m"

def resolver_caminho_imagem(nome_arquivo):
    """
    Resolve o caminho da imagem de forma inteligente, funcionando tanto 
    no VS Code quanto no executável compilado (.exe).
    """
    if getattr(sys, 'frozen', False):
        # Se for .exe, as imagens estão na pasta secreta _MEIPASS
        pasta_base = sys._MEIPASS
    else:
        # Se for no VS Code, volta uma pasta para pegar a raiz do projeto
        pasta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    return os.path.join(pasta_base, 'ImagensFederal', nome_arquivo)

def esperar_imagem_aparecer(nome_imagem_cru, tempo_maximo=30, confianca=0.8):
    """
    Esta função tenta encontrar uma imagem na tela.
    """
    nome_imagem = resolver_caminho_imagem(nome_imagem_cru)
    print(f"A aguardar a imagem '{nome_imagem_cru}' aparecer na tela...")
    
    tempo_inicial = time.time()
    while True:
        try:
            posicao = ad.locateOnScreen(nome_imagem, confidence=confianca)
            if posicao is not None:
                print(f"Imagem encontrada com sucesso!")
                return posicao
        except Exception:
            pass
            
        tempo_passado = time.time() - tempo_inicial
        if tempo_passado > tempo_maximo:
            print(f"Erro: O tempo limite passou e a imagem não carregou.")
            return None
            
        time.sleep(0.5)

def recolher_FEDERAL(CNPJ, site):
    # Verifica a matriz
    matriz = gerenciador_cnpj.obter_matriz_do_cnpj(CNPJ)
    if matriz:
        print(f"{COR_FEDERAL}[FEDERAL] CNPJ filial encontrado, usando matriz: {matriz}{COR_RESET}")
        CNPJ_USADO = matriz
    else:
        print(f"{COR_FEDERAL}[FEDERAL] CNPJ matriz não encontrado, usando CNPJ original{COR_RESET}")
        CNPJ_USADO = CNPJ

    try:
        print(f"{COR_FEDERAL}[FEDERAL] Abrindo o navegador via sistema operacional...{COR_RESET}")
        # ABRE DIRETO NO NAVEGADOR - Sem usar o Iniciar do Windows!
        webbrowser.open(site)
        time.sleep(4) # Espera o navegador abrir e carregar o site da Receita
        
        # Opcional: Dar um "F11" ou "Win+Seta pra Cima" para garantir tela cheia
        ad.hotkey('f11')
        time.sleep(1)
        
    except Exception as erro:
        msg = f"Não conseguiu abrir o navegador: {erro}"
        print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
        return False, msg

    try:
        time.sleep(2)
        print(f"{COR_FEDERAL}[FEDERAL] Procurando o campo do CNPJ...{COR_RESET}")
        
        posicao_da_imagem = esperar_imagem_aparecer("botaoCNPJ.png", tempo_maximo=20, confianca=0.8)

        if posicao_da_imagem is not None:
            centro_x, centro_y = ad.center(posicao_da_imagem)
            ad.click(centro_x, centro_y)
            ad.write(CNPJ_USADO)

            print(f"{COR_FEDERAL}[FEDERAL] Clicando no botão emitir{COR_RESET}")
            posicao_da_imagem = esperar_imagem_aparecer("botaoEmitir.png", tempo_maximo=20, confianca=0.8)
    
            if posicao_da_imagem is not None:
                centro_x, centro_y = ad.center(posicao_da_imagem)
                ad.click(centro_x, centro_y)
                print(f"{COR_FEDERAL}[FEDERAL] Sucesso! Cliquei no botão Emitir.{COR_RESET}")
            else:
                msg = "A imagem do botão 'Emitir' demorou muito a carregar."
                print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
                ad.hotkey('ctrl', 'w') # Fecha a aba para não acumular
                return False, msg
        else:
            msg = "A imagem do campo 'CNPJ' demorou muito a carregar."
            print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
            ad.hotkey('ctrl', 'w')
            return False, msg

    except Exception as erro:
        msg = f"Ocorreu um erro na execução: {erro}"
        print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
        ad.hotkey('ctrl', 'w')
        return False, msg

    time.sleep(4)

    # Verifica o pop-up de "Nova Certidão"
    try:
        print(f"{COR_FEDERAL}[FEDERAL] Atualizando a página...{COR_RESET}")
        ad.hotkey('f5')
        time.sleep(5)
        posicao_da_imagem = esperar_imagem_aparecer("botaoCNPJ.png", tempo_maximo=20, confianca=0.8)

        if posicao_da_imagem is not None:
            centro_x, centro_y = ad.center(posicao_da_imagem)
            ad.click(centro_x, centro_y)
            ad.write(CNPJ_USADO)
            print(f"{COR_FEDERAL}[FEDERAL] Clicando no botão emitir{COR_RESET}")
            posicao_da_imagem = esperar_imagem_aparecer("botaoEmitir.png", tempo_maximo=20, confianca=0.8)
    
            if posicao_da_imagem is not None:
                centro_x, centro_y = ad.center(posicao_da_imagem)
                ad.click(centro_x, centro_y)
                print(f"{COR_FEDERAL}[FEDERAL] Sucesso! Cliquei no botão Emitir.{COR_RESET}")
            else:
                msg = "A imagem do botão 'Emitir' demorou muito a carregar."
                print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
                ad.hotkey('ctrl', 'w') # Fecha a aba para não acumular
                return False, msg
        else:
            msg = "A imagem do botão 'CNPJ' demorou muito a carregar."
            print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
            ad.hotkey('ctrl', 'w')
            return False, msg

        print(f"{COR_FEDERAL}[FEDERAL] Verificando se existe certidão válida...{COR_RESET}")
        
        posicao_da_imagem = ad.locateOnScreen(resolver_caminho_imagem("JanelaExisteCertidaoValida.png"), confidence=0.95)

        if posicao_da_imagem is not None:
            botaoEmitirNovaCND = ad.locateOnScreen(resolver_caminho_imagem("JaExisteCND.png"), confidence=0.95)
            
            if botaoEmitirNovaCND is not None:
                centro_x, centro_y = ad.center(botaoEmitirNovaCND)
                ad.click(centro_x, centro_y)
                print(f"{COR_FEDERAL}[FEDERAL] Cliquei no botão Consultar certidão.")
                time.sleep(3)
                botaoconsultar = ad.locateOnScreen(resolver_caminho_imagem("ConsultarCND.png"), confidence=0.95)
                if botaoconsultar is not None:
                    centro_x, centro_y = ad.center(botaoconsultar)
                    ad.click(centro_x, centro_y)
                    print(f"{COR_FEDERAL}[FEDERAL] Cliquei no botão Consultar certidão.")
                    time.sleep(3) # Espera baixar
                    botao2via = ad.locateOnScreen(resolver_caminho_imagem("2via.png"), confidence=0.95)
                    
                    if botao2via is not None:
                        centro_x, centro_y = ad.center(botao2via)
                        ad.click(centro_x, centro_y)
                        print(f"{COR_FEDERAL}[FEDERAL] Cliquei no botão 2 via.")
                        time.sleep(3) # Espera baixar
                    else:
                        msg = "A janela de Certidão Válida apareceu, mas o botão para baixar a certidão não foi encontrado."
                        print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
                        ad.hotkey('ctrl', 'w') # Fecha a aba para não acumular
                        return False, msg

                else:
                    msg = "A janela de Certidão Válida apareceu, mas o botão 'Consultar Certidão' não foi encontrado."
                    print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
                    ad.hotkey('ctrl', 'w') # Fecha a aba para não acumular
                    return False, msg
                
                ad.hotkey('ctrl', 'w') # Fecha a aba
                return True, ""
            else:
                msg = "A janela de Certidão Válida apareceu, mas o botão não foi encontrado."
                print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
                ad.hotkey('ctrl', 'w')
                return False, msg
        else:
            # Se não apareceu a janela, significa que ele emitiu direto
            print(f"{COR_FEDERAL}[FEDERAL] A janela não apareceu. Certidão possivelmente emitida direto.{COR_RESET}")
            time.sleep(3) # Espera o download concluir
            ad.hotkey('ctrl', 'w') # Fecha a aba
            return True, ""

    except Exception as erro:
        msg = f"Erro na etapa de verificação de certidão: {erro}"
        print(f"{COR_ERRO}[FEDERAL] {msg}{COR_RESET}")
        ad.hotkey('ctrl', 'w')
        return False, msg

if __name__ == "__main__":
    # Permite importar a pasta Gerenciadores corretamente se o arquivo for rodado solto
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    
    # Variáveis de teste usando os dados originais do seu script
    CNPJ_TESTE = "13798155001996" 
    SITE_TESTE = "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj"

    print("\033[36m--- Teste Avulso: CND FEDERAL (PyAutoGUI) ---\033[0m")
    print(f"Testando para o CNPJ: {CNPJ_TESTE}\n")
    
    # Chama a função e captura a dupla de respostas (Sucesso, Mensagem)
    sucesso, mensagem = recolher_FEDERAL(CNPJ_TESTE, SITE_TESTE)
    
    # Exibe o resultado final do teste no terminal
    print("\n\033[36m--- Resultado Final do Teste ---\033[0m")
    if sucesso:
        print(f"\033[32m[SUCESSO]\033[0m A coleta foi concluída perfeitamente!")
    else:
        print(f"\033[31m[FALHA]\033[0m A coleta parou. Motivo: {mensagem}")