# [HEADLESS: COMPATÍVEL]
# O portal Megasoft realiza download direto do PDF via resposta HTTP.
# Totalmente compatível com modo headless utilizando as opções de download do Chrome.

import os
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

from CadastroDiagnostico.diagnostico_download import diagnosticar_download_falhou

siteCadastro = "https://floresdegoias.megasoftservicos.com.br/cidadao/emissao-certidao-negat"


def recolher(CNPJ, site, navegador, pasta_download):
    navegador.get(site)

    try:
        campo_tipo_emissao = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//ng-select[@id="tipoEmissao"]'))
        )
        campo_tipo_emissao.click()
    except Exception as e:
        msg_erro = "Campo de tipo de emissão não encontrado."
        print(f"\033[31m[Flores] Erro: {msg_erro} Detalhe: {e}\033[0m")
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
            EC.element_to_be_clickable((By.XPATH, '//i[@class="icomoon icon-ico-campo-busca"]/.. | //button[contains(., "Gerar Certidão")]'))
        )

        # Registra arquivos já existentes antes do clique
        os.makedirs(pasta_download, exist_ok=True)
        arquivos_antes = set(os.listdir(pasta_download))

        # Duplo clique necessário para o portal Megasoft
        botao_gerar.click()
        time.sleep(0.5)
        botao_gerar.click()

        inicio = time.time()
        timeout = 25
        sucesso = False
        msg_alerta_site = ""

        while time.time() - inicio < timeout:
            # 1. Captura notificações do portal (Avisos de erro, alerta ou informação)
            toasts = navegador.find_elements(
                By.XPATH,
                '//div[contains(@class, "toast-message") or contains(@class, "toast-container")]'
            )
            
            for t in toasts:
                if t.is_displayed():
                    texto = t.text.strip()
                    if texto and "sucesso" not in texto.lower():
                        # Se for um bloqueio ou aviso real (ex: débitos, pendências)
                        msg_alerta_site = texto
                        print(f"\033[31m[Flores de Goiás] Alerta do portal: {msg_alerta_site}\033[0m")
                        return False, f"Bloqueio: {msg_alerta_site}"

            # 2. Verifica se um NOVO PDF surgiu na pasta
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
                print(f"\033[32mMunicipal de Flores recolhida para o CNPJ: {CNPJ}\033[0m")
                print(f"Arquivo baixado: {arquivo_final}")
                sucesso = True
                break

            time.sleep(0.5)

        if not sucesso:
            msg_erro = "Tempo limite de download excedido (Nenhum PDF baixado)."
            print(f"\033[33m[Flores] Aviso: {msg_erro} para {CNPJ}.\033[0m")
            diagnosticar_download_falhou(navegador, pasta_download)
            return False, msg_erro
            
        return True, ""

    except Exception as e:
        msg_erro = f"Fluxo de emissão falhou devido a um erro inesperado: {e}"
        print(f"\033[33m[Flores] Aviso: {msg_erro} CNPJ: {CNPJ}.\033[0m")
        return False, msg_erro


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import criar_navegador_configurado

    cnpj_teste = "19758842001298"
    pasta_teste = r"N:\19. FERRAMENTAS\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_teste, exist_ok=True)

    print(f"\033[36m--- Teste Avulso: Flores de Goiás (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        sucesso, observacao = recolher(cnpj_teste, siteCadastro, navegador_teste, pasta_teste)
        print(f"\nResultado do Teste -> Sucesso: {sucesso} | Observação: '{observacao}'")
        input("\nPressione [ENTER] para encerrar o navegador de teste...")
    finally:
        navegador_teste.quit()