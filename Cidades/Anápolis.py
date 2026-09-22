import os
import sys
# Ajuste o import abaixo dependendo da pasta onde você salvou o assistente_manual.py
from Gerenciadores.assistente_manual import solicitar_acao_manual


def recolher(CNPJ, site, pasta_download):
    nome_cidade = "Estadual DF"

    print(f"[{nome_cidade}] Iniciando coleta assistida para o CNPJ: {CNPJ}...")
    
    # Chama o módulo isolado passando o nome do órgão para personalizar a janela
    sucesso, mensagem = solicitar_acao_manual(
        cnpj=CNPJ,
        site=site,
        pasta_download=pasta_download,
        nome_orgao=nome_cidade
    )
    
    return sucesso, mensagem

if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    
    CNPJ_TESTE = "13798155001996" 
    SITE_TESTE = "https://portaldocidadao.anapolis.go.gov.br"
    PASTA_TESTE = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    NOME_CIDADE = "Anápolis"

    print(f"\033[36m--- Teste Avulso: CND {NOME_CIDADE} ---\033[0m")
    sucesso, mensagem = recolher(CNPJ_TESTE,SITE_TESTE, PASTA_TESTE)
    
    print("\n\033[36m--- Resultado Final ---\033[0m")
    print(f"Sucesso: {sucesso} | Observação: '{mensagem}'")

