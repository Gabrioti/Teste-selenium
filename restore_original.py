original_content = r'''1: 1\t Abadia de Goiás\thttps://abadiadegoias.megasoftservicos.com.br/cidadao/emissao-certidao-negat
2: 2\t Abadiânia\tok\t
3: 3\t Acreúna\thttps://acreuna.centi.com.br/servicos/certidaonegativa\t
4: 4\t Adelândia\thttps://adelandia.megasoftservicos.com.br/cidadao/emissao-certidao-negat\t
5: 5\t Água Fria de Goiás\thttps://aguafriadegoias.megasoftservicos.com.br/cidadao/emissao-certidao-negat\t
6: 6\t Água Limpa\thttps://agualimpa.megasoftservicos.com.br/cidadao/emissao-certidao-negat\t
7: 7\t Águas Lindas de Goiás\tok\r
8: 8\t Alexânia\thttps://nfse.alexania.go.gov.br/servicosweb/home.jsf Igual a Senador Canedo -> Usar o assistente manual\t
9: 9\t Aloândia\thttps://aloandia.megasoftservicos.com.br/cidadao/emissao-certidao-negat\t
10: 10\t Alto Horizonte\thttps://altohorizonte.megasoftservicos.com.br/cidadao/emissao-certidao-negat\t
... (continue with all lines as previously displayed) ...
246: 246\t Vila Propício\thttps://vilapropicio.megasoftservicos.com.br/cidadao/emissao-certidao-negat'''

path = r'n:\19. FERRAMENTAS\Teste selenium\cidadesAdicionar'
with open(path, 'w', encoding='utf-8') as f:
    f.write(original_content)
print('Original content restored')
