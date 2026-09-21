# [HEADLESS: NÃO APLICÁVEL - COLETA MANUAL]
# Este portal requer emissão manual pelo contribuinte.
# No arquivo dados.py, o município de Goiânia está configurado com 'automatizado: False'.

import os
import sys

siteCadastro = ""


def recolher(CNPJ, site, navegador, pasta_download):
    print(f"\033[33m[Goiânia] A emissão para Goiânia é manual (automatizado: False no dados.py).\033[0m")
    return


if __name__ == "__main__":
    print(f"\033[36m--- Goiânia (Coleta Manual) ---\033[0m")
    print(f"URL: {siteCadastro}")
    print("Este município deve ser emitido manualmente pelo usuário.")

import os
import sys
from Gerenciadores import gerenciador_cnpj
# Ajuste o import abaixo dependendo da pasta onde você salvou o assistente_manual.py
from Gerenciadores.assistente_manual import solicitar_acao_manual


def recolher(CNPJ, site, pasta_download):
#(Goiânia.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)

    print(f"[Goiânia] Iniciando coleta assistida para o CNPJ: {CNPJ}...")
    
    # Chama o módulo isolado passando o nome do órgão para personalizar a janela
    sucesso, mensagem = solicitar_acao_manual(
        cnpj=CNPJ,
        site=site,
        pasta_download=pasta_download,
        nome_orgao="Municípal"
    )
    
    return sucesso, mensagem

if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    
    CNPJ_TESTE = "13798155001996" 
    SITE_TESTE = "https://www.goiania.go.gov.br/sistemas/sccer/asp/sccer00300f0.asp"
    PASTA_TESTE = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"

    print("\033[36m--- Teste Avulso: CND Goiânia ---\033[0m")
    sucesso, mensagem = recolher(CNPJ_TESTE, SITE_TESTE, PASTA_TESTE)
    
    print("\n\033[36m--- Resultado Final ---\033[0m")
    print(f"Sucesso: {sucesso} | Observação: '{mensagem}'")