"""
Módulo para gerenciar cadastro, leitura e persistência de CNPJs em dados.json
"""
import os
import sys
import json
import importlib

# Pasta base do módulo (quando rodando como script)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def obter_caminho_dados():
    """
    Retorna o caminho absoluto do arquivo dados.json.
    """
    if getattr(sys, 'frozen', False):
        pasta_base = os.path.dirname(sys.executable)
        caminho_destino = os.path.join(pasta_base, "dados.json")
        if not os.path.exists(caminho_destino):
            caminho_empacotado = os.path.join(getattr(sys, '_MEIPASS', pasta_base), "dados.json")
            if os.path.exists(caminho_empacotado):
                try:
                    import shutil
                    shutil.copy2(caminho_empacotado, caminho_destino)
                except Exception as e:
                    print(f"⚠️ Erro ao copiar dados.json empacotado: {e}")
        return caminho_destino
    else:
        # 1. Recua da pasta Gerenciadores para a raiz (Teste selenium)
        pasta_raiz = os.path.dirname(_BASE_DIR)
        
        # 2. Aponta para a pasta SQL onde o dados.json está agora
        return os.path.join(pasta_raiz, "SQL", "dados.json")

def carregar_banco_dados():
    """
    Lê o arquivo dados.json e retorna o dicionário completo com garantia
    das chaves 'mapa_municipal', 'mapa_matriz' e 'nomes_empreendimentos'.
    """
    caminho = obter_caminho_dados()
    if not os.path.exists(caminho):
        return {"mapa_municipal": {}, "mapa_matriz": {}, "nomes_empreendimentos": {}}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            db = json.load(f)
            if not isinstance(db, dict):
                db = {}
            if "mapa_municipal" not in db or not isinstance(db["mapa_municipal"], dict):
                db["mapa_municipal"] = {}
            if "mapa_matriz" not in db or not isinstance(db["mapa_matriz"], dict):
                db["mapa_matriz"] = {}
            if "nomes_empreendimentos" not in db or not isinstance(db["nomes_empreendimentos"], dict):
                db["nomes_empreendimentos"] = {}
            return db
    except Exception as e:
        print(f"❌ Erro ao carregar dados.json ({caminho}): {e}")
        return {"mapa_municipal": {}, "mapa_matriz": {}, "nomes_empreendimentos": {}}

def salvar_banco_dados(db):
    """
    Salva o dicionário completo no arquivo dados.json de forma segura e formatada.
    """
    caminho = obter_caminho_dados()
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar dados.json ({caminho}): {e}")
        return False

# ====================================================================
# CONSULTAS GERAIS
# ====================================================================

def obter_mapa_municipal():
    """
    Retorna o dicionário completo mapa_municipal {CNPJ: [cidades...]}.
    """
    return carregar_banco_dados()["mapa_municipal"]

def obter_todos_vinculos_matriz():
    """
    Retorna o dicionário completo de vínculos {CNPJ_FILIAL: CNPJ_MATRIZ}.
    """
    return carregar_banco_dados()["mapa_matriz"]

def obter_matriz_do_cnpj(cnpj_filial):
    """
    Retorna o CNPJ da matriz vinculada à filial, ou None se não houver vínculo.
    """
    return carregar_banco_dados()["mapa_matriz"].get(cnpj_filial)

def salvar_vinculo_matriz(cnpj_filial, cnpj_matriz):
    """
    Salva ou remove o vínculo de matriz de uma filial.
    Se cnpj_matriz for None ou vazio, o vínculo é removido.
    """
    db = carregar_banco_dados()
    if cnpj_matriz:
        db["mapa_matriz"][cnpj_filial] = cnpj_matriz
    else:
        db["mapa_matriz"].pop(cnpj_filial, None)
    return salvar_banco_dados(db)

def obter_nome_empreendimento(cnpj):
    """
    Retorna o nome do empreendimento associado ao CNPJ, se cadastrado.
    """
    return carregar_banco_dados()["nomes_empreendimentos"].get(cnpj, "")

