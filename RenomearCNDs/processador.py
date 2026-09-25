# processador.py

import os
import re
from datetime import datetime, timedelta
import pdfplumber
from tkinter import simpledialog

from regras import identificar_cnd
from leitor_ocr import extrair_texto_com_ocr
from Gerenciadores import gerenciador_historico

def extrair_cnpj(texto):
    """
    Procura o CNPJ tolerando rótulos mistos (CNPJ/CPF), corrigindo a falta 
    do zero à esquerda e blindado contra espaços em branco gerados pelo OCR.
    """
    # NOVO: Apaga os CNPJs das prefeituras do texto para o robô focar apenas no da empresa
    texto = texto.replace("01.505.643/0001-50", "").replace("01505643000150", "").replace("01.505.643-0001-50", "")

    # TENTATIVA 1: O jeito super seguro (Busca a linha que contém CNPJ e remove espaços dos números)
    # Procuramos o marcador e pegamos até 30 caracteres na frente dele
    busca_linha = re.search(r'CNPJ(?:/CPF)?\s*:?\s*(.{1,30})', texto)
    
    if busca_linha:
        # Pega o pedaço de texto encontrado na frente de "CNPJ:"
        trecho_cnpj = busca_linha.group(1)
        # Remove TODOS os espaços em branco de dentro desse trecho específico
        trecho_sem_espacos = trecho_cnpj.replace(" ", "")
        
        # Agora aplica a regex padrão no texto limpo (aceitando 13 ou 14 dígitos)
        busca_num = re.search(r'(\d{1,2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b', trecho_sem_espacos)
        if busca_num:
            return formatar_e_validar_cnpj(busca_num.group(1))

    # TENTATIVA 2: Fallback numérico clássico (no texto original completo)
    busca_generica = re.search(r'\b(\d{1,2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b', texto)
    if busca_generica:
        return formatar_e_validar_cnpj(busca_generica.group(1))
        
    return "CNPJ INDEFINIDO"

def formatar_e_validar_cnpj(cnpj_cru):
    """
    Função auxiliar para limpar, colocar zero à esquerda e formatar o CNPJ para o Windows.
    """
    numeros = re.sub(r'\D', '', cnpj_cru)
    
    if len(numeros) == 13:
        numeros = "0" + numeros
        
    if len(numeros) == 14:
        # Formata usando "-" no lugar da "/" para o Windows aceitar como nome de arquivo
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}-{numeros[8:12]}-{numeros[12:]}"
        
    return "CNPJ INDEFINIDO"

