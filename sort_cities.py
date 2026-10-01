import re, sys
path = r'n:\19. FERRAMENTAS\Teste selenium\cidadesAdicionar'
lines = open(path, encoding='utf-8').read().splitlines()
records = []
for line in lines:
    m = re.match(r"(\d+):\s*(\d+)\t ([^\t]+)\t(.*)", line)
    if not m:
        continue
    idx, num, city, site = m.groups()
    site = site.strip()
    typ = 'url' if site.lower().startswith('http') else ('ok' if site.lower() == 'ok' else 'notfound')
    records.append((typ, city.lower(), line))
priority = {'url': 0, 'ok': 1, 'notfound': 2}
records.sort(key=lambda x: (priority.get(x[0], 3), x[1]))
with open(path, 'w', encoding='utf-8') as f:
    for _, _, line in records:
        f.write(line + '\n')
print('Sorting completed')
