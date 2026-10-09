# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_all

# Caminho raiz do projeto
project_root = os.path.dirname(os.path.abspath(SPEC))

# Coleta completa de todos os módulos, dados e binários do Selenium e webdriver_manager
datas_selenium, binaries_selenium, hidden_selenium = collect_all('selenium')
datas_wdm, binaries_wdm, hidden_wdm = collect_all('webdriver_manager')
datas_ddddocr, binaries_ddddocr, hidden_ddddocr = collect_all('ddddocr')
datas_onnxruntime, binaries_onnxruntime, hidden_onnxruntime = collect_all('onnxruntime')

# Coleta todos os módulos das cidades automaticamente
cidades_hiddenimports = [
    f'Cidades.{f[:-3]}'
    for f in os.listdir(os.path.join(project_root, 'Cidades'))
    if f.endswith('.py') and not f.startswith('__')
]

a = Analysis(
    ['main.py'],
    pathex=[project_root, os.path.join(project_root, 'RenomearCNDs')],
    binaries=(
        binaries_selenium
        + binaries_wdm
        + binaries_ddddocr
        + binaries_onnxruntime
    ),
    datas=[
        # Recursos OCR; o código correspondente é empacotado como módulos Python.
        (
            os.path.join(project_root, 'RenomearCNDs', 'Motores'),
            os.path.join('RenomearCNDs', 'Motores'),
        ),
        # Inclui arquivo dados.json base como modelo inicial para o executável
        (os.path.join(project_root, 'SQL', 'dados.json'), 'SQL'),
        # Inclui arquivo historico_cnds.json base como modelo inicial para o executável
        (os.path.join(project_root, 'SQL', 'historico_cnds.json'), 'SQL'),
    ] + datas_selenium + datas_wdm + datas_ddddocr + datas_onnxruntime,
    hiddenimports=[
        # Módulos dentro da pasta Gerenciadores
        'Gerenciadores.gerenciador_cnpj',
        'Gerenciadores.gerenciador_pastas',
        'Gerenciadores.gerenciador_historico',
        'Gerenciadores.gerenciador_caminhos',

        # Módulos dentro da pasta Processos
        'Processos.teste_FEDERAL',
        'Processos.teste_ESTADUAL',
        'Processos.teste_TRABALISTA',
        'Processos.teste_COMPRASNET',
        'Processos.teste_FGTS',
        'Processos.teste_AGEHAB',
        'central',
        'processador',
        'regras',
        'leitor_ocr',

        # Módulos das Cidades (gerados dinamicamente acima)
        *cidades_hiddenimports,
        # Tkinter
        'tkinter',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.ttk',
        'tkinter.simpledialog',
    ] + hidden_selenium + hidden_wdm + hidden_ddddocr + hidden_onnxruntime,
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
    [],
    exclude_binaries=True,
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

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CND_Automatico_Test',
)
