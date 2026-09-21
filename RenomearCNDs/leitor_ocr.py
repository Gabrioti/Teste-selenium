# leitor_ocr.py

import sys
import os
import pytesseract
from pdf2image import convert_from_path



def extrair_texto_com_ocr(caminho_pdf):
    print("-> Fonte corrompida! Acionando OCR...")
    texto_extraido = ""

    # ==========================================
    # LÓGICA INTELIGENTE DE CAMINHOS
    # ==========================================
    if getattr(sys, 'frozen', False):
        # 1. Se estiver rodando como .EXE:
        pasta_exe = os.path.dirname(sys.executable) # Pasta dist/ onde o main.exe está

        # Agora TUDO (Poppler e Tesseract) é pego da pasta Motores ao lado do .exe
        caminho_poppler = os.path.join(pasta_exe, 'Motores', 'poppler-25.12.0', 'Library', 'bin')
        
        caminho_tesseract = os.path.join(pasta_exe, 'Motores', 'tesseract.exe')
        pasta_tessdata = os.path.join(pasta_exe, 'Motores', 'tessdata')

    else:
        # 2. Se estiver rodando solto no VS Code:
        # Volta uma pasta (de Codigos para PROG_CND) para achar a Motores
        pasta_atual = os.path.dirname(os.path.abspath(__file__))

        caminho_poppler = os.path.join(pasta_atual, 'Motores', 'poppler-25.12.0', 'Library', 'bin')
        caminho_tesseract = os.path.join(pasta_atual, 'Motores', 'tesseract.exe')
        pasta_tessdata = os.path.join(pasta_atual, 'Motores', 'tessdata')

    # ==========================================
    # CONFIGURAÇÃO E EXECUÇÃO DO OCR
    # ==========================================
    pytesseract.pytesseract.tesseract_cmd = caminho_tesseract
    os.environ["TESSDATA_PREFIX"] = pasta_tessdata

    try:
        # Agora o robô sabe exatamente onde o Poppler está!
        imagens = convert_from_path(caminho_pdf, poppler_path=caminho_poppler)
        
        for imagem in imagens:
            texto = pytesseract.image_to_string(imagem, lang='por')
            texto_extraido += texto + "\n"
            
        return texto_extraido.upper()
        
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return ""