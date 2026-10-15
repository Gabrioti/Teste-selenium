import os
import sys
import time
import base64

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# OCR library (ddddocr)
try:
    import ddddocr
    _ocr = ddddocr.DdddOcr(show_ad=False)
except Exception:
    _ocr = None

# Color codes for console output
COR_GOIAS = "\033[38;2;0;128;255m"  # Blue
COR_ERRO = "\033[31m"
COR_SUCESSO = "\033[32m"
COR_RESET = "\033[0m"

# Helpers for download handling
from CadastroDiagnostico.diagnostico_download import esperar_download, _arquivos_validos
from Gerenciadores.gerenciador_caminhos import obter_pasta_dados_usuario

def extrair_codigo_captcha(navegador):
    """Decode the CAPTCHA on the Goiânia portal using ddddocr.
    Returns a cleaned 5‑character string or None.
    """
    if _ocr is None:
        print(f"{COR_GOIAS}[GOIÂNIA] OCR (ddddocr) não está disponível.{COR_RESET}")
        return None
    try:
        print(f"{COR_GOIAS}[GOIÂNIA] Tentando ler CAPTCHA...{COR_RESET}")
        # Try to locate CAPTCHA image by common selectors; fallback to canvas if needed
        # Try to locate CAPTCHA image by common selectors; fallback to canvas if needed
        try:
            img_el = WebDriverWait(navegador, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//img[contains(@src,'captcha') or @id='id_img_captcha' or @id='captchaImage']"))
            )
        except Exception:
            # If no <img> found, attempt to capture a <canvas> element
            img_el = WebDriverWait(navegador, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "canvas"))
            )
        canvas_b64 = navegador.execute_script(
            """
            var img = document.getElementById('id_img_captcha');
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || 125;
            canvas.height = img.naturalHeight || 66;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png');
            """,
            img_el,
        )
        if canvas_b64 and 'base64,' in canvas_b64:
            raw_bytes = base64.b64decode(canvas_b64.split('base64,')[1].strip())
        else:
            raw_bytes = img_el.screenshot_as_png
        # Save for audit
        try:
            pasta_dataset = os.path.join(obter_pasta_dados_usuario(), "dataset_captchas", "goiania")
            os.makedirs(pasta_dataset, exist_ok=True)
            nome_arquivo = os.path.join(pasta_dataset, f"goiania_{int(time.time()*1000)}.png")
            with open(nome_arquivo, 'wb') as f:
                f.write(raw_bytes)
        except Exception:
            pass
        cod_pred = _ocr.classification(raw_bytes).strip()
        cod_limpo = "".join(c for c in cod_pred if c.isalnum() and c.isascii()).lower()
        print(f"{COR_GOIAS}[GOIÂNIA] OCR leu: '{cod_limpo}' ({len(cod_limpo)} chars){COR_RESET}")
        if len(cod_limpo) == 5:
            return cod_limpo
        print(f"{COR_GOIAS}[GOIÂNIA] Código inválido (precisa 5 chars).{COR_RESET}")
        return None
    except Exception as e:
        print(f"{COR_GOIAS}[GOIÂNIA] Erro ao extrair CAPTCHA: {e}{COR_RESET}")
        return None

def recarregar_captcha(navegador):
    """Force a new CAPTCHA by updating the image src timestamp via JS."""
    try:
        navegador.execute_script(
            """
            var img = document.querySelector('img[src*="captcha"]');
            if (img) {
                var base = img.src.split('&time=')[0];
                img.src = base + '&time=' + new Date().getTime();
            }
            """
        )
        time.sleep(1.5)
    except Exception as e:
        print(f"{COR_GOIAS}[GOIÂNIA] Aviso ao recarregar captcha: {e}{COR_RESET}")

def fechar_alerta_se_existir(navegador):
    """Close SweetAlert2 pop‑ups and return the message if present."""
    try:
        popups = navegador.find_elements(By.CSS_SELECTOR, ".swal2-container.swal2-shown, .swal2-modal")
        for p in popups:
            if p.is_displayed():
                texto = " ".join([t.text.strip() for t in p.find_elements(By.CSS_SELECTOR, ".swal2-html-container, .swal2-title, .swal2-content") if t.text.strip()])
                btn = p.find_elements(By.CSS_SELECTOR, "button.swal2-confirm")
                if btn:
                    navegador.execute_script("arguments[0].click();", btn[0])
                    time.sleep(1)
                return texto
    except Exception:
        pass
    return None

