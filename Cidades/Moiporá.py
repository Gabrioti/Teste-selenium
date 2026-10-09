import os
import sys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download

siteCadastro = "https://moipora.sigep.com.br/portal/person/search-certificate-debit.jsf"


def _resultado_consulta(navegador):
    mensagens_erro = navegador.find_elements(By.CSS_SELECTOR, "div.alert-danger")
    for mensagem in mensagens_erro:
        if mensagem.is_displayed() and mensagem.text.strip():
            return False, mensagem.text.strip()

    botao_imprimir_xpath = (
        "//*[self::button or self::input or self::a]"
        "[contains(translate(normalize-space(string(.)), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZÃÕÁÉÍÓÚÇ', "
        "'abcdefghijklmnopqrstuvwxyzãõáéíóúç'), 'imprimir certidão') "
        "or contains(translate(@value, "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZÃÕÁÉÍÓÚÇ', "
        "'abcdefghijklmnopqrstuvwxyzãõáéíóúç'), 'imprimir certidão')]"
    )
    botoes_imprimir = navegador.find_elements(By.XPATH, botao_imprimir_xpath)
    for botao in botoes_imprimir:
        if botao.is_displayed() and botao.is_enabled():
            return True, botao

    return False


def recolher(CNPJ, site, navegador, pasta_download):
    navegador.get(site)

    try:
        botao_pessoa_juridica = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable(
                (By.ID, "personCertificateDebitSearchForm:typePerson:1")
            )
        )
        botao_pessoa_juridica.click()

        campo_cnpj = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable(
                (By.ID, "personCertificateDebitSearchForm:personCNPJ")
            )
        )
        campo_cnpj.clear()
        campo_cnpj.send_keys(CNPJ)

        os.makedirs(pasta_download, exist_ok=True)
        arquivos_antes = set(os.listdir(pasta_download))

        botao_consultar = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable(
                (By.ID, "personCertificateDebitSearchForm:personSearch")
            )
        )
        botao_consultar.click()

        tipo_resultado, resultado = WebDriverWait(navegador, 15).until(
            _resultado_consulta
        )
        if not tipo_resultado:
            print(
                f"\033[31m[Moiporá] Consulta recusada para o CNPJ {CNPJ}: "
                f"{resultado}\033[0m"
            )
            return False, f"Bloqueio: {resultado}"

        resultado.click()
        arquivo = esperar_download(
            navegador,
            pasta_download,
            timeout=30,
            arquivos_antes=arquivos_antes,
        )
        print(f"\033[32mCertidão de Moiporá baixada para o CNPJ: {CNPJ}\033[0m")
        print(f"Arquivo baixado: {arquivo}")
        return True, ""

    except TimeoutException as e:
        msg_erro = (
            "Tempo limite excedido ao consultar o contribuinte ou localizar "
            "o botão de impressão."
        )
        print(f"\033[33m[Moiporá] Aviso: {msg_erro} Detalhe: {e}\033[0m")
        return False, msg_erro
    except TimeoutError as e:
        msg_erro = "Tempo limite de download da certidão excedido."
        print(f"\033[33m[Moiporá] Aviso: {msg_erro} Detalhe: {e}\033[0m")
        return False, msg_erro
    except Exception as e:
        msg_erro = "Fluxo de emissão da certidão falhou."
        print(f"\033[31m[Moiporá] Erro: {msg_erro} Detalhe: {e}\033[0m")
        return False, msg_erro


if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "39847300000146"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_teste, exist_ok=True)

    print(f"\033[36m--- Teste Avulso: Moiporá (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        sucesso, observacao = recolher(
            cnpj_teste,
            siteCadastro,
            navegador_teste,
            pasta_teste,
        )
        print(f"\nResultado do Teste -> Sucesso: {sucesso} | Observação: '{observacao}'")
        input("\nPressione [ENTER] para encerrar o navegador de teste...")
    finally:
        navegador_teste.quit()
