# [HEADLESS: COMPATÍVEL]
# O portal PrimeFaces/JSF de Senador Canedo gera e dispara o download do PDF.
# Compatível com modo headless utilizando 'plugins.always_open_pdf_externally' e CDP 'Page.setDownloadBehavior'.

import os
import sys
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download, diagnosticar_download_falhou

siteCadastro = "https://servicosweb.senadorcanedo.go.gov.br/servicosweb/home.jsf"


def recolher(CNPJ, site, navegador, pasta_download):
    navegador.get(site)

    try:
        # Tenta localizar a opção de Contribuinte no menu inicial (PrimeFaces)
        campo_tipo_emissao = WebDriverWait(navegador, 12).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//*[@id="formHome:j_idt1118:2:j_idt1120"] | //a[contains(., "Contribuinte")] | //span[contains(., "Contribuinte")]/parent::a'
            ))
        )
        campo_tipo_emissao.click()
        print("Opção Contribuinte selecionada em Senador Canedo.")
    except Exception as e:
        print(f"\033[31mErro: Opção de Contribuinte não encontrada em Senador Canedo. Detalhe: {e}\033[0m")
        return

    try:
        # Seleciona o radio button de Pessoa Jurídica (CNPJ)
        botao_escolha = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="compInformarContribuinte:formNumero:radioCadastroTipoPessoa:1"]'))
        )
        botao_escolha.click()
        print("Tipo de pessoa Jurídica (CNPJ) selecionado.")

        # Aguarda o campo de CNPJ e preenche via script para acionar os listeners do PrimeFaces
        WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, 'compInformarContribuinte:formNumero:itIdent'))
        )
        navegador.execute_script("""
            const campo = document.getElementById('compInformarContribuinte:formNumero:itIdent');
            const setter = Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype, 'value'
            ).set;
            campo.focus();
            setter.call(campo, arguments[0]);
            campo.dispatchEvent(new Event('input', { bubbles: true }));
            campo.dispatchEvent(new Event('change', { bubbles: true }));
        """, CNPJ)

        WebDriverWait(navegador, 10).until(
            lambda driver: driver.find_element(
                By.ID, 'compInformarContribuinte:formNumero:itIdent'
            ).get_attribute('value').replace('.', '').replace('/', '').replace('-', '').isdigit()
            and len(driver.find_element(
                By.ID, 'compInformarContribuinte:formNumero:itIdent'
            ).get_attribute('value').replace('.', '').replace('/', '').replace('-', '')) == 14
        )
        valor_cnpj = navegador.find_element(
            By.ID, 'compInformarContribuinte:formNumero:itIdent'
        ).get_attribute('value')
        print(f"CNPJ preenchido: {valor_cnpj}")

        # Clica no botão Validar / OK
        WebDriverWait(navegador, 10).until(
            lambda driver: driver.execute_script(
                "return document.getElementById(arguments[0]) !== null;",
                'compInformarContribuinte:formNumero:btnValidar'
            )
        )
        navegador.execute_script(
            "document.getElementById(arguments[0]).click();",
            'compInformarContribuinte:formNumero:btnValidar'
        )
        print("Botão OK/Validar clicado.")

        # Clica no link para emitir certidão negativa de débitos
        botao_negativa = WebDriverWait(navegador, 15).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//a[@title="Emitir certidão negativa de débitos"] | //a[contains(@aria-label, "certidão negativa")]'
            ))
        )

        # Registra arquivos já existentes antes do clique
        os.makedirs(pasta_download, exist_ok=True)
        arquivos_antes = set(os.listdir(pasta_download))

        botao_negativa.click()
        print("Solicitação de emissão enviada. Aguardando download ou mensagem...")

        # Monitora o download e mensagens de erro do PrimeFaces (.ui-messages-error, .ui-growl-message)
        inicio = time.time()
        timeout = 30
        sucesso = False

        while time.time() - inicio < timeout:
            # 1. Verifica se surgiram mensagens de erro/alerta do PrimeFaces na tela
            erros_primefaces = navegador.find_elements(
                By.XPATH,
                '//div[contains(@class, "ui-messages-error")] | //div[contains(@class, "ui-growl-message")] | //span[contains(@class, "ui-messages-error-summary")]'
            )
            mensagens = [e.text.strip() for e in erros_primefaces if e.is_displayed() and e.text.strip()]
            if mensagens:
                print(f"\033[31m[Senador Canedo] Bloqueio/Aviso fiscal para o CNPJ {CNPJ}: {' | '.join(mensagens)}\033[0m")
                return

            # 2. Verifica se o PDF foi baixado
            arquivos_atuais = set(os.listdir(pasta_download))
            novos = arquivos_atuais - arquivos_antes
            pdfs_validos = [
                f for f in novos
                if f.lower().endswith(".pdf")
                and not f.lower().endswith((".crdownload", ".tmp", ".part", ".download"))
                and os.path.getsize(os.path.join(pasta_download, f)) > 0
            ]

            if pdfs_validos:
                arquivo_final = os.path.join(pasta_download, sorted(pdfs_validos)[0])
                print(f"\033[32mMunicipal de Senador Canedo recolhida para o CNPJ: {CNPJ}\033[0m")
                print(f"Arquivo baixado: {arquivo_final}")
                sucesso = True
                break

            time.sleep(0.5)

        if not sucesso:
            print(f"\033[33mAviso: Operação de download não concluída em Senador Canedo para {CNPJ}.\033[0m")
            diagnosticar_download_falhou(navegador, pasta_download)

    except TimeoutError as e:
        print(f"\033[33mAviso: Operação de download não concluída em Senador Canedo para {CNPJ}. Detalhe: {e}\033[0m")
        return
    except Exception as e:
        print(f"\033[33mAviso: Fluxo de emissão falhou em Senador Canedo. CNPJ: {CNPJ}. Detalhe: {e}\033[0m")
        return


if __name__ == "__main__":
    # Permite executar e testar o arquivo de forma avulsa
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "39847300000146"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\CNDs"
    os.makedirs(pasta_teste, exist_ok=True)

    print(f"\033[36m--- Teste Avulso: Senador Canedo (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        recolher(cnpj_teste, siteCadastro, navegador_teste, pasta_teste)
        input("\nPressione [ENTER] para encerrar o navegador de teste...")
    finally:
        navegador_teste.quit()
