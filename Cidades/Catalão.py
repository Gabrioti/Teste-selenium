# [HEADLESS: COMPATÍVEL]
# O portal Prodata gera o relatório/certidão e dispara o download do PDF.
# Compatível com modo headless utilizando 'plugins.always_open_pdf_externally' e CDP 'Page.setDownloadBehavior'.

import time
import os
import sys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download

siteCadastro = "https://sig.catalao.go.gov.br/sig/app.html#/servicosonline/debito-contribuinte"


def recolher(CNPJ, site, navegador, pasta_download):
    navegador.get(site)

    try:
        campo_cnpj = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@id="64inputText"]'))
        )
        campo_cnpj.click()
        campo_cnpj.send_keys(CNPJ)
    except Exception as e:
        msg_erro = "Campo de CNPJ não encontrado no site."
        print(f"\033[31mErro: {msg_erro} Detalhe: {e}\033[0m")
        return False, msg_erro

    try:
        botao_pesquisar = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@ng-click="vm.pesquisar()"]'))
        )
        botao_pesquisar.click()

        botao_clicar_celula = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@nat="CellTemplate"]'))
        )
        botao_clicar_celula.click()

        botao_imprimir = WebDriverWait(navegador, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@ng-click="vm.imprimir()"]'))
        )
        # Registra arquivos antes do clique para capturar downloads imediatos
        os.makedirs(pasta_download, exist_ok=True)
        arquivos_antes = set(os.listdir(pasta_download))

        botao_imprimir.click()

        try:
            print("Aguardando processamento do site...")
            time.sleep(2)
            WebDriverWait(navegador, 15).until(
                EC.invisibility_of_element_located((By.XPATH, '//*[contains(text(), "Por favor, aguarde...")]'))
            )
        except TimeoutException:
            pass

        # 1. Verifica se surgiu pop-up de bloqueio (máximo 4s)
        try:
            alerta_element = WebDriverWait(navegador, 4).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@nat="pdBtnAlertOKBody"]'))
            )
            mensagem_aviso = alerta_element.text
            print(f"\033[31mAviso na tela (bloqueio): {mensagem_aviso}\033[0m")

            botao_ok_xpath = '//button[@ng-click="close()" or @id="pdBtnAlertOK"]'
            botao_encerrar = WebDriverWait(navegador, 5).until(
                EC.element_to_be_clickable((By.XPATH, botao_ok_xpath))
            )
            botao_encerrar.click()
            print("Pop-up fechado. Encerrando fluxo desta cidade.")
            return False, f"Bloqueio: {mensagem_aviso}"
        except TimeoutException:
            pass

        # 2. Em alguns portais Prodata surge modal com botão Confirmar; se aparecer, clica nele
        try:
            botao_confirmar = WebDriverWait(navegador, 3).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@ng-click="vm.imprimir()" and contains(., "Confirmar")]'))
            )
            botao_confirmar.click()
        except TimeoutException:
            pass

        arquivo = esperar_download(navegador, pasta_download, timeout=30, arquivos_antes=arquivos_antes)
        print(f"\033[32mMunicipal de Catalão recolhida para o CNPJ: {CNPJ}\033[0m")
        print(f"Arquivo baixado: {arquivo}")

        return True, ""

    except TimeoutError as e:
        msg_erro = "Tempo limite de download excedido."
        print(f"\033[33mAviso: {msg_erro} CNPJ: {CNPJ}. Detalhe: {e}\033[0m")
        return False, msg_erro
    except Exception as e:
        msg_erro = "Botão de imprimir não habilitado / Sem CND disponível."
        print(f"\033[33mAviso: {msg_erro} CNPJ: {CNPJ}. Detalhe: {e}\033[0m")
        return False, msg_erro


if __name__ == "__main__":
    # Permite executar e testar o arquivo de forma avulsa
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "39847300000146"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_teste, exist_ok=True)

    print(f"\033[36m--- Teste Avulso: Catalão (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        sucesso, observacao = recolher(cnpj_teste, siteCadastro, navegador_teste, pasta_teste)
        print(f"\nResultado do Teste -> Sucesso: {sucesso} | Observação: '{observacao}'")
        input("\nPressione [ENTER] para encerrar o navegador de teste...")
    finally:
        navegador_teste.quit()