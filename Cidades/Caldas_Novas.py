# [HEADLESS: COMPATÍVEL]
# O portal Prodata gera a certidão e dispara o download do PDF.
# Totalmente compatível com modo headless via 'plugins.always_open_pdf_externally' e CDP 'Page.setDownloadBehavior'.

import os
import sys
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download

siteCadastro = "https://caldasnovas.prodataweb.inf.br/sig/app.html#/servicosonline/debito-contribuinte"


def recolher(CNPJ, site, navegador, pasta_download):
    navegador.get(site)

    try:
        campo_cnpj = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@id="65inputText"]'))
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

        # Em Caldas Novas, clicar em vm.imprimir() dispara a geração e o download direto do PDF
        botao_imprimir.click()

        # Verifica se apareceu pop-up de aviso/bloqueio impeditivo
        try:
            alerta_element = WebDriverWait(navegador, 4).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@nat="pdBtnAlertOKBody"]'))
            )
            texto_aviso = alerta_element.text
            if "bloqueio" in texto_aviso.lower() or "débito" in texto_aviso.lower() or "pendência" in texto_aviso.lower():
                print(f"\033[31mAviso na tela (bloqueio): {texto_aviso}\033[0m")
                botao_ok = WebDriverWait(navegador, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@ng-click="close()" or @id="pdBtnAlertOK"]'))
                )
                botao_ok.click()
                return False, f"Bloqueio: {texto_aviso}"
        except TimeoutException:
            pass

        # Se houver botão de confirmação em algum fluxo, clica nele
        try:
            botao_confirmar = WebDriverWait(navegador, 3).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@ng-click="vm.imprimir()" and contains(., "Confirmar")]'))
            )
            botao_confirmar.click()
        except TimeoutException:
            pass

        arquivo = esperar_download(navegador, pasta_download, timeout=30, arquivos_antes=arquivos_antes)
        print(f"\033[32mMunicipal de Caldas Novas recolhida para o CNPJ: {CNPJ}\033[0m")
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
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "39847300000146"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_teste, exist_ok=True)

    print(f"\033[36m--- Teste Avulso: Caldas Novas (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        sucesso, observacao = recolher(cnpj_teste, siteCadastro, navegador_teste, pasta_teste)
        print(f"\nResultado do Teste -> Sucesso: {sucesso} | Observação: '{observacao}'")
        input("\nPressione [ENTER] para encerrar o navegador de teste...")
    finally:
        navegador_teste.quit()