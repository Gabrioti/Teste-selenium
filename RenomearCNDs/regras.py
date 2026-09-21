# regras.py

# ==========================================
# 1. FUNÇÃO DETETIVE
# ==========================================
def identificar_cnd(texto):
    if "FUNDO DE GARANTIA" in texto or "FGTS" in texto or "CAIXA ECONOMICA FEDERAL" in texto:
        return "FGTS", "6"
    elif "SICAF" in texto or "COMPRASNET" in texto or "SISTEMA DE CADASTRAMENTO UNIFICADO" in texto or "CADASTRO UNIFICADO DE FORNECEDORES" in texto:
        return "Comprasnet", "5"
    elif "ESTADO DE GOIAS" in texto or "RECEITA ESTADUAL" in texto or "FAZENDA PUBLICA ESTADUAL" in texto or "GOVERNO DO " in texto:
        if "DISTRITO FEDERAL" in texto:
            return "Estadual DF", "2"
        else:
            return "Estadual", "2"
    elif "AGEHAB" in texto or "AGÊNCIA GOIANA DE HABITAÇÃO" in texto or "AGENCIA GOIANA DE HABITACAO" in texto:
        return "AGEHAB", "7"
    elif "JUSTIÇA DO TRABALHO" in texto or "DÉBITOS TRABALHISTAS" in texto:
        return "Trabalhista", "4"
    elif "MUNICIPAL" in texto or "PREFEITURA" in texto or "MUNICÍPIO" in texto:
        return "Municipal", "3"
    elif "RECEITA FEDERAL" in texto or "FAZENDA NACIONAL" in texto or "MINISTÉRIO DA FAZENDA" in texto:
        return "Federal", "1"
    return None, None