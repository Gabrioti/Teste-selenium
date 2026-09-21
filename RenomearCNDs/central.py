import os
import sys
import subprocess
from processador import processar_todas_cnds

# ==========================================
# VACINA ANTI-TERMINAL (Para o OCR rodar invisível)
# ==========================================
if os.name == 'nt':
    CREATE_NO_WINDOW = 0x08000000
    original_popen = subprocess.Popen

    def popen_sem_janela(*args, **kwargs):
        kwargs['creationflags'] = CREATE_NO_WINDOW
        return original_popen(*args, **kwargs)

    subprocess.Popen = popen_sem_janela

# ==========================================
# EXECUÇÃO AUTOMÁTICA
# ==========================================
if __name__ == "__main__":
    # Descobre o caminho absoluto exato de onde o main.py está rodando
    pasta_do_script = os.path.dirname(os.path.abspath(__file__))
    
    # Junta a pasta do script com a pasta "CNDs" de forma segura
    caminho_da_pasta = os.path.join(pasta_do_script, "CNDs")
    
    # Se quiser ver o texto extraído no terminal da sua outra aplicação, mude para True
    modo_debug = False 

    # Validação simples para evitar que o código quebre se a pasta não existir
    if not os.path.exists(caminho_da_pasta):
        print(f"Erro: A pasta '{caminho_da_pasta}' não foi encontrada.")
        sys.exit(1)

    print(f"Iniciando automação silenciosa na pasta: {caminho_da_pasta}")
    
    # Chama o motor principal diretamente
    processar_todas_cnds(caminho_da_pasta, modo_debug)
    
    print("Processamento finalizado!")