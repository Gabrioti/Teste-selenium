import os
import sys
import json
import sqlite3
from contextlib import closing
from datetime import datetime
import time

from Gerenciadores.gerenciador_caminhos import (
    bloquear_dados_compartilhados,
    gravar_json_atomico,
    obter_pasta_dados_compartilhados,
    obter_pasta_dados_usuario,
    obter_pasta_recursos,
)

def obter_caminho_historico():
    """Retorna o caminho do histórico compartilhado."""
    pasta_sql = obter_pasta_dados_compartilhados()
    caminho = os.path.join(pasta_sql, "historico_cnds.json")
    if not os.path.exists(caminho):
        with bloquear_dados_compartilhados():
            if not os.path.exists(caminho):
                caminho_empacotado = os.path.join(
                    obter_pasta_recursos(),
                    "SQL",
                    "historico_cnds.json",
                )
                if os.path.isfile(caminho_empacotado):
                    with open(caminho_empacotado, "r", encoding="utf-8") as arquivo:
                        gravar_json_atomico(caminho, json.load(arquivo))
                else:
                    gravar_json_atomico(caminho, {})
    return caminho

def obter_caminho_banco_historico():
    """Retorna o caminho do banco SQLite que armazena as mudancas das CNDs."""
    return os.path.join(os.path.dirname(obter_caminho_historico()), "historico_alteracoes_cnds.sqlite3")

def _caminho_metadados():
    return os.path.join(obter_pasta_dados_compartilhados(), "metadados_compartilhados.json")

def _carregar_metadados():
    caminho = _caminho_metadados()
    if not os.path.exists(caminho):
        return {"dados": {}, "historico": {}}
    with open(caminho, "r", encoding="utf-8") as arquivo:
        metadados = json.load(arquivo)
    if not isinstance(metadados, dict):
        raise ValueError("O arquivo de metadados compartilhados não é válido.")
    metadados.setdefault("dados", {})
    metadados.setdefault("historico", {})
    if not isinstance(metadados["dados"], dict):
        raise ValueError("Os metadados de dados compartilhados não são válidos.")
    if not isinstance(metadados["historico"], dict):
        raise ValueError("Os metadados do histórico compartilhado não são válidos.")
    return metadados

def _preparar_banco(conexao):
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS alteracoes_cnds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            cnpj TEXT NOT NULL,
            certidao TEXT NOT NULL,
            validade_anterior TEXT NOT NULL,
            status_anterior TEXT NOT NULL,
            validade_atual TEXT NOT NULL,
            status_atual TEXT NOT NULL
        )
        """
    )
    conexao.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_alteracoes_cnds_chave
        ON alteracoes_cnds (cnpj, certidao, id DESC)
        """
    )

