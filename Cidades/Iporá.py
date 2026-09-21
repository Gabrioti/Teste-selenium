# [HEADLESS: NÃO COMPATÍVEL - EXIGE hCaptcha]
# O portal oficial de Iporá é Centi Soluções (https://ipora.centi.com.br/servicos/certidaonegativa).
# A página possui proteção obrigatória por hCaptcha, impedindo emissão automatizada em modo headless sem resolução de captcha.

import os
import sys
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download

siteCadastro = "https://ipora.centi.com.br/servicos/certidaonegativa"


def recolher(CNPJ, site, navegador, pasta_download, solicitar_captcha=None):
    """
    Portal Centi Soluções - Iporá.
    Campos reais da página:
      - Select tipo: id="file-control" ('control1' = Por contribuinte)
      - Input CNPJ: id="cpfcnpjcontribuinte"
      - CAPTCHA: div.h-captcha (obrigatório)
      - Botão Emitir: input[type="submit"][value="Emitir"]
    """
    navegador.get(site)

    try:
        campo_cnpj = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.ID, "cpfcnpjcontribuinte"))
        )
        campo_cnpj.click()
        campo_cnpj.send_keys(CNPJ)
    except Exception as e:
        print(f"\033[31mErro: Campo de CNPJ não encontrado em Iporá (Centi). Detalhe: {e}\033[0m")
        return

    print("\033[33m⚠️ Atenção: O portal de Iporá (Centi) possui proteção por hCaptcha.\033[0m")
    # Para prosseguir, o hCaptcha precisa ser resolvido pelo usuário ou serviço de captcha.
    return


if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "39847300000146"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_teste, exist_ok=True)

    print(f"\033[36m--- Teste Avulso: Iporá (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        recolher(cnpj_teste, siteCadastro, navegador_teste, pasta_teste)
        input("\nPressione [ENTER] para encerrar o navegador de teste...")
    finally:
        navegador_teste.quit()