import os
import sys

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download

siteCadastro = (
    "https://palmeiras.portalservicos.app.br/"
    "certidao-regularidade-fiscal?menu=8"
)


def _campo_cadastro(navegador):
    campos = navegador.find_elements(
        By.CSS_SELECTOR,
        "srv-opcao-pesquisa input",
    )
    campos_visiveis = [
        campo
        for campo in campos
        if campo.is_displayed()
        and campo.get_attribute("type") not in ("hidden", "checkbox", "radio")
        and campo.get_attribute("role") != "combobox"
    ]
    if not campos_visiveis:
        return False

    for campo in campos_visiveis:
        rotulo = " ".join(
            filter(
                None,
                (
                    campo.get_attribute("aria-label"),
                    campo.get_attribute("placeholder"),
                    campo.get_attribute("name"),
                    campo.get_attribute("id"),
                ),
            )
        ).lower()
        try:
            rotulo += " " + campo.find_element(
                By.XPATH,
                "./ancestor::*[.//label][1]",
            ).text.lower()
        except NoSuchElementException:
            pass
        if "cadastro" in rotulo or "cnpj" in rotulo or "documento" in rotulo:
            return campo

    return campos_visiveis[-1]


def recolher(CNPJ, site, navegador, pasta_download):
    navegador.get(site)

    try:
        WebDriverWait(navegador, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "srv-certidao-regularidade-fiscal")
            )
        )
        WebDriverWait(navegador, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "srv-opcao-pesquisa")
            )
        )

        seletor_pesquisa = navegador.find_elements(
            By.CSS_SELECTOR,
            "srv-opcao-pesquisa .dx-selectbox",
        )
        for seletor in seletor_pesquisa:
            if seletor.is_displayed():
                seletor.click()
                opcao_cnpj = navegador.find_elements(
                    By.XPATH,
                    "//*[contains(@class, 'dx-list-item') "
                    "and contains(translate(., 'cnpj', 'CNPJ'), 'CNPJ')]",
                )
                if opcao_cnpj:
                    opcao_cnpj[0].click()
                break

        campo_cnpj = WebDriverWait(navegador, 15).until(_campo_cadastro)
        campo_cnpj.click()
        campo_cnpj.clear()
        campo_cnpj.send_keys(CNPJ)

        botoes = navegador.find_elements(
            By.XPATH,
            "//*[self::button or @role='button']"
            "[contains(translate(normalize-space(.), "
            "'GERAR CERTIDÃO', 'gerar certidão'), 'gerar certidão')]",
        )
        botao_gerar = next(
            (
                botao
                for botao in botoes
                if botao.is_displayed() and botao.is_enabled()
            ),
            None,
        )
        if botao_gerar is None:
            return False, "Botão 'Gerar Certidão' não encontrado."

        os.makedirs(pasta_download, exist_ok=True)
        arquivos_antes = set(os.listdir(pasta_download))
        botao_gerar.click()

        arquivo = esperar_download(
            navegador,
            pasta_download,
            timeout=45,
            arquivos_antes=arquivos_antes,
        )
        print(f"Certidão de Palmeiras de Goiás baixada: {arquivo}")
        return True, ""

    except TimeoutException as e:
        mensagem = (
            "Tempo limite excedido ao carregar o formulário ou localizar "
            "o campo de cadastro."
        )
        print(f"[Palmeiras de Goiás] {mensagem} Detalhe: {e}")
        return False, mensagem
    except TimeoutError as e:
        mensagem = "Tempo limite excedido aguardando o download da certidão."
        print(f"[Palmeiras de Goiás] {mensagem} Detalhe: {e}")
        return False, mensagem
    except Exception as e:
        mensagem = f"Falha no fluxo de emissão: {e}"
        print(f"[Palmeiras de Goiás] {mensagem}")
        return False, mensagem


if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "39847300000146"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    navegador_teste = criar_navegador_configurado()
    try:
        sucesso, observacao = recolher(
            cnpj_teste,
            siteCadastro,
            navegador_teste,
            pasta_teste,
        )
        print(f"Sucesso: {sucesso} | Observação: '{observacao}'")
    finally:
        navegador_teste.quit()
