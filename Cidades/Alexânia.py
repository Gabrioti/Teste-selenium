import os
import sys

from Gerenciadores.assistente_manual import solicitar_acao_manual

siteCadastro = "https://nfse.alexania.go.gov.br/servicosweb/home.jsf"


def recolher(CNPJ, site, pasta_download):
    return solicitar_acao_manual(
        cnpj=CNPJ,
        site=site,
        pasta_download=pasta_download,
        nome_orgao="Alexânia",
    )


if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    cnpj_teste = "39847300000146"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    sucesso, mensagem = recolher(cnpj_teste, siteCadastro, pasta_teste)
    print(f"Sucesso: {sucesso} | Observação: '{mensagem}'")
