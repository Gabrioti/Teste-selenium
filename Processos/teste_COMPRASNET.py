import os
import sys
import time
import urllib.parse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download, _arquivos_validos

try:
    import ddddocr
    _ocr = ddddocr.DdddOcr(show_ad=False)
except Exception:
    _ocr = None


def extrair_codigo_captcha(navegador):
    """
    Tenta obter o código do CAPTCHA do Comprasnet de forma automática:
    1. Inspeciona se o código numérico está presente no parâmetro 'img=' do src da imagem.
    2. Caso não esteja, utiliza a rede neural leve (ddddocr).
    """
    try:
        img_el = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'ImageCaptcha') or contains(@id, 'Captcha')]"))
        )
        src = img_el.get_attribute("src") or ""
        if "img=" in src:
            parsed = urllib.parse.urlparse(src)
            params = urllib.parse.parse_qs(parsed.query)
            codigo_url = params.get("img", [""])[0].strip()
            if codigo_url and len(codigo_url) == 7 and codigo_url.isdigit():
                print(f"[COMPRASNET] Código obtido do portal: '{codigo_url}'")
                return codigo_url

        if _ocr is not None:
            codigo_ocr = _ocr.classification(img_el.screenshot_as_png).strip()
            if codigo_ocr:
                print(f"[COMPRASNET] OCR decifrou CAPTCHA: '{codigo_ocr}'")
                return codigo_ocr
    except Exception as e:
        print(f"[COMPRASNET] Aviso ao capturar CAPTCHA: {e}")

    return None


COR_COMPRASNET = "\033[38;2;255;255;204m"  # Amarelo claro (#FFFFCC)
COR_ERRO = "\033[31m"
COR_RESET = "\033[0m"


def recolher(CNPJ, site, navegador, pasta_download=None, solicitar_captcha=None):
    if not pasta_download:
        pasta_download = r"n:\19. FERRAMENTAS\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_download, exist_ok=True)

    # Garante que a URL utilize HTTPS para evitar bloqueios de conteúdo misto / downloads inseguros do Chrome
    if site.startswith("http://"):
        site = site.replace("http://", "https://")

    print(f"{COR_COMPRASNET}[COMPRASNET] Iniciando consulta para o CNPJ: {CNPJ}...{COR_RESET}")
    max_tentativas = 3

    for tentativa in range(1, max_tentativas + 1):
        try:
            # 1. Carrega ou recarrega a página e preenche o CNPJ novamente
            print(f"{COR_COMPRASNET}[COMPRASNET] Carregando portal (Tentativa {tentativa}/{max_tentativas})...{COR_RESET}")
            navegador.get(site)
            time.sleep(2)

            campo_cnpj = WebDriverWait(navegador, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_txtCNPJ"))
            )
            campo_cnpj.clear()
            campo_cnpj.send_keys(CNPJ)

            # 2. Obtém o código do CAPTCHA (automático com fallback para intervenção humana)
            codigo = extrair_codigo_captcha(navegador)

            # Se o automático não obteve um código válido de 7 dígitos, pede ao usuário
            if not codigo or len(codigo) != 7 or not codigo.isdigit():
                if solicitar_captcha is not None:
                    print("[COMPRASNET] Solicitando CAPTCHA ao usuário na interface...")
                    codigo = solicitar_captcha().strip()
                else:
                    codigo = input("[COMPRASNET] Digite o CAPTCHA exibido no navegador (7 dígitos): ").strip()

            if not codigo:
                print("\033[33m[COMPRASNET] Nenhum código fornecido. Recarregando...\033[0m")
                continue

            # 3. Preenche o campo de CAPTCHA
            campo_captcha = WebDriverWait(navegador, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_Captcha1_txtCodigoCaptcha"))
            )
            campo_captcha.clear()
            campo_captcha.send_keys(codigo)

            # 4. Registra arquivos antes e clica em Pesquisar / Emitir
            arquivos_antes = set(_arquivos_validos(pasta_download))

            btn_emitir = WebDriverWait(navegador, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_btnPesquisar"))
            )
            btn_emitir.click()
            time.sleep(3)

            # 5. Validação: Checa se deu 'Código Incorreto'
            mensagens_erro = navegador.find_elements(
                By.XPATH,
                "//span[@id='ctl00_ContentPlaceHolder1_Captcha1_lblMensagem' and contains(normalize-space(), 'Código Incorreto')]"
            )
            if any(m.is_displayed() and "Código Incorreto" in m.text for m in mensagens_erro):
                print(f"\033[33m[COMPRASNET] Código '{codigo}' foi recusado. Recarregando a página e preenchendo CNPJ novamente...\033[0m")
                continue

            # 6. Checa mensagens de bloqueio/débito
            mensagens_bloqueio = navegador.find_elements(
                By.XPATH,
                "//span[contains(@id, 'lblMensagem') or contains(@id, 'lblErro') or contains(@class, 'mensagem-erro')]"
            )
            houve_bloqueio = False
            texto_do_bloqueio = "Bloqueio desconhecido"
            
            for m in mensagens_bloqueio:
                txt = m.text.strip()
                if txt and "código incorreto" not in txt.lower():
                    print(f"\033[31m[COMPRASNET] Aviso do portal para o CNPJ {CNPJ}: {txt}\033[0m")
                    houve_bloqueio = True
                    texto_do_bloqueio = txt
                    
            if houve_bloqueio:
                # MODIFICADO AQUI: Interrompe e envia a mensagem exata do portal pro painel
                return False, f"Aviso do Portal: {texto_do_bloqueio}"

            # 7. Aguarda o download do PDF com tempo estendido para resposta do servidor estadual
            try:
                arquivo = esperar_download(navegador, pasta_download, timeout=45, arquivos_antes=arquivos_antes)
                print(f"{COR_COMPRASNET}[COMPRASNET] CND recolhida com sucesso para o CNPJ: {CNPJ}{COR_RESET}")
                print(f"{COR_COMPRASNET}Arquivo baixado: {arquivo}{COR_RESET}")
                
                # MODIFICADO AQUI: Sucesso! Devolve True e observação em branco
                return True, ""
                
            except TimeoutError:
                print(f"\033[33m[COMPRASNET] Arquivo não foi baixado dentro do tempo limite. Tentando novamente...\033[0m")
                continue

        except Exception as e:
            print(f"\033[31m[COMPRASNET] Erro na tentativa {tentativa}: {e}\033[0m")
            time.sleep(2)

    msg_falha = f"Falha ao emitir certidão após {max_tentativas} tentativas."
    print(f"\033[31m[COMPRASNET] {msg_falha} (CNPJ: {CNPJ})\033[0m")
    
    # MODIFICADO AQUI: Se gastou todas as tentativas, reporta ao painel
    return False, msg_falha


if __name__ == "__main__":
    from main import criar_navegador_configurado

    cnpj_teste = "41088225000129"
    site_padrao = "https://www.comprasnet.go.gov.br/paginas/fornecedor/CertidaoNegativaEmissao.aspx"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"

    print(f"\033[36m--- Teste Avulso: COMPRASNET (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        recolher(cnpj_teste, site_padrao, navegador_teste, pasta_teste)
    finally:
        navegador_teste.quit()