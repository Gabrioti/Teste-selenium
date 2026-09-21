import os
import time


def _arquivos_validos(pasta_download):
    """Lista apenas arquivos reais de download, ignorando temporários do browser."""
    if not os.path.exists(pasta_download):
        return []

    arquivos = []
    for nome in os.listdir(pasta_download):
        caminho = os.path.join(pasta_download, nome)
        if not os.path.isfile(caminho):
            continue
        if nome.lower().endswith(('.crdownload', '.part', '.tmp', '.download')):
            continue
        arquivos.append(nome)
    return arquivos


def diagnosticar_download_falhou(navegador, pasta_download):
    """Imprime um diagnóstico útil quando o download não acontece."""
    print("\n=== DIAGNÓSTICO DE DOWNLOAD ===")
    print(f"URL atual: {navegador.current_url}")
    print(f"Título da página: {navegador.title}")

    if not os.path.exists(pasta_download):
        print(f"Pasta de download não existe: {pasta_download}")
        return

    arquivos = _arquivos_validos(pasta_download)
    temporarios = [
        nome for nome in os.listdir(pasta_download)
        if nome.lower().endswith(('.crdownload', '.part', '.tmp', '.download'))
    ]

    print(f"Arquivos na pasta: {arquivos}")
    if temporarios:
        print(f"Arquivos temporários: {temporarios}")

    try:
        html = navegador.page_source[:1500]
        print(f"Trecho HTML: {html}")
    except Exception as e:
        print(f"Não foi possível ler o HTML: {e}")

    print("=== FIM DO DIAGNÓSTICO ===\n")


def esperar_download(navegador, pasta_download, extensao='.pdf', timeout=30, intervalo=0.5, arquivos_antes=None):
    """Espera um arquivo novo chegar na pasta e retorna o caminho do primeiro PDF válido."""
    os.makedirs(pasta_download, exist_ok=True)

    if arquivos_antes is None:
        arquivos_antes = set(_arquivos_validos(pasta_download))
    else:
        arquivos_antes = set(arquivos_antes)

    # Registra os tempos de modificação dos arquivos pré-existentes
    mtimes_antes = {}
    for nome in arquivos_antes:
        caminho = os.path.join(pasta_download, nome)
        try:
            mtimes_antes[nome] = os.path.getmtime(caminho)
        except OSError:
            pass

    inicio = time.time()

    while time.time() - inicio < timeout:
        arquivos_agora = set(_arquivos_validos(pasta_download))
        arquivos_novos = arquivos_agora - arquivos_antes

        # 1. Arquivos com nomes novos adicionados
        for nome in sorted(arquivos_novos):
            caminho = os.path.join(pasta_download, nome)
            if not os.path.isfile(caminho):
                continue

            if nome.lower().endswith(extensao.lower()) and os.path.getsize(caminho) > 0:
                print(f"Download confirmado: {nome}")
                return caminho

        # 2. Arquivos preexistentes que foram sobrescritos durante o download
        for nome in sorted(arquivos_agora & arquivos_antes):
            caminho = os.path.join(pasta_download, nome)
            if not os.path.isfile(caminho):
                continue

            if nome.lower().endswith(extensao.lower()) and os.path.getsize(caminho) > 0:
                try:
                    mtime_atual = os.path.getmtime(caminho)
                    mtime_anterior = mtimes_antes.get(nome, 0)
                    if mtime_atual > mtime_anterior and mtime_atual >= (inicio - 1.0):
                        print(f"Download confirmado (arquivo atualizado): {nome}")
                        return caminho
                except OSError:
                    pass

        time.sleep(intervalo)

    diagnosticar_download_falhou(navegador, pasta_download)
    raise TimeoutError(
        f"Nenhum arquivo {extensao.upper()} foi baixado dentro de {timeout} segundos."
    )
