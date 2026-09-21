import time
import os
import sys


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download

siteCadastro = "https://ww1.receita.fazenda.df.gov.br/cidadao/certidoes/Certidao"


def recolher(CNPJ, site, navegador, pasta_download):
    navegador.get(site)

    try:
        campo_cnpj = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//mat-expansion-panel-header[@id="mat-expansion-panel-header-0"]'))# <mat-expansion-panel-header _ngcontent-ywh-c154="" role="button" class="mat-expansion-panel-header mat-focus-indicator ng-tns-c141-1 ng-tns-c139-0 mat-expansion-toggle-indicator-after ng-star-inserted" id="mat-expansion-panel-header-0" tabindex="0" aria-controls="cdk-accordion-child-0" aria-expanded="false" aria-disabled="false"><span class="mat-content ng-tns-c141-1"><mat-panel-title _ngcontent-ywh-c154="" class="mat-expansion-panel-header-title ng-tns-c141-1"> Emissão de Certidão </mat-panel-title></span><span class="mat-expansion-indicator ng-tns-c141-1 ng-trigger ng-trigger-indicatorRotate ng-star-inserted" style="transform: rotate(0deg);"></span><!----></mat-expansion-panel-header>
        )
        campo_cnpj.click()
        campo_cnpj.send_keys(CNPJ)
    except Exception as e:
        print(f"\033[31mErro: Campo de CNPJ não encontrado em Estadual DF. Detalhe: {e}\033[0m")
        return

    try:
        botao_pesquisar = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@id=id="mat-radio-3-input"]'))# <input type="radio" class="mat-radio-input cdk-visually-hidden" id="mat-radio-3-input" tabindex="0" name="mat-radio-group-0" value="2">
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
            print(f"\033[31m[Águas Lindas] Aviso na tela (bloqueio): {mensagem_aviso}\033[0m")

            botao_ok_xpath = '//button[@ng-click="close()" or @id="pdBtnAlertOK"]'
            botao_encerrar = WebDriverWait(navegador, 5).until(
                EC.element_to_be_clickable((By.XPATH, botao_ok_xpath))
            )
            botao_encerrar.click()
            print("[Águas Lindas] Pop-up fechado. Encerrando fluxo desta cidade.")
            return
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
        print(f"\033[32mMunicipal de Águas Lindas recolhida para o CNPJ: {CNPJ}\033[0m")
        print(f"Arquivo baixado: {arquivo}")

    except TimeoutError as e:
        print(f"\033[33mAviso: operação de download não concluída em Águas Lindas para {CNPJ}. Detalhe: {e}\033[0m")
        return
    except Exception as e:
        print(f"\033[33mAviso: Botão de imprimir não habilitado ou fluxo falhou em Águas Lindas. CNPJ: {CNPJ}. Detalhe: {e}\033[0m")
        return


if __name__ == "__main__":
    # Permite executar e testar o arquivo de forma avulsa
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "39847300000146"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_teste, exist_ok=True)

    print(f"\033[36m--- Teste Avulso: Águas Lindas (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        recolher(cnpj_teste, siteCadastro, navegador_teste, pasta_teste)
        input("\nPressione [ENTER] para encerrar o navegador de teste...")
    finally:
        navegador_teste.quit()

