# PREGUNTAS A SQL SERVER DESDE PYTHON 

# Importacion de Recusrsos y librerias
import os
from sql_agent_utils import get_db_chain, consulta

# Configuración para SQL Server (puedes modificar estos valores)
db_type = "SQL Server"
conn_args = {
    # "server": "tu_servidor",  # Descomenta y ajusta si necesitas un servidor específico
    # "database": "tu_base_datos"  # Descomenta y ajusta si necesitas una base específica
}

# Crear la cadena de base de datos SQL
# Si conn_args está vacío, usará las variables de entorno o valores por defecto
db_chain, engine = get_db_chain(db_type, conn_args if any(conn_args.values()) else None)

# Ejemplo de uso
pregunta = "¿cual fue el total de ventas en dbo.Sales para el producto numero 436?"
respuesta = consulta(db_chain, engine, pregunta, db_type)
print(respuesta)
