"""
SQLTalk-AI CLI: Consultas SQL desde terminal
Uso: python -m scripts.cli
"""

import os
from sqltalk.sql_agent import get_db_chain, consulta


def main():
    """Entry point para la CLI"""
    db_type = "SQL Server"
    conn_args = {}

    chain, engine = get_db_chain(db_type, conn_args if any(conn_args.values()) else None)

    pregunta = "¿cual fue el total de ventas en dbo.Sales para el producto numero 436?"
    respuesta, sql = consulta(chain, engine, pregunta, db_type)
    print(respuesta)


if __name__ == "__main__":
    main()
