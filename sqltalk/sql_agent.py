import os
import re
from typing import Dict, Optional, Tuple, Union, Any
from sqlalchemy import create_engine, Engine
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain
from dotenv import load_dotenv
import pandas as pd

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
        Tupla con (SQLDatabaseChain, Engine) configurados y listos para usar

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
    db = SQLDatabase(engine)

    # Configuración del modelo — TODO debe venir del .env (sin defaults ocultos)
    ai_api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    ai_model = os.getenv("AI_MODEL")
    ai_base_url = os.getenv("AI_MODEL_BASE_URL")
    ai_temperature = os.getenv("AI_TEMPERATURE")

    missing = []
    if not ai_api_key:
        missing.append("DEEPSEEK_API_KEY (u OPENAI_API_KEY como fallback)")
    if not ai_model:
        missing.append("AI_MODEL")
    if not ai_base_url:
        missing.append("AI_MODEL_BASE_URL")
    if not ai_temperature:
        missing.append("AI_TEMPERATURE")
    if missing:
        raise ValueError(
            "Faltan variables en el archivo .env:\n  - " + "\n  - ".join(missing) +
            "\nCopia .env.example a .env y completa los valores."
        )
    ai_temperature = float(ai_temperature)

    llm = ChatOpenAI(
        model=ai_model,
        temperature=ai_temperature,
        openai_api_key=ai_api_key,
        openai_api_base=ai_base_url
    )
    chain = create_sql_query_chain(llm=llm, db=db)
    return chain, engine

PROMPT_TEMPLATES = {
    "SQL Server": """
Dada una pregunta del usuario:
1. Crea SOLAMENTE una consulta de SQL Server válida. NO uses markdown, NO uses ```sql.
2. Asegúrate de escapar los nombres de tablas y columnas con corchetes [] si son palabras reservadas o contienen espacios (ej. [Mi Tabla], [Mi Columna]).
3. La consulta debe ser SQL puro, sin comentarios ni explicaciones adicionales.
4. Revisa los resultados.
5. Devuelve el dato.
6. Si tienes que hacer alguna aclaración o devolver cualquier texto que sea, hazlo después de la consulta.

Pregunta: {question}
""",
    "PostgreSQL": """
Dada una pregunta del usuario:
1. Crea SOLAMENTE una consulta de PostgreSQL válida. NO uses markdown, NO uses ```sql.
2. Asegúrate de escapar los nombres de tablas y columnas con comillas dobles "" si son palabras reservadas o contienen espacios (ej. "Mi Tabla", "Mi Columna").
3. La consulta debe ser SQL puro, sin comentarios ni explicaciones adicionales.
4. Revisa los resultados.
5. Devuelve el dato.
6. Si tienes que hacer alguna aclaración o devolver cualquier texto que sea, hazlo después de la consulta.

Pregunta: {question}
""",
    "MySQL": """
Dada una pregunta del usuario:
1. Crea SOLAMENTE una consulta de MySQL válida. NO uses markdown, NO uses ```sql.
2. Asegúrate de escapar los nombres de tablas y columnas con acentos graves `` si son palabras reservadas o contienen espacios (ej. `Mi Tabla`, `Mi Columna`).
3. La consulta debe ser SQL puro, sin comentarios ni explicaciones adicionales.
4. Revisa los resultados.
5. Devuelve el dato.
6. Si tienes que hacer alguna aclaración o devolver cualquier texto que sea, hazlo después de la consulta.

Pregunta: {question}
""",
    "SQLite": """
Dada una pregunta del usuario:
1. Crea SOLAMENTE una consulta de SQLite válida. NO uses markdown, NO uses ```sql.
2. La consulta debe ser SQL puro, sin comentarios ni explicaciones adicionales.
3. Revisa los resultados.
4. Devuelve el dato.
5. Si tienes que hacer alguna aclaración o devolver cualquier texto que sea, hazlo después de la consulta.

Pregunta: {question}
"""
}

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
    formato = PROMPT_TEMPLATES.get(db_type, PROMPT_TEMPLATES["SQL Server"])
    consulta_formateada = formato.format(question=input_usuario)

    # create_sql_query_chain retorna el SQL generado como string
    sql_query = chain.invoke({"input": consulta_formateada})
    cleaned_sql = clean_sql_query(sql_query)

    if "select" in cleaned_sql.strip().lower():
        try:
            df = pd.read_sql_query(cleaned_sql, engine)
            return df, cleaned_sql
        except Exception as e:
            return f"Error ejecutando consulta: {e}", cleaned_sql

    return cleaned_sql, cleaned_sql
