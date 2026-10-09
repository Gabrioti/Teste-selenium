"""
Módulo para gerenciar cadastro, leitura e persistência de CNPJs em dados.json
"""
import os
import sys
import json
import importlib
import time

from Gerenciadores.gerenciador_caminhos import (
    bloquear_dados_compartilhados,
    gravar_json_atomico,
    obter_pasta_dados_compartilhados,
    obter_pasta_dados_usuario,
    obter_pasta_recursos,
)

# Pasta base do módulo (quando rodando como script)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def obter_caminho_dados():
    """
    Retorna o caminho absoluto do arquivo dados.json.
    """
    caminho = os.path.join(obter_pasta_dados_compartilhados(), "dados.json")
    with bloquear_dados_compartilhados():
        if not os.path.exists(caminho):
            caminho_empacotado = os.path.join(
                obter_pasta_recursos(),
                "SQL",
                "dados.json",
            )
            if not os.path.isfile(caminho_empacotado):
                raise FileNotFoundError(
                    f"Base inicial de dados não encontrada: {caminho_empacotado}"
                )
            with open(caminho_empacotado, "r", encoding="utf-8") as arquivo:
                gravar_json_atomico(caminho, json.load(arquivo))
    return caminho


def _normalizar_banco_dados(db):
    if not isinstance(db, dict):
        raise ValueError("O conteúdo de dados.json precisa ser um objeto JSON.")
    for chave in ("mapa_municipal", "mapa_matriz", "nomes_empreendimentos"):
        if chave not in db:
            db[chave] = {}
        elif not isinstance(db[chave], dict):
            raise ValueError(f"A chave '{chave}' de dados.json precisa ser um objeto.")
    return db


