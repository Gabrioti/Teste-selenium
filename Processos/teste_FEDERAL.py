import os
import sys
from Gerenciadores import gerenciador_cnpj
# Ajuste o import abaixo dependendo da pasta onde você salvou o assistente_manual.py
from Gerenciadores.assistente_manual import solicitar_acao_manual

COR_FEDERAL = "\033[38;2;51;153;255m"
COR_RESET = "\033[0m"

def recolher_FEDERAL(CNPJ, site, pasta_download):
    matriz = gerenciador_cnpj.obter_matriz_do_cnpj(CNPJ)
    CNPJ_USADO = matriz if matriz else CNPJ
    
    print(f"{COR_FEDERAL}[FEDERAL] Iniciando coleta assistida para o CNPJ: {CNPJ_USADO}...{COR_RESET}")
    
    # Chama o módulo isolado passando o nome do órgão para personalizar a janela
    sucesso, mensagem = solicitar_acao_manual(
        cnpj=CNPJ_USADO,
        site=site,
        pasta_download=pasta_download,
        nome_orgao="Federal"
    )
    
    return sucesso, mensagem

if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    
    CNPJ_TESTE = "13798155001996" 
    SITE_TESTE = "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj"
    PASTA_TESTE = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"

    print("\033[36m--- Teste Avulso: CND FEDERAL Híbrida ---\033[0m")
    sucesso, mensagem = recolher_FEDERAL(CNPJ_TESTE, SITE_TESTE, PASTA_TESTE)
    
    print("\n\033[36m--- Resultado Final ---\033[0m")
    print(f"Sucesso: {sucesso} | Observação: '{mensagem}'")