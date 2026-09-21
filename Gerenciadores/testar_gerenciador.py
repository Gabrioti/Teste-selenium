#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gerenciador_cnpj

print("Testando gerenciador_cnpj...")
print("=" * 60)

cidades = gerenciador_cnpj.listar_cidades_disponiveis()

print(f"\n✅ Total de cidades encontradas: {len(cidades)}\n")

for cidade, info in sorted(cidades.items()):
    auto = "✓ AUTO" if info["automatizado"] else "❌ MANUAL"
    url_display = info["url"][:40] + "..." if len(info["url"]) > 40 else info["url"]
    print(f"{auto}: {cidade:<30} | {url_display}")

print("\n" + "=" * 60)
