import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download, _arquivos_validos

siteCadastro = "https://nfe.valparaisodegoias.go.gov.br/Certidao_Index.aspx"

try:
    import ddddocr
    _ocr = ddddocr.DdddOcr(show_ad=False)
except Exception:
    _ocr = None

COR_MUNICIPAL = "\033[38;2;255;204;102m"
COR_ERRO = "\033[31m"
COR_RESET = "\033[0m"

def resolver_captcha(navegador, solicitar_captcha=None, max_tentativas=4):
    """
    Decifra o CAPTCHA de Valparaíso automaticamente via ddddocr.
    """
    for tentativa in range(1, max_tentativas + 1):
        img_captcha = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'CaptchaImage')]"))
        )

        codigo = None
        if _ocr is not None:
            try:
                codigo = _ocr.classification(img_captcha.screenshot_as_png).strip().upper()
            except Exception:
                codigo = None

        if not codigo or len(codigo) != 4:
            if solicitar_captcha is not None:
                codigo = solicitar_captcha().strip().upper()
            else:
                codigo = input(f"{COR_MUNICIPAL}[Valparaiso] Digite o CAPTCHA (4 caracteres): {COR_RESET}").strip().upper()

        campo_captcha = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_Captcha1_txtCodigo"))
        )
        campo_captcha.clear()
        campo_captcha.send_keys(codigo)

        btn_consultar = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_btnImprimir"))
        )
        btn_consultar.click()
        time.sleep(3)

        erros = navegador.find_elements(
            By.XPATH,
            "//span[@id='ctl00_ContentPlaceHolder1_Captcha1_lblMsg' and contains(., 'Codigo invalido')]"
        )
        if erros and any(e.is_displayed() for e in erros):
            continue

        return True
    return False

