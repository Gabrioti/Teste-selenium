#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar a variável siteCadastro em todos os arquivos de cidades
"""
import os

# Mapeamento de cidades para URLs baseado em dados.py
urls_map = {
    "Formosa": "https://formosa.prodataweb.inf.br/sig/app.html#/servicosonline/debito-contribuinte",
    "Águas_Lindas": "https://aguaslindas.prodataweb.inf.br/sig/app.html#/servicosonline/debito-contribuinte",
    "Cidade_Ocidental": "https://gestao.cidadeocidental.go.gov.br/sig/app.html#/servicosonline/debito-contribuinte",
    "Valparaiso": "https://nfe.valparaisodegoias.go.gov.br/Certidao_Index.aspx",
    "Catalão": "https://sig.catalao.go.gov.br/sig/app.html#/servicosonline/debito-contribuinte",
    "Aparecida_de_Goiânia": "https://sigp.aparecida.go.gov.br/sig/app.html#/servicosonline/debito-contribuinte",
    "Luiziana": "https://luziania.prodataweb.inf.br/sig/app.html#/servicosonline/debito-contribuinte",
    "Goianésia": "https://aplicacoes.goianesia.go.gov.br/sig/app.html#/servicosonline/debito-contribuinte",
    "Goiânia": "https://www.goiania.go.gov.br/sistemas/sccer/asp/sccer00300f0.asp",
}

cidades_dir = "Cidades"
arquivos = sorted([f for f in os.listdir(cidades_dir) if f.endswith(".py") and f != "__init__.py"])

print("=" * 60)
print("ADICIONANDO VARIÁVEL siteCadastro EM TODOS OS ARQUIVOS")
print("=" * 60)

for arquivo in arquivos:
    nome_arquivo = arquivo.replace(".py", "")
    url = urls_map.get(nome_arquivo, "")
    status = "✓ COM URL" if url else "❌ SEM URL"
    
    caminho = os.path.join(cidades_dir, arquivo)
    
    # Lê o arquivo
    with open(caminho, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    # Verifica se siteCadastro já existe
    if any("siteCadastro" in linha for linha in linhas):
        print(f"  {status}: {arquivo} - JÁ TEM siteCadastro")
        continue
    
    # Encontra o local para inserir (após últimos imports)
    idx_insercao = 0
    for i, linha in enumerate(linhas):
        if linha.startswith('import ') or linha.startswith('from '):
            idx_insercao = i + 1
    
    # Adiciona a variável após imports com uma linha em branco
    siteCadastro_line = f'\nsiteCadastro = "{url}"\n\n'
    linhas.insert(idx_insercao, siteCadastro_line)
    
    # Escreve de volta
    with open(caminho, 'w', encoding='utf-8') as f:
        f.writelines(linhas)
    
    print(f"  {status}: {arquivo} - ADICIONADO")

print("\n" + "=" * 60)
print("✅ CONCLUÍDO! Todos os arquivos foram atualizados!")
print("=" * 60)
