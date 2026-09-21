# [HEADLESS: NÃO APLICÁVEL - COLETA MANUAL]
# Este portal requer emissão manual pelo contribuinte.
# No arquivo dados.py, o município de Anápolis está configurado com 'automatizado: False'.

import os
import sys

siteCadastro = "https://portaldocidadao.anapolis.go.gov.br"


def recolher(CNPJ, site, navegador, pasta_download):
    print(f"\033[33m[Anápolis] A emissão para Anápolis é manual (automatizado: False no dados.py).\033[0m")
    return


if __name__ == "__main__":
    print(f"\033[36m--- Anápolis (Coleta Manual) ---\033[0m")
    print(f"URL: {siteCadastro}")
    print("Este município deve ser emitido manualmente pelo usuário.")

