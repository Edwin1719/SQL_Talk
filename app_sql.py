# Librerias  y Recursos
import streamlit as st
import os
from sqlalchemy import create_engine
from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain_experimental.sql import SQLDatabaseChain
from st_social_media_links import SocialMediaIcons

# Configuración de la aplicación Streamlit
st.markdown("""
    <style>
    .title {
        text-align: center;
        background-color: #333;
        color: white;  /* Aseguramos que el color del texto sea blanco */
        padding: 10px;
        border-radius: 5px;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    <div class="title">
        CONSULTA TU BASE DE DATOS SQL
    </div>
    """, unsafe_allow_html=True)

# Solicitar la API de OpenAI del usuario
openai_api_key = st.text_input("Introduce tu API de OpenAI:", type="password")
os.environ["OPENAI_API_KEY"] = openai_api_key

# Solicitar el nombre del servidor y de la base de datos
server_name = st.text_input("Introduce el nombre del servidor SQL:")
database_name = st.text_input("Introduce el nombre de la base de datos:")

# Configuración de la conexión con SQL Server
connection_string = (
    f"mssql+pyodbc://{server_name}/{database_name}"
    "?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
)

# Crear el engine usando SQLAlchemy
engine = create_engine(connection_string)

# Crear una instancia de SQLDatabase
sql_database = SQLDatabase(engine)

# Crear el LLM
llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0)

# Crear la cadena de base de datos SQL
db_chain = SQLDatabaseChain(llm=llm, database=sql_database, verbose=False)

# Formato personalizado de respuesta
formato = """ 
Dada una pregunta del usuario:
1. Crea una consulta de SQL Server
2. Revisa los resultados
3. Devuelve el dato
4. Si tienes que hacer alguna aclaración o devolver cualquier texto que sea #{question}
"""

# Definir la función de consulta
def consulta(input_usuario):
    consulta_formateada = formato.format(question=input_usuario)
    resultado = db_chain.run(consulta_formateada)
    return resultado

# Interfaz de usuario para realizar consultas
input_usuario = st.text_input("Introduce tu consulta SQL:")
if st.button("Consultar"):
    if openai_api_key and server_name and database_name and input_usuario:
        respuesta = consulta(input_usuario)
        st.write(respuesta)
    else:
        st.write("Por favor, completa todos los campos antes de realizar la consulta.")

# Pie de página con información del desarrollador y logos de redes sociales
st.markdown("""
---
**Desarrollador:** Edwin Quintero Alzate<br>
**Email:** egqa1975@gmail.com<br>
""")

social_media_links = [
    "https://www.facebook.com/edwin.quinteroalzate",
    "https://www.linkedin.com/in/edwinquintero0329/",
    "https://github.com/Edwin1719"]

social_media_icons = SocialMediaIcons(social_media_links)
social_media_icons.render()
