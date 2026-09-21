import os
import sys
import json

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def obter_caminho_historico():
    """Garante que o arquivo historico_cnds.json seja salvo na pasta SQL."""
    if getattr(sys, 'frozen', False):
        pasta_base = os.path.dirname(sys.executable)
        caminho = os.path.join(pasta_base, "SQL", "historico_cnds.json")
    else:
        pasta_raiz = os.path.dirname(_BASE_DIR)
        caminho = os.path.join(pasta_raiz, "SQL", "historico_cnds.json")
    
    # Garante que a pasta SQL exista
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    return caminho

def carregar_historico():
    """Lê o histórico atual. Se não existir, retorna um dicionário vazio."""
    caminho = obter_caminho_historico()
    if not os.path.exists(caminho):
        return {}
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def registrar_resultado(cnpj, certidao, validade, status, observacao):
    """Salva o resultado de uma coleta no JSON do histórico."""
    
    # 1. BLINDAGEM: Garante que o CNPJ seja sempre apenas números!
    cnpj_limpo = "".join(c for c in str(cnpj) if c.isdigit())
    
    historico = carregar_historico()
    
    if cnpj_limpo not in historico:
        historico[cnpj_limpo] = {}
        
    historico[cnpj_limpo][certidao] = {
        "validade": validade,
        "status": status,
        "observacao": observacao
    }
    
    caminho = obter_caminho_historico()
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    # ISSO AQUI FORÇA A CRIAÇÃO DO ARQUIVO PARA TESTARMOS
    print("Testando a criação do Banco de Dados de Histórico...")
    
    # Simula um robô salvando um resultado qualquer
    registrar_resultado(
        cnpj="12345678000199", 
        certidao="Teste de Sistema", 
        validade="31/12/2099", 
        status="Negativa", 
        observacao="Arquivo criado com sucesso!"
    )
    
    caminho = obter_caminho_historico()
    print(f"Verifique se o arquivo apareceu na pasta: {caminho}")