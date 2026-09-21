import os
import sys
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download

COR_FGTS = "\033[38;2;51;255;255m"  # Azul claro / Ciano (#33FFFF)
COR_ERRO = "\033[31m"
COR_RESET = "\033[0m"


def recolher_FGTS(CNPJ, site, navegador, pasta_download=None):
    """
    Realiza a consulta da CND do FGTS (CRF) no portal da Caixa Econômica Federal.
    - Se a empresa estiver regular: emite e baixa o Certificado em PDF.
    - Se houver débito, impossibilidade ou erro cadastral: captura a mensagem real da Caixa e encerra com aviso.
    """
    if not pasta_download:
        pasta_download = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_download, exist_ok=True)

    print(f"{COR_FGTS}[FGTS] Acessando portal da Caixa para o CNPJ: {CNPJ}...{COR_RESET}")
    navegador.get(site)

    # 1. Preenchimento do CNPJ
    try:
        campo_cnpj = WebDriverWait(navegador, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="mainForm:txtInscricao1"]'))
        )
        campo_cnpj.clear()
        campo_cnpj.send_keys(CNPJ)
    except Exception as e:
        msg = "Campo de inscrição não encontrado no portal da Caixa."
        print(f"\033[31m[FGTS] Erro: {msg} Detalhe: {e}\033[0m")
        return False, msg

    # 2. Seleção de UF (GO) e clique em Consultar
    try:
        campo_uf = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="mainForm:uf"]'))
        )
        Select(campo_uf).select_by_value("GO")

        btn_consultar = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="mainForm:btnConsultar"]'))
        )
        btn_consultar.click()

        # Aguarda a resposta do portal (mensagem de feedback ou link do certificado)
        try:
            WebDriverWait(navegador, 15).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//span[@class="feedback-text"] | //div[contains(@class, "feedback")] | //a[contains(., "Certificado de Regularidade") or contains(., "CRF")]'
                ))
            )
        except TimeoutException:
            msg = "Tempo limite excedido aguardando resposta da CAIXA."
            print(f"\033[31m[FGTS] Erro: {msg} (CNPJ {CNPJ})\033[0m")
            return False, msg

        # 3. Tratamento de mensagens de retorno (erros, bloqueios ou pendências da Caixa)
        elementos_feedback = navegador.find_elements(
            By.XPATH,
            '//span[@class="feedback-text"] | //div[contains(@class, "feedback")]'
        )
        mensagens = [el.text.strip() for el in elementos_feedback if el.is_displayed() and el.text.strip()]
        texto_completo = " | ".join(mensagens) if mensagens else ""

        if texto_completo:
            texto_lower = texto_completo.lower()
            termos_bloqueio = [
                "não foi possível verificar a regularidade",
                "irregular",
                "não localizada",
                "pendência",
                "agências da caixa",
                "comparecer a uma das agências"
            ]
            if any(termo in texto_lower for termo in termos_bloqueio):
                msg_principal = mensagens[0] if mensagens else texto_completo
                print(f"\033[31m[FGTS] Bloqueio/Aviso da CAIXA para o CNPJ {CNPJ}: {msg_principal}\033[0m")
                return False, f"Aviso CAIXA: {msg_principal}"

        # 4. Acesso ao link do Certificado de Regularidade (CRF)
        try:
            link_crf = WebDriverWait(navegador, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//a[contains(., "Certificado de Regularidade") or contains(., "CRF") or contains(@id, "mainForm:j_id")]'
                ))
            )
            link_crf.click()
        except TimeoutException:
            aviso = texto_completo if texto_completo else "Certificado não disponível para emissão direta."
            print(f"\033[31m[FGTS] Aviso: Não foi possível acessar o Certificado para o CNPJ {CNPJ}. Detalhe: {aviso}\033[0m")
            return False, aviso

        # 5. Clica em Visualizar
        try:
            btn_visualizar = WebDriverWait(navegador, 12).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="mainForm:btnVisualizar"] | //input[@value="Visualizar"]'))
            )
            btn_visualizar.click()
        except TimeoutException:
            msg = "Botão de visualização do CRF não encontrado."
            print(f"\033[31m[FGTS] Erro: {msg}\033[0m")
            return False, msg

        # 6. Registra arquivos e clica em Imprimir (gera o download do PDF via Chrome)
        arquivos_antes = set(os.listdir(pasta_download))

        try:
            btn_imprimir = WebDriverWait(navegador, 12).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="mainForm:btImprimir4"] | //input[@value="Imprimir"]'))
            )
            btn_imprimir.click()
        except TimeoutException:
            msg = "Botão de impressão não encontrado."
            print(f"\033[31m[FGTS] Erro: {msg}\033[0m")
            return False, msg

        # 7. Aguarda a gravação do PDF no disco
        arquivo = esperar_download(navegador, pasta_download, timeout=25, arquivos_antes=arquivos_antes)
        print(f"{COR_FGTS}[FGTS] CND recolhida com sucesso para o CNPJ: {CNPJ}{COR_RESET}")
        print(f"{COR_FGTS}Arquivo baixado: {arquivo}{COR_RESET}")
        
        return True, ""

    except TimeoutError as e:
        msg = "Tempo esgotado aguardando o download do arquivo."
        print(f"\033[33m[FGTS] Aviso: {msg} Detalhe: {e}\033[0m")
        return False, msg
    except Exception as e:
        msg = f"Erro inesperado no fluxo do FGTS: {e}"
        print(f"\033[31m[FGTS] {msg}\033[0m")
        return False, msg


if __name__ == "__main__":
    # Permite executar e testar o arquivo de forma avulsa
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from main import criar_navegador_configurado

    site_padrao = "https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"

    print("\033[36m--- Teste Avulso: FGTS ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        # Teste 1: CNPJ que apresenta mensagem de pendência da Caixa
        recolher_FGTS("58740525000143", site_padrao, navegador_teste, pasta_teste)

        # Teste 2: CNPJ regular
        recolher_FGTS("39847300000146", site_padrao, navegador_teste, pasta_teste)
    finally:
        navegador_teste.quit()