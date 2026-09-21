import json # Essa biblioteca permite que você trabalhe com arquivos JSON, que são muito usados para armazenar dados de forma estruturada.
import os # Essa biblioteca permite que você interaja com o sistema operacional, como criar pastas, apagar arquivos, etc.
import glob # Essa biblioteca permite que você busque arquivos usando padrões, como "*.pdf" para todos os PDFs.
import shutil # Essa biblioteca permite mover e sobrescrever arquivos em uma pasta para outra de forma limpa
import re # Essa biblioteca permite que você trabalhe com expressões regulares, que são muito usadas para buscar padrões em textos.
import queue # Essa biblioteca permite que você trabalhe com filas, que são muito usadas para armazenar dados de forma estruturada.
import sys # Essa biblioteca permite que você trabalhe com o sistema operacional, como criar pastas, apagar arquivos, etc.
import threading # Essa biblioteca permite que você execute várias tarefas ao mesmo tempo, em paralelo.
import tkinter as tk # Essa biblioteca permite que você crie interfaces gráficas para seus programas.
from tkinter import messagebox, scrolledtext, ttk, simpledialog # Essas bibliotecas permitem que você trabalhe com filas, que são muito usadas para armazenar dados de forma estruturada.
from datetime import datetime # Essa biblioteca permite que você trabalhe com datas e horas.
import subprocess # Essa biblioteca permite que você execute comandos do sistema operacional.

from selenium import webdriver # Essa biblioteca permite que você automatize ações no navegador.
from webdriver_manager.chrome import ChromeDriverManager # Essa biblioteca permite que você gerencie o driver do Chrome.
from selenium.webdriver.chrome.service import Service # Essa biblioteca permite que você configure o driver do Chrome.
from selenium.webdriver.chrome.options import Options # Essa biblioteca permite que você configure o Chrome.

from Processos import teste_FEDERAL, teste_ESTADUAL, teste_TRABALISTA,teste_COMPRASNET, teste_FGTS, teste_AGEHAB
from Cidades import Anápolis, Águas_Lindas, Cidade_Ocidental, Formosa, Catalão, Aparecida_de_Goiânia, Luziana, Goianésia, Novo_Gama, Aragoiania, Paraúna, Abadiânia, Santo_Antônio, Mara_Rosa, Nerópolis, Terezópolis, Porangatu, Flores, Iporá, Bom_Jesus, Valparaiso, Goiânia, Caldas_Novas, Campo_Alegre, Nova_Veneza, Senador_Canedo, Planaltina, Itaberai

import pandas as pd
from openpyxl.styles import PatternFill

from Gerenciadores import gerenciador_cnpj
from Gerenciadores import gerenciador_pastas
from Gerenciadores import gerenciador_historico # Ajuste o caminho se necessário

# 1. Pega o caminho absoluto da pasta onde o main.py está e entra na pasta SQL
pasta_atual = os.path.dirname(os.path.abspath(__file__))
caminho_banco = os.path.join(pasta_atual, 'SQL', 'dados.json')

# 2. Abre o arquivo JSON e carrega os dados para um dicionário Python
with open(caminho_banco, 'r', encoding='utf-8') as arquivo_json:
    dados = json.load(arquivo_json)

# 3. Puxa as chaves específicas do JSON para as suas variáveis
mapa_municipal = dados.get("mapa_municipal", {})
mapa_matriz = dados.get("mapa_matriz", {})

CNPJ = ["21370540000137"]

from config import Usuario

site = [
        "https://www.sefaz.go.gov.br/Certidao/Emissao/",                                        #ESTADUAL
        "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj",                 #FEDERAL
        "https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf",           #FGTS
        "http://appweb2.agehab.com.br/",                                                        # AGEHAB
        "https://www.comprasnet.go.gov.br/paginas/fornecedor/CertidaoNegativaEmissao.aspx",     # COMPRASNET
        "https://cndt-certidao.tst.jus.br/gerarCertidao"                                        # TRABALHISTA
]

lista_cnds_manuais = []
flag_cancelamento = False

def injetar_cnpj_filial_no_nome(pasta, mapa_vinculos):
    """
    Procura PDFs com o CNPJ da matriz e adiciona o CNPJ da filial no nome,
    garantindo que a lógica de interseção encontre a pasta correta.
    """
    pdfs = glob.glob(os.path.join(pasta, "*.pdf"))
    
    for caminho_pdf in pdfs:
        nome_arquivo = os.path.basename(caminho_pdf)
        cnpjs_no_arquivo = extrair_cnpjs_do_nome(nome_arquivo) # Usa a sua função existente
        
        for filial, matriz in mapa_vinculos.items():
            # Se o arquivo tem o CNPJ da Matriz, mas ainda não tem o da Filial
            if matriz in cnpjs_no_arquivo and filial not in cnpjs_no_arquivo:
                # Opcional: Garantir que isso só ocorra na CND Federal
                if "Federal" in nome_arquivo or "Receita" in nome_arquivo:
                    # Adiciona o CNPJ da filial no final, antes da extensão
                    novo_nome = nome_arquivo.replace(".pdf", f" - {filial}.pdf")
                    novo_caminho = os.path.join(pasta, novo_nome)
                    
                    os.rename(caminho_pdf, novo_caminho)
                    print(f"\033[36m🔄 Vínculo Matriz-Filial aplicado: {novo_nome}\033[0m")

def acionar_robo_cnd():
    print("Iniciando a etapa de renomear os PDFs...")
    
    # 1. Descobre onde a sua aplicação principal está rodando agora
    pasta_app_principal = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Monta o caminho exato até o central.py do robô de CNDs
    caminho_robo_cnd = os.path.join(pasta_app_principal, "RenomearCNDs", "central.py")
    
    # 3. Executa o robô de forma segura e espera ele terminar!
    try:
        # sys.executable garante que o robô use o MESMO ambiente virtual da sua aplicação, 
        # evitando aquele erro de "No module named pdfplumber" que você já conhece!
        subprocess.run([sys.executable, caminho_robo_cnd], check=True)
        print("Robô de CNDs finalizou o trabalho com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Ocorreu um erro ao rodar o robô de CNDs: {e}")
        return False

def extrair_cnpjs_do_nome(nome):
    """Extrai CNPJs formatados ou sem separadores de um nome de arquivo/pasta."""
    padrao_cnpj = re.compile(
        r"(?<!\d)(?:\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s-]?\d{4}[-\s]?\d{2})(?!\d)"
    )
    cnpjs = set()
    for cnpj_encontrado in padrao_cnpj.findall(nome):
        cnpj_normalizado = ''.join(caractere for caractere in cnpj_encontrado if caractere.isdigit())
        if len(cnpj_normalizado) == 14:
            cnpjs.add(cnpj_normalizado)
    return cnpjs

def criar_navegador_configurado():
    
    """Função auxiliar para gerar navegadores idênticos e isolados"""
    opcoes = Options()

    # Argumentos originais de segurança
    opcoes.add_argument('--safebrowsing-disable-download-protection')
    opcoes.add_argument('--safebrowsing-disable-extension-blacklist')
    opcoes.add_argument('--ignore-certificate-errors')
    opcoes.add_argument('--disable-features=InsecureDownloadWarnings')

    # NOVO: Argumento que força o Chrome a "clicar" em imprimir automaticamente sem mostrar a tela
    opcoes.add_argument('--kiosk-printing')

    # NOVO: Configuração que diz ao Chrome que o destino da impressão é "Salvar como PDF"
    app_state = {
        "recentDestinations": [{
            "id": "Save as PDF",
            "origin": "local",
            "account": ""
        }],
        "selectedDestinationId": "Save as PDF",
        "version": 2
    }

    preferencias = {
        # Suas configurações originais
        "download.default_directory": pasta_download,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True,                      
        "safebrowsing.disable_download_protection": True,   
        "profile.default_content_setting_values.automatic_downloads": 1,
        
        # NOVO: Desabilita o visualizador de PDF interno do Chrome por precaução extra
        "plugins.plugins_disabled": ["Chrome PDF Viewer"],
        
        # NOVO: Injeta as configurações de "Salvar como PDF" no perfil do Chrome
        "printing.print_preview_sticky_settings.appState": json.dumps(app_state),
        
        # NOVO: Define o diretório padrão para onde os arquivos "Salvos como PDF" vão
        "savefile.default_directory": pasta_download
    }

    opcoes.add_experimental_option("prefs", preferencias)
    opcoes.add_experimental_option("detach", True)

    servico = Service(ChromeDriverManager().install())

    # IMPORTANTE: Removi o "detach: True" para que o código Python consiga fechar as janelas no final
    return webdriver.Chrome(service=servico, options=opcoes)

