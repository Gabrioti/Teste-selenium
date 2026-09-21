import time

import glob 
import time
import os

import pyautogui as ad
 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import json # Essa biblioteca permite que você trabalhe com arquivos JSON, que são muito usados para armazenar dados de forma estruturada.
import os # Essa biblioteca permite que você interaja com o sistema operacional, como criar pastas, apagar arquivos, etc.
import glob # Essa biblioteca permite que você busque arquivos usando padrões, como "*.pdf" para todos os PDFs.
import shutil # Essa biblioteca permite mover e sobrescrever arquivos em uma pasta para outra de forma limpa
import re
from datetime import datetime
from CadastroDiagnostico.diagnostico_download import esperar_download

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By 


SITE = "https://appweb2.agehab.com.br/"
CNPJ = "54563863000104"

def criar_navegador_configurado():
    """Função auxiliar para gerar navegadores idênticos e isolados para CNDs"""
    opcoes = Options()

    # Argumentos originais de segurança
    opcoes.add_argument('--safebrowsing-disable-download-protection')
    opcoes.add_argument('--safebrowsing-disable-extension-blacklist')
    opcoes.add_argument('--ignore-certificate-errors')
    opcoes.add_argument('--disable-features=InsecureDownloadWarnings')

    # Mantemos o Kiosk Printing para o "Confirmar" e "Imprimir"
    opcoes.add_argument('--kiosk-printing')

    pasta_download = r"C:\Users\FAGabrioti\Desktop\CNDs"

    # Configuração para o destino da impressão ser "Salvar como PDF"
    app_state = {
        "recentDestinations": [{
            "id": "Save as PDF",
            "origin": "local",
            "account": ""
        }],
        "selectedDestinationId": "Save as PDF",
        "version": 2
    }

    preferencias = {
        # OBRIGATÓRIO: Força o Chrome a baixar PDFs externos e não abri-los
        "plugins.always_open_pdf_externally": True,
        
        # Pasta padrão para downloads normais (fora do fluxo de impressão)
        "download.default_directory": pasta_download,
        
        # Desabilita o pop-up de confirmação de download
        "download.prompt_for_download": False,
        
        # Desabilitamos a navegação segura e a proteção de download
        "safebrowsing.enabled": True,
        "safebrowsing.disable_download_protection": True,
        
        # Permite downloads automáticos
        "profile.default_content_setting_values.automatic_downloads": 1,
        
        # Injeta as configurações de "Salvar como PDF"
        "printing.print_preview_sticky_settings.appState": json.dumps(app_state),
        
        # Define o diretório para onde os arquivos "Salvos como PDF" vão
        "savefile.default_directory": pasta_download,

        # ADICIONAL: Desabilita o download.directory_upgrade para consistência
        "download.directory_upgrade": True,
    }

    # Removemos a linha obsoleta "plugins.plugins_disabled": ["Chrome PDF Viewer"]
    # No Chrome moderno, "plugins.always_open_pdf_externally" já resolve.

    opcoes.add_experimental_option("prefs", preferencias)
    
    # Importante manter False para o main.py poder dar quit()
    opcoes.add_experimental_option("detach", False)

    servico = Service(ChromeDriverManager().install())

    return webdriver.Chrome(service=servico, options=opcoes)

from urllib.parse import urlparse, quote
#[AGEHAB]
def montar_url_com_autenticacao(site, usuario, senha):
    """Gera a URL com autenticação embutida para sites que pedem login via HTTP Auth."""
    partes = urlparse(site)
    usuario = quote(usuario, safe='')
    senha = quote(senha, safe='')
    nova_url = f"{partes.scheme}://{usuario}:{senha}@{partes.netloc}{partes.path or '/'}"
    if partes.query:
        nova_url += f"?{partes.query}"
    if partes.fragment:
        nova_url += f"#{partes.fragment}"
    return nova_url


def recolher_agehab(CNPJ, site, navegador, usuario="FAGabrioti", senha="Lara@285428"):
    url_com_login = montar_url_com_autenticacao(site, usuario, senha)
    print(f"[AGEHAB] Acessando o Palladium Gerencial com autenticação por URL: {url_com_login}")
    navegador.get(url_com_login)
    navegador.maximize_window()

    WebDriverWait(navegador, 20).until(
        lambda d: d.current_url.lower().startswith("http")
    )

    time.sleep(2)

    try:
        navegador.find_element(By.XPATH, "//a[contains(@href, 'palladiogerencial')]").click()
        pass
    except:
        print("[AGEHAB] Não foi possivel clicar no botão!")
        pass 

    time.sleep(1)

    try:
        navegador.find_element(By.XPATH,'//span[@class="rpText" and text()="Certidões"]').click()
        pass
    except:
        print("[AGEHAB] Não foi possivel clicar no botão!")
        pass

    time.sleep(1)

    try:
        navegador.find_element(By.XPATH,'//span[@class="rpText" and text()="CND - Emitir Certidão"]').click()
        pass
    except:
        print("[AGEHAB] Não foi possivel clicar no botão!")
        pass

    time.sleep(1)

    try:
        navegador.find_element(By.XPATH, '//*[@id="ctl00_cphRoot_PesqConveniado_rbDigitar"]').click()
        pass
    except:
        print("[AGEHAB] Não foi possivel clicar no botão!")
        pass

    time.sleep(1)

    try:
        colocar_CNPJ = navegador.find_element(By.XPATH, '//*[@id="ctl00_cphRoot_PesqConveniado_txtCNPJ"]')
        colocar_CNPJ.click()
        colocar_CNPJ.send_keys(CNPJ)
        pass
    except:
        print("[AGEHAB] Não foi possivel clicar no botão!")
        pass
    
    time.sleep(1)

    try:
        navegador.find_element(By.XPATH,'//*[@id="ctl00_cphRoot_btnEmitirCertidao"]').click()
        pass
    except:
        print("[AGEHAB] Não foi possivel clicar no botão!")
        pass

    time.sleep(1)

    # --- MUDANDO DE ABA ---

    # 1. Pegamos uma lista com todas as abas que o navegador abriu até agora
    abas_abertas = navegador.window_handles

    # 2. Mudamos o foco do Selenium para a última aba da lista (índice -1), que é a aba nova. Se uma nova aba realmente abriu, mudamos para ela
    try:
        if len(abas_abertas) > 1:
            navegador.switch_to.window(abas_abertas[-1])
        pass
    except:
        print("[AGEHAB] Não foi possivel mudar de aba!")
        pass
    
    time.sleep(1)
    try:
        navegador.find_element(By.XPATH, '//a[@href="javascript:window.print();"] or //u[text()="Imprimir"]').click()
        print("[AGEHAB] Certidão recolhida com sucesso!")
        pass
    except:
        print("[AGEHAB] Não foi possivel clicar no botão!")
        pass


if __name__ == "__main__":

    pasta_download = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    pasta_raiz_empresas = r"N:\16. CERTIDÕES\1. Empresas"

    navegador = criar_navegador_configurado()

    try:
        # Mude debug=False para debug=True se quiser ver informações de debug
        recolher_agehab(CNPJ, SITE, navegador, pasta_download)
        input("Pressione Enter para sair...")
    finally:
        navegador.quit()
