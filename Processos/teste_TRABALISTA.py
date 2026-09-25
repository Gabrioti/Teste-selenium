import os
import sys
import time
import base64

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from CadastroDiagnostico.diagnostico_download import esperar_download, _arquivos_validos

try:
    import ddddocr
    _ocr = ddddocr.DdddOcr(show_ad=False)
except Exception:
    _ocr = None

COR_TRABALHISTA = "\033[38;2;102;204;255m"  # Azul claro (#66CCFF)
COR_ERRO = "\033[31m"
COR_RESET = "\033[0m"


def extrair_codigo_captcha(navegador):
    """
    Tenta decifrar o código CAPTCHA do TST usando OCR (ddddocr).
    O CAPTCHA do TST consiste em 5 caracteres alfanuméricos.
    """
    if _ocr is None:
        print(f"{COR_TRABALHISTA}[TRABALHISTA] OCR (ddddocr) não está disponível no ambiente.{COR_RESET}")
        return None

    try:
        print(f"{COR_TRABALHISTA}[TRABALHISTA] Tentando ler CAPTCHA via OCR...{COR_RESET}")
        # Aguarda a imagem estar presente e com src em base64 carregado
        img_el = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, "//img[@id='captcha-imagem' or contains(@src, 'data:image')]"))
        )
        src = img_el.get_attribute("src") or ""
        if "base64," not in src:
            time.sleep(1)
            src = img_el.get_attribute("src") or ""

        if "base64," in src:
            b64_str = src.split("base64,")[1].strip()
            raw_bytes = base64.b64decode(b64_str)
        else:
            raw_bytes = img_el.screenshot_as_png

        # Cria a pasta se não existir
        if not os.path.exists("dataset_captchas"):
            os.makedirs("dataset_captchas")

        # Salva a imagem com um timestamp para não sobrescrever
        nome_arquivo = f"dataset_captchas/img_{int(time.time())}.png"
        with open(nome_arquivo, "wb") as f:
            f.write(raw_bytes)

        cod_pred = _ocr.classification(raw_bytes).strip()
        cod_limpo = "".join(c for c in cod_pred if c.isalnum() and c.isascii())

        print(f"{COR_TRABALHISTA}[TRABALHISTA] OCR fez a leitura da imagem: '{cod_limpo}' ({len(cod_limpo)} caracteres){COR_RESET}")

        if len(cod_limpo) == 6:
            print(f"{COR_TRABALHISTA}[TRABALHISTA] Código de 6 caracteres decifrado com sucesso: '{cod_limpo}'{COR_RESET}")
            return cod_limpo
        else:
            print(f"{COR_TRABALHISTA}[TRABALHISTA] Leitura do OCR descartada por ter {len(cod_limpo)} caracteres (o portal exige exatamente 6).{COR_RESET}")
            return None
    except Exception as e:
        print(f"{COR_TRABALHISTA}[TRABALHISTA] Aviso OCR: {e}{COR_RESET}")

    return None


