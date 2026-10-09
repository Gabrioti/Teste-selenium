import base64
import os
import time
from datetime import datetime
from urllib.parse import urlparse, quote

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# [AGEHAB]
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

def recolher_agehab(CNPJ, site, navegador, usuario, senha, pasta_download):
    url_com_login = montar_url_com_autenticacao(site, usuario, senha)
    print(f"[AGEHAB] Acessando o Palladium Gerencial: {site}")
    navegador.get(url_com_login)
    navegador.maximize_window()

    try:
        WebDriverWait(navegador, 20).until(
            lambda d: d.current_url.lower().startswith("http")
        )
    except Exception as e:
        return False, "O site da AGEHAB demorou muito para responder (Timeout)."

    time.sleep(2)

    try:
        navegador.find_element(By.XPATH, "//a[contains(@href, 'palladiogerencial')]").click()
    except:
        msg = "Não foi possível clicar no botão Palladium Gerencial."
        print(f"[AGEHAB] {msg}")
        # MODIFICADO AQUI: Interrompe e envia o erro pro painel
        return False, msg 

    time.sleep(1)

    try:
        navegador.find_element(By.XPATH,'//span[@class="rpText" and text()="Certidões"]').click()
    except:
        msg = "Não foi possível clicar na aba de Certidões."
        print(f"[AGEHAB] {msg}")
        return False, msg

    time.sleep(1)

    try:
        navegador.find_element(By.XPATH,'//span[@class="rpText" and text()="CND - Emitir Certidão"]').click()
    except:
        msg = "Não foi possível clicar em CND - Emitir Certidão."
        print(f"[AGEHAB] {msg}")
        return False, msg

    time.sleep(1)

    try:
        navegador.find_element(By.XPATH, '//*[@id="ctl00_cphRoot_PesqConveniado_rbDigitar"]').click()
    except:
        msg = "Não foi possível selecionar a opção de digitar CNPJ."
        print(f"[AGEHAB] {msg}")
        return False, msg

    time.sleep(1)

    try:
        colocar_CNPJ = navegador.find_element(By.XPATH, '//*[@id="ctl00_cphRoot_PesqConveniado_txtCNPJ"]')
        colocar_CNPJ.click()
        colocar_CNPJ.send_keys(CNPJ)
    except:
        msg = "Não foi possível preencher a caixa do CNPJ."
        print(f"[AGEHAB] {msg}")
        return False, msg
    
    time.sleep(1)

    try:
        navegador.find_element(By.XPATH,'//*[@id="ctl00_cphRoot_btnEmitirCertidao"]').click()
    except:
        # Se a empresa não tem cadastro na AGEHAB, ela trava exatamente neste botão
        msg = "Não foi possível emitir. (Empresa não cadastrada na AGEHAB?)"
        print(f"[AGEHAB] {msg}")
        return False, msg

    time.sleep(1)
    try:
        abas_abertas = navegador.window_handles
        if len(abas_abertas) > 1:
            navegador.switch_to.window(abas_abertas[-1])
        WebDriverWait(navegador, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)

        resultado_pdf = navegador.execute_cdp_cmd(
            "Page.printToPDF",
            {
                "printBackground": True,
                "preferCSSPageSize": True,
            },
        )
        dados_pdf = base64.b64decode(resultado_pdf["data"], validate=True)
        if not dados_pdf.startswith(b"%PDF-"):
            raise ValueError("O Chrome não retornou um documento PDF válido.")

        os.makedirs(pasta_download, exist_ok=True)
        cnpj_limpo = "".join(digito for digito in str(CNPJ) if digito.isdigit())
        nome_pdf = (
            f"AGEHAB_{cnpj_limpo}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
        )
        caminho_pdf = os.path.join(pasta_download, nome_pdf)
        with open(caminho_pdf, "wb") as arquivo_pdf:
            arquivo_pdf.write(dados_pdf)

        print(f"[AGEHAB] PDF salvo em: {caminho_pdf}")
        print("[AGEHAB] Certidão recolhida com sucesso!")
        return True, ""
    except Exception as e:
        msg = f"Não foi possível gerar e salvar o PDF da certidão: {e}"
        print(f"[AGEHAB] {msg}")
        return False, msg