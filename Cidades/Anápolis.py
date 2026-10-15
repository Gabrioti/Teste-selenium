import os
import sys
import time
import base64

# Garante que a raiz do projeto esteja no sys.path para importações locais
RAIZ_PROJETO = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if RAIZ_PROJETO not in sys.path:
    sys.path.insert(0, RAIZ_PROJETO)

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download, _arquivos_validos
from Gerenciadores.gerenciador_caminhos import obter_pasta_dados_usuario

try:
    import ddddocr
    _ocr = ddddocr.DdddOcr(show_ad=False)
except Exception:
    _ocr = None

COR_ANAPOLIS = "\033[38;2;255;165;0m"  # Laranja (#FFA500)
COR_ERRO = "\033[31m"
COR_SUCESSO = "\033[32m"
COR_RESET = "\033[0m"


def extrair_codigo_captcha(navegador):
    """
    Decifra o código CAPTCHA do portal de Anápolis usando ddddocr.
    O CAPTCHA possui 5 caracteres alfanuméricos.
    Extrai a imagem diretamente via canvas com as dimensões naturais (125x66),
    evitando a distorção horizontal gerada pelo CSS da página (width: 100%).
    """
    if _ocr is None:
        print(f"{COR_ANAPOLIS}[ANÁPOLIS] OCR (ddddocr) não está disponível no ambiente.{COR_RESET}")
        return None

    try:
        print(f"{COR_ANAPOLIS}[ANÁPOLIS] Tentando capturar e ler CAPTCHA via OCR...{COR_RESET}")
        
        # Localiza o elemento da imagem do CAPTCHA
        img_el = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.step-img, img[src*='captcha.action']"))
        )

        # Captura via Canvas HTML5 usando as dimensões naturais (sem distorção de CSS)
        canvas_b64 = navegador.execute_script("""
            var img = arguments[0];
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || 125;
            canvas.height = img.naturalHeight || 66;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png');
        """, img_el)

        if canvas_b64 and "base64," in canvas_b64:
            b64_str = canvas_b64.split("base64,")[1].strip()
            raw_bytes = base64.b64decode(b64_str)
        else:
            raw_bytes = img_el.screenshot_as_png

        # Salva no dataset de captchas para auditoria e histórico
        try:
            pasta_dataset = os.path.join(
                obter_pasta_dados_usuario(),
                "dataset_captchas",
                "anapolis"
            )
            os.makedirs(pasta_dataset, exist_ok=True)
            nome_arquivo = os.path.join(
                pasta_dataset,
                f"anapolis_{int(time.time() * 1000)}.png",
            )
            with open(nome_arquivo, "wb") as f:
                f.write(raw_bytes)
        except Exception:
            pass

        # Predição com ddddocr
        cod_pred = _ocr.classification(raw_bytes).strip()
        cod_limpo = "".join(c for c in cod_pred if c.isalnum() and c.isascii()).lower()

        print(f"{COR_ANAPOLIS}[ANÁPOLIS] OCR fez a leitura da imagem: '{cod_limpo}' ({len(cod_limpo)} caracteres){COR_RESET}")

        if len(cod_limpo) == 5:
            print(f"{COR_ANAPOLIS}[ANÁPOLIS] Código de 5 caracteres decifrado: '{cod_limpo}'{COR_RESET}")
            return cod_limpo
        else:
            print(f"{COR_ANAPOLIS}[ANÁPOLIS] Leitura descartada por ter {len(cod_limpo)} caracteres (exige exatamente 5).{COR_RESET}")
            return None

    except Exception as e:
        print(f"{COR_ANAPOLIS}[ANÁPOLIS] Erro ao extrair CAPTCHA: {e}{COR_RESET}")
        return None


def recarregar_captcha(navegador):
    """
    Força o recarregamento do CAPTCHA via JavaScript alterando o timestamp do src,
    sem precisar recarregar toda a página.
    """
    try:
        navegador.execute_script("""
            var img = document.querySelector('img.step-img, img[src*="captcha.action"]');
            if (img) {
                var baseUrl = img.src.split('&time=')[0];
                img.src = baseUrl + '&time=' + new Date().getTime() + '&lua=';
            }
        """)
        time.sleep(1.5)
    except Exception as e:
        print(f"{COR_ANAPOLIS}[ANÁPOLIS] Aviso ao recarregar captcha: {e}{COR_RESET}")


