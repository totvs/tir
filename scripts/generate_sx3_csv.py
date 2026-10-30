#!/usr/bin/env python3
"""Gera sx3.csv a partir das tabelas obrigatórias SX3 e SX3T10."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

try:
    import pyodbc
except ImportError as exc:
    raise SystemExit("Dependência ausente: pyodbc.") from exc

# Altere somente o nome da base quando trocar de ambiente.
ENV_DB_DRIVER = ""  # Vazio detecta automaticamente ODBC Driver 18/17.
ENV_DB_SERVER = "SPON010126556"
ENV_DB_PORT = 1433
ENV_DB_DATABASE = "P1212510MNTDBEXP"
ENV_DB_USER = "sa"
ENV_DB_PASSWORD = "sa"
ENV_DB_SCHEMA = ""  # Vazio procura em todos os schemas.
ENV_BASE_FILE = r"C:\Path\to\core\data\sx3.csv"  # Vazio não compara. 

# Fonte obrigatória do dicionário: não tornar configurável.
SX3_TABLES = ("SX3T10",)
READ_BATCH_SIZE = 50_000
DEFAULT_OUTPUT = Path.cwd() / "sx3.csv"
REQUIRED_COLUMNS = {"X3_CAMPO", "X3_TIPO", "X3_TAMANHO", "R_E_C_N_O_"}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera sx3.csv da base Protheus configurada neste arquivo.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Destino do CSV (padrão: sx3.csv na pasta atual).")
    parser.add_argument("--dry-run", action="store_true", help="Consulta e compara, mas não grava o CSV.")
    return parser.parse_args()


def choose_odbc_driver() -> str:
    installed = pyodbc.drivers()
    if ENV_DB_DRIVER:
        if ENV_DB_DRIVER in installed:
            return ENV_DB_DRIVER
        raise SystemExit(f"Driver ODBC não instalado: {ENV_DB_DRIVER}")
    for driver in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"):
        if driver in installed:
            return driver
    raise SystemExit("Nenhum driver ODBC do SQL Server foi encontrado.")


def quote_identifier(identifier: str) -> str:
    if not identifier or "]" in identifier:
        raise SystemExit(f"Identificador SQL inválido: {identifier!r}")
    return f"[{identifier}]"


def connect() -> pyodbc.Connection:
    values = {
        "ENV_DB_SERVER": ENV_DB_SERVER,
        "ENV_DB_DATABASE": ENV_DB_DATABASE,
        "ENV_DB_USER": ENV_DB_USER,
        "ENV_DB_PASSWORD": ENV_DB_PASSWORD,
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise SystemExit("Preencha as variáveis: " + ", ".join(missing))
    connection_string = (
        f"DRIVER={{{choose_odbc_driver()}}};SERVER={ENV_DB_SERVER},{ENV_DB_PORT};"
        f"DATABASE={ENV_DB_DATABASE};UID={ENV_DB_USER};PWD={ENV_DB_PASSWORD};TrustServerCertificate=yes;"
    )
    try:
        return pyodbc.connect(connection_string, timeout=15)
    except pyodbc.Error as exc:
        raise SystemExit(f"Falha ao conectar ao SQL Server: {exc}") from exc


def find_sx3_tables(connection: pyodbc.Connection) -> list[tuple[str, str, set[str]]]:
    placeholders = ", ".join("?" for _ in SX3_TABLES)
    conditions = [f"TABLE_NAME IN ({placeholders})"]
    parameters: list[str] = list(SX3_TABLES)
    if ENV_DB_SCHEMA:
        conditions.append("TABLE_SCHEMA = ?")
        parameters.append(ENV_DB_SCHEMA)

    metadata = connection.cursor().execute(
        "SELECT TABLE_SCHEMA, TABLE_NAME, UPPER(COLUMN_NAME) FROM INFORMATION_SCHEMA.COLUMNS WHERE "
        + " AND ".join(conditions),
        parameters,
    ).fetchall()
    candidates: dict[tuple[str, str], set[str]] = {}
    for schema, table, column in metadata:
        candidates.setdefault((schema, table), set()).add(column)

    sources: list[tuple[str, str, set[str]]] = []
    for expected in SX3_TABLES:
        matches = [(schema, table, columns) for (schema, table), columns in candidates.items()
                   if table.upper() == expected and REQUIRED_COLUMNS.issubset(columns)]
        if not matches:
            raise SystemExit(f"Tabela obrigatória {expected} não encontrada ou inválida.")
        if len(matches) > 1:
            raise SystemExit(f"Mais de uma tabela {expected} encontrada. Preencha ENV_DB_SCHEMA.")
        sources.append(matches[0])
    return sources


def clean_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return f"{value:.1f}"
    return str(value).replace("\r", " ").replace("\n", " ")


def column_or_default(columns: set[str], column: str, fallback: str = "''") -> str:
    return quote_identifier(column) if column in columns else fallback


def iter_sx3_rows(
    connection: pyodbc.Connection, schema: str, table: str, columns: set[str]
) -> Iterator[tuple[Any, ...]]:
    """Lê por faixas de R_E_C_N_O_ para não ordenar nem acumular a SX3T10."""
    title_pt = column_or_default(columns, "X3_TITULO")
    title_es = column_or_default(columns, "X3_TITSPA", title_pt)
    title_en = column_or_default(columns, "X3_TITENG", title_pt)
    deleted_filter = ""
    if "R_E_C_D_E_L_" in columns:
        deleted_filter = " AND CONVERT(VARCHAR(30), [R_E_C_D_E_L_]) <> '*'"

    table_name = f"{quote_identifier(schema)}.{quote_identifier(table)}"
    cursor = connection.cursor()
    maximum_record = cursor.execute(f"SELECT MAX([R_E_C_N_O_]) FROM {table_name}").fetchone()[0] or 0
    query = f"""
        SELECT [X3_CAMPO], [X3_TIPO], [X3_TAMANHO],
               {title_pt} AS [TITULO_PT], {title_es} AS [TITULO_ES], {title_en} AS [TITULO_EN]
          FROM {table_name}
         WHERE [R_E_C_N_O_] > ? AND [R_E_C_N_O_] <= ?{deleted_filter}
    """
    for start in range(0, maximum_record, READ_BATCH_SIZE):
        for row in cursor.execute(query, start, start + READ_BATCH_SIZE).fetchall():
            yield tuple(row)


def read_base_field_names(base_file: Path) -> set[str]:
    if not base_file.is_file():
        raise SystemExit(f"Arquivo base não encontrado: {base_file}")
    with base_file.open("r", encoding="latin-1", errors="replace", newline="") as csv_file:
        return {row[0].strip() for row in csv.reader(csv_file, delimiter=";") if row and row[0].strip()}


def print_comparison(base_names: set[str], current_names: set[str], base_file: Path) -> None:
    print("Resumo da comparação:")
    print(f"  Arquivo base: {base_file}")
    print(f"  Campos no arquivo base: {len(base_names)}")
    print(f"  Campos gerados: {len(current_names)}")
    print(f"  Campos novos: {len(current_names - base_names)}")
    print(f"  Campos excluídos: {len(base_names - current_names)}")


def generate(connection: pyodbc.Connection, output: Path | None) -> tuple[dict[str, int], set[str]]:
    counts: dict[str, int] = {}
    field_names: set[str] = set()
    csv_file = None
    temporary = None
    try:
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = output.with_suffix(output.suffix + ".tmp")
            csv_file = temporary.open("w", encoding="latin-1", errors="replace", newline="")
            writer = csv.writer(csv_file, delimiter=";", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        else:
            writer = None

        for schema, table, columns in find_sx3_tables(connection):
            source = f"{schema}.{table}"
            counts[source] = 0
            for row in iter_sx3_rows(connection, schema, table, columns):
                counts[source] += 1
                if row[0]:
                    field_names.add(clean_value(row[0]).strip())
                if writer:
                    writer.writerow(tuple(clean_value(value) for value in row))
    except Exception:
        if temporary and temporary.exists():
            temporary.unlink()
        raise
    finally:
        if csv_file:
            csv_file.close()
    return counts, field_names


def main() -> int:
    args = parse_arguments()
    base_file = Path(ENV_BASE_FILE).expanduser() if ENV_BASE_FILE.strip() else None
    base_names = read_base_field_names(base_file) if base_file else set()

    with connect() as connection:
        counts, current_names = generate(connection, None if args.dry_run else args.output)

    for source, count in counts.items():
        print(f"{count} registros lidos de {source}.")
    print(f"{len(current_names)} campos únicos nas duas tabelas.")
    if base_file:
        print_comparison(base_names, current_names, base_file)
    if args.dry_run:
        print("Dry-run concluído: o sx3.csv não foi alterado.")
        return 0

    backup = args.output.with_suffix(args.output.suffix + "." + datetime.now().strftime("%Y%m%d%H%M%S") + ".bak")
    if args.output.exists():
        args.output.replace(backup)
    args.output.with_suffix(args.output.suffix + ".tmp").replace(args.output)
    print(f"Arquivo gerado: {args.output}")
    print(f"Backup anterior: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
