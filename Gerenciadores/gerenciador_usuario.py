import base64
import ctypes
import hashlib
import hmac
import json
import os
import secrets
import tempfile
import threading
from ctypes import wintypes

from Gerenciadores.gerenciador_caminhos import obter_pasta_dados_usuario


_NOME_APLICACAO = "CND_Automatico"
_ITERACOES_HASH = 310_000
_TAMANHO_HASH = 32
_TAMANHO_MAXIMO_SENHA_AGEHAB = 5120
_USUARIO_ATUAL = None
_LOCK = threading.RLock()


class ErroAutenticacao(ValueError):
    pass


class CredenciaisAGEHABAusentesError(RuntimeError):
    pass


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _exigir_windows():
    if os.name != "nt":
        raise OSError("O armazenamento protegido de credenciais exige Windows.")


def obter_caminho_usuarios():
    return os.path.join(
        obter_pasta_dados_usuario(),
        "usuarios.json",
    )


def _chave_usuarios_existe():
    return os.path.isfile(obter_caminho_usuarios())


def _carregar_usuarios():
    caminho = obter_caminho_usuarios()
    if not os.path.exists(caminho):
        return {}

    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    if not isinstance(dados, dict):
        raise ValueError("O arquivo de usuários está em formato inválido.")
    usuarios = dados.get("usuarios")
    if not isinstance(usuarios, dict):
        raise ValueError("O arquivo de usuários não contém um cadastro válido.")
    return usuarios


def _salvar_usuarios(usuarios):
    caminho = obter_caminho_usuarios()
    pasta = os.path.dirname(caminho)
    os.makedirs(pasta, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=pasta,
            prefix=".usuarios-",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            temporario = arquivo.name
            json.dump(
                {"versao": 1, "usuarios": usuarios},
                arquivo,
                ensure_ascii=False,
                indent=2,
            )
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    finally:
        if temporario and os.path.exists(temporario):
            os.remove(temporario)


def _proteger_dados(dados):
    _exigir_windows()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    entrada_buffer = ctypes.create_string_buffer(dados)
    entrada = _DataBlob(
        len(dados),
        ctypes.cast(entrada_buffer, ctypes.POINTER(ctypes.c_ubyte)),
    )
    saida = _DataBlob()
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        wintypes.LPCWSTR,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    if not crypt32.CryptProtectData(
        ctypes.byref(entrada),
        "CND_Automatico AGEHAB",
        None,
        None,
        None,
        0,
        ctypes.byref(saida),
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(saida.pbData, saida.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(saida.pbData, ctypes.c_void_p))


def _desproteger_dados(dados):
    _exigir_windows()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    entrada_buffer = ctypes.create_string_buffer(dados)
    entrada = _DataBlob(
        len(dados),
        ctypes.cast(entrada_buffer, ctypes.POINTER(ctypes.c_ubyte)),
    )
    saida = _DataBlob()
    descricao = wintypes.LPWSTR()
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    if not crypt32.CryptUnprotectData(
        ctypes.byref(entrada),
        ctypes.byref(descricao),
        None,
        None,
        None,
        0,
        ctypes.byref(saida),
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(saida.pbData, saida.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(saida.pbData, ctypes.c_void_p))
        if descricao:
            kernel32.LocalFree(ctypes.cast(descricao, ctypes.c_void_p))


def _normalizar_usuario(usuario):
    return usuario.strip().casefold()


def listar_usuarios():
    with _LOCK:
        usuarios = _carregar_usuarios()
    return sorted(
        (
            registro.get("usuario", chave)
            for chave, registro in usuarios.items()
            if isinstance(registro, dict)
        ),
        key=str.casefold,
    )


def cadastrar_usuario(usuario, senha, usuario_agehab, senha_agehab):
    usuario = usuario.strip()
    usuario_agehab = usuario_agehab.strip()
    if len(usuario) < 3:
        raise ValueError("O usuário do programa deve ter ao menos 3 caracteres.")
    if len(senha) < 8:
        raise ValueError("A senha do programa deve ter ao menos 8 caracteres.")
    if not usuario_agehab or not senha_agehab:
        raise ValueError("Informe o usuário e a senha da AGEHAB.")
    if len(senha_agehab.encode("utf-16-le")) > _TAMANHO_MAXIMO_SENHA_AGEHAB:
        raise ValueError("A senha da AGEHAB excede o limite aceito pelo Windows.")

    chave = _normalizar_usuario(usuario)
    sal = secrets.token_bytes(16)
    resumo = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        sal,
        _ITERACOES_HASH,
        dklen=_TAMANHO_HASH,
    )
    agehab_protegido = _proteger_dados(senha_agehab.encode("utf-8"))
    registro = {
        "usuario": usuario,
        "sal": base64.b64encode(sal).decode("ascii"),
        "hash_senha": base64.b64encode(resumo).decode("ascii"),
        "usuario_agehab": usuario_agehab,
        "senha_agehab_protegida": base64.b64encode(
            agehab_protegido
        ).decode("ascii"),
    }

    with _LOCK:
        usuarios = _carregar_usuarios()
        if chave in usuarios:
            raise ValueError("Esse usuário já está cadastrado.")
        usuarios[chave] = registro
        _salvar_usuarios(usuarios)
    return usuario


def autenticar_usuario(usuario, senha):
    global _USUARIO_ATUAL
    chave = _normalizar_usuario(usuario)
    if not chave or not senha:
        raise ErroAutenticacao("Informe o usuário e a senha.")

    with _LOCK:
        registro = _carregar_usuarios().get(chave)
    if not isinstance(registro, dict):
        raise ErroAutenticacao("Usuário ou senha incorretos.")

    try:
        sal = base64.b64decode(registro["sal"], validate=True)
        hash_armazenado = base64.b64decode(
            registro["hash_senha"],
            validate=True,
        )
        hash_fornecido = hashlib.pbkdf2_hmac(
            "sha256",
            senha.encode("utf-8"),
            sal,
            _ITERACOES_HASH,
            dklen=len(hash_armazenado),
        )
    except (KeyError, TypeError, ValueError) as erro:
        raise ValueError("O registro do usuário está inválido.") from erro

    if not hmac.compare_digest(hash_fornecido, hash_armazenado):
        raise ErroAutenticacao("Usuário ou senha incorretos.")

    _USUARIO_ATUAL = chave
    return registro.get("usuario", usuario.strip())


def obter_credenciais_agehab():
    if not _USUARIO_ATUAL:
        raise ErroAutenticacao("Entre no programa antes de iniciar a coleta.")

    with _LOCK:
        registro = _carregar_usuarios().get(_USUARIO_ATUAL)
    if not isinstance(registro, dict):
        raise ErroAutenticacao("A conta conectada não está mais cadastrada.")

    try:
        dados_protegidos = base64.b64decode(
            registro["senha_agehab_protegida"],
            validate=True,
        )
        senha = _desproteger_dados(dados_protegidos).decode("utf-8")
        usuario_agehab = registro["usuario_agehab"]
    except (KeyError, TypeError, ValueError) as erro:
        raise CredenciaisAGEHABAusentesError(
            "As credenciais AGEHAB desta conta estão ausentes ou inválidas."
        ) from erro
    return usuario_agehab, senha


def primeiro_cadastro_necessario():
    return not _carregar_usuarios()


def numero_usuarios_cadastrados():
    with _LOCK:
        return len(_carregar_usuarios())
