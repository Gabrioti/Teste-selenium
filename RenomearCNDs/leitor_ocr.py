# leitor_ocr.py

import os
import pytesseract
from pdf2image import convert_from_path

from Gerenciadores.gerenciador_caminhos import obter_pasta_recursos


def extrair_texto_com_ocr(caminho_pdf):
    print("-> Fonte corrompida! Acionando OCR...")
    texto_extraido = ""

    # ==========================================
    # LÓGICA INTELIGENTE DE CAMINHOS
    # ==========================================
    pasta_motores = os.path.join(
        obter_pasta_recursos(),
        "RenomearCNDs",
        "Motores",
    )
    caminho_poppler = os.path.join(
        pasta_motores,
        "poppler-25.12.0",
        "Library",
        "bin",
    )
    caminho_tesseract = os.path.join(pasta_motores, "tesseract.exe")
    pasta_tessdata = os.path.join(pasta_motores, "tessdata")

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