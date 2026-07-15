import os
import re
from typing import Dict, Optional, Tuple, Union, Any
from sqlalchemy import create_engine, Engine, inspect
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import pandas as pd
import json

load_dotenv()

def clean_sql_query(sql_query: str) -> str:
    """
    Limpia la consulta SQL eliminando markdown, comentarios y caracteres problemáticos

    Args:
        sql_query: Consulta SQL con posibles caracteres markdown o comentarios

    Returns:
        Consulta SQL limpia y lista para ejecutar
    """
    if not sql_query:
        return sql_query

    # Eliminar markdown SQL (```sql y ```)
    sql_query = re.sub(r'```sql\s*', '', sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r'```\s*$', '', sql_query)
    sql_query = re.sub(r'^```\s*', '', sql_query)

    # Eliminar comentarios de línea (-- comentario)
    sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)

    # Eliminar comentarios de bloque (/* comentario */)
    sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)

    # Limpiar espacios y saltos de línea excesivos
    sql_query = re.sub(r'\s+', ' ', sql_query)
    sql_query = sql_query.strip()

    # Asegurar que termine con punto y coma si no lo tiene
    if not sql_query.endswith(';'):
        sql_query += ';'

    return sql_query

def get_db_chain(db_type: str = "SQL Server", conn_args: Optional[Dict[str, str]] = None) -> Tuple[Any, Engine]:
    """
    Crea y devuelve una cadena de base de datos SQL y un motor de SQLAlchemy
    basado en el tipo de base de datos y los parámetros de conexión.
    Mantiene la compatibilidad con la configuración anterior de SQL Server vía .env.

    Args:
        db_type: Tipo de base de datos ("SQL Server", "PostgreSQL", "MySQL", "SQLite")
        conn_args: Diccionario con parámetros de conexión específicos por motor

    Returns:
        Tupla con (Runnable (create_sql_query_chain), Engine) configurados y listos para usar

    Raises:
        ValueError: Si el tipo de BD no es soportado o faltan parámetros requeridos
    """
    # Compatibilidad hacia atrás: si no se pasan argumentos, usa .env para SQL Server
    if conn_args is None:
        conn_args = {}
        if db_type == "SQL Server":
            server_name = os.getenv("SERVER_NAME")
            database_name = os.getenv("DATABASE_NAME")
            if server_name and database_name:
                conn_args = {"server": server_name, "database": database_name}
            else:
                try:
                    import socket
                    hostname = socket.gethostname()
                    conn_args = {"server": f"{hostname}\\SQLEXPRESS", "database": "master"}
                except:
                    conn_args = {"server": "localhost", "database": "master"}

    connection_string = ""
    if db_type == "SQL Server":
        server = conn_args.get("server")
        database = conn_args.get("database")
        if not server or not database:
            raise ValueError("Para SQL Server, se requieren 'server' y 'database'.")
        connection_string = f"mssql+pyodbc://{server}/{database}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

    elif db_type == "PostgreSQL":
        required_keys = ['user', 'password', 'host', 'port', 'database']
        if not all(k in conn_args for k in required_keys):
            raise ValueError(f"Para PostgreSQL, se requieren los siguientes argumentos: {', '.join(required_keys)}")
        connection_string = f"postgresql+psycopg2://{conn_args['user']}:{conn_args['password']}@{conn_args['host']}:{conn_args['port']}/{conn_args['database']}"

    elif db_type == "MySQL":
        required_keys = ['user', 'password', 'host', 'port', 'database']
        if not all(k in conn_args for k in required_keys):
            raise ValueError(f"Para MySQL, se requieren los siguientes argumentos: {', '.join(required_keys)}")
        connection_string = f"mysql+pymysql://{conn_args['user']}:{conn_args['password']}@{conn_args['host']}:{conn_args['port']}/{conn_args['database']}"

    elif db_type == "SQLite":
        db_path = conn_args.get("database_path")
        if not db_path:
            raise ValueError("Para SQLite, se requiere 'database_path'.")
        connection_string = f"sqlite:///{db_path}"

    else:
        raise ValueError(f"Tipo de base de datos no soportado: {db_type}")

    engine = create_engine(connection_string)

    # Obtener tablas de TODOS los schemas (SQL Server con multiple schemas como AdventureWorks)
    db_inspector = inspect(engine)
    all_schemas = [s for s in db_inspector.get_schema_names()
                   if s.lower() not in ('information_schema', 'sys', 'guest',
                                        'db_owner', 'db_accessadmin', 'db_securityadmin',
                                        'db_ddladmin', 'db_backupoperator', 'db_datareader',
                                        'db_datawriter', 'db_denydatareader', 'db_denydatawriter')]

    all_tables = []
    custom_table_info = {}
    for schema in all_schemas:
        for table_name in db_inspector.get_table_names(schema=schema):
            all_tables.append(table_name)
            qualified = f"{schema}.{table_name}" if schema != 'dbo' else table_name
            cols = db_inspector.get_columns(table_name, schema=schema)
            col_lines = []
            for c in cols:
                nullable = " NOT NULL" if not c.get('nullable', True) else ""
                col_lines.append(f"  [{c['name']}] {c['type']}{nullable}")
            custom_table_info[table_name] = f"CREATE TABLE [{qualified}] (\n" + "\n".join(col_lines) + "\n)"

    db = SQLDatabase(engine, custom_table_info=custom_table_info)

    # SQLDatabase solo refleja el schema default (dbo) internamente.
    # AdventureWorks usa múltiples schemas (Person, Production, Sales, etc.)
    # — sobrescribimos los sets internos para que cubran todas las tablas.
    db._all_tables = set(all_tables)
    db._usable_tables = set(all_tables)
    db._custom_table_info = custom_table_info

    # Reemplazar get_table_info para que use custom_table_info directamente
    # (sin depender del reflection de metadata que solo ve schema dbo)
    _custom_info = custom_table_info
    _all_names = list(all_tables)
    def _patched_get_table_info(self, table_names=None, get_col_comments=False):
        names = table_names if table_names else _all_names
        result = []
        for name in names:
            if name in _custom_info:
                result.append(_custom_info[name])
            else:
                result.append(f"-- {name}: no disponible")
        return "\n\n".join(result)
    db.get_table_info = _patched_get_table_info.__get__(db, type(db))

    # Inicializar LLM desde variables de entorno (mismo patrón que assistant.py)
    env_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    env_model = os.getenv("AI_MODEL")
    env_base_url = os.getenv("AI_MODEL_BASE_URL")
    env_temp = os.getenv("AI_TEMPERATURE")

    if not all([env_key, env_model, env_base_url, env_temp]):
        raise ValueError(
            "Faltan variables de entorno: DEEPSEEK_API_KEY (u OPENAI_API_KEY), "
            "AI_MODEL, AI_MODEL_BASE_URL, AI_TEMPERATURE"
        )

    llm = ChatOpenAI(
        model=env_model,
        temperature=float(env_temp),
        openai_api_key=env_key,
        openai_api_base=env_base_url,
    )

    chain = create_sql_query_chain(llm, db, prompt=CUSTOM_PROMPT)

    return chain, engine

