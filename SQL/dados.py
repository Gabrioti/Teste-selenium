"""
Módulo de compatibilidade e acesso dinâmico aos dados do sistema.
Todos os dados reais são armazenados e persistidos em dados.json.
"""
import sys
from Gerenciadores import gerenciador_cnpj

def __getattr__(name):
    """
    Permite acesso dinâmico em tempo real aos dados atualizados em dados.json:
    - dados.mapa_municipal
    - dados.mapa_matriz
    - dados.nomes_empreendimentos
    """
    if name == "mapa_municipal":
        return gerenciador_cnpj.obter_mapa_municipal()
    elif name == "mapa_matriz":
        return gerenciador_cnpj.obter_todos_vinculos_matriz()
    elif name == "nomes_empreendimentos":
        return gerenciador_cnpj.carregar_banco_dados().get("nomes_empreendimentos", {})
    raise AttributeError(f"Módulo 'dados' não possui o atributo '{name}'")

def __dir__():
    return ["mapa_municipal", "mapa_matriz", "nomes_empreendimentos"]