def preencher_cnpj_e_solicitar_captcha(navegador, cnpj, pasta_download=None, solicitar_captcha=None):
    """
    Preenche CNPJ, tenta resolver o CAPTCHA com OCR (até 5 tentativas, recarregando a página).
    Se falhar 5 vezes, recorre à digitação humana nas tentativas restantes.
    """
    if not pasta_download:
        pasta_download = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_download, exist_ok=True)

    tentativas = 0
    max_tentativas_ocr = 5      # Quantas vezes o OCR vai tentar sozinho
    max_tentativas_totais = 8   # Dá 5 chances pro robô e 3 para o humano

    while tentativas < max_tentativas_totais:
        try:
            tentativas += 1
            print(f"{COR_TRABALHISTA}[TRABALHISTA] [Tentativa {tentativas}/{max_tentativas_totais}] Processando emissao para CNPJ: {cnpj}...{COR_RESET}")

            # 1. Localiza e preenche o campo de CNPJ
            campo_cnpj = None
            for selector in [(By.ID, "cpfCnpj"), (By.ID, "gerarCertidaoForm:cpfCnpj"), (By.NAME, "cpfCnpj")]:
                try:
                    campo_cnpj = WebDriverWait(navegador, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    break
                except Exception:
                    continue

            if not campo_cnpj:
                print(f"{COR_ERRO}[TRABALHISTA] Campo de CNPJ nao encontrado!{COR_RESET}")
                continue

            # Se o campo não estiver preenchido com o CNPJ, preenche
            valor_atual = campo_cnpj.get_attribute("value") or ""
            valor_limpo = "".join(c for c in valor_atual if c.isdigit())
            cnpj_limpo = "".join(c for c in cnpj if c.isdigit())

            if valor_limpo != cnpj_limpo:
                campo_cnpj.clear()
                campo_cnpj.send_keys(cnpj)
                print(f"{COR_TRABALHISTA}[TRABALHISTA] CNPJ preenchido: {cnpj}{COR_RESET}")

            time.sleep(1)

            # 2. Tenta obter o código. Usa OCR até a tentativa 5. Depois pede ajuda.
            codigo_captcha = None
            if tentativas <= max_tentativas_ocr:
                codigo_captcha = extrair_codigo_captcha(navegador)
                
                # Se o OCR não decifrou (retornou None), recarrega a página para pegar outro
                if not codigo_captcha:
                    print(f"{COR_TRABALHISTA}[TRABALHISTA] OCR falhou na leitura. Recarregando a página...{COR_RESET}")
                    navegador.refresh()
                    time.sleep(3)
                    # Reentra no iframe caso a página tenha recarregado
                    try:
                        iframes = navegador.find_elements(By.TAG_NAME, "iframe")
                        if len(iframes) > 0:
                            navegador.switch_to.frame(iframes[0])
                    except:
                        pass
                    continue
            else:
                # 3. Limite do OCR atingido. Solicitando ao usuário
                print(f"{COR_TRABALHISTA}[TRABALHISTA] Limite de tentativas do OCR atingido.{COR_RESET}")
                if solicitar_captcha is not None:
                    print(f"{COR_TRABALHISTA}[TRABALHISTA] Solicitando CAPTCHA ao usuario na interface...{COR_RESET}")
                    codigo_captcha = solicitar_captcha().strip()
                else:
                    codigo_captcha = input(f"{COR_TRABALHISTA}[TRABALHISTA] Digite os 5 caracteres do CAPTCHA exibido: {COR_RESET}").strip()

            if not codigo_captcha:
                print(f"\033[31m[TRABALHISTA] Nenhum codigo informado. Tentando novamente...\033[0m")
                continue

            # 4. Preenche o campo de resposta do CAPTCHA
            campo_captcha = None
            for selector in [(By.ID, "captcha-resposta"), (By.ID, "idCampoResposta"), (By.NAME, "resposta")]:
                try:
                    campo_captcha = WebDriverWait(navegador, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    break
                except Exception:
                    continue

            if not campo_captcha:
                print("\033[31m[TRABALHISTA] Campo de resposta do CAPTCHA nao encontrado!\033[0m")
                continue

            campo_captcha.clear()
            campo_captcha.send_keys(codigo_captcha)

            # 5. Registra arquivos antes e clica em Emitir Certidão
            arquivos_antes = set(_arquivos_validos(pasta_download))

            btn_submit = None
            for selector in [
                (By.ID, "botao-emitir"),
                (By.ID, "gerarCertidaoForm:btnEmitirCertidao"),
                (By.XPATH, "//input[@type='submit' and contains(@value, 'Emitir')]")
            ]:
                try:
                    els = navegador.find_elements(*selector)
                    if els and els[0].is_displayed() and els[0].is_enabled():
                        btn_submit = els[0]
                        break
                except Exception:
                    continue

            if btn_submit:
                btn_submit.click()
                print(f"{COR_TRABALHISTA}[TRABALHISTA] Botao de emissao acionado com codigo: '{codigo_captcha}'.{COR_RESET}")
            else:
                print("\033[31m[TRABALHISTA] Botao de emissao nao encontrado ou desabilitado.\033[0m")
                continue

            time.sleep(3)

            # 6. Verifica se o código foi recusado pelo portal
            try:
                mensagens_erro = navegador.find_elements(
                    By.XPATH,
                    "//*[@id='mensagens' and not(contains(@class, 'oculto'))] | //li[contains(text(), 'incorreta') or contains(text(), 'invalido')]"
                )
                houve_erro = False
                for err in mensagens_erro:
                    if err.is_displayed():
                        txt = err.text.strip()
                        if txt and any(p in txt.lower() for p in ["incorreta", "invalida", "invalido", "erro"]):
                            print(f"\033[31m[TRABALHISTA] Aviso do portal: {txt}\033[0m")
                            houve_erro = True
                            break

                if houve_erro:
                    print(f"{COR_TRABALHISTA}[TRABALHISTA] Codigo '{codigo_captcha}' foi recusado. Recarregando a página...{COR_RESET}")
                    navegador.refresh()
                    time.sleep(3)
                    # Reentra no iframe caso a página tenha recarregado
                    try:
                        iframes = navegador.find_elements(By.TAG_NAME, "iframe")
                        if len(iframes) > 0:
                            navegador.switch_to.frame(iframes[0])
                    except:
                        pass
                    continue
            except Exception:
                pass

            # 7. Aguarda o download do arquivo PDF
            try:
                arquivo = esperar_download(navegador, pasta_download, timeout=20, arquivos_antes=arquivos_antes)
                print(f"{COR_TRABALHISTA}[TRABALHISTA] CND recolhida com sucesso para o CNPJ: {cnpj}{COR_RESET}")
                print(f"{COR_TRABALHISTA}Arquivo baixado: {arquivo}{COR_RESET}")
                
                # MODIFICADO AQUI: Sucesso! Devolve True e observação vazia.
                return True, ""
                
            except TimeoutError:
                sucesso_els = navegador.find_elements(
                    By.XPATH,
                    "//*[@id='secao-sucesso' and not(contains(@class, 'oculto'))]"
                )
                if any(s.is_displayed() for s in sucesso_els):
                    print(f"{COR_TRABALHISTA}[TRABALHISTA] Mensagem de certidao emitida exibida. Aguardando finalizacao do download...{COR_RESET}")
                    try:
                        arquivo = esperar_download(navegador, pasta_download, timeout=10, arquivos_antes=arquivos_antes)
                        print(f"{COR_TRABALHISTA}[TRABALHISTA] CND recolhida com sucesso: {arquivo}{COR_RESET}")
                        
                        # MODIFICADO AQUI: Sucesso!
                        return True, ""
                        
                    except Exception:
                        pass

                print(f"{COR_TRABALHISTA}[TRABALHISTA] Download nao confirmado no tempo limite. Tentando novamente...{COR_RESET}")
                continue

        except TimeoutException:
            print(f"\033[31m[TRABALHISTA] Timeout ao aguardar elemento na tentativa {tentativas}\033[0m")
            continue
        except Exception as e:
            print(f"\033[31m[TRABALHISTA] Erro na tentativa {tentativas}: {e}\033[0m")
            continue

    msg_falha = f"Falha após {max_tentativas_totais} tentativas (possível instabilidade do portal)."
    print(f"\033[31m[TRABALHISTA] {msg_falha} para o CNPJ {cnpj}\033[0m")
    
    # MODIFICADO AQUI: Esgotou tentativas, envia falha formatada pro painel
    return False, msg_falha


def recolher(CNPJ, site, navegador, pasta_download=None, solicitar_captcha=None, debug=False):
    """
    Função principal para recolher certidão do site TST (Trabalhista).
    Redireciona diretamente para o novo portal da CNDT caso a URL antiga com iframe seja fornecida.
    """
    if not pasta_download:
        pasta_download = r"n:\19. FERRAMENTAS\Teste selenium\RenomearCNDs\CNDs"
    os.makedirs(pasta_download, exist_ok=True)

    url_direta = "https://cndt-certidao.tst.jus.br/gerarCertidao"
    if "tst.jus.br" in site:
        site = url_direta

    try:
        print(f"{COR_TRABALHISTA}[TRABALHISTA] Acessando o portal CNDT...{COR_RESET}")
        navegador.get(site)
        time.sleep(2)

        # Se houver iframe (portal antigo embutido), entra nele
        iframes = navegador.find_elements(By.TAG_NAME, "iframe")
        if len(iframes) > 0:
            try:
                navegador.switch_to.frame(iframes[0])
            except Exception:
                pass

        # Se houver botão preliminar 'Emitir Certidão' (sistema legado), clica
        try:
            botoes_iniciais = navegador.find_elements(By.XPATH, "//input[@value='Emitir Certidão' and not(@id='botao-emitir')]")
            if botoes_iniciais and botoes_iniciais[0].is_displayed():
                botoes_iniciais[0].click()
                time.sleep(2)
        except Exception:
            pass

        # MODIFICADO AQUI: A variável 'sucesso' agora recebe a dupla (True, "") ou (False, "Erro")
        sucesso = preencher_cnpj_e_solicitar_captcha(
            navegador,
            CNPJ,
            pasta_download=pasta_download,
            solicitar_captcha=solicitar_captcha
        )

        try:
            navegador.switch_to.default_content()
        except Exception:
            pass

        return sucesso

    except Exception as e:
        msg = f"Erro geral no fluxo: {e}"
        print(f"\033[31m[TRABALHISTA] {msg}\033[0m")
        try:
            navegador.switch_to.default_content()
        except Exception:
            pass
            
        # MODIFICADO AQUI: Erro fatal de carregamento devolve a dupla para o painel
        return False, msg


if __name__ == "__main__":
    from main import criar_navegador_configurado

    cnpj_teste = "17920217000112"
    site_tst = "https://cndt-certidao.tst.jus.br/gerarCertidao"
    pasta_teste = r"C:\Users\FAGabrioti\Desktop\Teste selenium\RenomearCNDs\CNDs"

    print(f"\033[36m--- Teste Avulso: Trabalhista TST (CNPJ: {cnpj_teste}) ---\033[0m")
    navegador_teste = criar_navegador_configurado()
    try:
        recolher(cnpj_teste, site_tst, navegador_teste, pasta_download=pasta_teste)
    finally:
        navegador_teste.quit()