def recolher(CNPJ, site, navegador, pasta_download, solicitar_captcha=None):
    os.makedirs(pasta_download, exist_ok=True)
    print(f"{COR_MUNICIPAL}[Valparaiso] Acessando portal para o CNPJ: {CNPJ}...{COR_RESET}")
    navegador.get(site)

    # 1. Preenche CNPJ
    try:
        campo_cnpj = WebDriverWait(navegador, 15).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_txtCPF_CNPJ"))
        )
        campo_cnpj.clear()
        campo_cnpj.send_keys(CNPJ)
        navegador.find_element(By.TAG_NAME, "body").click()
        time.sleep(2)
    except Exception as e:
        msg_erro = "Erro ao preencher CNPJ no portal."
        print(f"\033[31m[Valparaiso] {msg_erro} Detalhe: {e}\033[0m")
        # MODIFICADO AQUI: Retorna erro
        return False, msg_erro

    # 2. Resolve o CAPTCHA
    sucesso_captcha = resolver_captcha(navegador, solicitar_captcha)
    if not sucesso_captcha:
        msg_erro = "Não foi possível validar o CAPTCHA."
        print(f"\033[31m[Valparaiso] {msg_erro} CNPJ: {CNPJ}.\033[0m")
        # MODIFICADO AQUI: Retorna erro de Captcha
        return False, msg_erro

    # 3. Verifica mensagens de bloqueio/débito
    texto_alerta_site = ""
    try:
        mensagens_alerta = navegador.find_elements(
            By.XPATH,
            "//span[contains(@id, 'lblMsg') or contains(@id, 'lblErro') or contains(@id, 'Mensagem')]"
        )
        # MODIFICADO AQUI: Vamos guardar os alertas para usar no retorno caso a tabela não carregue!
        msgs_encontradas = [msg.text.strip() for msg in mensagens_alerta if msg.text.strip() and "invalido" not in msg.text.strip().lower()]
        
        if msgs_encontradas:
            texto_alerta_site = " | ".join(msgs_encontradas)
            print(f"\033[33m[Valparaiso] Aviso do portal: {texto_alerta_site}\033[0m")
    except Exception:
        pass

    # 4. Clica em 'Gerar Nova' para emitir uma certidão com a data de hoje
    try:
        botoes_gerar = navegador.find_elements(By.XPATH, "//input[@value='Gerar Nova' or contains(@id, 'btnEmitirNova')]")
        if botoes_gerar and botoes_gerar[0].is_displayed():
            botoes_gerar[0].click()
            time.sleep(3)
    except Exception:
        pass

    # 5. Inspeciona a tabela de certidões e seleciona a mais recente
    try:
        linhas_tabela = WebDriverWait(navegador, 12).until(
            lambda nav: nav.find_elements(By.XPATH, "//table[contains(@id, 'grvCertidoes')]//tr[td]")
        )
        if not linhas_tabela:
            msg_erro = "Nenhuma certidão listada na tabela."
            print(f"\033[33m[Valparaiso] {msg_erro} CNPJ {CNPJ}.\033[0m")
            # MODIFICADO AQUI
            return False, msg_erro

        ultima_linha = linhas_tabela[-1]
        colunas = [td.text.strip() for td in ultima_linha.find_elements(By.TAG_NAME, "td")]
        tipo_certidao = colunas[5].upper() if len(colunas) > 5 else ""

        if "POSITIVA" in tipo_certidao and "EFEITO DE NEGATIVA" not in tipo_certidao:
            print(f"\033[31m[Valparaiso] Alerta: A certidão emitida é POSITIVA DE DÉBITOS para {CNPJ}.\033[0m")

        botoes_impressora = ultima_linha.find_elements(By.XPATH, ".//input[contains(@id, 'ImageButton') or contains(@src, 'impressora')]")
        if not botoes_impressora:
            msg_erro = "Botão de impressão não encontrado na linha da certidão."
            # MODIFICADO AQUI
            return False, msg_erro

        icone_impressora = botoes_impressora[0]

    except TimeoutException:
        # MODIFICADO AQUI: Se a tabela não apareceu, provavelmente houve bloqueio. Devolvemos o alerta capturado no passo 3!
        msg_erro = f"Bloqueio: {texto_alerta_site}" if texto_alerta_site else "Tabela de certidões não encontrada."
        print(f"\033[33m[Valparaiso] {msg_erro} para o CNPJ {CNPJ}.\033[0m")
        return False, msg_erro

    # 6. Registra arquivos antes e clica no ícone de impressão
    arquivos_antes = set(_arquivos_validos(pasta_download))
    icone_impressora.click()

    # 7. Aguarda a gravação do PDF no disco
    try:
        arquivo = esperar_download(navegador, pasta_download, timeout=30, arquivos_antes=arquivos_antes)
        print(f"{COR_MUNICIPAL}Municipal de Valparaíso recolhida para o CNPJ: {CNPJ}{COR_RESET}")
        print(f"{COR_MUNICIPAL}Arquivo baixado: {arquivo}{COR_RESET}")
        
        # MODIFICADO AQUI: Tudo certo, retorna True e observação limpa!
        return True, ""
        
    except TimeoutError as e:
        msg_erro = "Tempo limite de download excedido."
        print(f"\033[33mAviso: {msg_erro} Detalhe: {e}\033[0m")
        # MODIFICADO AQUI
        return False, msg_erro
    except Exception as e:
        msg_erro = "Falha ao baixar certidão após o clique."
        print(f"\033[33mAviso: {msg_erro} Detalhe: {e}\033[0m")
        # MODIFICADO AQUI
        return False, msg_erro


if __name__ == "__main__":
    # Teste avulso mantido e ajustado para receber a tupla
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "17920217000112"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_teste, exist_ok=True)

    print(f"\033[36m--- Teste Avulso: Valparaíso de Goiás (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        deu_certo, msg = recolher(cnpj_teste, siteCadastro, navegador_teste, pasta_teste)
        print(f"\nResultado do Teste -> Sucesso: {deu_certo} | Observação: '{msg}'")
    finally:
        navegador_teste.quit()