def principal(lista_cnpjs, tipos_cnd, solicitar_captcha=None, interface=None):
    global flag_cancelamento
    flag_cancelamento = False
    
    # Loop passando por cada CNPJ
    for cnpj_idx, cnpj in enumerate(lista_cnpjs):
        if flag_cancelamento:
            print("\033[31mColeta cancelada pelo usuário.\033[0m")
            break
            
        print(f"\033[33m\n--- Coleta {cnpj_idx + 1}/{len(lista_cnpjs)}: CNPJ {cnpj} ---\033[0m")
        print(f"Tipos de CND selecionados: {', '.join(tipos_cnd)}\n")
        CNPJ[:] = [cnpj]
        
        tipos_cnd_norm = {t.upper() for t in tipos_cnd}

        # 1. Criamos os navegadores fixos
        navegadores_fixos = []
        if "ESTADUAL" in tipos_cnd_norm:
            nav_estadual = criar_navegador_configurado()
            nav_estadual.maximize_window()
            nav_estadual.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': pasta_download})
            navegadores_fixos.append(nav_estadual)
        
        if "FGTS" in tipos_cnd_norm:
            nav_fgts = criar_navegador_configurado()
            nav_fgts.maximize_window()
            nav_fgts.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': pasta_download})
            navegadores_fixos.append(nav_fgts)
        
        if "AGEHAB" in tipos_cnd_norm:
            nav_agehab = criar_navegador_configurado()
            nav_agehab.maximize_window()
            nav_agehab.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': pasta_download})
            navegadores_fixos.append(nav_agehab)

        if "TRABALHISTA" in tipos_cnd_norm and not flag_cancelamento:
            nav_trabalhista = criar_navegador_configurado()
            nav_trabalhista.maximize_window()
            nav_trabalhista.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': pasta_download})
            navegadores_fixos.append(nav_trabalhista)

        if "COMPRASNET" in tipos_cnd_norm and not flag_cancelamento:
            nav_comprasnet = criar_navegador_configurado()
            nav_comprasnet.maximize_window()
            nav_comprasnet.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': pasta_download})
            navegadores_fixos.append(nav_comprasnet)

        # Lista para guardar os navegadores municipais DINÂMICOS
        navegadores_municipais = []
        
        # Busca o dicionário de cidades deste CNPJ
        print("[MUNICIPAL] Coletando municípios!")
        print(f"[MUNICIPAL] Procurando no dicionário o CNPJ: '{cnpj}'")
        cidades_da_empresa = gerenciador_cnpj.obter_cidades_cnpj(cnpj)
        print(f"[MUNICIPAL] Resultado da busca: Encontrou {len(cidades_da_empresa)} cidades.")

        # =========================================================
        # 2. EXECUÇÃO SEQUENCIAL (Uma aba por vez)
        # =========================================================
        houve_falha = False

        # Criamos um "Ajudante" para rodar a função, esperar ela acabar e anotar falhas
        def rodar_coleta(funcao, nome_da_certidao, *args, **kwargs):
            nonlocal houve_falha
            if flag_cancelamento:
                return
            
            print(f"\n⏳ Iniciando coleta sequencial: {nome_da_certidao}")
            try:
                # O código do Python "pausa" aqui e só vai pra linha de baixo quando a função terminar
                resultado = funcao(*args, **kwargs)
                
                # Se a função devolveu a dupla (Sucesso, Observacao), salvamos no Histórico
                if isinstance(resultado, tuple) and len(resultado) == 2:
                    sucesso, observacao = resultado
                    if not sucesso:
                        gerenciador_historico.registrar_resultado(
                            cnpj=cnpj,
                            certidao=nome_da_certidao,
                            validade="",
                            status="Falha na Coleta",
                            observacao=observacao
                        )
                        houve_falha = True
            except Exception as e:
                print(f"❌ Erro crítico ao executar a tarefa {nome_da_certidao}: {e}")

        # ---------------------------------------------------------
        # A. COLETAS FIXAS
        # ---------------------------------------------------------
        if "ESTADUAL" in tipos_cnd_norm and not flag_cancelamento:
            rodar_coleta(teste_ESTADUAL.recolher_estadual, "Estadual", cnpj, site[0], nav_estadual, pasta_download)
            
        if "FGTS" in tipos_cnd_norm and not flag_cancelamento:
            rodar_coleta(teste_FGTS.recolher_FGTS, "FGTS", cnpj, site[2], nav_fgts, pasta_download)
            
        if "AGEHAB" in tipos_cnd_norm and not flag_cancelamento:
            rodar_coleta(teste_AGEHAB.recolher_agehab, "AGEHAB", cnpj, site[3], nav_agehab, usuario=Usuario.AGEHAB_USUARIO, senha=Usuario.AGEHAB_SENHA)

        if "COMPRASNET" in tipos_cnd_norm and not flag_cancelamento:
            rodar_coleta(teste_COMPRASNET.recolher, "Comprasnet", cnpj, site[4], nav_comprasnet, pasta_download=pasta_download, solicitar_captcha=solicitar_captcha)

        if "TRABALHISTA" in tipos_cnd_norm and not flag_cancelamento:
            rodar_coleta(teste_TRABALISTA.recolher, "Trabalhista", cnpj, site[5], nav_trabalhista, pasta_download=pasta_download, solicitar_captcha=solicitar_captcha)


        # ---------------------------------------------------------
        # B. ROTEADOR MUNICIPAL
        # ---------------------------------------------------------
        if "MUNICIPAL" in tipos_cnd_norm:
            for municipio in cidades_da_empresa:
                if flag_cancelamento:
                    break
                    
                nome_cidade = municipio["cidade"]
                print(f"\n[{nome_cidade}] Iniciando verificação do município: {nome_cidade}")
                
                # Se for manual, anota na lista e pula
                if not municipio["automatizado"]:
                    lista_cnds_manuais.append(f"{cnpj} - {nome_cidade}")
                    print(f"\033[31m⚠️ {nome_cidade} separada para coleta manual.\033[0m")
                    continue

                site_da_cidade = municipio["url"]
                
                # Cria um navegador exclusivo pra ela e já aplica o CDP CMD
                nav_mun = criar_navegador_configurado()
                nav_mun.maximize_window()
                nav_mun.execute_cdp_cmd('Page.setDownloadBehavior', {
                    'behavior': 'allow', 
                    'downloadPath': pasta_download
                })
                navegadores_municipais.append(nav_mun)
                
                # CHAMA A FUNÇÃO DIRETO (O código vai esperar ela terminar)
                if nome_cidade == "Águas Lindas":
                    rodar_coleta(Águas_Lindas.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Cidade Ocidental":
                    rodar_coleta(Cidade_Ocidental.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Valparaiso":
                    rodar_coleta(Valparaiso.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download, solicitar_captcha=solicitar_captcha)
                elif nome_cidade == "Formosa":
                    rodar_coleta(Formosa.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Catalão":
                    rodar_coleta(Catalão.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Aparecida de Goiânia":
                    rodar_coleta(Aparecida_de_Goiânia.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Luziana":
                    rodar_coleta(Luziana.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Goianésia":
                    rodar_coleta(Goianésia.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Novo Gama":
                    rodar_coleta(Novo_Gama.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Aragoiania":
                    rodar_coleta(Aragoiania.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Paraúna":
                    rodar_coleta(Paraúna.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Abadiânia":
                    rodar_coleta(Abadiânia.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Santo Antônio":
                    rodar_coleta(Santo_Antônio.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Mara Rosa":
                    rodar_coleta(Mara_Rosa.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Terezópolis":
                    rodar_coleta(Terezópolis.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Nerópolis":
                    rodar_coleta(Nerópolis.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Flores":
                    rodar_coleta(Flores.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Iporá":
                    rodar_coleta(Iporá.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Porangatu":
                    rodar_coleta(Porangatu.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Bom Jesus":
                    rodar_coleta(Bom_Jesus.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade in ("Anápolis", "Ánapolis"):
                    rodar_coleta(Anápolis.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Goiânia":
                    rodar_coleta(Goiânia.recolher, nome_cidade, cnpj, site_da_cidade, pasta_download)
                elif nome_cidade == "Caldas Novas":
                    rodar_coleta(Caldas_Novas.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Campo Alegre":
                    rodar_coleta(Campo_Alegre.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Nova Veneza":
                    rodar_coleta(Nova_Veneza.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Senador Canedo":
                    rodar_coleta(Senador_Canedo.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Planaltina":
                    rodar_coleta(Planaltina.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                elif nome_cidade == "Itaberai":
                    rodar_coleta(Itaberai.recolher, nome_cidade, cnpj, site_da_cidade, nav_mun, pasta_download)
                else:
                    print(f"\033[33m⚠️ Nenhuma automação vinculada para a cidade: {nome_cidade}\033[0m")
                    navegadores_municipais.remove(nav_mun)
                    nav_mun.quit()
        else:
            print("[MUNICIPAL] Coleta de municípios desabilitada")
        
        # ---------------------------------------------------------
        # 3. VERIFICAÇÃO E ENCERRAMENTO
        # ---------------------------------------------------------
        # Se alguma prefeitura deu erro, atualizamos a tela em tempo real para pintar de vermelho!
        if houve_falha and interface:
            try:
                interface.janela.after(0, interface.atualizar_painel_conferencia)
            except:
                pass

        # Fechar navegadores fixos
        for nav in navegadores_fixos:
            nav.quit()
            
        for nav in navegadores_municipais:
            nav.quit()
        
        # A FEDERAL É A ÚNICA QUE RODA FORA DO SELENIUM
        if "FEDERAL" in tipos_cnd_norm and not flag_cancelamento:
            teste_FEDERAL.recolher_FEDERAL(cnpj, site[1], pasta_download)

        # LIMPEZA DE ARQUIVOS INDESEJADOS 

        # 1. Busca qualquer arquivo que termine com .htm ou .html na pasta
        arquivos_lixo = glob.glob(os.path.join(pasta_download, "*.htm*"))

        # 2. Percorre a lista e apaga um por um
        for lixo in arquivos_lixo:
            try:
                os.remove(lixo)
                print(f"\033[33m Lixo apagado com sucesso: {os.path.basename(lixo)}\033[0m")
            except Exception as e:
                print(f"\033[33m Não foi possível apagar o arquivo {lixo}: {e}\033[0m")

        print(f"\033[33mColetas finalizadas para o CNPJ {CNPJ}!\033[0m\n")

        pasta_relatorios = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relatorios")
        gerar_relatorio_txt(pasta_relatorios, lista_cnds_manuais)

def organizar_certidoes_por_cnpj(pasta_download, pasta_raiz_empresas, interface=None):
    """
    Localiza os PDFs na pasta_download, varre as subpastas em 'pasta_raiz_empresas'
    procurando a pasta que contém o CNPJ correspondente. 
    Aplica a regra de negócio de substituição baseada no Status (Negativa vs Positiva) 
    e na data de vigência (Hoje).
    """
    # 0. chama o renomeador de CNDs
    if acionar_robo_cnd(): 
        print("\033[33mRobô CND acionado com sucesso!\033[0m\n") 
        
        # 4. Injeta CNPJ da filial nos PDFs cujo CNPJ no texto seja a matriz 
        # (Usando o obter_todos_vinculos_matriz como ajustamos antes!)
        injetar_cnpj_filial_no_nome(pasta_download, gerenciador_cnpj.obter_todos_vinculos_matriz()) 
        
        # =========================================================
        # NOVO: ATUALIZA O PAINEL DE CONFERÊNCIA COM OS NOVOS DADOS
        # =========================================================
        if interface:
            # Usamos o .after(0, ...) para o Tkinter atualizar a tela com segurança
            interface.janela.after(0, interface.atualizar_painel_conferencia)
            
    else: 
        print("\033[31mRobô CND não acionado!\033[0m\n")
    # 1. Pega todos os arquivos .pdf que estão na pasta de downloads
    pdfs_novos = glob.glob(os.path.join(pasta_download, "*.pdf"))

    if not pdfs_novos:
        print("Nenhum arquivo PDF encontrado na pasta de downloads.")
        return

    # Pega a data de hoje e zera as horas para a comparação ser exata
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for caminho_novo in pdfs_novos:
        nome_novo = os.path.basename(caminho_novo)
        
        # Exemplo de nome_novo: "1 - CND Federal - Negativa - 04.01.27 - 12.655.348-0001-04.pdf"
        partes_novo = nome_novo.replace(".pdf", "").split(" - ")
        
        if len(partes_novo) < 5:
            print(f"⚠️ Arquivo ignorado (fora do padrão): {nome_novo}")
            continue

        id_tipo = partes_novo[0]                        # "3"
        nome_cnd = partes_novo[1]                       # "CND Formosa"
        status_novo = partes_novo[2].strip().lower()    # Pega o status e joga pra minúsculo (ex: "positiva")
        data_str_nova = partes_novo[3]                  # 14.05.27
        cnpj = partes_novo[4]                           # 12.655.348-0001-04
        cnpjs_do_pdf = extrair_cnpjs_do_nome(nome_novo) #
        if not cnpjs_do_pdf:
            print(f"❌ Nenhum CNPJ válido foi encontrado no nome do PDF: {nome_novo}")
            continue

        # Converte o texto da data nova em objeto datetime
        try:
            data_nova = datetime.strptime(data_str_nova, "%d.%m.%y")
        except ValueError:
            print(f"❌ Erro ao converter a data do arquivo novo: {nome_novo}")
            continue

        # 2. BUSCA RECURSIVA DA PASTA
        padrao_pasta = os.path.join(pasta_raiz_empresas, "**", "*")
        pastas_encontradas = [
            p for p in glob.glob(padrao_pasta, recursive=True)
            if os.path.isdir(p)
            and cnpjs_do_pdf.intersection(extrair_cnpjs_do_nome(os.path.basename(p)))
        ]

        if not pastas_encontradas:
            print(f"❌ Nenhuma pasta contendo o CNPJ '{cnpj}' foi encontrada na rede para: {nome_novo}")
            continue

        if len(pastas_encontradas) > 1:
            print("⚠️ Mais de uma pasta correspondeu ao CNPJ do PDF:")
            for pasta in pastas_encontradas:
                print(f"   - {pasta}")

        pasta_destino = pastas_encontradas[0]
        cnpjs_da_pasta = extrair_cnpjs_do_nome(os.path.basename(pasta_destino))
        print(f"\n📁 CNPJ {cnpj} -> Analisando pasta: {os.path.basename(pasta_destino)}")
        print(f"   CNPJs identificados na pasta: {', '.join(sorted(cnpjs_da_pasta))}")

        # 3. VERIFICA SE JÁ EXISTE UMA CERTIDÃO ANTIGA
        padrao_busca_antigo = f"{id_tipo} - {nome_cnd} - * - * - {cnpj}.pdf"
        arquivos_antigos = sorted(glob.glob(os.path.join(pasta_destino, padrao_busca_antigo)))

        print(f"🔎 Padrão usado para localizar a certidão antiga: {padrao_busca_antigo}")
        if arquivos_antigos:
            print("🔎 Certidões antigas encontradas:")
            for arquivo_antigo in arquivos_antigos:
                print(f"   - {os.path.basename(arquivo_antigo)}")

        if arquivos_antigos:
            caminho_antigo = arquivos_antigos[0]
            nome_antigo = os.path.basename(caminho_antigo)
            partes_antigo = nome_antigo.replace(".pdf", "").split(" - ")

            if len(partes_antigo) >= 5:
                data_str_antiga = partes_antigo[3]
                try:
                    data_antiga = datetime.strptime(data_str_antiga, "%d.%m.%y")
                except ValueError:
                    data_antiga = datetime.min

                # --- 4. O MOTOR DE REGRAS DE NEGÓCIO ---
                substituir = False
                motivo = ""

                # Verifica se é estritamente Positiva (se tiver "efeito" no texto, ele ignora esse if)
                if "positiva" in status_novo and "efeito" not in status_novo:
                    # REGRA 2: A NOVA É POSITIVA (RUIM)
                    if data_antiga < hoje:
                        substituir = True
                        motivo = "A certidão antiga já venceu. Atualizando para a nova (mesmo sendo Positiva)."
                    else:
                        substituir = False
                        motivo = f"A antiga ainda é válida até {data_str_antiga}. Bloqueando a nova certidão Positiva."
                else:
                    # REGRA 1: A NOVA É NEGATIVA OU POSITIVA COM EFEITO (BOA)
                    if data_nova > data_antiga:
                        substituir = True
                        motivo = f"Nova certidão 'Boa' possui validade maior ({data_str_nova} > {data_str_antiga})."
                    else:
                        substituir = False
                        motivo = f"A certidão antiga já possui validade igual ou maior ({data_str_antiga}). Descartando a nova."
                
                # --- FIM DO MOTOR DE REGRAS ---

                # Executa a ação decidida pelo motor
                if substituir:
                    print(f"🔄 TROCA APROVADA: {motivo}")
                    print(f"   PDF antigo que será apagado: {nome_antigo}")
                    print(f"   PDF novo que será colocado: {nome_novo}")
                    print(f"   Destino da troca: {pasta_destino}")
                    os.remove(caminho_antigo)
                    if os.path.exists(caminho_antigo):
                        raise OSError(f"O PDF antigo ainda existe após a remoção: {caminho_antigo}")
                    shutil.move(caminho_novo, os.path.join(pasta_destino, nome_novo))
                    print(f"✅ Troca concluída: {nome_antigo} -> {nome_novo}")
                    if interface:
                        # Passamos o CNPJ (que já existe no loop) em vez do empresa_nome
                        interface.janela.after(0, lambda c=cnpj, nd=nome_cnd, dn=data_str_nova, sn=status_novo, m=motivo: 
                                               interface.adicionar_linha_conferencia(c, nd, dn, sn, m))
                else:
                    print(f"ℹ️ TROCA RECUSADA: {motivo}")
                    os.remove(caminho_novo) # Apaga o download indesejado

            else:
                # Se o arquivo antigo tem um nome zoado que não podemos ler, substituímos por precaução
                os.remove(caminho_antigo)
                shutil.move(caminho_novo, os.path.join(pasta_destino, nome_novo))
                print(f"✅ Arquivo antigo fora de padrão substituído pela nova certidão.")
        else:
            # REGRA 3: Não existe certidão antiga na pasta (salva direto)
            shutil.move(caminho_novo, os.path.join(pasta_destino, nome_novo))
            print(f"✅ Primeira certidão desse tipo adicionada à pasta!")

PASTA_RELATORIOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relatorios")

def gerar_relatorio_txt(pasta_destino=None, lista_pendencias=None):
    if lista_pendencias is None:
        lista_pendencias = []
    if pasta_destino is None:
        pasta_destino = PASTA_RELATORIOS

    os.makedirs(pasta_destino, exist_ok=True)
    # Se a lista estiver vazia, significa que o robô fez 100% de tudo sozinho!
    if not lista_pendencias:
        print("\n🎉 Nenhuma CND manual pendente hoje! Relatório não gerado.")
        return None

    # Pega a data atual formatada (Ex: 13-08-2026)
    data_hoje = datetime.now().strftime("%d-%m-%Y")
    
    # Define o nome e o caminho do arquivo de texto
    nome_arquivo = f"Relatorio_CNDs_Manuais_{data_hoje}.txt"
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)

    with open(caminho_completo, "w", encoding="utf-8") as arquivo:
        arquivo.write(f"--- RELATÓRIO DE CNDs MANUAIS PENDENTES ({data_hoje}) ---\n\n")
        arquivo.write("As seguintes certidões não possuem automação e devem ser emitidas pela equipe:\n\n")

        # Escreve item por item da lista no arquivo de texto
        for pendencia in lista_pendencias:
            arquivo.write(f"- {pendencia}\n")

        arquivo.write("\n--- FIM DO RELATÓRIO ---")

    print(f"\n📄 Relatório de pendências gerado com sucesso em:\n   {caminho_completo}")
    return caminho_completo

def obter_ultimo_relatorio(pasta_destino=None):
    """
    Retorna (nome_arquivo, conteudo) do relatório de texto mais recente na pasta relatorios/.
    """
    if pasta_destino is None:
        pasta_destino = PASTA_RELATORIOS
    if not os.path.exists(pasta_destino):
        return None, "Pasta de relatórios não encontrada."
    
    arquivos = glob.glob(os.path.join(pasta_destino, "*.txt"))
    if not arquivos:
        return None, "Nenhum relatório encontrado na pasta relatorios/."
    
    ultimo = max(arquivos, key=os.path.getmtime)
    nome = os.path.basename(ultimo)
    try:
        with open(ultimo, "r", encoding="utf-8", errors="replace") as f:
            conteudo = f.read()
        return nome, conteudo
    except Exception as e:
        return nome, f"Erro ao ler relatório {nome}: {e}"

class EscritorTerminal:
    def __init__(self, fila):
        self.fila = fila

    def write(self, texto):
        if texto:
            self.fila.put(texto)

    def flush(self):
        pass

class InterfaceAutomacao:
    def ao_clicar_vincular_matriz(self):
        if not hasattr(self, 'cnpj_atual_em_edicao') or not self.cnpj_atual_em_edicao:
            self.lbl_feedback_edicao.config(text="⚠️ Carregue um CNPJ primeiro antes de vincular a matriz.", fg="#facc15")
            return
            
        matriz_digitada = simpledialog.askstring(
            "Vincular Matriz",
            f"Qual é o CNPJ da MATRIZ para a filial {self.cnpj_atual_em_edicao}?\n(Deixe em branco para remover o vínculo)",
            parent=self.janela
        )
        
        # Se o usuário clicou em Cancelar, o retorno é None
        if matriz_digitada is not None:
            matriz_limpa = "".join(re.findall(r'\d+', matriz_digitada))
            
            if matriz_limpa == "":
                self.lbl_cnpj_matriz_atual.config(text="Nenhuma", fg="#94a3b8")
                self.lbl_feedback_edicao.config(text="Vínculo removido. Clique em 'Salvar Alterações'.", fg="#38bdf8")
                self.matriz_em_edicao = None
                
            elif len(matriz_limpa) == 14:
                self.lbl_cnpj_matriz_atual.config(text=matriz_limpa, fg="#38bdf8")
                self.lbl_feedback_edicao.config(text="Matriz vinculada! Clique em 'Salvar Alterações'.", fg="#38bdf8")
                self.matriz_em_edicao = matriz_limpa
                
            else:
                messagebox.showerror(
                    "CNPJ Inválido", 
                    "O CNPJ da matriz deve conter exatamente 14 números.", 
                    parent=self.janela
                )
    def __init__(self):
        self.janela = tk.Tk()
        self.janela.title("Coleta de Certidoes")
        self.janela.geometry("1000x720")
        self.janela.minsize(900, 600)
        self.janela.configure(bg="#002b36")
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

        # Centraliza a janela na tela
        largura = 1000
        altura = 720
        largura_tela = self.janela.winfo_screenwidth()
        altura_tela = self.janela.winfo_screenheight()
        pos_x = max(0, (largura_tela - largura) // 2)
        pos_y = max(0, (altura_tela - altura) // 2)
        self.janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

        self.fila_terminal = queue.Queue()
        self.fila_captcha = queue.Queue()
        self.thread_automacao = None
        self.saida_original = sys.stdout
        self.resposta_captcha_atual = None
        self.coleta_foi_cancelada = False
        self.tag_cnd_ativa = "normal"
        self.tags_configuradas = set()

        self.cidades_disponiveis = {}
        self.cidades_selecionadas = set()
        self.linhas_painel_conferencia = []

        # TELA DE CARREGAMENTO IMEDIATA (A janela abre instantaneamente em < 50ms)
        self.tela_splash = tk.Frame(self.janela, bg="#002b36")
        self.tela_splash.place(relx=0, rely=0, relwidth=1, relheight=1)

        frame_splash_centro = tk.Frame(self.tela_splash, bg="#002b36")
        frame_splash_centro.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame_splash_centro,
            text="⚡ Coleta de Certidões",
            font=("Segoe UI", 22, "bold"),
            bg="#002b36",
            fg="#38bdf8"
        ).pack(pady=(0, 10))

        self.lbl_splash_status = tk.Label(
            frame_splash_centro,
            text="Iniciando sistema e carregando interface...",
            font=("Segoe UI", 11),
            bg="#002b36",
            fg="#839496"
        )
        self.lbl_splash_status.pack(pady=(0, 15))

        self.canvas_splash = tk.Canvas(frame_splash_centro, width=320, height=8, bg="#073642", highlightthickness=0)
        self.canvas_splash.pack()
        self.canvas_splash.create_rectangle(0, 0, 120, 8, fill="#38bdf8", outline="")

        # Força o Windows a renderizar a janela imediatamente para o usuário
        self.janela.update()

        # Constrói a interface completa em seguida
        self.janela.after(60, self.construir_interface)

    def construir_interface(self):
        # Estilo moderno escuro das abas (Solarized Dark)
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except Exception:
            pass
        estilo.configure("TNotebook", background="#002b36", borderwidth=0)
        estilo.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=[18, 9],
            background="#073642",
            foreground="#839496",
            borderwidth=0
        )
        estilo.map(
            "TNotebook.Tab",
            background=[("selected", "#002b36"), ("active", "#0d4350")],
            foreground=[("selected", "#38bdf8"), ("active", "#ffffff")]
        )

        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # ABA 1: COLETA DE CERTIDÕES
        # -------------------------------------------------------------
        self.aba_coleta = tk.Frame(self.notebook, bg="#002b36")
        self.notebook.add(self.aba_coleta, text="  📥 Coleta de Certidões  ")

        painel_config = tk.Frame(self.aba_coleta, bg="#002b36")
        painel_config.pack(fill="x", padx=14, pady=10)

        tk.Label(
            painel_config,
            text="CNPJs (um por linha):",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#e2e8f0"
        ).pack(anchor="w")

        # Campo de CNPJs inicializado vazio conforme solicitado
        self.campo_cnpjs = tk.Text(
            painel_config,
            height=4,
            width=40,
            font=("Consolas", 10),
            bg="#073642",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0e4957",
            highlightcolor="#38bdf8"
        )
        self.campo_cnpjs.pack(fill="x", pady=(4, 8))

        tk.Label(
            painel_config,
            text="Tipos de CND a coletar:",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#e2e8f0"
        ).pack(anchor="w", pady=(4, 2))
        
        self.vars_cnd = {}
        # Ordem solicitada: Federal, estadual, municipal, trabalhista, comprasnet, fgts, agehab (em MAIÚSCULAS)
        self.tipos_cnd_opcoes = [
            "FEDERAL",
            "ESTADUAL",
            "MUNICIPAL",
            "TRABALHISTA",
            "COMPRASNET",
            "FGTS",
            "AGEHAB",
        ]
        
        painel_checkboxes = tk.Frame(painel_config, bg="#002b36")
        painel_checkboxes.pack(fill="x", pady=(2, 8))


        for tipo in self.tipos_cnd_opcoes:
            var = tk.BooleanVar(value=True)
            self.vars_cnd[tipo] = var
            tk.Checkbutton(
                painel_checkboxes,
                text=tipo,
                variable=var,
                command=self.ao_alterar_check_cnd_individual,
                bg="#002b36",
                fg="#e2e8f0",
                activebackground="#002b36",
                activeforeground="#38bdf8",
                selectcolor="#073642",
                font=("Segoe UI", 9, "bold")
            ).pack(side="left", padx=6)

        # Caixinha mais afastada para marcar ou desmarcar todas as opções
        self.var_marcar_todas = tk.BooleanVar(value=True)
        self.check_marcar_todas = tk.Checkbutton(
            painel_checkboxes,
            text="MARCAR TODAS",
            variable=self.var_marcar_todas,
            command=self.ao_alternar_todas_cnds,
            bg="#002b36",
            fg="#38bdf8",
            activebackground="#002b36",
            activeforeground="#ffffff",
            selectcolor="#073642",
            font=("Segoe UI", 9, "bold")
        )
        self.check_marcar_todas.pack(side="left", padx=(28, 6))

        painel_botoes = tk.Frame(painel_config, bg="#002b36")
        painel_botoes.pack(fill="x", pady=(4, 0))
        
        self.botao_iniciar = tk.Button(
            painel_botoes,
            text="▶ Iniciar coleta",
            command=self.iniciar_coleta,
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=7,
        )
        self.botao_iniciar.pack(side="left", padx=(0, 8))
        
        self.botao_cancelar = tk.Button(
            painel_botoes,
            text="✖ Cancelar",
            command=self.cancelar_coleta,
            bg="#ef4444",
            fg="#ffffff",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=7,
            state="disabled",
        )
        self.botao_cancelar.pack(side="left", padx=6)

        self.terminal = scrolledtext.ScrolledText(
            self.aba_coleta,
            state="disabled",
            bg="#001e26",
            fg="#e2e8f0",
            insertbackground="#38bdf8",
            wrap="word",
            font=("Consolas", 9),
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#0e4957"
        )
        self.terminal.pack(fill="both", expand=True, padx=14, pady=(10, 10))
        self.configurar_cores_terminal()

        # Crie e posicione a sua label de assinatura no rodapé
        self.label_assinatura = tk.Label(
            self.aba_coleta, # Certifique-se de que está no mesmo frame
            text="Desenvolvido por: [Felipe Andrade Gabrioti/AGEHAB] © 2026",
            bg="#001e26", 
            fg="white"
        )
        self.label_assinatura.pack(side="bottom", pady=5) # Fixa na parte inferior

        # O terminal continua expandindo, mas o Tkinter agora sabe 
        # que precisa respeitar o espaço da label abaixo dele.
        self.terminal.pack(fill="both", expand=True, padx=14, pady=(10, 5))

        self.painel_captcha = tk.Frame(
            self.aba_coleta,
            bg="#073642",
            highlightthickness=1,
            highlightbackground="#0e4957"
        )
        tk.Label(
            self.painel_captcha,
            text="CAPTCHA do navegador:",
            bg="#073642",
            fg="#e2e8f0",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(10, 4), pady=8)
        self.campo_captcha = tk.Entry(
            self.painel_captcha,
            width=16,
            font=("Consolas", 10),
            bg="#002b36",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0e4957"
        )
        self.campo_captcha.pack(side="left", padx=4, pady=8)
        self.botao_captcha = tk.Button(
            self.painel_captcha,
            text="Enviar CAPTCHA",
            command=self.enviar_captcha,
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4
        )
        self.botao_captcha.pack(side="left", padx=(6, 8), pady=8)
        self.status_captcha = tk.Label(self.painel_captcha, text="", bg="#073642", fg="#e2e8f0")
        self.status_captcha.pack(side="left", padx=4, pady=8)

        # -------------------------------------------------------------
        # ABA 2: CADASTRAR NOVO CNPJ (TUDO NA MESMA JANELA!)
        # -------------------------------------------------------------
        self.aba_cadastro = tk.Frame(self.notebook, bg="#002b36")
        self.notebook.add(self.aba_cadastro, text="  ➕ Cadastrar Novo CNPJ  ")

        self.construir_aba_cadastro()

        # Carrega cidades e construtoras da rede
        self.carregar_cidades()
        self.carregar_construtoras()

        # -------------------------------------------------------------
        # ABA 3: ATUALIZAR CADASTRO (NOVA ABA!)
        # -------------------------------------------------------------
        self.aba_atualizar = tk.Frame(self.notebook, bg="#002b36")
        self.notebook.add(self.aba_atualizar, text="  🔄 Atualizar Cadastro  ")

        self.construir_aba_atualizar()
        # -------------------------------------------------------------
        # ABA 4: PAINEL DE CONFERÊNCIA (NOVA ABA HÍBRIDA)
        # -------------------------------------------------------------
        self.aba_conferencia = tk.Frame(self.notebook, bg="#002b36")
        self.notebook.add(self.aba_conferencia, text="  📊 Painel de Conferência  ")

        # --- NOVA BARRA DE BUSCA ---
        frame_busca_conf = tk.Frame(self.aba_conferencia, bg="#002b36")
        frame_busca_conf.pack(fill="x", padx=14, pady=(14, 0))
        
        tk.Label(
            frame_busca_conf, text="🔍 Buscar (CNPJ ou Nome):", 
            bg="#002b36", fg="#38bdf8", font=("Segoe UI", 9, "bold")
        ).pack(side="left")
        
        self.campo_busca_conf = tk.Entry(
            frame_busca_conf, width=40, font=("Segoe UI", 10),
            bg="#073642", fg="#f8fafc", insertbackground="#38bdf8", relief="flat"
        )
        self.campo_busca_conf.pack(side="left", padx=10)
        # Aciona o filtro toda vez que uma tecla for solta
        self.campo_busca_conf.bind("<KeyRelease>", lambda event: self.atualizar_painel_conferencia(self.campo_busca_conf.get()))

        # Configurando a Tabela (Treeview)
        colunas = ("Empresa", "Certidão", "Data Validade", "Status Original", "Observações")
        self.tabela_conferencia = ttk.Treeview(self.aba_conferencia, columns=colunas, show="headings", height=20)

        # Cabeçalhos e Larguras
        for col in colunas:
            self.tabela_conferencia.heading(col, text=col)
            self.tabela_conferencia.column(col, width=150, anchor="center")
        self.tabela_conferencia.column("Observações", width=350, anchor="w") # Observação precisa ser mais larga

        # Barra de rolagem
        scroll_tabela = ttk.Scrollbar(self.aba_conferencia, orient="vertical", command=self.tabela_conferencia.yview)
        self.tabela_conferencia.configure(yscroll=scroll_tabela.set)

        self.tabela_conferencia.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        scroll_tabela.pack(side="right", fill="y", pady=10)

        # Botão para exportar para Excel
        btn_exportar = tk.Button(
            self.aba_conferencia,
            text="📥 Exportar Painel para Excel",
            command=self.exportar_excel,
            bg="#10b981", fg="#ffffff", font=("Segoe UI", 10, "bold"), padx=15, pady=5, cursor="hand2"
        )
        btn_exportar.pack(side="bottom", pady=10)
        
        # Cores das linhas para bater com o padrão da sua imagem
        # Configurando as tags de cores da tabela
        self.tabela_conferencia.tag_configure('cabecalho', background='#d1d5db', foreground='#0f172a', font=("Segoe UI", 9, "bold"))
        self.tabela_conferencia.tag_configure('negativa', background='#86efac', foreground='#064e3b') # Verde
        self.tabela_conferencia.tag_configure('atencao', background='#fde047', foreground='#713f12') # Amarelo
        self.tabela_conferencia.tag_configure('erro', background='#fca5a5', foreground='#7f1d1d') # Vermelho
        self.tabela_conferencia.tag_configure('pendente', background='#f8fafc', foreground='#64748b') # Branco

        # Remove tela de carregamento suavemente
        self.tela_splash.destroy()

        # Inicia loop de atualização do terminal
        self.janela.after(100, self.atualizar_interface)

    def atualizar_painel_conferencia(self, filtro=""):
        """Constrói o painel criando as Linhas Mestres e as Certidões Esperadas"""
        # 1. Limpa a tabela
        for item in self.tabela_conferencia.get_children():
            self.tabela_conferencia.delete(item)
            
        termo = filtro.strip().lower()
        
        # 2. Puxa os bancos de dados
        mapa_municipal = gerenciador_cnpj.obter_mapa_municipal()
        historico = gerenciador_historico.carregar_historico()
        
        # Certidões padrão que toda empresa tem
        certidoes_padrao = ["Federal", "Estadual", "Trabalhista", "FGTS", "Comprasnet", "AGEHAB"]

        # 3. Monta a árvore para cada empresa
        for cnpj, cidades_config in mapa_municipal.items():
            nome_empresa = gerenciador_cnpj.obter_nome_empreendimento(cnpj) or "Empresa Não Cadastrada"
            matriz = gerenciador_cnpj.obter_matriz_do_cnpj(cnpj)
            
            # Se tiver pesquisa, verifica se o CNPJ ou Nome batem. Se não, pula para o próximo.
            if termo and termo not in cnpj and termo not in nome_empresa.lower():
                continue
            
            # --- LINHA MESTRE (CABEÇALHO DA EMPRESA) ---
            if matriz:
                texto_cabecalho = f"🏢 CERTIDÕES {nome_empresa} (CNPJ: {cnpj} | Matriz: {matriz})"
            else:
                texto_cabecalho = f"🏢 CERTIDÕES {nome_empresa} (CNPJ: {cnpj})"
                
            # Inserimos uma linha onde apenas a coluna "Empresa" tem texto, o resto fica vazio.
            # A tag 'cabecalho' deixará a linha cinza/destacada
            self.tabela_conferencia.insert(
                "", "end", 
                values=(texto_cabecalho, "", "", "", ""), 
                tags=("cabecalho",)
            )
            
            # --- DESCOBRE TODAS AS CNDS DESSA EMPRESA ---
            certidoes_esperadas = certidoes_padrao.copy()
            for config in cidades_config:
                # Adiciona as cidades automatizadas na lista de esperadas
                if config.get("automatizado"):
                    certidoes_esperadas.append(config.get("cidade"))
                    
            # --- PREENCHE OS ESPAÇOS DAS CNDS ---
            hist_empresa = historico.get(cnpj, {})
            
            for certidao in certidoes_esperadas:
                # Busca se já tem resultado no JSON, se não, preenche como vazio/Pendente
                dados_cnd = hist_empresa.get(certidao, {"validade": "", "status": "Pendente", "observacao": ""})
                
                val = dados_cnd["validade"]
                stat = dados_cnd["status"]
                obs = dados_cnd["observacao"]
                
                # Regras de Cor para as tags (Igual a sua planilha)
                tag = "pendente" # Branco ou cinza clarinho
                if "Falha" in stat or "Bloqueio" in obs or "Vencida" in stat:
                    tag = "erro" # Vermelho
                elif "Efeito" in stat:
                    tag = "atencao" # Amarelo
                elif "Positiva" in stat:
                    tag = "erro"
                elif "Negativa" in stat:
                    tag = "negativa" # Verde
                    
                # Insere a certidão embaixo do cabeçalho
                self.tabela_conferencia.insert(
                    "", "end", 
                    values=("", certidao, val, stat, obs), 
                    tags=(tag,)
                )

    def construir_aba_cadastro(self):
        conteiner_cadastro = tk.Frame(self.aba_cadastro, bg="#002b36")
        conteiner_cadastro.pack(fill="both", expand=True, padx=20, pady=12)

        # Cabeçalho
        tk.Label(
            conteiner_cadastro,
            text="Cadastro de Empreendimento, Pastas e Cidades",
            font=("Segoe UI", 15, "bold"),
            bg="#002b36",
            fg="#38bdf8"
        ).pack(anchor="w")

        tk.Label(
            conteiner_cadastro,
            text="Cria a pasta na rede (N:\\16. CERTIDÕES\\1. Empresas), cadastra o CNPJ e vincula as cidades para a automação.",
            font=("Segoe UI", 9),
            bg="#002b36",
            fg="#839496"
        ).pack(anchor="w", pady=(2, 10))

        # -------------------------------------------------------------
        # 1. SEÇÃO CONSTRUTORA E GESTÃO DE PASTAS DE REDE
        # -------------------------------------------------------------
        frame_construtora_card = tk.LabelFrame(
            conteiner_cadastro,
            text=" 🏢 Construtora e Pastas de Rede ",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#38bdf8",
            padx=10,
            pady=8,
            relief="groove",
            highlightthickness=1,
            highlightbackground="#073642"
        )
        frame_construtora_card.pack(fill="x", pady=(0, 10))

        # Linha 1: Seleção e criação de Construtora
        row1_const = tk.Frame(frame_construtora_card, bg="#002b36")
        row1_const.pack(fill="x", pady=(0, 6))

        tk.Label(
            row1_const,
            text="Construtora:",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#e2e8f0"
        ).pack(side="left", padx=(0, 6))

        self.combo_construtora = ttk.Combobox(
            row1_const,
            state="readonly",
            width=26,
            font=("Segoe UI", 9)
        )
        self.combo_construtora.pack(side="left", padx=(0, 8))
        self.combo_construtora.bind("<<ComboboxSelected>>", self.ao_selecionar_construtora)

        btn_nova_const = tk.Button(
            row1_const,
            text="➕ Nova Construtora",
            command=self.ao_clicar_nova_construtora,
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2
        )
        btn_nova_const.pack(side="left", padx=(0, 6))

        btn_abrir_const = tk.Button(
            row1_const,
            text="📂 Abrir Pasta",
            command=self.ao_abrir_pasta_construtora,
            bg="#073642",
            fg="#38bdf8",
            activebackground="#0e4957",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2
        )
        btn_abrir_const.pack(side="left", padx=(0, 6))

        btn_excluir_const = tk.Button(
            row1_const,
            text="🗑️ Excluir Construtora",
            command=self.ao_clicar_excluir_construtora,
            bg="#7f1d1d",
            fg="#fecaca",
            activebackground="#991b1b",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2
        )
        btn_excluir_const.pack(side="left")

        # Linha 2: Visualizar empreendimentos existentes nessa construtora
        row2_const = tk.Frame(frame_construtora_card, bg="#002b36")
        row2_const.pack(fill="x")

        tk.Label(
            row2_const,
            text="Pastas existentes:",
            font=("Segoe UI", 9),
            bg="#002b36",
            fg="#94a3b8"
        ).pack(side="left", padx=(0, 6))

        self.combo_empreendimentos_existentes = ttk.Combobox(
            row2_const,
            state="readonly",
            width=42,
            font=("Segoe UI", 9)
        )
        self.combo_empreendimentos_existentes.pack(side="left", padx=(0, 8))

        btn_abrir_emp = tk.Button(
            row2_const,
            text="📂 Abrir no Explorer",
            command=self.ao_abrir_pasta_empreendimento,
            bg="#073642",
            fg="#94a3b8",
            activebackground="#0e4957",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2
        )
        btn_abrir_emp.pack(side="left", padx=(0, 6))

        btn_excluir_emp = tk.Button(
            row2_const,
            text="🗑️ Excluir Pasta",
            command=self.ao_clicar_excluir_empreendimento,
            bg="#450a0a",
            fg="#f87171",
            activebackground="#7f1d1d",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2
        )
        btn_excluir_emp.pack(side="left")
    
        
        

        # -------------------------------------------------------------
        # 2. SEÇÃO NOVO EMPREENDIMENTO E CNPJ
        # -------------------------------------------------------------
        frame_dados_novo = tk.Frame(conteiner_cadastro, bg="#002b36")
        frame_dados_novo.pack(fill="x", pady=(0, 10))

        # Coluna Esquerda: Nome do Empreendimento
        col_nome = tk.Frame(frame_dados_novo, bg="#002b36")
        col_nome.pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Label(
            col_nome,
            text="Nome do Empreendimento (ex: SPE RESERVA 1 LTDA):",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#e2e8f0"
        ).pack(anchor="w")

        self.campo_nome_empreendimento = tk.Entry(
            col_nome,
            font=("Segoe UI", 10),
            bg="#073642",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0e4957",
            highlightcolor="#38bdf8"
        )
        self.campo_nome_empreendimento.pack(fill="x", pady=(3, 0))

        # Coluna Direita: CNPJ
        col_cnpj = tk.Frame(frame_dados_novo, bg="#002b36")
        col_cnpj.pack(side="left", fill="x", expand=False)

        tk.Label(
            col_cnpj,
            text="CNPJ (14 dígitos - apenas números):",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#e2e8f0"
        ).pack(anchor="w")

        self.campo_cnpj_novo = tk.Entry(
            col_cnpj,
            width=24,
            font=("Consolas", 11),
            bg="#073642",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0e4957",
            highlightcolor="#38bdf8"
        )
        self.campo_cnpj_novo.pack(anchor="w", pady=(3, 0))

        # -------------------------------------------------------------
        # 3. SEÇÃO SELEÇÃO DE MUNICÍPIOS
        # -------------------------------------------------------------
        frame_cidades_header = tk.Frame(conteiner_cadastro, bg="#002b36")
        frame_cidades_header.pack(fill="x", pady=(0, 4))

        tk.Label(
            frame_cidades_header,
            text="Municípios correspondentes para a automação municipal:",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#e2e8f0"
        ).pack(side="left")

        self.lbl_contador_cidades = tk.Label(
            frame_cidades_header,
            text="Selecionadas: 0",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#38bdf8"
        )
        self.lbl_contador_cidades.pack(side="right")

        # Barra de busca de cidades
        frame_busca = tk.Frame(conteiner_cadastro, bg="#002b36")
        frame_busca.pack(fill="x", pady=(0, 4))

        tk.Label(frame_busca, text="🔍 Filtrar:", font=("Segoe UI", 9), bg="#002b36", fg="#839496").pack(side="left", padx=(0, 6))
        self.campo_busca_cidade = tk.Entry(
            frame_busca,
            width=24,
            font=("Segoe UI", 9),
            bg="#073642",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0e4957",
            highlightcolor="#38bdf8"
        )
        self.campo_busca_cidade.pack(side="left")
        self.campo_busca_cidade.bind("<KeyRelease>", self.ao_filtrar_cidades)

        btn_sel_todas = tk.Button(
            frame_busca,
            text="Marcar todas visíveis",
            command=self.selecionar_todas_visiveis,
            font=("Segoe UI", 8),
            bg="#073642",
            fg="#e2e8f0",
            activebackground="#0e4957",
            activeforeground="#ffffff",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2"
        )
        btn_sel_todas.pack(side="left", padx=6)

        btn_limpar_sel = tk.Button(
            frame_busca,
            text="Desmarcar todas",
            command=self.limpar_selecao_cidades,
            font=("Segoe UI", 8),
            bg="#073642",
            fg="#e2e8f0",
            activebackground="#0e4957",
            activeforeground="#ffffff",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2"
        )
        btn_limpar_sel.pack(side="left")

        # Listbox de Cidades com Scrollbar
        frame_lista = tk.Frame(
            conteiner_cadastro,
            bg="#073642",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0e4957"
        )
        frame_lista.pack(fill="both", expand=True, pady=(0, 8))

        scroll_cidades = tk.Scrollbar(frame_lista)
        scroll_cidades.pack(side="right", fill="y")

        self.listbox_cidades = tk.Listbox(
            frame_lista,
            selectmode="multiple",
            yscrollcommand=scroll_cidades.set,
            font=("Segoe UI", 9),
            bg="#073642",
            fg="#f8fafc",
            selectbackground="#268bd2",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            activestyle="none",
            height=6
        )
        self.listbox_cidades.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scroll_cidades.config(command=self.listbox_cidades.yview)
        self.listbox_cidades.bind("<<ListboxSelect>>", self.ao_selecionar_cidade)

        # Mensagem de status inline
        self.lbl_status_cadastro = tk.Label(
            conteiner_cadastro,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#10b981",
            wraplength=800
        )
        self.lbl_status_cadastro.pack(fill="x", pady=(0, 6))

        # Botões de Ação do Cadastro
        frame_acoes_cadastro = tk.Frame(conteiner_cadastro, bg="#002b36")
        frame_acoes_cadastro.pack(fill="x")

        self.btn_salvar_cadastro = tk.Button(
            frame_acoes_cadastro,
            text="✔ Salvar Cadastro e Criar Pasta na Rede",
            command=self.confirmar_cadastro,
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6
        )
        self.btn_salvar_cadastro.pack(side="left", padx=(0, 8))

        btn_limpar_campos = tk.Button(
            frame_acoes_cadastro,
            text="Limpar Formulário",
            command=self.limpar_formulario_cadastro,
            bg="#334155",
            fg="#e2e8f0",
            activebackground="#475569",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6
        )
        btn_limpar_campos.pack(side="left", padx=6)

        btn_voltar = tk.Button(
            frame_acoes_cadastro,
            text="← Voltar para Coleta",
            command=self.ir_para_coleta,
            bg="#073642",
            fg="#38bdf8",
            activebackground="#0e4957",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6
        )
        btn_voltar.pack(side="left", padx=6)

    def carregar_construtoras(self):
        try:
            construtoras = gerenciador_pastas.listar_construtoras()
            if hasattr(self, 'combo_construtora'):
                self.combo_construtora['values'] = construtoras
                if construtoras:
                    atual = self.combo_construtora.get()
                    if atual in construtoras:
                        self.combo_construtora.set(atual)
                    else:
                        self.combo_construtora.current(0)
                    self.ao_selecionar_construtora()
                else:
                    self.combo_construtora.set("")
                    self.combo_empreendimentos_existentes['values'] = []
                    self.combo_empreendimentos_existentes.set("")
        except Exception as e:
            print(f"⚠️ Erro ao listar construtoras na rede: {e}")

    def ao_selecionar_construtora(self, event=None):
        if not hasattr(self, 'combo_construtora') or not hasattr(self, 'combo_empreendimentos_existentes'):
            return
        construtora = self.combo_construtora.get().strip()
        if not construtora:
            self.combo_empreendimentos_existentes['values'] = []
            self.combo_empreendimentos_existentes.set("")
            return

        try:
            empreendimentos = gerenciador_pastas.listar_empreendimentos(construtora)
            self.combo_empreendimentos_existentes['values'] = empreendimentos
            if empreendimentos:
                self.combo_empreendimentos_existentes.current(0)
            else:
                self.combo_empreendimentos_existentes.set("(Nenhuma pasta nesta construtora)")
        except Exception as e:
            print(f"⚠️ Erro ao listar empreendimentos de {construtora}: {e}")

    def ao_clicar_nova_construtora(self):
        nome = simpledialog.askstring(
            "Nova Construtora",
            "Digite o nome da nova Construtora (pasta principal):",
            parent=self.janela
        )
        if not nome or not nome.strip():
            return

        try:
            caminho = gerenciador_pastas.criar_pasta_construtora(nome.strip())
            self.carregar_construtoras()
            nome_sanitizado = os.path.basename(caminho)
            self.combo_construtora.set(nome_sanitizado)
            self.ao_selecionar_construtora()
            self.lbl_status_cadastro.config(
                text=f"✅ Construtora '{nome_sanitizado}' criada com sucesso na rede!",
                fg="#10b981"
            )
        except Exception as e:
            messagebox.showerror("Erro ao criar construtora", str(e), parent=self.janela)

    def ao_clicar_excluir_construtora(self):
        construtora = self.combo_construtora.get().strip()
        if not construtora:
            messagebox.showwarning("Aviso", "Selecione uma construtora para excluir.", parent=self.janela)
            return

        try:
            raiz = gerenciador_pastas.obter_pasta_raiz_empresas()
            caminho = os.path.join(raiz, construtora)
            total_arq, total_sub, amostras = gerenciador_pastas.contar_conteudo_pasta(caminho)

            msg = f"Atenção: A construtora '{construtora}' contém {total_sub} pasta(s) de empreendimento e {total_arq} arquivo(s)."
            if total_arq > 0:
                msg += f"\n\nArquivos encontrados (amostra):\n- " + "\n- ".join(amostras)
            msg += "\n\nDeseja REALMENTE excluir esta construtora e TODO o seu conteúdo permanentemente da rede?"

            confirma = messagebox.askyesno("Confirmar Exclusão de Construtora", msg, icon="warning", parent=self.janela)
            if not confirma:
                return

            gerenciador_pastas.excluir_pasta_segura(caminho)
            self.carregar_construtoras()
            self.lbl_status_cadastro.config(
                text=f"🗑️ Construtora '{construtora}' excluída da rede.",
                fg="#f59e0b"
            )
        except Exception as e:
            messagebox.showerror("Erro ao excluir", str(e), parent=self.janela)

    def ao_abrir_pasta_construtora(self):
        construtora = self.combo_construtora.get().strip()
        if not construtora:
            return
        try:
            raiz = gerenciador_pastas.obter_pasta_raiz_empresas()
            caminho = os.path.join(raiz, construtora)
            os.startfile(caminho)
        except Exception as e:
            messagebox.showerror("Erro ao abrir pasta", str(e), parent=self.janela)

    def ao_abrir_pasta_empreendimento(self):
        construtora = self.combo_construtora.get().strip()
        emp = self.combo_empreendimentos_existentes.get().strip()
        if not construtora or not emp or emp.startswith("("):
            return
        try:
            raiz = gerenciador_pastas.obter_pasta_raiz_empresas()
            caminho = os.path.join(raiz, construtora, emp)
            os.startfile(caminho)
        except Exception as e:
            messagebox.showerror("Erro ao abrir pasta", str(e), parent=self.janela)

    def ao_clicar_excluir_empreendimento(self):
        construtora = self.combo_construtora.get().strip()
        emp = self.combo_empreendimentos_existentes.get().strip()
        if not construtora or not emp or emp.startswith("("):
            messagebox.showwarning("Aviso", "Selecione uma pasta de empreendimento para excluir.", parent=self.janela)
            return

        try:
            raiz = gerenciador_pastas.obter_pasta_raiz_empresas()
            caminho = os.path.join(raiz, construtora, emp)
            total_arq, total_sub, amostras = gerenciador_pastas.contar_conteudo_pasta(caminho)

            msg = f"Atenção: A pasta do empreendimento '{emp}' contém {total_arq} arquivo(s) (certidões/PDFs)."
            if total_arq > 0:
                msg += f"\n\nArquivos encontrados:\n- " + "\n- ".join(amostras)
            msg += "\n\nDeseja REALMENTE excluir permanentemente esta pasta da rede?"

            confirma = messagebox.askyesno("Confirmar Exclusão de Empreendimento", msg, icon="warning", parent=self.janela)
            if not confirma:
                return

            gerenciador_pastas.excluir_pasta_segura(caminho)

            # Verifica se essa pasta tinha CNPJ e se ele está em dados.py
            cnpjs_encontrados = re.findall(r'\d{14}', emp)
            if cnpjs_encontrados:
                cnpj_alvo = cnpjs_encontrados[0]
                if gerenciador_cnpj.cnpj_ja_existe(cnpj_alvo):
                    remover_dados = messagebox.askyesno(
                        "Remover Cadastro",
                        f"O CNPJ {cnpj_alvo} associado a esta pasta também está cadastrado no sistema.\n\nDeseja removê-lo do robô de certidões também?",
                        parent=self.janela
                    )
                    if remover_dados:
                        gerenciador_cnpj.remover_cnpj_de_dados(cnpj_alvo)
                        global mapa_municipal
                        mapa_municipal = gerenciador_cnpj.obter_mapa_municipal()
                        if hasattr(self, 'combo_atualizar_cnpj'):
                            self.cnpjs_cadastrados = gerenciador_cnpj.listar_cnpjs_cadastrados()
                            self.combo_atualizar_cnpj['values'] = self.cnpjs_cadastrados

            self.ao_selecionar_construtora()
            self.lbl_status_cadastro.config(
                text=f"🗑️ Pasta '{emp}' excluída da rede com sucesso.",
                fg="#f59e0b"
            )
        except Exception as e:
            messagebox.showerror("Erro ao excluir", str(e), parent=self.janela)

    def carregar_cidades(self):
        try:
            self.cidades_disponiveis = gerenciador_cnpj.listar_cidades_disponiveis()
        except Exception as e:
            self.cidades_disponiveis = {}
            print(f"Erro ao carregar cidades: {e}")
        self.atualizar_listbox_cidades()

    def atualizar_listbox_cidades(self, filtro=""):
        if not hasattr(self, 'listbox_cidades'):
            return
        self.listbox_cidades.delete(0, "end")
        termo = filtro.strip().lower()
        self.cidades_visiveis = []
        for cidade_nome in sorted(self.cidades_disponiveis.keys()):
            if not termo or termo in cidade_nome.lower():
                self.cidades_visiveis.append(cidade_nome)
                self.listbox_cidades.insert("end", cidade_nome)
                if cidade_nome in self.cidades_selecionadas:
                    idx = self.listbox_cidades.size() - 1
                    self.listbox_cidades.selection_set(idx)
        self.lbl_contador_cidades.config(text=f"Selecionadas: {len(self.cidades_selecionadas)}")

    def ao_filtrar_cidades(self, event=None):
        self.sincronizar_selecao_visivel()
        filtro = self.campo_busca_cidade.get()
        self.atualizar_listbox_cidades(filtro)

    def sincronizar_selecao_visivel(self):
        indices = self.listbox_cidades.curselection()
        selecionados_visiveis = {self.listbox_cidades.get(i) for i in indices}
        if hasattr(self, 'cidades_visiveis'):
            for c in self.cidades_visiveis:
                if c in self.cidades_selecionadas and c not in selecionados_visiveis:
                    self.cidades_selecionadas.remove(c)
        self.cidades_selecionadas.update(selecionados_visiveis)
        self.lbl_contador_cidades.config(text=f"Selecionadas: {len(self.cidades_selecionadas)}")

    def ao_selecionar_cidade(self, event=None):
        self.sincronizar_selecao_visivel()

    def selecionar_todas_visiveis(self):
        for i in range(self.listbox_cidades.size()):
            self.listbox_cidades.selection_set(i)
        self.sincronizar_selecao_visivel()

    def limpar_selecao_cidades(self):
        self.listbox_cidades.selection_clear(0, "end")
        self.cidades_selecionadas.clear()
        self.lbl_contador_cidades.config(text="Selecionadas: 0")

    def limpar_formulario_cadastro(self):
        if hasattr(self, 'campo_nome_empreendimento'):
            self.campo_nome_empreendimento.delete(0, "end")
        self.campo_cnpj_novo.delete(0, "end")
        self.campo_busca_cidade.delete(0, "end")
        self.limpar_selecao_cidades()
        self.atualizar_listbox_cidades()
        self.lbl_status_cadastro.config(text="")

    def ir_para_cadastro(self):
        self.notebook.select(self.aba_cadastro)
        if hasattr(self, 'campo_nome_empreendimento'):
            self.campo_nome_empreendimento.focus_set()
        else:
            self.campo_cnpj_novo.focus_set()

    def ir_para_coleta(self):
        self.notebook.select(self.aba_coleta)

    def ao_alternar_todas_cnds(self):
        estado = self.var_marcar_todas.get()
        for var in self.vars_cnd.values():
            var.set(estado)

    def ao_alterar_check_cnd_individual(self):
        todos_marcados = all(var.get() for var in self.vars_cnd.values())
        self.var_marcar_todas.set(todos_marcados)

    def confirmar_cadastro(self):
        self.sincronizar_selecao_visivel()
        construtora = self.combo_construtora.get().strip()
        nome_emp = self.campo_nome_empreendimento.get().strip()
        cnpj_novo = self.campo_cnpj_novo.get().strip()

        # Validação da Construtora
        if not construtora:
            self.lbl_status_cadastro.config(
                text="⚠️ Selecione uma Construtora existente ou clique em '➕ Nova Construtora'.",
                fg="#ef4444"
            )
            return

        # Validação do Nome do Empreendimento
        if not nome_emp:
            self.lbl_status_cadastro.config(
                text="⚠️ Informe o Nome do Empreendimento (ex: SPE RESERVA 1 LTDA).",
                fg="#ef4444"
            )
            return

        # Validação do CNPJ
        cnpj_numeros = "".join(re.findall(r'\d+', cnpj_novo))
        if len(cnpj_numeros) != 14:
            self.lbl_status_cadastro.config(
                text="⚠️ Digite um CNPJ válido com exatamente 14 dígitos numéricos.",
                fg="#ef4444"
            )
            return

        # Verifica duplicidade em dados.py
        if gerenciador_cnpj.cnpj_ja_existe(cnpj_numeros):
            self.lbl_status_cadastro.config(
                text=f"⚠️ O CNPJ {cnpj_numeros} já está cadastrado em dados.py!",
                fg="#ef4444"
            )
            return

        # Valida cidades selecionadas
        if not self.cidades_selecionadas:
            aceita_sem = messagebox.askyesno(
                "Sem Cidades Municipais",
                "Nenhum município foi selecionado para este CNPJ.\n\n"
                "Deseja criar a pasta na rede e cadastrá-lo apenas para as certidões gerais (Federal, Estadual, Trabalhista, FGTS, etc.)?",
                parent=self.janela
            )
            if not aceita_sem:
                return

        try:
            # 1. Cria a pasta na rede
            caminho_pasta = gerenciador_pastas.criar_pasta_empreendimento(
                construtora,
                nome_emp,
                cnpj_numeros
            )

            # 2. Configura as cidades
            cidades_config = []
            for cidade_nome in sorted(self.cidades_selecionadas):
                cidade_info = self.cidades_disponiveis.get(cidade_nome, {})
                cidades_config.append({
                    "cidade": cidade_nome,
                    "url": cidade_info.get("url", ""),
                    "automatizado": cidade_info.get("automatizado", False)
                })

            # 3. Salva no banco de dados (dados.json)
            if gerenciador_cnpj.adicionar_cnpj_em_dados(cnpj_numeros, cidades_config, nome_empreendimento=nome_emp):
                global mapa_municipal
                mapa_municipal = gerenciador_cnpj.obter_mapa_municipal()

                # Adiciona o novo CNPJ na lista da tela de coleta
                texto_atual = self.campo_cnpjs.get("1.0", "end").strip()
                if texto_atual:
                    if cnpj_numeros not in texto_atual:
                        self.campo_cnpjs.insert("end", f"\n{cnpj_numeros}")
                else:
                    self.campo_cnpjs.insert("1.0", cnpj_numeros)

                nome_pasta_final = os.path.basename(caminho_pasta)
                self.fila_terminal.put(f"\n\033[32m[PASTAS] Pasta criada na rede: {nome_pasta_final}\033[0m")
                self.fila_terminal.put(f"\033[32m[CADASTRO] CNPJ {cnpj_numeros} ({nome_emp}) cadastrado com sucesso com {len(cidades_config)} cidade(s)!\033[0m\n")

                # Atualiza as listas de pastas
                self.ao_selecionar_construtora()
                self.combo_empreendimentos_existentes.set(nome_pasta_final)

                self.lbl_status_cadastro.config(
                    text=f"✅ Pasta '{nome_pasta_final}' criada na rede e CNPJ cadastrado com sucesso! Retornando para a coleta...",
                    fg="#10b981"
                )
                self.limpar_formulario_cadastro()

                if hasattr(self, 'combo_atualizar_cnpj'):
                    self.cnpjs_cadastrados = gerenciador_cnpj.listar_cnpjs_cadastrados()
                    self.combo_atualizar_cnpj['values'] = self.cnpjs_cadastrados
                if hasattr(self, 'atualizar_display_cidades_manuais'):
                    self.atualizar_display_cidades_manuais()

                self.janela.after(1400, self.ir_para_coleta)
            else:
                self.lbl_status_cadastro.config(
                    text="❌ Ocorreu um erro ao salvar o CNPJ em dados.py.",
                    fg="#ef4444"
                )
        except Exception as e:
            self.lbl_status_cadastro.config(
                text=f"❌ Erro: {e}",
                fg="#ef4444"
            )

    # -------------------------------------------------------------
    # MÉTODOS DA ABA 3: ATUALIZAR CADASTRO
    # -------------------------------------------------------------
    def construir_aba_atualizar(self):
        self.cnpj_atual_em_edicao = None
        self.cidades_em_edicao = []

        conteiner = tk.Frame(self.aba_atualizar, bg="#002b36")
        conteiner.pack(fill="both", expand=True, padx=20, pady=12)

        # Cabeçalho
        tk.Label(
            conteiner,
            text="Atualização de Cadastro e Auditoria de Cidades",
            font=("Segoe UI", 15, "bold"),
            bg="#002b36",
            fg="#38bdf8"
        ).pack(anchor="w")

        tk.Label(
            conteiner,
            text="Gerencie as cidades e status de automação dos CNPJs, audite cidades manuais/pendentes e consulte o último relatório.",
            font=("Segoe UI", 9),
            bg="#002b36",
            fg="#839496"
        ).pack(anchor="w", pady=(1, 10))

        # Barra Superior de Seleção de CNPJ
        frame_topo = tk.Frame(conteiner, bg="#073642", highlightthickness=1, highlightbackground="#0e4957", padx=10, pady=8)
        frame_topo.pack(fill="x", pady=(0, 10))

        tk.Label(
            frame_topo,
            text="CNPJ a gerenciar:",
            font=("Segoe UI", 10, "bold"),
            bg="#073642",
            fg="#e2e8f0"
        ).pack(side="left", padx=(0, 8))

        self.cnpjs_cadastrados = gerenciador_cnpj.listar_cnpjs_cadastrados()
        self.combo_atualizar_cnpj = ttk.Combobox(
            frame_topo,
            values=self.cnpjs_cadastrados,
            width=24,
            font=("Consolas", 10)
        )
        self.combo_atualizar_cnpj.pack(side="left", padx=(0, 8))
        self.combo_atualizar_cnpj.bind("<<ComboboxSelected>>", self.ao_selecionar_cnpj_combo)
        self.combo_atualizar_cnpj.bind("<Return>", self.ao_selecionar_cnpj_combo)

        btn_carregar = tk.Button(
            frame_topo,
            text="🔍 Carregar",
            command=self.carregar_cnpj_para_atualizacao,
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=3
        )
        btn_carregar.pack(side="left", padx=(0, 12))

        self.lbl_status_cnpj_atualizar = tk.Label(
            frame_topo,
            text="Selecione ou digite um CNPJ cadastrado e clique em Carregar.",
            font=("Segoe UI", 9),
            bg="#073642",
            fg="#94a3b8"
        )
        self.lbl_status_cnpj_atualizar.pack(side="left")

        # Corpo com 2 Colunas (Esquerda: Edição do CNPJ | Direita: Auditoria + Relatório)
        frame_corpo = tk.Frame(conteiner, bg="#002b36")
        frame_corpo.pack(fill="both", expand=True)

        # === COLUNA ESQUERDA (Edição de Cidades do CNPJ) ===
        col_esquerda = tk.Frame(frame_corpo, bg="#002b36")
        col_esquerda.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            col_esquerda,
            text="Cidades Vinculadas ao CNPJ:",
            font=("Segoe UI", 10, "bold"),
            bg="#002b36",
            fg="#38bdf8"
        ).pack(anchor="w", pady=(0, 4))

        frame_listbox = tk.Frame(col_esquerda, bg="#073642", highlightthickness=1, highlightbackground="#0e4957")
        frame_listbox.pack(fill="both", expand=True, pady=(0, 6))

        scroll_edicao = tk.Scrollbar(frame_listbox)
        scroll_edicao.pack(side="right",fill="y")

        self.listbox_cidades_edicao = tk.Listbox(
            frame_listbox,
            yscrollcommand=scroll_edicao.set,
            font=("Consolas", 10),
            bg="#073642",
            fg="#f8fafc",
            selectbackground="#268bd2",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            activestyle="none",
            height=12
        )
        self.listbox_cidades_edicao.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scroll_edicao.config(command=self.listbox_cidades_edicao.yview)

        # --- NOVO BLOCO: ÁREA DO CNPJ DA MATRIZ ---

        frame_botoes_lista = tk.Frame(col_esquerda, bg="#002b36")
        frame_botoes_lista.pack(fill="x", pady=(0, 8))

        btn_alternar_status = tk.Button(
        frame_botoes_lista,
        text="⚡ Alternar Status",
        command=self.alternar_status_cidade_selecionada,
        bg="#073642",
        fg="#38bdf8",
        activebackground="#0e4957",
        activeforeground="#ffffff",
        font=("Segoe UI", 8, "bold"),
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=4
        )
        btn_alternar_status.pack(side="left", padx=(0, 6))

        btn_remover_cidade = tk.Button(
            frame_botoes_lista,
            text="🗑️ Remover",
            command=self.remover_cidade_selecionada,
            bg="#073642",
            fg="#f87171",
            activebackground="#0e4957",
            activeforeground="#ffffff",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4
        )
        # Adicionamos um padding maior (padx=20) na direita para separar os botões da cidade dos controles da Matriz
        btn_remover_cidade.pack(side="left", padx=(0, 20))

        # --- CONTROLES DA MATRIZ EMBUTIDOS ---
        tk.Label(
            frame_botoes_lista,
            text="Matriz:",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#e2e8f0"
        ).pack(side="left")

        self.lbl_cnpj_matriz_atual = tk.Label(
            frame_botoes_lista,
            text="Nenhuma",
            font=("Segoe UI", 9, "italic"),
            bg="#002b36",
            fg="#94a3b8"
        )
        self.lbl_cnpj_matriz_atual.pack(side="left", padx=(4, 10))

        btn_vincular_matriz = tk.Button(
            frame_botoes_lista,
            text="🔗 Vincular Matriz",
            command=self.ao_clicar_vincular_matriz, 
            bg="#8b5cf6", 
            fg="#ffffff",
            activebackground="#7c3aed",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=2
        )
        btn_vincular_matriz.pack(side="left")

        # ------------------------------------------

        # Botões de Ação na Lista de Cidades (Alternar Status e Remover)
        # [O restante do código de frame_botoes_lista segue idêntico aqui para baixo...]

        # Botões de Ação na Lista de Cidades (Alternar Status e Remover)
        frame_botoes_lista = tk.Frame(col_esquerda, bg="#002b36")
        frame_botoes_lista.pack(fill="x", pady=(0, 8))

        # Seção para Adicionar Nova Cidade a este CNPJ
        frame_add_cidade = tk.Frame(col_esquerda, bg="#073642", highlightthickness=1, highlightbackground="#0e4957", padx=8, pady=6)
        frame_add_cidade.pack(fill="x", pady=(0, 8))

        tk.Label(
            frame_add_cidade,
            text="Adicionar Cidade:",
            font=("Segoe UI", 9, "bold"),
            bg="#073642",
            fg="#e2e8f0"
        ).pack(side="left", padx=(0, 6))

        cidades_nomes = sorted(list(self.cidades_disponiveis.keys())) if hasattr(self, 'cidades_disponiveis') and self.cidades_disponiveis else sorted(list(gerenciador_cnpj.listar_cidades_disponiveis().keys()))
        self.combo_add_cidade = ttk.Combobox(
            frame_add_cidade,
            values=cidades_nomes,
            width=20,
            font=("Segoe UI", 9)
        )
        self.combo_add_cidade.pack(side="left", padx=(0, 6))

        self.var_add_aut = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frame_add_cidade,
            text="Automatizado?",
            variable=self.var_add_aut,
            bg="#073642",
            fg="#e2e8f0",
            activebackground="#073642",
            activeforeground="#38bdf8",
            selectcolor="#002b36",
            font=("Segoe UI", 8)
        ).pack(side="left", padx=(0, 6))

        btn_adicionar = tk.Button(
            frame_add_cidade,
            text="+ Incluir",
            command=self.adicionar_cidade_ao_cnpj_atual,
            bg="#3b82f6",
            fg="#ffffff",
            activebackground="#2563eb",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=2
        )
        btn_adicionar.pack(side="left")

        # Botão Salvar Edição do CNPJ
        frame_salvar_cnpj = tk.Frame(col_esquerda, bg="#002b36")
        frame_salvar_cnpj.pack(fill="x", pady=(2, 0))

        self.btn_salvar_edicao_cnpj = tk.Button(
            frame_salvar_cnpj,
            text="✔ Salvar Alterações no CNPJ",
            command=self.salvar_alteracoes_cnpj,
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=7
        )
        self.btn_salvar_edicao_cnpj.pack(side="left", padx=(0, 8))

        self.lbl_feedback_edicao = tk.Label(
            frame_salvar_cnpj,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg="#002b36",
            fg="#10b981"
        )
        self.lbl_feedback_edicao.pack(side="left")

        # === COLUNA DIREITA (Auditoria de Cidades Manuais/False + Último Relatório) ===
        col_direita = tk.Frame(frame_corpo, bg="#002b36")
        col_direita.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # 1. Auditoria: Cidades Manuais / False / Em Branco
        frame_header_manuais = tk.Frame(col_direita, bg="#002b36")
        frame_header_manuais.pack(fill="x", pady=(0, 4))

        self.lbl_titulo_manuais = tk.Label(
            frame_header_manuais,
            text="Cidades com Status False / Em Branco:",
            font=("Segoe UI", 10, "bold"),
            bg="#002b36",
            fg="#facc15"
        )
        self.lbl_titulo_manuais.pack(side="left")

        btn_recarregar_manuais = tk.Button(
            frame_header_manuais,
            text="🔄 Atualizar",
            command=self.atualizar_display_cidades_manuais,
            bg="#073642",
            fg="#e2e8f0",
            activebackground="#0e4957",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=1
        )
        btn_recarregar_manuais.pack(side="right")

        self.txt_cidades_manuais = scrolledtext.ScrolledText(
            col_direita,
            height=7,
            bg="#001e26",
            fg="#e2e8f0",
            font=("Consolas", 9),
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0e4957"
        )
        self.txt_cidades_manuais.pack(fill="both", expand=True, pady=(0, 8))

        # 2. Último Relatório Gerado (pasta relatorios/)
        frame_header_relatorio = tk.Frame(col_direita, bg="#002b36")
        frame_header_relatorio.pack(fill="x", pady=(0, 4))

        self.lbl_titulo_relatorio = tk.Label(
            frame_header_relatorio,
            text="Último Relatório Gerado (relatorios/):",
            font=("Segoe UI", 10, "bold"),
            bg="#002b36",
            fg="#38bdf8"
        )
        self.lbl_titulo_relatorio.pack(side="left")

        btn_recarregar_rel = tk.Button(
            frame_header_relatorio,
            text="📄 Recarregar",
            command=self.atualizar_display_ultimo_relatorio,
            bg="#073642",
            fg="#e2e8f0",
            activebackground="#0e4957",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=1
        )
        btn_recarregar_rel.pack(side="right")

        self.txt_ultimo_relatorio = scrolledtext.ScrolledText(
            col_direita,
            height=7,
            bg="#001e26",
            fg="#e2e8f0",
            font=("Consolas", 9),
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0e4957"
        )
        self.txt_ultimo_relatorio.pack(fill="both", expand=True)

        # Popula displays iniciais
        self.atualizar_display_cidades_manuais()
        self.atualizar_display_ultimo_relatorio()

    def carregar_cnpj_para_atualizacao(self, event=None):
        cnpj = self.combo_atualizar_cnpj.get().strip()
        if not cnpj:
            self.lbl_status_cnpj_atualizar.config(text="⚠️ Digite ou selecione um CNPJ.", fg="#facc15")
            return
        if not gerenciador_cnpj.cnpj_ja_existe(cnpj):
            self.lbl_status_cnpj_atualizar.config(text=f"⚠️ CNPJ {cnpj} não encontrado em dados.py.", fg="#ef4444")
            self.cidades_em_edicao = []
            self.atualizar_listbox_edicao()
            return
        
        self.cnpj_atual_em_edicao = cnpj
        self.cidades_em_edicao = gerenciador_cnpj.obter_cidades_cnpj(cnpj)

        # Carrega também a matriz se houver
        matriz_atual = gerenciador_cnpj.obter_matriz_do_cnpj(cnpj)
        if matriz_atual:
            self.lbl_cnpj_matriz_atual.config(text=matriz_atual, fg="#38bdf8")
            self.matriz_em_edicao = matriz_atual
        else:
            self.lbl_cnpj_matriz_atual.config(text="Nenhuma", fg="#94a3b8")
            self.matriz_em_edicao = None

        self.atualizar_listbox_edicao()
        self.lbl_status_cnpj_atualizar.config(
            text=f"CNPJ {cnpj}: {len(self.cidades_em_edicao)} cidade(s) carregada(s).",
            fg="#10b981"
        )
        self.lbl_feedback_edicao.config(text="")

    def ao_selecionar_cnpj_combo(self, event=None):
        self.carregar_cnpj_para_atualizacao()

    def atualizar_listbox_edicao(self):
        self.listbox_cidades_edicao.delete(0, "end")
        for c in self.cidades_em_edicao:
            status = "SIM (Auto)" if c.get("automatizado") else "NÃO (Manual)"
            nome = c.get("cidade", "")
            texto = f"[{status:<12}] {nome}"
            self.listbox_cidades_edicao.insert("end", texto)

    def alternar_status_cidade_selecionada(self):
        sel = self.listbox_cidades_edicao.curselection()
        if not sel:
            self.lbl_feedback_edicao.config(text="⚠️ Selecione uma cidade na lista para alternar.", fg="#facc15")
            return
        idx = sel[0]
        atual = bool(self.cidades_em_edicao[idx].get("automatizado", False))
        self.cidades_em_edicao[idx]["automatizado"] = not atual
        self.atualizar_listbox_edicao()
        self.listbox_cidades_edicao.selection_set(idx)
        novo_status = "AUTOMATIZADO" if not atual else "MANUAL"
        self.lbl_feedback_edicao.config(
            text=f"Status alterado para {novo_status}. Clique em 'Salvar Alterações'.",
            fg="#38bdf8"
        )

    def remover_cidade_selecionada(self):
        sel = self.listbox_cidades_edicao.curselection()
        if not sel:
            self.lbl_feedback_edicao.config(text="⚠️ Selecione uma cidade para remover.", fg="#facc15")
            return
        idx = sel[0]
        removida = self.cidades_em_edicao.pop(idx)
        self.atualizar_listbox_edicao()
        self.lbl_feedback_edicao.config(
            text=f"Cidade '{removida.get('cidade')}' removida. Clique em 'Salvar Alterações'.",
            fg="#f87171"
        )

    def adicionar_cidade_ao_cnpj_atual(self):
        if not hasattr(self, 'cnpj_atual_em_edicao') or not self.cnpj_atual_em_edicao:
            self.lbl_feedback_edicao.config(text="⚠️ Carregue um CNPJ primeiro antes de adicionar cidades.", fg="#facc15")
            return
        cidade_nome = self.combo_add_cidade.get().strip()
        if not cidade_nome:
            self.lbl_feedback_edicao.config(text="⚠️ Selecione uma cidade para adicionar.", fg="#facc15")
            return
        
        if any(c.get("cidade") == cidade_nome for c in self.cidades_em_edicao):
            self.lbl_feedback_edicao.config(text=f"⚠️ A cidade '{cidade_nome}' já está nesta lista.", fg="#facc15")
            return
        
        todas_cidades = self.cidades_disponiveis if hasattr(self, 'cidades_disponiveis') and self.cidades_disponiveis else gerenciador_cnpj.listar_cidades_disponiveis()
        url = todas_cidades.get(cidade_nome, {}).get("url", "")
        automatizado = self.var_add_aut.get()

        self.cidades_em_edicao.append({
            "cidade": cidade_nome,
            "automatizado": automatizado,
            "url": url
        })
        self.atualizar_listbox_edicao()
        self.lbl_feedback_edicao.config(
            text=f"Cidade '{cidade_nome}' incluída! Clique em 'Salvar Alterações'.",
            fg="#38bdf8"
        )

    def salvar_alteracoes_cnpj(self):
        if not hasattr(self, 'cnpj_atual_em_edicao') or not self.cnpj_atual_em_edicao:
            self.lbl_feedback_edicao.config(text="⚠️ Nenhum CNPJ carregado para salvar.", fg="#ef4444")
            return
        
        cnpj = self.cnpj_atual_em_edicao
        sucesso = gerenciador_cnpj.salvar_atualizacao_cnpj(cnpj, self.cidades_em_edicao)
        if sucesso:
            # ---- NOVO: SALVA A MATRIZ -----
            if hasattr(self, 'matriz_em_edicao'):
                gerenciador_cnpj.salvar_vinculo_matriz(cnpj, self.matriz_em_edicao)
            # -------------------------------
            global mapa_municipal
            mapa_municipal = gerenciador_cnpj.obter_mapa_municipal()
            self.lbl_feedback_edicao.config(
                text=f"✔ Cadastro do CNPJ {cnpj} atualizado com sucesso!",
                fg="#10b981"
            )
            self.atualizar_display_cidades_manuais()
        else:
            self.lbl_feedback_edicao.config(
                text=f"❌ Erro ao gravar dados do CNPJ {cnpj} no banco de dados.",
                fg="#ef4444"
            )

    def atualizar_display_cidades_manuais(self):
        pendentes = gerenciador_cnpj.listar_cidades_manuais_ou_pendentes()
        self.lbl_titulo_manuais.config(text=f"Cidades com Status False / Em Branco ({len(pendentes)}):")
        self.txt_cidades_manuais.configure(state="normal")
        self.txt_cidades_manuais.delete("1.0", "end")
        if not pendentes:
            self.txt_cidades_manuais.insert("end", "🎉 Nenhuma cidade com status False ou em branco no sistema!\nTodas as cidades estão 100% automatizadas.")
        else:
            self.txt_cidades_manuais.insert("end", f"Total de cidades manuais/pendentes: {len(pendentes)}\n")
            self.txt_cidades_manuais.insert("end", "=" * 55 + "\n\n")
            for p in pendentes:
                aut_txt = "False" if p["automatizado"] is False else "Em branco"
                cid_txt = p["cidade"] if p["cidade"] else "(Sem nome)"
                self.txt_cidades_manuais.insert("end", f"• CNPJ: {p['cnpj']} | Cidade: {cid_txt:<16} | Status: [{aut_txt}]\n")
        self.txt_cidades_manuais.configure(state="disabled")

    def atualizar_display_ultimo_relatorio(self):
        pasta_rel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relatorios")
        nome, conteudo = obter_ultimo_relatorio(pasta_rel)
        if nome:
            self.lbl_titulo_relatorio.config(text=f"Último Relatório: {nome}")
        else:
            self.lbl_titulo_relatorio.config(text="Último Relatório (pasta relatorios/):")
        self.txt_ultimo_relatorio.configure(state="normal")
        self.txt_ultimo_relatorio.delete("1.0", "end")
        self.txt_ultimo_relatorio.insert("end", conteudo)
        self.txt_ultimo_relatorio.configure(state="disabled")

    def detectar_cnd_linha(self, linha):
        up = linha.upper()
        if "[FEDERAL]" in up or "RECEITA FEDERAL" in up:
            return "federal"
        if "[ESTADUAL]" in up or "SEFAZ" in up:
            return "estadual"
        if "[TRABALHISTA]" in up or "JUSTIÇA DO TRABALHO" in up or "CNDT" in up:
            return "trabalhista"
        if "[COMPRASNET]" in up:
            return "comprasnet"
        if "[FGTS]" in up or "CRF" in up or "CAIXA ECONÔMICA" in up or "CAIXA ECONOMICA" in up:
            return "fgts"
        if any(kw in up for kw in [
            "[MUNICIPAL]", "MUNICÍPIO", "MUNICIPIO", "PREFEITURA", "MUNICIPAL DE",
            "VALPARAISO", "ÁGUAS LINDAS", "AGUAS LINDAS", "CIDADE OCIDENTAL",
            "FORMOSA", "CATALÃO", "CATALAO", "APARECIDA DE GOIÂNIA",
            "APARECIDA DE GOIANIA", "LUZIANA", "LUZIÂNIA", "GOIANÉSIA",
            "GOIANESIA", "NOVO GAMA", "ARAGOIANIA", "ARAGOIÂNIA", "PARAÚNA",
            "PARAUNA", "ABADIÂNIA", "ABADIANIA", "SANTO ANTÔNIO", "SANTO ANTONIO",
            "MARA ROSA", "NERÓPOLIS", "NEROPOLIS", "TEREZÓPOLIS", "TEREZOPOLIS",
            "PORANGATU", "FLORES", "IPORÁ", "IPORA", "BOM JESUS", "GOIÂNIA",
            "GOIANIA", "CALDAS NOVAS", "CAMPO ALEGRE", "NOVA VENEZA",
            "SENADOR CANEDO", "ANÁPOLIS", "ANAPOLIS"
        ]):
            return "municipal"
        return "normal"

    def escrever_terminal(self, texto):
        self.terminal.configure(state="normal")
        linhas = texto.splitlines(keepends=True)
        for linha in linhas:
            tag_detectada = self.detectar_cnd_linha(linha)
            if tag_detectada != "normal":
                self.tag_cnd_ativa = tag_detectada

            tag_atual = self.tag_cnd_ativa

            partes = re.split(r"(\x1b\[[0-9;]*m)", linha)
            for parte in partes:
                if not parte:
                    continue
                if parte == "\x1b[0m":
                    tag_atual = self.tag_cnd_ativa
                elif parte.startswith("\x1b[38;2;"):
                    try:
                        _, _, r, g, b = parte[2:-1].split(";")
                        hex_cor = f"#{int(r):02X}{int(g):02X}{int(b):02X}"
                        if hex_cor not in self.tags_configuradas:
                            self.terminal.tag_configure(hex_cor, foreground=hex_cor)
                            self.tags_configuradas.add(hex_cor)
                        tag_atual = hex_cor
                    except Exception:
                        tag_atual = self.tag_cnd_ativa
                elif parte in {"\x1b[31m", "\x1b[91m"}:
                    tag_atual = "vermelho"
                elif parte in {"\x1b[32m", "\x1b[92m"}:
                    tag_atual = "estadual"
                elif parte in {"\x1b[33m"}:
                    tag_atual = self.tag_cnd_ativa if self.tag_cnd_ativa != "normal" else "municipal"
                elif parte in {"\x1b[93m"}:
                    tag_atual = "comprasnet"
                elif parte in {"\x1b[34m"}:
                    tag_atual = "federal"
                elif parte in {"\x1b[94m"}:
                    tag_atual = "trabalhista"
                elif parte in {"\x1b[36m", "\x1b[96m"}:
                    tag_atual = self.tag_cnd_ativa if self.tag_cnd_ativa != "normal" else "fgts"
                elif parte in {"\x1b[35m", "\x1b[95m"}:
                    tag_atual = "magenta"
                else:
                    self.terminal.insert("end", parte, tag_atual)

            if linha.endswith("\n"):
                self.tag_cnd_ativa = "normal"

        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def configurar_cores_terminal(self):
        cores = {
            "normal": "#e5e7eb",
            "vermelho": "#f87171",
            # Cores padrão solicitadas pelo usuário por CND:
            "federal": "#3399FF",      # Azul
            "estadual": "#66CC66",     # Verde
            "municipal": "#FFCC66",    # Laranja
            "trabalhista": "#66CCFF",  # Azul claro
            "comprasnet": "#FFFFCC",   # Amarelo claro
            "fgts": "#33FFFF",         # Azul claro / Ciano
            # Aliases e compatibilidade com códigos ANSI clássicos
            "verde": "#66CC66",
            "amarelo": "#FFFFCC",
            "azul": "#3399FF",
            "magenta": "#e879f9",
            "ciano": "#33FFFF",
            "laranja": "#FFCC66",
            "azul_claro": "#66CCFF",
        }
        self.tags_configuradas = set(cores.keys())
        for nome, cor in cores.items():
            self.terminal.tag_configure(nome, foreground=cor)

    def atualizar_interface(self):
        while True:
            try:
                self.escrever_terminal(self.fila_terminal.get_nowait())
            except queue.Empty:
                break

        while True:
            try:
                evento, resposta = self.fila_captcha.get_nowait()
            except queue.Empty:
                break
            if evento == "solicitar":
                self.abrir_janela_captcha(resposta)

        self.janela.after(100, self.atualizar_interface)

    def iniciar_coleta(self):
        texto_cnpjs = self.campo_cnpjs.get("1.0", "end").strip()
        if not texto_cnpjs:
            messagebox.showerror("Sem CNPJs", "Informe pelo menos um CNPJ.", parent=self.janela)
            return
        
        linhas = texto_cnpjs.split("\n")
        cnpjs_validos = []
        linhas_com_erro = []
        
        for idx, linha in enumerate(linhas, 1):
            linha = linha.strip()
            if not linha:
                continue
            if not linha.isdigit():
                linhas_com_erro.append(f"Linha {idx}: '{linha}' - Contém caracteres não numéricos")
                continue
            if len(linha) != 14:
                linhas_com_erro.append(f"Linha {idx}: '{linha}' - Tem {len(linha)} dígitos (deve ser 14)")
                continue
            if " " in linha:
                linhas_com_erro.append(f"Linha {idx}: '{linha}' - Contém espaços")
                continue
            cnpjs_validos.append(linha)
        
        if linhas_com_erro:
            mensagem_erro = "⚠️ Erros na formatação dos CNPJs:\n\n"
            mensagem_erro += "\n".join(linhas_com_erro)
            mensagem_erro += "\n\n📋 Formato correto:\n"
            mensagem_erro += "Apenas números, exatamente 14 dígitos por linha, sem espaços\n\n"
            mensagem_erro += "✅ Exemplo correto:\n"
            mensagem_erro += "21370540000137\n"
            mensagem_erro += "12655348000104\n"
            mensagem_erro += "57029627000192"
            messagebox.showerror("CNPJs Inválidos", mensagem_erro, parent=self.janela)
            return
        
        if not cnpjs_validos:
            messagebox.showerror("Sem CNPJs", "Nenhum CNPJ válido encontrado.", parent=self.janela)
            return
        
        tipos_selecionados = [tipo for tipo, var in self.vars_cnd.items() if var.get()]
        if not tipos_selecionados:
            messagebox.showerror("Sem tipos", "Selecione pelo menos um tipo de CND.", parent=self.janela)
            return
        
        global flag_cancelamento
        flag_cancelamento = False
        self.coleta_foi_cancelada = False
        
        self.botao_iniciar.configure(state="disabled")
        self.botao_cancelar.configure(state="normal")
        self.campo_cnpjs.configure(state="disabled")
        
        self.escrever_terminal(f"Iniciando coleta de {len(cnpjs_validos)} CNPJ(s)...\n")
        sys.stdout = EscritorTerminal(self.fila_terminal)
        self.thread_automacao = threading.Thread(
            target=self.executar_automacao,
            args=(cnpjs_validos, tipos_selecionados),
            daemon=True,
        )
        self.thread_automacao.start()

    def executar_automacao(self, cnpjs, tipos_cnd):
        try:
            principal(cnpjs, tipos_cnd, solicitar_captcha=self.solicitar_captcha, interface=self)
        except Exception as erro:
            print(f"Erro na automacao: {erro}")
        finally:
            self.janela.after(0, self.confirmar_organizacao)
    
    def cancelar_coleta(self):
        global flag_cancelamento
        flag_cancelamento = True
        self.coleta_foi_cancelada = True
        self.escrever_terminal("\033[31mCancelamento requisitado...\033[0m\n")

    def confirmar_organizacao(self):
        self.botao_cancelar.configure(state="disabled")
        self.campo_cnpjs.configure(state="normal")
        
        if self.coleta_foi_cancelada:
            self.escrever_terminal("\033[31mColeta cancelada. PDFs não serão organizados.\033[0m\n")
            self.botao_iniciar.configure(state="normal")
            return
        
        organizar = messagebox.askyesno(
            "Organizar certidoes",
            "A coleta terminou. Deseja organizar os PDFs nas pastas das empresas?",
            parent=self.janela,
        )

        if organizar:
            self.escrever_terminal("Organizando os PDFs...\n")
            threading.Thread(
                target=self.executar_organizacao,
                daemon=True,
            ).start()
        else:
            self.escrever_terminal("Organizacao dos PDFs cancelada pelo usuario.\n")
            self.escrever_terminal("\033[32mTudo acabou.\033[0m\n")
            self.botao_iniciar.configure(state="normal")

    def executar_organizacao(self):
        try:
            organizar_certidoes_por_cnpj(
                pasta_download,
                r"N:\16. CERTIDÕES\1. Empresas",
                interface=self
            )
        except Exception as erro:
            print(f"Erro ao organizar os PDFs: {erro}")
        finally:
            self.fila_terminal.put("\n\033[32mTudo acabou.\033[0m\n")
            self.janela.after(0, lambda: self.botao_iniciar.configure(state="normal"))

    def solicitar_captcha(self):
        resposta = {"evento": threading.Event(), "codigo": ""}
        self.fila_captcha.put(("solicitar", resposta))
        resposta["evento"].wait()
        return resposta["codigo"]

    def abrir_janela_captcha(self, resposta):
        self.resposta_captcha_atual = resposta
        self.campo_captcha.delete(0, "end")
        self.status_captcha.configure(text="Digite o codigo exibido no navegador.")
        self.painel_captcha.pack(fill="x", padx=12, pady=(0, 10), before=self.terminal)
        self.campo_captcha.focus_set()


    def enviar_captcha(self):
        if self.resposta_captcha_atual is None:
            return

        codigo = self.campo_captcha.get().strip()
        if not codigo: 
            self.status_captcha.configure(text="Informe o código do CAPTCHA.", foreground="#dc2626")
            return

        self.resposta_captcha_atual["codigo"] = codigo
        self.resposta_captcha_atual["evento"].set()
        self.resposta_captcha_atual = None
        self.painel_captcha.pack_forget()
    
    def exportar_excel(self):
        # 1. Coleta os dados que estão aparecendo no Treeview
        dados_tabela = []
        for child in self.tabela_conferencia.get_children():
            dados_tabela.append(self.tabela_conferencia.item(child)["values"])
            
        if not dados_tabela:
            messagebox.showwarning("Vazio", "Não há dados no painel para exportar.", parent=self.janela)
            return
            
        # 2. Converte para uma estrutura de dados do Pandas
        df = pd.DataFrame(dados_tabela, columns=["Empresa", "Certidão", "Data Validade", "Status Original", "Observações"])
        
        # 3. Salva no Excel usando openpyxl para podermos pintar as células
        caminho_excel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Relatorio_CNDs_Global.xlsx")
        
        try:
            with pd.ExcelWriter(caminho_excel, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Painel Geral")
                worksheet = writer.sheets["Painel Geral"]
                
                # Prepara as cores em Hexadecimal
                fill_vermelho = PatternFill(start_color="F87171", end_color="F87171", fill_type="solid")
                fill_verde = PatternFill(start_color="86EFAC", end_color="86EFAC", fill_type="solid")
                fill_amarelo = PatternFill(start_color="FEF08A", end_color="FEF08A", fill_type="solid")
                
                # Pinta as linhas no Excel baseado na coluna 'Status Original'
                for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=1, max_col=5):
                    status = str(row[3].value).lower()
                    
                    if "positiva" in status and "efeito" not in status:
                        fill_color = fill_vermelho
                    elif "negativa" in status:
                        fill_color = fill_verde
                    else:
                        fill_color = fill_amarelo # Efeito de negativa
                        
                    for cell in row:
                        cell.fill = fill_color

            messagebox.showinfo("Sucesso", f"Planilha gerada com sucesso em:\n{caminho_excel}", parent=self.janela)
        except PermissionError:
            messagebox.showerror("Erro", "Feche a planilha Excel antes de exportar novamente!", parent=self.janela)


    def fechar(self):
        if self.thread_automacao and self.thread_automacao.is_alive():
            messagebox.showwarning(
                "Coleta em andamento",
                "Aguarde a automacao terminar antes de fechar.",
                parent=self.janela
            )
            return
        sys.stdout = self.saida_original
        self.janela.destroy()

    def executar(self):
        self.janela.mainloop()


if __name__ == "__main__":
    pasta_download = r"N:\19. FERRAMENTAS\Teste selenium\RenomearCNDs\CNDs"
    try:
        pasta_raiz_empresas = gerenciador_pastas.obter_pasta_raiz_empresas()
    except Exception:
        pasta_raiz_empresas = r"N:\16. CERTIDÕES\1. Empresas"

    InterfaceAutomacao().executar()


