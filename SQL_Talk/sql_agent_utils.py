import os
import re
from typing import Dict, Optional, Tuple, Union, Any
from sqlalchemy import create_engine, Engine
from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain_experimental.sql import SQLDatabaseChain
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

def get_db_chain(db_type: str = "SQL Server", conn_args: Optional[Dict[str, str]] = None) -> Tuple[SQLDatabaseChain, Engine]:
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
                # Si no hay variables de entorno, intentar conectar con autenticación de Windows
                # Usar el servidor local por defecto si no se especifica
                try:
                    # Intentar detectar una instancia local de SQL Server
                    import socket
                    hostname = socket.gethostname()
                    conn_args = {"server": f"{hostname}\\SQLEXPRESS", "database": "master"}
                except:
                    # Fallback a localhost si no se puede detectar
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
    sql_database = SQLDatabase(engine)
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0)
    db_chain = SQLDatabaseChain(llm=llm, database=sql_database, verbose=False, return_intermediate_steps=True)
    return db_chain, engine

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

def consulta(db_chain: SQLDatabaseChain, engine: Engine, input_usuario: str, db_type: str = "SQL Server") -> Union[pd.DataFrame, str]:
    """
    Ejecuta una consulta SQL usando lenguaje natural
    
    Args:
        db_chain: Cadena de LangChain configurada para SQL
        engine: Motor de SQLAlchemy para ejecutar consultas
        input_usuario: Consulta en lenguaje natural del usuario
        db_type: Tipo de base de datos para seleccionar el prompt apropiado
        
    Returns:
        DataFrame con los resultados si es una consulta SELECT, 
        o string con la respuesta del LLM en otros casos
    """
    # Seleccionar la plantilla de prompt adecuada
    formato = PROMPT_TEMPLATES.get(db_type, PROMPT_TEMPLATES["SQL Server"])
    consulta_formateada = formato.format(question=input_usuario)
    
    response = db_chain(consulta_formateada)
    result = response['result']
    
    sql_query = None
    if 'intermediate_steps' in response:
        for step in reversed(response['intermediate_steps']):
            if isinstance(step, dict) and 'sql_query' in step:
                sql_query = step['sql_query']
                break
    
    if sql_query and "select" in sql_query.strip().lower():
        try:
            # Limpiar el SQL de markdown y caracteres especiales
            cleaned_sql = clean_sql_query(sql_query)
            df = pd.read_sql_query(cleaned_sql, engine)
            return df
        except Exception as e:
            # Si la ejecución directa falla, devuelve el resultado del LLM que puede contener la explicación.
            return f"Se intentó ejecutar la consulta, pero falló: {e}. Resultado del LLM: {result}"
    
    return result