def _carregar_json(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def _caminho_metadados():
    return os.path.join(obter_pasta_dados_compartilhados(), "metadados_compartilhados.json")


def _carregar_metadados():
    metadados = _carregar_json(_caminho_metadados(), {})
    if not isinstance(metadados, dict):
        raise ValueError("O arquivo de metadados compartilhados não é válido.")
    metadados.setdefault("dados", {})
    if not isinstance(metadados["dados"], dict):
        raise ValueError("Os metadados de dados compartilhados não são válidos.")
    return metadados


def _salvar_banco_dados_bloqueado(db):
    caminho = os.path.join(obter_pasta_dados_compartilhados(), "dados.json")
    db = _normalizar_banco_dados(db)
    anterior = _normalizar_banco_dados(
        _carregar_json(caminho, {
            "mapa_municipal": {},
            "mapa_matriz": {},
            "nomes_empreendimentos": {},
        })
    )
    metadados = _carregar_metadados()
    timestamps = metadados["dados"]
    agora = time.time()

    for secao in ("mapa_municipal", "mapa_matriz", "nomes_empreendimentos"):
        registros = timestamps.setdefault(secao, {})
        if not isinstance(registros, dict):
            raise ValueError(f"Metadados inválidos para '{secao}'.")
        for chave in set(anterior[secao]) | set(db[secao]):
            if anterior[secao].get(chave) != db[secao].get(chave):
                registros[chave] = agora

    gravar_json_atomico(caminho, db)
    gravar_json_atomico(_caminho_metadados(), metadados)


def migrar_dados_locais():
    """Mescla a cópia antiga deste usuário no compartilhamento uma única vez."""
    if not getattr(sys, "frozen", False):
        return

    pasta_usuario = obter_pasta_dados_usuario()
    caminho_marcador = os.path.join(
        pasta_usuario,
        "dados_compartilhados_v1_migrados",
    )
    caminho_local = os.path.join(pasta_usuario, "SQL", "dados.json")
    if os.path.exists(caminho_marcador):
        return

    with bloquear_dados_compartilhados():
        caminho_compartilhado = os.path.join(
            obter_pasta_dados_compartilhados(),
            "dados.json",
        )
        if not os.path.exists(caminho_compartilhado):
            caminho_empacotado = os.path.join(
                obter_pasta_recursos(),
                "SQL",
                "dados.json",
            )
            if not os.path.isfile(caminho_empacotado):
                raise FileNotFoundError(
                    f"Base inicial de dados não encontrada: {caminho_empacotado}"
                )
            with open(caminho_empacotado, "r", encoding="utf-8") as arquivo:
                atual = _normalizar_banco_dados(json.load(arquivo))
            gravar_json_atomico(caminho_compartilhado, atual)

        if os.path.isfile(caminho_local):
            local = _normalizar_banco_dados(_carregar_json(caminho_local, {}))
            atual = _normalizar_banco_dados(_carregar_json(caminho_compartilhado, {}))
            metadados = _carregar_metadados()
            timestamps = metadados["dados"]
            data_local = os.path.getmtime(caminho_local)
            data_compartilhada = os.path.getmtime(caminho_compartilhado)
            alterado = False

            for secao in ("mapa_municipal", "mapa_matriz", "nomes_empreendimentos"):
                marcas = timestamps.setdefault(secao, {})
                if not isinstance(marcas, dict):
                    raise ValueError(f"Metadados inválidos para '{secao}'.")
                for chave, valor in local[secao].items():
                    instante_atual = marcas.setdefault(chave, data_compartilhada)
                    if chave not in atual[secao] or data_local > instante_atual:
                        atual[secao][chave] = valor
                        marcas[chave] = data_local
                        alterado = True

            if alterado:
                gravar_json_atomico(caminho_compartilhado, atual)
            gravar_json_atomico(_caminho_metadados(), metadados)

        with open(caminho_marcador, "w", encoding="utf-8") as marcador:
            marcador.write("ok")

def carregar_banco_dados():
    """
    Lê o arquivo dados.json e retorna o dicionário completo com garantia
    das chaves 'mapa_municipal', 'mapa_matriz' e 'nomes_empreendimentos'.
    """
    caminho = obter_caminho_dados()
    db = _normalizar_banco_dados(
        _carregar_json(caminho, {
            "mapa_municipal": {},
            "mapa_matriz": {},
            "nomes_empreendimentos": {},
        })
    )
    return db

def salvar_banco_dados(db):
    """
    Salva o dicionário completo no arquivo dados.json de forma segura e formatada.
    """
    obter_caminho_dados()
    with bloquear_dados_compartilhados():
        _salvar_banco_dados_bloqueado(db)
    return True


def _atualizar_banco_dados(atualizar):
    caminho = obter_caminho_dados()
    with bloquear_dados_compartilhados():
        db = _normalizar_banco_dados(
            _carregar_json(
                caminho,
                {
                    "mapa_municipal": {},
                    "mapa_matriz": {},
                    "nomes_empreendimentos": {},
                },
            )
        )
        atualizar(db)
        _salvar_banco_dados_bloqueado(db)
    return True

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
    def atualizar(db):
        if cnpj_matriz:
            db["mapa_matriz"][cnpj_filial] = cnpj_matriz
        else:
            db["mapa_matriz"].pop(cnpj_filial, None)

    return _atualizar_banco_dados(atualizar)

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
    def atualizar(db):
        db["mapa_municipal"][cnpj] = novas_cidades_config
        if nome_empreendimento:
            db["nomes_empreendimentos"][cnpj] = nome_empreendimento.strip()

    return _atualizar_banco_dados(atualizar)

def remover_cnpj_de_dados(cnpj):
    """
    Remove o CNPJ especificado do mapa municipal, dos vínculos de matriz
    e dos nomes de empreendimentos.
    """
    removido = False

    def atualizar(db):
        nonlocal removido
        if cnpj in db["mapa_municipal"]:
            del db["mapa_municipal"][cnpj]
            removido = True
        db["mapa_matriz"].pop(cnpj, None)
        db["nomes_empreendimentos"].pop(cnpj, None)

    _atualizar_banco_dados(atualizar)
    return removido

def listar_cidades_manuais_ou_pendentes():
    """
    Retorna uma lista de todas as cidades onde a tecnologia é "centi", "manual" ou não definida.
    """
    db = carregar_banco_dados()
    pendentes = []
    for cnpj, lista_cidades in db.get("mapa_municipal", {}).items():
        if not isinstance(lista_cidades, list):
            continue
        for c in lista_cidades:
            if not isinstance(c, dict):
                continue
            
            # Pega a chave tecnologia (se não existir, usa 'manual' como padrão seguro)
            tech = str(c.get("tecnologia", c.get("automatizado", "manual"))).lower()
            
            # Se for 'centi', 'manual' ou tiver valor em branco
            if tech in ["centi", "manual", "false", "none", ""]:
                pendentes.append({
                    "cnpj": cnpj,
                    "cidade": c.get("cidade", "Desconhecida"),
                    "tecnologia": tech,
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
