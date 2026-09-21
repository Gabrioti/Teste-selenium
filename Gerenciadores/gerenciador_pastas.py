"""
Módulo para gerenciamento de pastas de Construtoras e Empreendimentos na rede.
Suporta caminho mapeado (N:) e caminho UNC (\\\\10.6.57.8\\coogesap\\16. CERTIDÕES\\1. Empresas).
"""
import os
import re
import shutil


# Caminhos padrão para a raiz das empresas
CAMINHO_MAPEA_N = r"N:\16. CERTIDÕES\1. Empresas"
CAMINHO_REDE_UNC = r"\\10.6.57.8\coogesap\16. CERTIDÕES\1. Empresas"


def obter_pasta_raiz_empresas():
    """
    Retorna o caminho acessível da raiz das empresas na rede.
    Prioriza o drive N: se existir; caso contrário, utiliza o caminho UNC direto.
    """
    if os.path.exists(CAMINHO_MAPEA_N):
        return CAMINHO_MAPEA_N
    if os.path.exists(CAMINHO_REDE_UNC):
        return CAMINHO_REDE_UNC
    raise FileNotFoundError(
        f"Não foi possível acessar a pasta de empresas na rede.\n"
        f"Verifique se o drive N: ou a rede '{CAMINHO_REDE_UNC}' estão acessíveis."
    )


def sanitizar_nome_pasta(nome):
    """
    Remove ou substitui caracteres proibidos pelo sistema de arquivos do Windows:
    < > : " / \\ | ? *
    Remove espaços extras no início e fim.
    """
    if not nome:
        return ""
    # Substitui caracteres inválidos por vazio
    nome_limpo = re.sub(r'[<>:"/\\|?*]', '', nome)
    nome_limpo = " ".join(nome_limpo.split()).strip()
    return nome_limpo


def listar_construtoras():
    """
    Retorna a lista ordenada de nomes de pastas de construtoras existentes na raiz de empresas.
    """
    raiz = obter_pasta_raiz_empresas()
    itens = [
        d for d in os.listdir(raiz)
        if os.path.isdir(os.path.join(raiz, d)) and not d.startswith(".")
    ]
    return sorted(itens, key=lambda s: s.lower())


def criar_pasta_construtora(nome_construtora):
    """
    Cria uma nova pasta de construtora na raiz de empresas.
    Retorna o caminho completo da pasta criada.
    """
    nome_sanitizado = sanitizar_nome_pasta(nome_construtora).upper()
    if not nome_sanitizado:
        raise ValueError("O nome da construtora não pode ser vazio ou conter apenas caracteres inválidos.")

    raiz = obter_pasta_raiz_empresas()
    caminho_destino = os.path.join(raiz, nome_sanitizado)

    if os.path.exists(caminho_destino):
        raise FileExistsError(f"A construtora '{nome_sanitizado}' já possui pasta cadastrada na rede.")

    os.makedirs(caminho_destino, exist_ok=True)
    return caminho_destino


def listar_empreendimentos(nome_construtora):
    """
    Retorna a lista ordenada de pastas de empreendimentos contidas dentro de uma construtora.
    """
    if not nome_construtora:
        return []
    raiz = obter_pasta_raiz_empresas()
    pasta_construtora = os.path.join(raiz, nome_construtora)
    if not os.path.exists(pasta_construtora) or not os.path.isdir(pasta_construtora):
        return []

    itens = [
        d for d in os.listdir(pasta_construtora)
        if os.path.isdir(os.path.join(pasta_construtora, d)) and not d.startswith(".")
    ]
    return sorted(itens, key=lambda s: s.lower())


def criar_pasta_empreendimento(nome_construtora, nome_empreendimento, cnpj):
    """
    Cria a pasta do empreendimento dentro da pasta da construtora.
    Padrão de nomenclatura: '<NOME DO EMPREENDIMENTO> - <CNPJ>'
    Exemplo: 'SPE RESERVA 1 LTDA - 37407156000100'
    """
    if not nome_construtora:
        raise ValueError("Selecione ou informe uma construtora válida.")

    nome_emp_limpo = sanitizar_nome_pasta(nome_empreendimento).upper()
    if not nome_emp_limpo:
        raise ValueError("O nome do empreendimento não pode ser vazio.")

    # Garante apenas 14 dígitos numéricos do CNPJ
    cnpj_numeros = "".join(re.findall(r'\d+', cnpj))
    if len(cnpj_numeros) != 14:
        raise ValueError(f"O CNPJ informado deve conter 14 dígitos numéricos. Informado: '{cnpj}'")

    raiz = obter_pasta_raiz_empresas()
    pasta_construtora = os.path.join(raiz, nome_construtora)
    if not os.path.exists(pasta_construtora):
        os.makedirs(pasta_construtora, exist_ok=True)

    nome_pasta_final = f"{nome_emp_limpo} - {cnpj_numeros}"
    caminho_empreendimento = os.path.join(pasta_construtora, nome_pasta_final)

    if os.path.exists(caminho_empreendimento):
        return caminho_empreendimento  # Já existe a pasta

    os.makedirs(caminho_empreendimento, exist_ok=True)
    return caminho_empreendimento


def contar_conteudo_pasta(caminho_pasta):
    """
    Percorre a pasta recursivamente e retorna:
    - total de arquivos
    - total de subpastas
    - lista com os primeiros 5 nomes de arquivos (para exibir amostra no alerta)
    """
    if not os.path.exists(caminho_pasta):
        return 0, 0, []

    total_arquivos = 0
    total_subpastas = 0
    amostras = []

    for root, dirs, files in os.walk(caminho_pasta):
        total_subpastas += len(dirs)
        for f in files:
            total_arquivos += 1
            if len(amostras) < 5:
                amostras.append(f)

    return total_arquivos, total_subpastas, amostras


def excluir_pasta_segura(caminho_pasta):
    """
    Exclui a pasta indicada garantindo que esteja dentro do escopo de pasta_raiz_empresas.
    Evita qualquer risco de apagar diretórios do sistema ou fora do compartilhamento.
    """
    if not os.path.exists(caminho_pasta):
        raise FileNotFoundError(f"A pasta '{caminho_pasta}' não foi encontrada.")

    raiz = obter_pasta_raiz_empresas()
    caminho_abs = os.path.abspath(caminho_pasta)
    raiz_abs = os.path.abspath(raiz)

    # Verificação estrita de segurança: o caminho deve ser um subdiretório direto ou indireto da raiz
    if not caminho_abs.startswith(raiz_abs) or caminho_abs == raiz_abs:
        raise PermissionError("Operação negada por segurança: não é permitido apagar a raiz ou caminhos externos.")

    shutil.rmtree(caminho_abs)
    return True