def fechar_alerta_se_existir(navegador):
    """
    Verifica se o portal exibiu popup SweetAlert2 de erro ou aviso e fecha clicando em OK.
    Retorna o texto do alerta se houver.
    """
    try:
        popups = navegador.find_elements(By.CSS_SELECTOR, ".swal2-container.swal2-shown, .swal2-modal")
        for pop in popups:
            if pop.is_displayed():
                texto_el = pop.find_elements(By.CSS_SELECTOR, ".swal2-html-container, .swal2-title, .swal2-content")
                msg = " ".join([t.text.strip() for t in texto_el if t.text.strip()])

                btn_ok = pop.find_elements(By.CSS_SELECTOR, "button.swal2-confirm")
                if btn_ok and btn_ok[0].is_displayed():
                    navegador.execute_script("arguments[0].click();", btn_ok[0])
                    time.sleep(1)

                return msg
    except Exception:
        pass
    return None


def preencher_cnpj_e_solicitar_captcha(navegador, cnpj, pasta_download=None, solicitar_captcha=None):
    """
    Preenche CNPJ, seleciona o tipo de documento, resolve o CAPTCHA com OCR
    (até 5 tentativas) e baixa a Certidão Negativa de Débitos Municipais.
    Se o OCR falhar nas 5 tentativas, permite digitação humana nas tentativas restantes.
    """
    if not pasta_download:
        pasta_download = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_download, exist_ok=True)

    tentativas = 0
    max_tentativas_ocr = 5
    max_tentativas_totais = 8

    while tentativas < max_tentativas_totais:
        try:
            tentativas += 1
            print(f"{COR_ANAPOLIS}[ANÁPOLIS] [Tentativa {tentativas}/{max_tentativas_totais}] Processando emissão para CNPJ: {cnpj}...{COR_RESET}")

            # 1. Seleciona a opção "CNPJ" no dropdown "Informar *"
            try:
                campo_select = WebDriverWait(navegador, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//select[contains(@id, '106262') or @variavel='108513']"))
                )
                valor_selecionado = navegador.execute_script("return $(arguments[0]).val();", campo_select)
                if valor_selecionado != "CNPJ":
                    print(f"{COR_ANAPOLIS}[ANÁPOLIS] Selecionando tipo de documento: CNPJ...{COR_RESET}")
                    navegador.execute_script("""
                        var sel = $('select[variavel="108513"], select#106262');
                        sel.val('CNPJ').trigger('change');
                    """)
                    time.sleep(1.5)
            except Exception as e:
                try:
                    s2_elem = navegador.find_element(By.CSS_SELECTOR, "div[id*='s2id_']")
                    s2_elem.click()
                    time.sleep(0.5)
                    opcao_cnpj = WebDriverWait(navegador, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'select2-result-label') and contains(text(), 'CNPJ')]"))
                    )
                    opcao_cnpj.click()
                    time.sleep(1.5)
                except Exception as ex:
                    print(f"{COR_ERRO}[ANÁPOLIS] Falha ao selecionar CNPJ no dropdown: {ex}{COR_RESET}")

            # 2. Localiza e preenche o campo de CNPJ
            campo_cnpj = None
            try:
                campo_cnpj = WebDriverWait(navegador, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'CNPJ')]/following::input[1]"))
                )
            except Exception:
                for sel in [(By.ID, "106264"), (By.ID, "106263"), (By.CSS_SELECTOR, "input[variavel='108512']")]:
                    try:
                        campo_cnpj = navegador.find_element(*sel)
                        if campo_cnpj.is_displayed():
                            break
                    except Exception:
                        continue

            if not campo_cnpj:
                print(f"{COR_ERRO}[ANÁPOLIS] Campo de CNPJ não encontrado!{COR_RESET}")
                time.sleep(2)
                continue

            cnpj_limpo = "".join(c for c in cnpj if c.isdigit())
            valor_atual = "".join(c for c in (campo_cnpj.get_attribute("value") or "") if c.isdigit())

            if valor_atual != cnpj_limpo:
                campo_cnpj.clear()
                campo_cnpj.send_keys(cnpj_limpo)
                print(f"{COR_ANAPOLIS}[ANÁPOLIS] CNPJ preenchido: {cnpj}{COR_RESET}")

            time.sleep(0.5)

            # 3. Obtenção do código CAPTCHA
            codigo_captcha = None
            if tentativas <= max_tentativas_ocr:
                codigo_captcha = extrair_codigo_captcha(navegador)

                if not codigo_captcha:
                    print(f"{COR_ANAPOLIS}[ANÁPOLIS] OCR não identificou 5 caracteres. Recarregando captcha...{COR_RESET}")
                    recarregar_captcha(navegador)
                    time.sleep(1)
                    continue
            else:
                print(f"{COR_ANAPOLIS}[ANÁPOLIS] Limite de tentativas do OCR atingido.{COR_RESET}")
                if solicitar_captcha is not None:
                    print(f"{COR_ANAPOLIS}[ANÁPOLIS] Solicitando CAPTCHA ao usuário na interface...{COR_RESET}")
                    codigo_captcha = solicitar_captcha().strip()
                else:
                    codigo_captcha = input(f"{COR_ANAPOLIS}[ANÁPOLIS] Digite os 5 caracteres do CAPTCHA exibido na tela: {COR_RESET}").strip()

            if not codigo_captcha:
                print(f"{COR_ERRO}[ANÁPOLIS] Nenhum código de CAPTCHA informado. Tentando novamente...{COR_RESET}")
                recarregar_captcha(navegador)
                continue

            # 4. Preenche o campo de resposta do CAPTCHA
            campo_captcha = None
            try:
                campo_captcha = WebDriverWait(navegador, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Imagem')]/following::input[1]"))
                )
            except Exception:
                for sel in [(By.ID, "106270"), (By.CSS_SELECTOR, "input[variavel='108518']")]:
                    try:
                        campo_captcha = navegador.find_element(*sel)
                        if campo_captcha.is_displayed():
                            break
                    except Exception:
                        continue

            if not campo_captcha:
                print(f"{COR_ERRO}[ANÁPOLIS] Campo de resposta do CAPTCHA não encontrado!{COR_RESET}")
                continue

            campo_captcha.clear()
            campo_captcha.send_keys(codigo_captcha)
            print(f"{COR_ANAPOLIS}[ANÁPOLIS] Código inserido no campo: '{codigo_captcha}'{COR_RESET}")

            # 5. Registra arquivos antes e clica em Consultar
            arquivos_antes = set(_arquivos_validos(pasta_download))

            btn_consultar = None
            try:
                btn_consultar = WebDriverWait(navegador, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@value[contains(., 'Consultar')]] | //input[@id='106273']"))
                )
            except Exception:
                pass

            if btn_consultar:
                navegador.execute_script("arguments[0].click();", btn_consultar)
                print(f"{COR_ANAPOLIS}[ANÁPOLIS] Botão 'Consultar' acionado.{COR_RESET}")
            else:
                print(f"{COR_ERRO}[ANÁPOLIS] Botão Consultar não encontrado ou desabilitado.{COR_RESET}")
                continue

            time.sleep(3)

            # 6. Verifica se apareceu SweetAlert2 com erro de CAPTCHA ou bloqueio cadastral
            alerta_msg = fechar_alerta_se_existir(navegador)
            if alerta_msg:
                print(f"{COR_ANAPOLIS}[ANÁPOLIS] Mensagem do portal: '{alerta_msg}'{COR_RESET}")
                msg_lower = alerta_msg.lower()

                if any(w in msg_lower for w in ["não confere", "nao confere", "incorret", "inválid", "invalido", "captcha"]):
                    print(f"{COR_ANAPOLIS}[ANÁPOLIS] Código '{codigo_captcha}' rejeitado pelo portal. Gerando novo CAPTCHA...{COR_RESET}")
                    recarregar_captcha(navegador)
                    time.sleep(1)
                    continue

                if any(w in msg_lower for w in ["não cadastrad", "nao cadastrad", "pendênc", "pendenc", "bloque", "débito", "debito"]):
                    print(f"{COR_ERRO}[ANÁPOLIS] Bloqueio definitivo do portal: {alerta_msg}{COR_RESET}")
                    return False, f"Bloqueio: {alerta_msg}"

            # 7. Verifica se a página de resultado com o PDF foi gerada
            try:
                link_download = WebDriverWait(navegador, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//a[@title='Download do Arquivo' or contains(@href, 'downloadanexo.action')]"
                    ))
                )
                print(f"{COR_SUCESSO}[ANÁPOLIS] Certidão gerada com sucesso! Iniciando download...{COR_RESET}")

                try:
                    navegador.execute_script("arguments[0].removeAttribute('target');", link_download)
                except Exception:
                    pass

                href_download = link_download.get_attribute("href") or ""

                # Download direto via requisição autenticada com cookies da sessão
                if href_download and "downloadanexo.action" in href_download:
                    try:
                        import urllib.request
                        if not href_download.startswith("http"):
                            href_download = "https://portaldocidadao.anapolis.go.gov.br" + href_download

                        cookies = navegador.get_cookies()
                        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                        req = urllib.request.Request(
                            href_download,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                "Cookie": cookie_header
                            }
                        )
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            conteudo = resp.read()
                            if len(conteudo) > 500 and (b"%PDF" in conteudo[:20] or "pdf" in (resp.headers.get("Content-Type") or "").lower()):
                                nome_arquivo_pdf = f"Certidao_Anapolis_{cnpj}_{int(time.time())}.pdf"
                                caminho_final = os.path.join(pasta_download, nome_arquivo_pdf)
                                with open(caminho_final, "wb") as f_pdf:
                                    f_pdf.write(conteudo)
                                print(f"{COR_SUCESSO}[ANÁPOLIS] CND recolhida com sucesso via stream: {caminho_final}{COR_RESET}")
                                return True, ""
                    except Exception as ex_stream:
                        print(f"{COR_ANAPOLIS}[ANÁPOLIS] Aviso download direto: {ex_stream}. Tentando clique padrão...{COR_RESET}")

                # Fallback: clique no elemento
                link_download.click()
                arquivo = esperar_download(navegador, pasta_download, timeout=20, arquivos_antes=arquivos_antes)
                print(f"{COR_SUCESSO}[ANÁPOLIS] CND recolhida com sucesso para o CNPJ: {cnpj}{COR_RESET}")
                print(f"{COR_SUCESSO}[ANÁPOLIS] Arquivo baixado: {arquivo}{COR_RESET}")
                return True, ""

            except TimeoutException:
                alerta_tardio = fechar_alerta_se_existir(navegador)
                if alerta_tardio:
                    print(f"{COR_ERRO}[ANÁPOLIS] Aviso do portal após consulta: {alerta_tardio}{COR_RESET}")
                    return False, f"Aviso do portal: {alerta_tardio}"

                print(f"{COR_ANAPOLIS}[ANÁPOLIS] Link de download não identificado nesta tentativa. Reavaliando...{COR_RESET}")
                try:
                    navegador.get("https://portaldocidadao.anapolis.go.gov.br")
                    time.sleep(2)
                    btn_reinicio = WebDriverWait(navegador, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-navigation="7021"]'))
                    )
                    navegador.execute_script("arguments[0].click();", btn_reinicio)
                    time.sleep(2)
                except Exception:
                    pass
                continue

        except TimeoutException:
            print(f"{COR_ERRO}[ANÁPOLIS] Timeout aguardando elemento na tentativa {tentativas}.{COR_RESET}")
            try:
                navegador.get("https://portaldocidadao.anapolis.go.gov.br")
                time.sleep(2)
                btn_reinicio = WebDriverWait(navegador, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-navigation="7021"]'))
                )
                navegador.execute_script("arguments[0].click();", btn_reinicio)
                time.sleep(2)
            except Exception:
                pass
            continue
        except Exception as e:
            print(f"{COR_ERRO}[ANÁPOLIS] Erro na tentativa {tentativas}: {e}{COR_RESET}")
            try:
                navegador.get("https://portaldocidadao.anapolis.go.gov.br")
                time.sleep(2)
                btn_reinicio = WebDriverWait(navegador, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-navigation="7021"]'))
                )
                navegador.execute_script("arguments[0].click();", btn_reinicio)
                time.sleep(2)
            except Exception:
                pass
            continue

    msg_falha = f"Falha após {max_tentativas_totais} tentativas no portal de Anápolis."
    print(f"{COR_ERRO}[ANÁPOLIS] {msg_falha} para o CNPJ {cnpj}{COR_RESET}")
    return False, msg_falha