def _registrar_alteracao(cnpj, certidao, anterior, atual):
    caminho = os.path.join(
        obter_pasta_dados_compartilhados(),
        "historico_alteracoes_cnds.sqlite3",
    )
    with closing(sqlite3.connect(caminho, timeout=30)) as conexao:
        with conexao:
            _preparar_banco(conexao)
            conexao.execute(
                """
                INSERT INTO alteracoes_cnds (
                    data_hora, cnpj, certidao,
                    validade_anterior, status_anterior,
                    validade_atual, status_atual
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    cnpj,
                    certidao,
                    anterior.get("validade", ""),
                    anterior.get("status", ""),
                    atual.get("validade", ""),
                    atual.get("status", ""),
                ),
            )

def _normalizar_comparacao(valor):
    return "".join(str(valor or "").split()).casefold()

def _obter_ultima_alteracao(cnpj, certidao):
    caminho = os.path.join(
        obter_pasta_dados_compartilhados(),
        "historico_alteracoes_cnds.sqlite3",
    )
    if not os.path.exists(caminho):
        return None

    with closing(sqlite3.connect(caminho)) as conexao:
        conexao.row_factory = sqlite3.Row
        linha = conexao.execute(
            """
            SELECT validade_atual, status_atual
            FROM alteracoes_cnds
            WHERE cnpj = ? AND certidao = ?
            ORDER BY data_hora DESC, id DESC
            LIMIT 1
            """,
            (cnpj, certidao),
        ).fetchone()
        if linha is None:
            return None
        return {"validade": linha["validade_atual"], "status": linha["status_atual"]}

def listar_alteracoes(limite=None):
    """Lista as mudancas registradas, da mais recente para a mais antiga."""
    caminho = obter_caminho_banco_historico()
    if not os.path.exists(caminho):
        return []

    consulta = """
        SELECT data_hora, cnpj, certidao,
               validade_anterior, status_anterior,
               validade_atual, status_atual
        FROM alteracoes_cnds
        ORDER BY data_hora DESC, id DESC
    """
    parametros = ()
    if limite is not None:
        limite = max(0, int(limite))
        consulta += " LIMIT ?"
        parametros = (limite,)

    with closing(sqlite3.connect(caminho)) as conexao:
        conexao.row_factory = sqlite3.Row
        return [dict(linha) for linha in conexao.execute(consulta, parametros)]

def carregar_historico():
    """Lê o histórico atual. Se não existir, retorna um dicionário vazio."""
    caminho = obter_caminho_historico()
    if not os.path.exists(caminho):
        return {}
    with open(caminho, 'r', encoding='utf-8') as f:
        historico = json.load(f)
    if not isinstance(historico, dict):
        raise ValueError("O arquivo de histórico precisa conter um objeto JSON.")
    return historico

def _timestamp_data_hora(valor):
    return datetime.fromisoformat(valor).timestamp()

def _ultima_data_hora(conexao, cnpj, certidao):
    linha = conexao.execute(
        """
        SELECT data_hora FROM alteracoes_cnds
        WHERE cnpj = ? AND certidao = ?
        ORDER BY data_hora DESC, id DESC LIMIT 1
        """,
        (cnpj, certidao),
    ).fetchone()
    return _timestamp_data_hora(linha[0]) if linha else None

def migrar_historico_local():
    """Mescla o histórico antigo deste usuário no banco compartilhado."""
    if not getattr(sys, "frozen", False):
        return

    pasta_usuario = obter_pasta_dados_usuario()
    caminho_marcador = os.path.join(
        pasta_usuario,
        "historico_compartilhado_v1_migrado",
    )
    if os.path.exists(caminho_marcador):
        return

    pasta_local_sql = os.path.join(pasta_usuario, "SQL")
    caminho_json_local = os.path.join(pasta_local_sql, "historico_cnds.json")
    caminho_db_local = os.path.join(
        pasta_local_sql,
        "historico_alteracoes_cnds.sqlite3",
    )

    obter_caminho_historico()
    caminho_json_compartilhado = os.path.join(
        obter_pasta_dados_compartilhados(),
        "historico_cnds.json",
    )
    caminho_db_compartilhado = os.path.join(
        obter_pasta_dados_compartilhados(),
        "historico_alteracoes_cnds.sqlite3",
    )

    with bloquear_dados_compartilhados():
        local = {}
        if os.path.isfile(caminho_json_local):
            with open(caminho_json_local, "r", encoding="utf-8") as arquivo:
                local = json.load(arquivo)
            if not isinstance(local, dict):
                raise ValueError("O histórico local não contém um objeto JSON.")

        with open(caminho_json_compartilhado, "r", encoding="utf-8") as arquivo:
            atual = json.load(arquivo)
        if not isinstance(atual, dict):
            raise ValueError("O histórico compartilhado não contém um objeto JSON.")
        if any(not isinstance(certidoes, dict) for certidoes in atual.values()):
            raise ValueError("Existem registros inválidos no histórico compartilhado.")
        if any(not isinstance(certidoes, dict) for certidoes in local.values()):
            raise ValueError("Existem registros inválidos no histórico local.")

        os.makedirs(os.path.dirname(caminho_db_compartilhado), exist_ok=True)
        with closing(sqlite3.connect(caminho_db_compartilhado, timeout=30)) as conexao:
            with conexao:
                _preparar_banco(conexao)
                local_eventos = {}
                if os.path.isfile(caminho_db_local):
                    with closing(sqlite3.connect(caminho_db_local, timeout=30)) as origem:
                        origem.row_factory = sqlite3.Row
                        try:
                            linhas = origem.execute(
                                """
                                SELECT data_hora, cnpj, certidao,
                                       validade_anterior, status_anterior,
                                       validade_atual, status_atual
                                FROM alteracoes_cnds ORDER BY id
                                """
                            ).fetchall()
                        except sqlite3.OperationalError as erro:
                            if "no such table" in str(erro).lower():
                                linhas = []
                            else:
                                raise
                    for linha in linhas:
                        evento = dict(linha)
                        chave = (evento["cnpj"], evento["certidao"])
                        local_eventos[chave] = max(
                            local_eventos.get(chave, 0),
                            _timestamp_data_hora(evento["data_hora"]),
                        )
                        existe = conexao.execute(
                            """
                            SELECT 1 FROM alteracoes_cnds
                            WHERE data_hora = ? AND cnpj = ? AND certidao = ?
                              AND validade_anterior = ? AND status_anterior = ?
                              AND validade_atual = ? AND status_atual = ?
                            LIMIT 1
                            """,
                            tuple(evento.values()),
                        ).fetchone()
                        if not existe:
                            conexao.execute(
                                """
                                INSERT INTO alteracoes_cnds (
                                    data_hora, cnpj, certidao,
                                    validade_anterior, status_anterior,
                                    validade_atual, status_atual
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                tuple(evento.values()),
                            )

                metadados = _carregar_metadados()
                marcas = metadados["historico"]
                if not isinstance(marcas, dict):
                    raise ValueError("Metadados de histórico compartilhado inválidos.")
                data_local_json = (
                    os.path.getmtime(caminho_json_local)
                    if os.path.isfile(caminho_json_local)
                    else 0
                )
                data_compartilhada_json = os.path.getmtime(caminho_json_compartilhado)

                for cnpj, certidoes in local.items():
                    atual.setdefault(cnpj, {})
                    for certidao, estado in certidoes.items():
                        chave_tuple = (str(cnpj), str(certidao))
                        chave_meta = f"{cnpj}|{certidao}"
                        timestamp_evento = local_eventos.get(chave_tuple)
                        timestamp_local = max(
                            timestamp
                            for timestamp in (timestamp_evento, data_local_json)
                            if timestamp is not None
                        )
                        timestamp_atual = marcas.get(chave_meta)
                        if timestamp_atual is None:
                            timestamp_atual = _ultima_data_hora(
                                conexao,
                                *chave_tuple,
                            )
                        if timestamp_atual is None:
                            timestamp_atual = data_compartilhada_json
                        if (
                            certidao not in atual[cnpj]
                            or timestamp_local > timestamp_atual
                        ):
                            atual[cnpj][certidao] = estado
                            marcas[chave_meta] = timestamp_local

                gravar_json_atomico(caminho_json_compartilhado, atual)
                gravar_json_atomico(_caminho_metadados(), metadados)

    with open(caminho_marcador, "w", encoding="utf-8") as marcador:
        marcador.write("ok")

def registrar_resultado(
    cnpj,
    certidao,
    validade,
    status,
    observacao,
    registrar_mudanca=False,
):
    """Salva o estado atual e, quando solicitado, registra uma mudança efetiva."""

    # 1. BLINDAGEM: Garante que o CNPJ seja sempre apenas números!
    cnpj_limpo = "".join(c for c in str(cnpj) if c.isdigit())

    caminho_historico = obter_caminho_historico()
    with bloquear_dados_compartilhados():
        historico = {}
        if os.path.exists(caminho_historico):
            with open(caminho_historico, "r", encoding="utf-8") as arquivo:
                historico = json.load(arquivo)
        if not isinstance(historico, dict):
            raise ValueError("O arquivo de histórico precisa conter um objeto JSON.")

        if cnpj_limpo not in historico:
            historico[cnpj_limpo] = {}

        anterior = historico[cnpj_limpo].get(certidao, {})
        atual = {
            "validade": validade,
            "status": status,
            "observacao": observacao
        }

        if registrar_mudanca:
            estado_anterior = _obter_ultima_alteracao(cnpj_limpo, certidao) or anterior
            status_anterior = str(estado_anterior.get("status", "")).strip().casefold()
            if any(
                marcador in status_anterior
                for marcador in ("falha", "pendente", "manual", "sem automação")
            ):
                estado_anterior = {}

            if (
                _normalizar_comparacao(estado_anterior.get("validade", ""))
                != _normalizar_comparacao(validade)
                or _normalizar_comparacao(estado_anterior.get("status", ""))
                != _normalizar_comparacao(status)
            ):
                _registrar_alteracao(cnpj_limpo, certidao, estado_anterior, atual)

        historico[cnpj_limpo][certidao] = atual
        gravar_json_atomico(caminho_historico, historico)

        metadados = _carregar_metadados()
        metadados["historico"][f"{cnpj_limpo}|{certidao}"] = time.time()
        gravar_json_atomico(_caminho_metadados(), metadados)

if __name__ == "__main__":
    # ISSO AQUI FORÇA A CRIAÇÃO DO ARQUIVO PARA TESTARMOS
    print("Testando a criação do Banco de Dados de Histórico...")
    
    # Simula um robô salvando um resultado qualquer
    registrar_resultado(
        cnpj="12345678000199", 
        certidao="Teste de Sistema", 
        validade="31/12/2099", 
        status="Negativa", 
        observacao="Arquivo criado com sucesso!"
    )
    
    caminho = obter_caminho_historico()
    print(f"Verifique se o arquivo apareceu na pasta: {caminho}")