import os
import sys
import json
import msvcrt
import tempfile
import time
from contextlib import contextmanager


_NOME_APLICACAO = "CND_Automatico"
_PASTA_DADOS_COMPARTILHADOS = (
    r"\\10.6.57.8\COOGESAP\19. FERRAMENTAS\Teste selenium\SQL"
)


def obter_pasta_recursos():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def obter_pasta_dados_usuario():
    base = (
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("APPDATA")
        or os.path.expanduser("~")
    )
    pasta = os.path.join(base, _NOME_APLICACAO)
    os.makedirs(pasta, exist_ok=True)
    return pasta


def obter_pasta_dados_compartilhados():
    try:
        os.makedirs(_PASTA_DADOS_COMPARTILHADOS, exist_ok=True)
    except OSError as erro:
        raise OSError(
            "Não foi possível acessar a pasta compartilhada de dados "
            f"'{_PASTA_DADOS_COMPARTILHADOS}'. Verifique a conexão e as "
            "permissões de gravação no compartilhamento."
        ) from erro
    return _PASTA_DADOS_COMPARTILHADOS


@contextmanager
def bloquear_dados_compartilhados(timeout=60):
    caminho_lock = os.path.join(
        obter_pasta_dados_compartilhados(),
        ".cnd_automatico.lock",
    )
    inicio = time.monotonic()
    with open(caminho_lock, "a+b") as arquivo_lock:
        arquivo_lock.seek(0, os.SEEK_END)
        if arquivo_lock.tell() == 0:
            arquivo_lock.write(b"\0")
            arquivo_lock.flush()

        while True:
            arquivo_lock.seek(0)
            try:
                msvcrt.locking(arquivo_lock.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError as erro:
                if time.monotonic() - inicio >= timeout:
                    raise TimeoutError(
                        "Aguarde outro computador concluir a atualização dos "
                        "dados compartilhados e tente novamente."
                    ) from erro
                time.sleep(0.1)

        try:
            yield
        finally:
            arquivo_lock.seek(0)
            msvcrt.locking(arquivo_lock.fileno(), msvcrt.LK_UNLCK, 1)


def gravar_json_atomico(caminho, dados):
    pasta = os.path.dirname(caminho)
    os.makedirs(pasta, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=pasta,
            prefix=".cnd-",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            temporario = arquivo.name
            json.dump(dados, arquivo, indent=4, ensure_ascii=False)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    finally:
        if temporario and os.path.exists(temporario):
            os.remove(temporario)


def obter_pasta_downloads():
    pasta_documentos = os.path.join(
        os.path.expanduser("~"),
        "Documents",
        _NOME_APLICACAO,
        "CNDs",
    )
    os.makedirs(pasta_documentos, exist_ok=True)
    return pasta_documentos


def obter_pasta_relatorios():
    pasta = os.path.join(obter_pasta_dados_usuario(), "relatorios")
    os.makedirs(pasta, exist_ok=True)
    return pasta