def preencher_cnpj_e_captcha(navegador, cnpj, pasta_download=None, solicitar_captcha=None):
    """Fill CNPJ, solve CAPTCHA (OCR up to 5 attempts) and submit.
    Returns (success: bool, message: str).
    """
    if not pasta_download:
        pasta_download = r"C:\\Users\\FAGabrioti\\Desktop\\Teste selenium\\RenomearCNDs\\CNDs"
    os.makedirs(pasta_download, exist_ok=True)
    tentativas = 0
    max_ocr = 5
    max_total = 8
    while tentativas < max_total:
        tentativas += 1
        print(f"{COR_GOIAS}[GOIÂNIA] Tentativa {tentativas}/{max_total}...{COR_RESET}")
        # Locate CNPJ input
        try:
            campo_cnpj = WebDriverWait(navegador, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@name='txt_nr_cpfcnpj']"))
            )
        except Exception as e:
            print(f"{COR_ERRO}[GOIÂNIA] Campo CNPJ não encontrado: {e}{COR_RESET}")
            return False, "Campo CNPJ não encontrado"
        cnpj_limpo = "".join(filter(str.isdigit, cnpj))
        campo_cnpj.clear()
        campo_cnpj.send_keys(cnpj_limpo)
        print(f"{COR_GOIAS}[GOIÂNIA] CNPJ preenchido: {cnpj_limpo}{COR_RESET}")
        # Resolve CAPTCHA
        codigo = None
        if tentativas <= max_ocr:
            codigo = extrair_codigo_captcha(navegador)
            if not codigo:
                print(f"{COR_GOIAS}[GOIÂNIA] OCR falhou, recarregando captcha...{COR_RESET}")
                recarregar_captcha(navegador)
                continue
        else:
            if solicitar_captcha:
                codigo = solicitar_captcha().strip()
            else:
                codigo = input(f"{COR_GOIAS}[GOIÂNIA] Digite o CAPTCHA (5 chars): {COR_RESET}").strip()
        if not codigo:
            print(f"{COR_ERRO}[GOIÂNIA] Código CAPTCHA vazio. Tentando novamente.{COR_RESET}")
            recarregar_captcha(navegador)
            continue
        # Fill CAPTCHA field
        try:
            campo_cap = WebDriverWait(navegador, 5).until(
                EC.element_to_be_clickable((By.ID, "id_txt_captcha"))
            )
            campo_cap.clear()
            campo_cap.send_keys(codigo)
            print(f"{COR_GOIAS}[GOIÂNIA] CAPTCHA inserido: {codigo}{COR_RESET}")
        except Exception as e:
            print(f"{COR_ERRO}[GOIÂNIA] Campo CAPTCHA não encontrado: {e}{COR_RESET}")
            return False, "Campo CAPTCHA não encontrado"
        # Submit
        try:
            btn = WebDriverWait(navegador, 5).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//input[@value[contains(.,'Consultar')] or @id='consultar'] | //button[contains(.,'Consultar')] | //a[contains(@href,'consultar')]"))
            )
            navegador.execute_script("arguments[0].click();", btn)
            print(f"{COR_GOIAS}[GOIÂNIA] Botão Consultar clicado.{COR_RESET}")
        except Exception as e:
            print(f"{COR_ERRO}[GOIÂNIA] Botão Consultar não encontrado: {e}{COR_RESET}")
            return False, "Botão Consultar não encontrado"
        time.sleep(3)
        # Check for alerts
        alerta = fechar_alerta_se_existir(navegador)
        if alerta:
            msg = alerta.lower()
            if any(w in msg for w in ["não confere", "incorret", "captcha"]):
                print(f"{COR_GOIAS}[GOIÂNIA] CAPTCHA rejeitado, recarregando...{COR_RESET}")
                recarregar_captcha(navegador)
                continue
            if any(w in msg for w in ["não cadastrad", "pendênc", "bloque"]):
                return False, f"Bloqueio do portal: {alerta}"
        # Attempt download
        try:
            link = WebDriverWait(navegador, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@title,'Download') or contains(@href,'downloadanexo.action')]") )
            )
            href = link.get_attribute('href') or ''
            if href and 'downloadanexo.action' in href:
                import urllib.request
                if not href.startswith('http'):
                    href = 'https://www.goiania.go.gov.br' + href
                cookies = navegador.get_cookies()
                cookie_header = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
                req = urllib.request.Request(href, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Cookie': cookie_header,
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                    if len(data) > 500 and (b"%PDF" in data[:20] or 'pdf' in (resp.headers.get('Content-Type') or '').lower()):
                        nome = f"CND_Goiania_{cnpj}_{int(time.time())}.pdf"
                        caminho = os.path.join(pasta_download, nome)
                        with open(caminho, 'wb') as f:
                            f.write(data)
                        print(f"{COR_SUCESSO}[GOIÂNIA] CND salva via stream: {caminho}{COR_RESET}")
                        return True, ""
            # Fallback click
            link.click()
            arquivos_antes = set(_arquivos_validos(pasta_download))
            arquivo = esperar_download(navegador, pasta_download, timeout=20, arquivos_antes=arquivos_antes)
            print(f"{COR_SUCESSO}[GOIÂNIA] CND baixada: {arquivo}{COR_RESET}")
            return True, ""
        except Exception as e:
            print(f"{COR_ERRO}[GOIÂNIA] Erro ao obter PDF: {e}{COR_RESET}")
            try:
                navegador.get('https://www.goiania.go.gov.br/sistemas/sccer/asp/sccer00300f0.asp')
                time.sleep(2)
            except Exception:
                pass
            continue
    return False, f"Falha após {max_total} tentativas"

def recolher(CNPJ, site, pasta_download=None, solicitar_captcha=None):
    """Public entry point compatible with the existing main workflow."""
    if not pasta_download:
        pasta_download = r"C:\\Users\\FAGabrioti\\Desktop\\Teste selenium\\RenomearCNDs\\CNDs"
    os.makedirs(pasta_download, exist_ok=True)
    from main import criar_navegador_configurado
    navegador = criar_navegador_configurado(headless=False)
    try:
        navegador.get(site)
        time.sleep(2)
        sucesso, msg = preencher_cnpj_e_captcha(
            navegador=navegador,
            cnpj=CNPJ,
            pasta_download=pasta_download,
            solicitar_captcha=solicitar_captcha,
        )
        return sucesso, msg
    finally:
        navegador.quit()

if __name__ == "__main__":
    CNPJ_EXEMPLO = "13798155001996"
    SITE_GOIAS = "https://www.goiania.go.gov.br/sistemas/sccer/asp/sccer00300f0.asp"
    PASTA = r"C:\\Users\\FAGabrioti\\Desktop\\Teste selenium\\RenomearCNDs\\CNDs"
    print(f"--- Teste Goiânia {CNPJ_EXEMPLO} ---")
    sucesso, msg = recolher(CNPJ_EXEMPLO, SITE_GOIAS, PASTA)
    print(f"Sucesso: {sucesso} | Mensagem: {msg}")