def cnpj_ja_existe(cnpj):
    """
    Verifica se o CNPJ já está cadastrado no mapa municipal.
    """
    return cnpj in carregar_banco_dados()["mapa_municipal"]

def listar_cnpjs_cadastrados():
    """
    Retorna a lista ordenada de todos os CNPJs atualmente cadastrados.
    """
    return sorted(list(carregar_banco_dados()["mapa_municipal"].keys()))

def obter_cidades_cnpj(cnpj):
    """
    Retorna a lista de cidades configuradas para o CNPJ indicado.
    """
    lista = carregar_banco_dados()["mapa_municipal"].get(cnpj, [])
    return [dict(c) for c in lista]

def adicionar_cnpj_em_dados(cnpj, cidades_config, nome_empreendimento=None):
    """
    Adiciona ou atualiza um CNPJ no banco de dados.
    """
    return salvar_atualizacao_cnpj(cnpj, cidades_config, nome_empreendimento=nome_empreendimento)

def salvar_atualizacao_cnpj(cnpj, novas_cidades_config, nome_empreendimento=None):
    """
    Atualiza as configurações de cidades de um CNPJ e seu nome no banco de dados.
    """
    db = carregar_banco_dados()
    db["mapa_municipal"][cnpj] = novas_cidades_config
    if nome_empreendimento:
        db["nomes_empreendimentos"][cnpj] = nome_empreendimento.strip()
    return salvar_banco_dados(db)

def remover_cnpj_de_dados(cnpj):
    """
    Remove o CNPJ especificado do mapa municipal, dos vínculos de matriz
    e dos nomes de empreendimentos.
    """
    db = carregar_banco_dados()
    removido = False
    if cnpj in db["mapa_municipal"]:
        del db["mapa_municipal"][cnpj]
        removido = True
    db["mapa_matriz"].pop(cnpj, None)
    db["nomes_empreendimentos"].pop(cnpj, None)
    if removido:
        salvar_banco_dados(db)
    return removido

def listar_cidades_manuais_ou_pendentes():
    """
    Retorna uma lista de todas as cidades onde automatizado é False, None ou não definido.
    """
    db = carregar_banco_dados()
    pendentes = []
    for cnpj, lista_cidades in db["mapa_municipal"].items():
        if not isinstance(lista_cidades, list):
            continue
        for c in lista_cidades:
            if not isinstance(c, dict):
                continue
            aut = c.get("automatizado")
            if aut is False or aut is None or aut == "":
                pendentes.append({
                    "cnpj": cnpj,
                    "cidade": c.get("cidade", "Desconhecida"),
                    "automatizado": aut,
                    "url": c.get("url", "")
                })
    return pendentes

def listar_cidades_disponiveis():
    """
    Retorna lista de cidades disponíveis na pasta Cidades.
    Formato: {"Formosa": {"arquivo": ..., "url": ..., "automatizado": bool}, ...}
    """
    # 1. Sai da pasta 'Gerenciadores' e volta para a raiz do projeto
    pasta_raiz = os.path.dirname(_BASE_DIR)
    
    # 2. Aponta para a pasta 'Cidades' que está na raiz
    cidades_dir = os.path.join(pasta_raiz, "Cidades")
    cidades = {}
    
    if not os.path.exists(cidades_dir):
        return cidades

    arquivos = sorted([f for f in os.listdir(cidades_dir) 
                      if f.endswith(".py") and f != "__init__.py"])
    
    for arquivo in arquivos:
        nome_modulo = arquivo.replace(".py", "")
        nome_cidade = nome_modulo.replace("_", " ")
        
        try:
            modulo = importlib.import_module(f"Cidades.{nome_modulo}")
            url = getattr(modulo, "siteCadastro", "")
            cidades[nome_cidade] = {
                "arquivo": nome_modulo,
                "url": url,
                "automatizado": bool(url)
            }
        except ImportError:
            print(f"⚠️ Erro ao importar {nome_modulo}")
            continue
    
    return cidades