def recolher(CNPJ, site, *args, **kwargs):
    """
    Função principal compatível com todas as chamadas do main.py:
    - Chamada assistida: recolher(CNPJ, site, pasta_download)
    - Chamada selenium padrão: recolher(CNPJ, site, navegador, pasta_download)
    """
    navegador = None
    pasta_download = None
    solicitar_captcha = kwargs.get("solicitar_captcha", None)

    # Identifica a ordem dos argumentos posicionais
    if len(args) == 1:
        # Apenas pasta_download foi passada (modo assistido do main)
        pasta_download = args[0]
    elif len(args) >= 2:
        # navegador e pasta_download foram passados (modo selenium padrão do main)
        navegador = args[0]
        pasta_download = args[1]

    if "navegador" in kwargs:
        navegador = kwargs["navegador"]
    if "pasta_download" in kwargs:
        pasta_download = kwargs["pasta_download"]

    if not pasta_download:
        pasta_download = r"n:\19. FERRAMENTAS\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_download, exist_ok=True)

    url_portal = "https://portaldocidadao.anapolis.go.gov.br"
    if not site or "anapolis.go.gov.br" not in site:
        site = url_portal

    criou_navegador = False
    if navegador is None:
        from main import criar_navegador_configurado
        navegador = criar_navegador_configurado(headless=False)
        criou_navegador = True

    try:
        print(f"{COR_ANAPOLIS}[ANÁPOLIS] Acessando o Portal do Cidadão de Anápolis...{COR_RESET}")
        navegador.get(site)
        time.sleep(2)

        # Clica no item de menu "Certidões -> Certidão de Regularidade Fiscal do Contribuinte" (7021)
        try:
            btn_certidao = WebDriverWait(navegador, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-navigation="7021"]'))
            )
            navegador.execute_script("arguments[0].click();", btn_certidao)
            print(f"{COR_ANAPOLIS}[ANÁPOLIS] Acessando tela de Certidão de Regularidade Fiscal (7021)...{COR_RESET}")
            time.sleep(3)
        except Exception as e:
            msg = f"Falha ao navegar até o menu de Certidão: {e}"
            print(f"{COR_ERRO}[ANÁPOLIS] {msg}{COR_RESET}")
            return False, msg

        # Executa o preenchimento e resolução de CAPTCHA
        sucesso, msg = preencher_cnpj_e_solicitar_captcha(
            navegador=navegador,
            cnpj=CNPJ,
            pasta_download=pasta_download,
            solicitar_captcha=solicitar_captcha
        )

        return sucesso, msg

    except Exception as e:
        msg = f"Erro geral no fluxo de Anápolis: {e}"
        print(f"{COR_ERRO}[ANÁPOLIS] {msg}{COR_RESET}")
        return False, msg

    finally:
        if criou_navegador and navegador:
            navegador.quit()


if __name__ == "__main__":
    from main import criar_navegador_configurado

    CNPJ_TESTE = "48158886000122"
    SITE_ANAPOLIS = "https://portaldocidadao.anapolis.go.gov.br"
    PASTA_TESTE = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"

    print(f"\033[36m--- Teste Avulso: CND Anápolis Oficial (CNPJ: {CNPJ_TESTE}) ---\033[0m")
    navegador_teste = criar_navegador_configurado(headless=False)
    try:
        sucesso, msg = recolher(CNPJ_TESTE, SITE_ANAPOLIS, navegador_teste, pasta_download=PASTA_TESTE)
        print(f"\n\033[36m--- Resultado Final ---\033[0m")
        print(f"Sucesso: {sucesso} | Observação: '{msg}'")
    finally:
        navegador_teste.quit()
