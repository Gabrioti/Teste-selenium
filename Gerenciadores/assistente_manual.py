import os
import shutil
import webbrowser
import pyperclip
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import pyautogui

def solicitar_acao_manual(cnpj, site, pasta_download, nome_orgao="Órgão"):
    """
    Abre o navegador, copia o CNPJ e lança um assistente de tela interativo 
    para coleta de PDFs em sites com bloqueios severos ou CAPTCHAs intransponíveis.
    """
    os.makedirs(pasta_download, exist_ok=True)
    pyperclip.copy(cnpj)

    try:
        webbrowser.open(site)
    except Exception as e:
        return False, f"Falha ao abrir navegador: {e}"

    resultado = {"sucesso": False, "mensagem": "Cancelado pelo usuário ou timeout."}
    
    janela = tk.Tk()
    janela.title(f"Assistente {nome_orgao} - {cnpj}")
    janela.geometry("350x180-10-60")
    janela.attributes("-topmost", True)
    janela.configure(bg="#f8fafc")

    lbl_instrucao = tk.Label(
        janela, 
        text=f"CNPJ copiado: {cnpj}\n\nCole no site, resolva o Captcha\ne selecione a opção abaixo:", 
        bg="#f8fafc", 
        font=("Segoe UI", 10)
    )
    lbl_instrucao.pack(pady=10)

    def acao_sucesso():
        filepath = filedialog.askopenfilename(
            title=f"Selecione o PDF gerado ({nome_orgao})",
            filetypes=[("PDF Files", "*.pdf")],
            parent=janela
        )
        if filepath:
            try:
                nome_arq = os.path.basename(filepath)
                destino = os.path.join(pasta_download, f"{nome_orgao}_{cnpj}_{nome_arq}")
                shutil.copy(filepath, destino)
                
                resultado["sucesso"] = True
                resultado["mensagem"] = ""
                pyautogui.hotkey('ctrl', 'w')
                janela.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao anexar arquivo: {e}")

    def acao_falha():
        motivo = simpledialog.askstring(
            "Reportar Erro", 
            f"Cole ou digite a mensagem de erro do portal {nome_orgao}:",
            parent=janela
        )
        if motivo:
            resultado["sucesso"] = False
            resultado["mensagem"] = f"Aviso do Portal: {motivo.strip()}"
            pyautogui.hotkey('ctrl', 'w')
            janela.destroy()

    frame_botoes = tk.Frame(janela, bg="#f8fafc")
    frame_botoes.pack(pady=10)

    btn_sucesso = tk.Button(frame_botoes, text="✅ Anexar PDF", bg="#86efac", command=acao_sucesso)
    btn_sucesso.grid(row=0, column=0, padx=5)

    btn_falha = tk.Button(frame_botoes, text="❌ Reportar Erro", bg="#fca5a5", command=acao_falha)
    btn_falha.grid(row=0, column=1, padx=5)

    janela.mainloop()
    pyperclip.copy("")
    
    return resultado["sucesso"], resultado["mensagem"]