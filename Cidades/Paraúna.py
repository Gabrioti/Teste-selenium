# [HEADLESS: COMPATÍVEL]
# O portal Megasoft realiza download direto do PDF via resposta HTTP.
# Totalmente compatível com modo headless utilizando as opções de download do Chrome.

import os
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from CadastroDiagnostico.diagnostico_download import diagnosticar_download_falhou

siteCadastro = "https://parauna.megasoftservicos.com.br/cidadao/emissao-certidao-negat"


def recolher(CNPJ, site, navegador, pasta_download):
    navegador.get(site)

    try:
        campo_tipo_emissao = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//ng-select[@id="tipoEmissao"]'))
        )
        campo_tipo_emissao.click()
    except Exception as e:
        msg_erro = "Campo de tipo de emissão não encontrado."
        print(f"\033[31m[Abadiânia] Erro: {msg_erro} Detalhe: {e}\033[0m")
        # MODIFICADO AQUI: Retorna False e a mensagem
        return False, msg_erro

    try:
        botao_escolha = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[@class="ng-option-label"]'))
        )
        botao_escolha.click()

        botao_CNPJ = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@id="cpfCnpj"]'))
        )
        botao_CNPJ.click()
        botao_CNPJ.send_keys(CNPJ)
        botao_CNPJ.send_keys(Keys.ENTER)

        botao_gerar = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, '//i[@class="icomoon icon-ico-campo-busca"]')) # <button type="submit" class="btn btn-mega"><!----><!----><!----><!----><i class="icomoon icon-ico-campo-busca"></i><!----> Gerar Certidão <!----><!----><!----></button>
        )

        # Registra arquivos já existentes antes do clique para detectar o novo PDF
        os.makedirs(pasta_download, exist_ok=True)
        arquivos_antes = set(os.listdir(pasta_download))

        # Força o clique injetando JavaScript direto na página
        botao_gerar.click()
        time.sleep(0.5)
        botao_gerar.click()

        # Monitora ativamente se o download concluiu ou se apareceu balão de erro (toast)
        inicio = time.time()
        timeout = 25
        sucesso = False

        while time.time() - inicio < timeout:
            # 1. Verifica se surgiu balão de erro/bloqueio na página (apenas toast-error ou toast-warning)
            toasts = navegador.find_elements(
                By.XPATH,
                '//div[contains(@class, "toast-error") or contains(@class, "toast-warning")]'
            )
            mensagens = []
            for t in toasts:
                if t.is_displayed():
                    msg_elem = t.find_elements(By.XPATH, './/div[contains(@class, "toast-message")]')
                    texto = msg_elem[0].text.strip() if msg_elem else t.text.strip()
                    if texto and texto not in mensagens:
                        if "sucesso" not in texto.lower():
                            mensagens.append(texto)

            if mensagens:
                texto_erro_site = ' | '.join(mensagens)
                print(f"\033[31m[Paraúna] Bloqueio/Aviso do portal para o CNPJ {CNPJ}: {texto_erro_site}\033[0m")
                # MODIFICADO AQUI: Retorna False e o texto exato do bloqueio pego do balão (toast)
                return False, f"Bloqueio: {texto_erro_site}"

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
                print(f"\033[32mMunicipal de Paraúna recolhida para o CNPJ: {CNPJ}\033[0m")
                print(f"Arquivo baixado: {arquivo_final}")
                sucesso = True
                break

            time.sleep(0.5)

        if not sucesso:
            msg_erro = "Tempo limite de download excedido (Nenhum PDF baixado)."
            print(f"\033[33m[Paraúna] Aviso: {msg_erro} para {CNPJ}.\033[0m")
            diagnosticar_download_falhou(navegador, pasta_download)
            return False, msg_erro

        # MODIFICADO AQUI: Se a variável sucesso for True (PDF baixado e validado), retorna True e observação vazia.
        return True, ""

    except Exception as e:
        msg_erro = "Fluxo de emissão falhou devido a um erro inesperado."
        print(f"\033[33m[Paraúna] Aviso: {msg_erro} CNPJ: {CNPJ}. Detalhe: {e}\033[0m")
        # MODIFICADO AQUI: Retorna False e a exceção genérica.
        return False, msg_erro


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "39847300000146"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_teste, exist_ok=True)

    print(f"\033[36m--- Teste Avulso: Paraúna (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        sucesso, observacao = recolher(cnpj_teste, siteCadastro, navegador_teste, pasta_teste)
        print(f"\nResultado do Teste -> Sucesso: {sucesso} | Observação: '{observacao}'")
        input("\nPressione [ENTER] para encerrar o navegador de teste...")
    finally:
        navegador_teste.quit()