CUSTOM_PROMPT = PromptTemplate(
    input_variables=["input", "table_info"],
    partial_variables={"top_k": "5"},
    template="""Convierte esta pregunta en una consulta SQL.

{table_info}

Pregunta: {input}"""
)

def consulta(chain, engine, input_usuario: str, db_type: str = "SQL Server") -> tuple:
    """
    Ejecuta una consulta SQL usando lenguaje natural

    Args:
        chain: Cadena de LangChain (create_sql_query_chain) para generar SQL
        engine: Motor de SQLAlchemy para ejecutar consultas
        input_usuario: Consulta en lenguaje natural del usuario
        db_type: Tipo de base de datos para seleccionar el prompt apropiado

    Returns:
        Tupla (resultado, sql_generado):
        - resultado: DataFrame si es SELECT, string con error/texto en otros casos
        - sql_generado: string con el SQL generado por el LLM (para mostrar en UI)
    """
    # create_sql_query_chain retorna el SQL generado como string
    # El prompt ya lo maneja el chain con CUSTOM_PROMPT (en español)
    sql_query = chain.invoke({"question": input_usuario})

    cleaned_sql = clean_sql_query(sql_query)

    # Detectar respuesta JSON estructurada (LLM responde con datos en vez de SQL)
    try:
        data = json.loads(cleaned_sql)
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            return df, cleaned_sql
    except (json.JSONDecodeError, ValueError):
        pass

    if "select" in cleaned_sql.strip().lower():
        try:
            df = pd.read_sql_query(cleaned_sql, engine)
            return df, cleaned_sql
        except Exception as e:
            return f"Error ejecutando consulta: {e}", cleaned_sql

    return cleaned_sql, cleaned_sql