def processar_todas_cnds(pasta_trabalho, modo_debug=False):
    arquivos_pdf = [arquivo for arquivo in os.listdir(pasta_trabalho) if arquivo.lower().endswith('.pdf')]
    if not arquivos_pdf:
        print("\n[!] Nenhum arquivo PDF encontrado nesta pasta.")
        return

    print(f"\nIniciando AUTO-DETECÇÃO em {len(arquivos_pdf)} arquivo(s) PDF...")

    for nome_arquivo in arquivos_pdf:
        caminho_atual = os.path.join(pasta_trabalho, nome_arquivo)
        print(f"\n{'-'*50}\nLendo: {nome_arquivo}")
        
        status, data_atualizacao, data_encontrada = "Indefinido", "00.00.00", None
        origem, numero_categoria, cidade = None, None, "" 
        
        try:
            with pdfplumber.open(caminho_atual) as pdf:
                primeira_pagina = pdf.pages[0]
                texto_do_pdf = primeira_pagina.extract_text()

                #TRANSFORMA TUDO EM MAIÚSCULO
                if texto_do_pdf:
                    texto_do_pdf = texto_do_pdf.upper()
                
                letras_normais = len(re.findall(r'[A-Z]', texto_do_pdf)) if texto_do_pdf else 0
                if not texto_do_pdf or len(texto_do_pdf.strip()) < 20 or letras_normais < 20:
                    texto_do_pdf = extrair_texto_com_ocr(caminho_atual)

            # ==========================================
            # O TRUQUE DO MODO DEBUG FICA AQUI
            # ==========================================
            if modo_debug:
                print(f"\n[ MODO DEBUG ATIVADO] O que o robô leu no arquivo {nome_arquivo}:")
                print("========================================")
                print(texto_do_pdf)
                print("========================================\n")

            origem, numero_categoria = identificar_cnd(texto_do_pdf)
            if not origem:
                print("-> AVISO: Órgão não identificado. Pulando...")
                continue

            cnpj = extrair_cnpj(texto_do_pdf)
            
            if not modo_debug:
                print(f"-> Identificado: CND {origem}")

            # REGRAS DE LEITURA
            if origem == "Federal":
                # STATUS FEDERAL BLINDADO
                if re.search(r'\bEFEITOS? DE NEGATIVA\b', texto_do_pdf): status = "Positiva com Efeito Negativo"
                elif re.search(r'\bNEGATIVA\b', texto_do_pdf) or "NÃO CONSTA" in texto_do_pdf or "NAO CONSTA" in texto_do_pdf: status = "Negativa"
                elif re.search(r'\bPOSITIVA\b', texto_do_pdf) or re.search(r'\bCONSTA\b', texto_do_pdf): status = "Positiva"
                busca_validade = re.search(r'V[ÁA]LIDA AT[ÉE]\s*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                if busca_validade: data_encontrada = busca_validade.group(1)

            elif origem == "Estadual":
                # STATUS ESTADUAL BLINDADO
                if re.search(r'\bEFEITOS? DE NEGATIVA\b', texto_do_pdf): status = "Positiva com Efeito Negativo"
                elif re.search(r'\bNEGATIVA\b', texto_do_pdf) or "NAO CONSTA DEBITO" in texto_do_pdf: status = "Negativa"
                elif re.search(r'\bPOSITIVA\b', texto_do_pdf) or "CONSTA DEBITO" in texto_do_pdf: status = "Positiva"
                
                meses = {"JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12}
                data_encontrada = None
                dias_validade = 60 # Validade padrão de segurança

                # 1. Pega os dias de validade (Cobre: "VALIDA POR 120 DIAS" do GO ou "60 DIAS" comuns)
                busca_dias = re.search(r'V[AÁ]LIDA POR\s+(\d+)\s+DIAS', texto_do_pdf)
                if busca_dias: 
                    dias_validade = int(busca_dias.group(1))

                # TENTATIVA 1: Padrão da data final explícita (Cobre: DF)
                # Ex: "VÁLIDA ATÉ 04 DE AGOSTO DE 2026"
                busca_validade_direta = re.search(r'V[AÁ]LIDA AT[EÉ]\s+(\d{1,2})\s+DE\s+([A-ZÇ]+)\s+DE\s+(\d{4})', texto_do_pdf)
                if busca_validade_direta:
                    dia = int(busca_validade_direta.group(1))
                    mes_texto = busca_validade_direta.group(2).replace("Ç", "C")
                    ano = int(busca_validade_direta.group(3))
                    if meses.get(mes_texto):
                        data_encontrada = datetime(ano, meses[mes_texto], dia).strftime("%d/%m/%Y")

                # TENTATIVA 2: Padrão Emissão Numérica (Cobre: DF)
                # Ex: "EMITIDA VIA INTERNET EM 06/05/2026"
                if not data_encontrada:
                    busca_emissao_num = re.search(r'EM\s+(\d{2})/(\d{2})/(\d{4})', texto_do_pdf)
                    if busca_emissao_num:
                        dia, mes, ano = int(busca_emissao_num.group(1)), int(busca_emissao_num.group(2)), int(busca_emissao_num.group(3))
                        data_encontrada = (datetime(ano, mes, dia) + timedelta(days=dias_validade)).strftime("%d/%m/%Y")

                # TENTATIVA 3: Padrão Emissão por Extenso Ancorado (Cobre: Goiás)
                # Ex: "LOCAL E DATA: GOIANIA, 13 ABRIL DE 2026"
                if not data_encontrada:
                    # Usamos "LOCAL E DATA" como âncora para forçar o robô a ignorar as leis antigas
                    busca_emissao_go = re.search(r'LOCAL E DATA:.*?(?:,\s*)?(\d{1,2})\s+(?:DE\s+)?([A-ZÇ]+)\s+DE\s+(\d{4})', texto_do_pdf)
                    if busca_emissao_go:
                        dia = int(busca_emissao_go.group(1))
                        mes_texto = busca_emissao_go.group(2).replace("Ç", "C")
                        ano = int(busca_emissao_go.group(3))
                        if meses.get(mes_texto):
                            try:
                                data_encontrada = (datetime(ano, meses[mes_texto], dia) + timedelta(days=dias_validade)).strftime("%d/%m/%Y")
                            except:
                                pass
            

            elif origem == "Estadual DF":
                # STATUS ESTADUAL BLINDADO
                if re.search(r'\bEFEITOS?\s+DE\s+NEGATIVA\b', texto_do_pdf): status = "Positiva com Efeito Negativo"
                elif re.search(r'\bNEGATIVA\b', texto_do_pdf) or "NAO CONSTA" in texto_do_pdf or "NÃO CONSTA" in texto_do_pdf: status = "Negativa"
                elif re.search(r'\bPOSITIVA\b', texto_do_pdf) or "CONSTA" in texto_do_pdf: status = "Positiva"

                data_encontrada = None
                meses = {"JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "MARÇO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12}

                # 1. Busca validade expressa por extenso (Ex: "Válida até 13 de dezembro de 2026")
                busca_validade_extenso = re.search(r'(?:V[AÁ]LIDA\s+AT[EÉ]|VALIDADE)[^\d]*?(\d{1,2})\s+(?:DE\s+)?([A-ZÇ]+)\s+(?:DE\s+)?(\d{4})', texto_do_pdf)
                if busca_validade_extenso:
                    dia = int(busca_validade_extenso.group(1))
                    mes_texto = busca_validade_extenso.group(2).replace("Ç", "C")
                    ano = int(busca_validade_extenso.group(3))
                    if meses.get(mes_texto):
                        try:
                            data_encontrada = datetime(ano, meses[mes_texto], dia).strftime("%d/%m/%Y")
                        except:
                            pass

                # 2. Busca validade numérica com barras (Ex: "Válida até 13/12/2026" ou "Validade: 13/12/2026")
                if not data_encontrada:
                    busca_validade_barras = re.search(r'(?:V[AÁ]LIDA\s+AT[EÉ]|VALIDADE)\s*:?\s*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                    if busca_validade_barras:
                        data_encontrada = busca_validade_barras.group(1)

                # 3. Fallback: Se não encontrar a data de validade expressa, calcula emissão + 90 dias (Decreto Distrital nº 23.873/2003)
                # Ex: "Certidão emitida via internet em 14/09/2026" -> + 90 dias -> 13/12/2026
                if not data_encontrada:
                    busca_emissao = re.search(r'EMITIDA.*?EM\s+(\d{2})/(\d{2})/(\d{4})', texto_do_pdf)
                    if busca_emissao:
                        dia, mes, ano = int(busca_emissao.group(1)), int(busca_emissao.group(2)), int(busca_emissao.group(3))
                        try:
                            data_encontrada = (datetime(ano, mes, dia) + timedelta(days=90)).strftime("%d/%m/%Y")
                        except:
                            pass

                
            elif origem == "Municipal":
                # As três formas de buscar (Apenas procurando, ainda não decidindo)
                busca_nome_cidade = re.search(r'(?:PREFEITURA MUNICIPAL DE|MUNIC[ÍI]PIO DE)\s+([A-ZÁÀÂÃÉÈÊÍÏÓÒÔÕÚÙÛÇ ]+)', texto_do_pdf)
                
                # CORREÇÃO 1: Tiramos o \s de dentro dos colchetes. Agora ele só captura espaços na mesma linha e para no "Enter"
                busca_alt = re.search(r'ADMINISTRADOS PELA\s+([A-ZÁÀÂÃÉÈÊÍÏÓÒÔÕÚÙÛÇ ]+)', texto_do_pdf)
                
                busca_cidade_direta = re.search(r'(?:CIDADE|MUNIC[ÍI]PIO):[\s:]*(.*?)(?=\n|$)', texto_do_pdf)
                
                # Lógica de definição da cidade (NOVA ORDEM DE PRIORIDADE)
                if busca_nome_cidade:
                    cidade = re.sub(r'(?i)\s+DE\s+GOI[ÁA]S$', '', busca_nome_cidade.group(1).split('\n')[0].strip()).title()

                elif busca_cidade_direta:
                    cidade_crua = busca_cidade_direta.group(1).replace("-GO", "").replace("- GO", "").strip()
                    cidade = re.sub(r'(?i)\s+DE\s+GOI[ÁA]S$', '', cidade_crua).title()

                elif busca_alt:
                    # CORREÇÃO 2: A cidade já vem limpinha da Regex. Adeus gambiarra do Águas Lindas!
                    cidade_limpa = busca_alt.group(1).strip()
                    cidade = re.sub(r'(?i)\s+DE\s+GOI[ÁA]S$', '', cidade_limpa).title()
                    
                # Se nada funcionar, pede ajuda ao usuário
                else:
                    resposta = simpledialog.askstring("Cidade não identificada", f"Arquivo: {nome_arquivo}\nPor favor, digite o nome da cidade:")
                    cidade = resposta.strip().title() if resposta else "Desconhecida"

                if cidade == "Águas" or cidade == "Aguas":
                    cidade = "Águas Lindas"

                # Faxina anti-erro do Windows
                cidade = re.sub(r'[<>:"/\\|?*]', '', cidade).strip()
                
                # CORREÇÃO 3: Status Municipal blindado com \b para evitar falsos positivos
                if re.search(r'\bEFEITOS? DE NEGATIVA\b', texto_do_pdf) or "EFEITO NEGATIVO" in texto_do_pdf: 
                    status = "Positiva com Efeito Negativo"
                elif re.search(r'\bNEGATIVA\b', texto_do_pdf) or "NÃO CONSTA" in texto_do_pdf or "NAO CONSTA" in texto_do_pdf: 
                    status = "Negativa"
                elif re.search(r'\bPOSITIVA\b', texto_do_pdf): 
                    status = "Positiva"
                    
                data_encontrada = None
                busca_emissao = re.search(r'VALIDADE[^\d]*(\d{1,2})\s+(?:DE\s+)?([A-ZÇ]+)\s+(?:DE\s+)?(\d{4})', texto_do_pdf)
                if busca_emissao:
                    dia, mes_texto, ano = int(busca_emissao.group(1)), busca_emissao.group(2).replace("Ç", "C"), int(busca_emissao.group(3))
                    meses = {"JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12}
                    if meses.get(mes_texto):
                        try: 
                            data_encontrada = datetime(ano, meses[mes_texto], dia).strftime("%d/%m/%Y")
                        except: 
                            pass
                
                if not data_encontrada:
                    busca_validade_barras = re.search(r'(?:V[ÁA]LIDA AT[ÉE]|VALIDADE).*?(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                    if busca_validade_barras: 
                        data_encontrada = busca_validade_barras.group(1)

            elif origem == "Trabalhista":
                # STATUS TRABALHISTA BLINDADO
                if re.search(r'\bEFEITOS? DE NEGATIVA\b', texto_do_pdf): status = "Positiva com Efeito Negativo"
                elif re.search(r'\bCERTID[ÃA]O NEGATIVA\b', texto_do_pdf) or "NÃO CONSTA COMO INADIMPLENTE" in texto_do_pdf: status = "Negativa"
                elif re.search(r'\bCERTID[ÃA]O POSITIVA\b', texto_do_pdf): status = "Positiva"
                busca_validade = re.search(r'VALIDADE:\s*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                if busca_validade: data_encontrada = busca_validade.group(1)

            elif origem == "Comprasnet":
                # STATUS COMPRASNET BLINDADO
                if re.search(r'\bEFEITOS? DE NEGATIVA\b', texto_do_pdf): status = "Positiva com Efeito Negativo"
                elif "CERTIDÃO - NEGATIVA" in texto_do_pdf or "NÃO CONSTA REGISTRO" in texto_do_pdf: status = "Negativa"
                elif "CERTIDÃO - POSITIVA" in texto_do_pdf: status = "Positiva"
                
                busca_dias = re.search(r'VÁLIDA POR\s+(\d+)\s+DIAS', texto_do_pdf)
                dias_validade = int(busca_dias.group(1)) if busca_dias else 30
                
                busca_emissao = re.search(r'DATA DE EMISSÃO:\s*(\d{2}[./]\d{2}[./]\d{2,4})', texto_do_pdf)
                if busca_emissao:
                    data_emissao_str = busca_emissao.group(1).replace(".", "/") 
                    try:
                        formato = "%d/%m/%Y" if len(data_emissao_str) == 10 else "%d/%m/%y"
                        data_encontrada = (datetime.strptime(data_emissao_str, formato) + timedelta(days=dias_validade)).strftime("%d/%m/%Y")
                    except: data_encontrada = data_emissao_str

            elif origem == "FGTS":
                # STATUS FGTS BLINDADO
                if re.search(r'\bEFEITOS?\s+DE\s+NEGATIVA\b', texto_do_pdf): 
                    status = "Positiva com Efeito Negativo"
                elif re.search(r'\bSITUA[ÇC][ÃA]O\s+REGULAR\b', texto_do_pdf) or "REGULAR PERANTE O FUNDO" in texto_do_pdf: 
                    status = "Negativa" 
                else: 
                    status = "Positiva"
                
                busca_data = re.search(r'VALIDADE.*?\d{2}[./]\d{2}[./]\d{2,4}[^\d]+(\d{2}[./]\d{2}[./]\d{2,4})', texto_do_pdf)
                if busca_data: data_encontrada = busca_data.group(1)

            elif origem == "AGEHAB":
                # STATUS AGEHAB BLINDADO
                if re.search(r'\bEFEITOS? DE NEGATIVA\b', texto_do_pdf): status = "Positiva com Efeito Negativo"
                elif re.search(r'\bNEGATIVA\b', texto_do_pdf): status = "Negativa"
                elif re.search(r'\bPOSITIVA\b', texto_do_pdf): status = "Positiva"
                busca_validade = re.search(r'V[ÁA]LIDA AT[ÉE][^\d]*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                if busca_validade: data_encontrada = busca_validade.group(1)

            if not data_encontrada:
                busca_data_solta = re.search(r'\d{2}[./]\d{2}[./]\d{2,4}', texto_do_pdf)
                if busca_data_solta: data_encontrada = busca_data_solta.group()

            if data_encontrada:
                partes = data_encontrada.replace("/", ".").split(".")
                if len(partes) == 3: data_atualizacao = f"{partes[0]}.{partes[1]}.{partes[2][-2:]}"
                else: data_atualizacao = data_encontrada.replace("/", ".")

        except Exception as e:
            print(f"Erro ao ler arquivo: {e}")
            continue

        nome_origem = cidade if origem == "Municipal" and cidade else origem
        nome_base = f"{numero_categoria} - CND {nome_origem} - {status} - {data_atualizacao} - {cnpj}"
        nome_final = f"{nome_base}.pdf"
        caminho_final = os.path.join(pasta_trabalho, nome_final)
        
        if caminho_atual == caminho_final:
            if not modo_debug:
                print(f"-> O arquivo já está perfeitamente atualizado: '{nome_final}' (Nenhuma mudança necessária).")
            continue

        contador = 1
        while os.path.exists(caminho_final):
            nome_final = f"{nome_base} ({contador}).pdf"
            caminho_final = os.path.join(pasta_trabalho, nome_final)
            contador += 1
        
        try: 
            os.rename(caminho_atual, caminho_final) 
            if not modo_debug: 
                print(f"-> SUCESSO! Renomeado para: '{nome_final}'") 
                
            # =========================================================
            # NOVO: REGISTRAR A LEITURA DO PDF NO HISTÓRICO JSON
            # =========================================================
            gerenciador_historico.registrar_resultado(
                cnpj=cnpj,
                certidao=nome_origem,      # Ex: "Federal" ou "Águas Lindas"
                validade=data_atualizacao, # A data limpa que o seu robô já encontrou
                status=status,             # Ex: "Negativa", "Positiva"
                observacao=""              # Deixa vazio, pois o PDF deu certo!
            )
            # =========================================================

        except Exception as e: 
            print(f"-> ERRO ao renomear: {e}")

    print(f"\n{'-'*50}\nAutomação concluída!")
