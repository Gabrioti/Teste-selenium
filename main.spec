# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_all

# Caminho raiz do projeto
project_root = os.path.dirname(os.path.abspath(SPEC))

# Coleta completa de todos os módulos, dados e binários do Selenium e webdriver_manager
datas_selenium, binaries_selenium, hidden_selenium = collect_all('selenium')
datas_wdm, binaries_wdm, hidden_wdm = collect_all('webdriver_manager')

# Coleta todos os módulos das cidades automaticamente
cidades_hiddenimports = [
    f'Cidades.{f[:-3]}'
    for f in os.listdir(os.path.join(project_root, 'Cidades'))
    if f.endswith('.py') and not f.startswith('__')
]

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=binaries_selenium + binaries_wdm,
    datas=[
        # Inclui a pasta inteira de Cidades como pacote Python
        (os.path.join(project_root, 'Cidades'), 'Cidades'),
        # Inclui o robô de CNDs (será chamado via subprocess)
        (os.path.join(project_root, 'RenomearCNDs'), 'RenomearCNDs'),
        # Inclui pasta de imagens
        (os.path.join(project_root, 'ImagensFederal'), 'ImagensFederal'),
        # Inclui pasta de tratamento de imagem
        (os.path.join(project_root, 'TratamentoImagem'), 'TratamentoImagem'),
        # Inclui arquivo dados.json base como modelo inicial para o executável
        (os.path.join(project_root, 'SQL', 'dados.json'), 'SQL'),
        # Inclui arquivo historico_cnds.json base como modelo inicial para o executável
        (os.path.join(project_root, 'SQL', 'historico_cnds.json'), 'SQL'),
    ] + datas_selenium + datas_wdm,
    hiddenimports=[
        # Módulos dentro da pasta Gerenciadores
        'Gerenciadores.gerenciador_cnpj',
        'Gerenciadores.gerenciador_pastas',
        'Gerenciadores.gerenciador_historico',

        # Módulos dentro da pasta Processos
        'Processos.teste_FEDERAL',
        'Processos.teste_ESTADUAL',
        'Processos.teste_TRABALISTA',
        'Processos.teste_COMPRASNET',
        'Processos.teste_FGTS',
        'Processos.teste_AGEHAB',

        # Módulos das Cidades (gerados dinamicamente acima)
        *cidades_hiddenimports,
        # Tkinter
        'tkinter',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.ttk',
        'tkinter.simpledialog',
    ] + hidden_selenium + hidden_wdm,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CND_Automatico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
