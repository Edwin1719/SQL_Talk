# Librerías y Recursos
import streamlit as st

# MUST be first Streamlit command
st.set_page_config(
    page_title="SQLTalk-AI",
    page_icon=":material/database:",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import pandas as pd
import plotly.express as px
from typing import Dict, List, Any, Optional
from sqltalk.sql_agent import get_db_chain, consulta
from sqltalk.viz import auto_visualize, show_data_summary, parse_text_to_dataframe
from sqltalk.assistant import IntelligentAssistant
from dotenv import load_dotenv

# Configuración inicial
load_dotenv()
if os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Session state
for key, default in [('query_results', None), ('query_dataframe', None), ('last_query', ""),
                     ('ai_assistant', None), ('ai_insights', None), ('follow_up_queries', [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# Inicializar asistente IA
if st.session_state.ai_assistant is None:
    st.session_state.ai_assistant = IntelligentAssistant()

# =====================================================
# SIDEBAR — Conexión y configuración
# =====================================================
with st.sidebar:
    st.markdown("##### :material/database: Conexión")

    db_type = st.selectbox(
        "Motor de base de datos",
        ["SQL Server", "PostgreSQL", "MySQL", "SQLite"],
        label_visibility="collapsed"
    )

    conn_args = {}
    if db_type == "SQL Server":
        st.caption("💡 Campos vacíos = autenticación Windows")
        conn_args['server'] = st.text_input("Servidor", placeholder="localhost\\SQLEXPRESS",
                                           help="Vacío = detección automática")
        conn_args['database'] = st.text_input("Base de datos", placeholder="master",
                                             help="Vacío = master por defecto")
    elif db_type in ["PostgreSQL", "MySQL"]:
        col_host, col_port = st.columns(2)
        with col_host:
            conn_args['host'] = st.text_input("Host", placeholder="localhost")
        with col_port:
            conn_args['port'] = st.text_input("Puerto", placeholder="5432")
        conn_args['user'] = st.text_input("Usuario")
        conn_args['password'] = st.text_input("Contraseña", type="password")
        conn_args['database'] = st.text_input("Base de datos")
    elif db_type == "SQLite":
        conn_args['database_path'] = st.text_input("Ruta al archivo .db", placeholder="C:/datos/mibd.db")

    # Estado del asistente IA en sidebar
    st.markdown("---")
    st.markdown("##### :material/smart_toy: Asistente IA")
    if st.session_state.ai_assistant and hasattr(st.session_state.ai_assistant, 'session_history'):
        st.metric("Consultas analizadas", len(st.session_state.ai_assistant.session_history))
        if st.session_state.ai_assistant.session_history:
            if st.button(":material/delete: Limpiar historial", use_container_width=True):
                st.session_state.ai_assistant.session_history = []
                st.session_state.ai_assistant.context_memory = {}
                st.success("Historial limpiado")
                st.rerun()
    else:
        st.caption("Sin consultas aún")

    st.markdown("---")
    st.caption("SQLTalk-AI v1.0 — Edwin Quintero Alzate")

# =====================================================
# HEADER — Título principal
# =====================================================
st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px;
                display: flex; align-items: center; gap: 15px;">
        <span style="font-size: 36px;">🗄️</span>
        <div>
            <div style="font-size: 26px; font-weight: 700; letter-spacing: -0.5px;">
                SQLTalk-AI
            </div>
            <div style="font-size: 14px; opacity: 0.8; margin-top: 2px;">
                Consulta tu base de datos en lenguaje natural
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

input_usuario = st.text_input(
    "Tu consulta en lenguaje natural",
    placeholder="Ej: ¿Cuáles fueron las ventas totales por producto el mes pasado?",
    label_visibility="collapsed"
)

# UI - Controles
with st.container(horizontal=True, horizontal_alignment="distribute"):
    consultar_btn = st.button(
        ":material/search: Consultar",
        type="primary",
        use_container_width=True,
        disabled=not input_usuario
    )

with st.container(horizontal=True, horizontal_alignment="left"):
    mostrar_graficos = st.checkbox("Mostrar gráficos", value=True)
    activar_ia = st.checkbox("Asistente IA", value=True, help="Activa análisis inteligente con insights automáticos")

    if st.button(":material/delete: Limpiar", type="secondary"):
        for key in ['query_results', 'query_dataframe', 'last_query', 'ai_insights', 'follow_up_queries']:
            st.session_state[key] = None if key != 'last_query' else "" if key == 'last_query' else []
        st.rerun()

# Procesamiento de consulta
if consultar_btn and input_usuario:
    # Validar que los campos necesarios no estén vacíos
    required_fields = {
        "SQL Server": [],  # SQL Server permite campos vacíos para autenticación de Windows
        "PostgreSQL": ["host", "port", "user", "password", "database"],
        "MySQL": ["host", "port", "user", "password", "database"],
        "SQLite": ["database_path"]
    }

    missing_fields = [field for field in required_fields[db_type] if not conn_args.get(field)]

    if not missing_fields:
        try:
            with st.spinner(f"Conectando a {db_type} y procesando tu consulta..."):
                # Para SQL Server, filtrar argumentos vacíos para usar valores por defecto
                if db_type == "SQL Server":
                    conn_args_filtered = {k: v for k, v in conn_args.items() if v.strip()}
                    chain, engine = get_db_chain(db_type, conn_args_filtered if conn_args_filtered else None)
                else:
                    chain, engine = get_db_chain(db_type, conn_args)
                respuesta = consulta(chain, engine, input_usuario, db_type)

            st.session_state.query_results = respuesta
            st.session_state.last_query = input_usuario

            if isinstance(respuesta, pd.DataFrame):
                st.session_state.query_dataframe = respuesta
            elif mostrar_graficos:
                df_parsed = parse_text_to_dataframe(respuesta, input_usuario)
                if df_parsed is not None:
                    st.session_state.query_dataframe = df_parsed

            # Análisis inteligente con IA
            if activar_ia and st.session_state.query_dataframe is not None:
                with st.spinner("🤖 Analizando datos con IA..."):
                    try:
                        ai_analysis = st.session_state.ai_assistant.get_full_analysis(
                            input_usuario,
                            st.session_state.query_dataframe
                        )
                        st.session_state.ai_insights = ai_analysis.get('insights', '')
                        st.session_state.follow_up_queries = ai_analysis.get('follow_up_queries', [])
                    except Exception as ai_error:
                        st.warning(f"Error en análisis IA: {ai_error}")

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning(f"Por favor, completa los siguientes campos para {db_type}: {', '.join(missing_fields)}")

# Mostrar resultados
if st.session_state.query_results is not None:
    st.space("small")
    st.markdown(f"##### :material/search_insights: {st.session_state.last_query}")

    if isinstance(st.session_state.query_results, pd.DataFrame):
        st.dataframe(st.session_state.query_results, use_container_width=True)
    else:
        st.markdown(st.session_state.query_results)
        if st.session_state.query_dataframe is not None:
            st.markdown("##### :material/table_chart: Datos extraídos para visualización")
            st.dataframe(st.session_state.query_dataframe, use_container_width=True)

# Visualizaciones
if (st.session_state.query_dataframe is not None and
    len(st.session_state.query_dataframe) > 0 and mostrar_graficos):

    df = st.session_state.query_dataframe
    st.space("small")

    # Estadísticas (colapsadas)
    with st.expander(":material/analytics: Resumen Estadístico", expanded=False):
        show_data_summary(df)

    # Gráfico automático
    fig = auto_visualize(df)
    if fig:
        st.markdown("##### :material/bar_chart: Visualización automática")
        st.plotly_chart(fig, use_container_width=True)

    # Gráficos personalizados
    with st.expander(":material/tune: Crear gráfico personalizado"):
        chart_types = ["Barras", "Torta", "Dispersión", "Histograma", "Líneas"]
        selected_chart = st.selectbox("Tipo de gráfico:", chart_types, label_visibility="collapsed")

        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Función auxiliar para crear gráficos
        def create_custom_chart(chart_type: str, df: pd.DataFrame, numeric_cols: List[str], categorical_cols: List[str]) -> Optional[Any]:
            if chart_type == "Barras" and categorical_cols and numeric_cols:
                col1, col2 = st.columns(2)
                with col1:
                    x_col = st.selectbox("Eje X:", categorical_cols, key="x")
                with col2:
                    y_col = st.selectbox("Eje Y:", numeric_cols, key="y")
                return px.bar(df, x=x_col, y=y_col, title=f'{y_col} por {x_col}')

            elif chart_type == "Torta" and categorical_cols and numeric_cols:
                col1, col2 = st.columns(2)
                with col1:
                    name_col = st.selectbox("Etiquetas:", categorical_cols, key="names")
                with col2:
                    value_col = st.selectbox("Valores:", numeric_cols, key="values")
                return px.pie(df, names=name_col, values=value_col, title=f'Distribución de {value_col}')

            elif chart_type == "Dispersión" and len(numeric_cols) >= 2:
                col1, col2 = st.columns(2)
                with col1:
                    x_col = st.selectbox("Eje X:", numeric_cols, key="scatter_x")
                with col2:
                    y_col = st.selectbox("Eje Y:", [c for c in numeric_cols if c != x_col], key="scatter_y")
                return px.scatter(df, x=x_col, y=y_col, title=f'{y_col} vs {x_col}')

            elif chart_type == "Histograma" and numeric_cols:
                col_hist = st.selectbox("Columna:", numeric_cols, key="hist")
                return px.histogram(df, x=col_hist, title=f'Distribución de {col_hist}')

            elif chart_type == "Líneas" and categorical_cols and numeric_cols:
                col1, col2 = st.columns(2)
                with col1:
                    x_col = st.selectbox("Eje X:", categorical_cols + numeric_cols, key="line_x")
                with col2:
                    y_col = st.selectbox("Eje Y:", numeric_cols, key="line_y")
                return px.line(df, x=x_col, y=y_col, title=f'{y_col} por {x_col}')

            return None

        fig_custom = create_custom_chart(selected_chart, df, numeric_cols, categorical_cols)
        if fig_custom:
            st.plotly_chart(fig_custom, use_container_width=True)

# Sección del Asistente Inteligente
if st.session_state.ai_insights is not None and st.session_state.ai_insights.strip():
    st.space("small")

    # Header del asistente IA
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 12px 18px; border-radius: 10px; margin-bottom: 18px;">
        <div style="font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px;">
            <span>:material/smart_toy:</span> Asistente Inteligente — Análisis y Recomendaciones
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Insights principales
    with st.container():
        st.markdown("##### :material/insights: Insights Clave")
        insights_formatted = st.session_state.ai_insights.replace('\n', '<br>')
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 18px; border-radius: 10px;
                    border-left: 5px solid #667eea; margin-bottom: 18px;">
            {insights_formatted}
        </div>
        """, unsafe_allow_html=True)

    # Consultas de seguimiento sugeridas
    if st.session_state.follow_up_queries:
        st.markdown("##### :material/lightbulb: Consultas Sugeridas")

        for i, suggested_query in enumerate(st.session_state.follow_up_queries):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{i+1}.** {suggested_query}")
            with col2:
                if st.button(":material/content_copy:", key=f"copy_{i}", help="Copiar consulta"):
                    st.success("¡Copiado!")

        st.markdown("---")
        selected_query = st.selectbox(
            "Ejecutar consulta sugerida:",
            ["Seleccionar..."] + st.session_state.follow_up_queries,
            key="suggested_query_select",
            label_visibility="collapsed"
        )

        if selected_query != "Seleccionar..." and st.button(":material/send: Ejecutar Consulta Sugerida"):
            st.session_state.suggested_query_to_run = selected_query
            st.info(f"💡 Consulta seleccionada: {selected_query}")
            st.info("👆 Cópiala en el campo de arriba y presiona Consultar")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <div style="font-size: 18px; margin-bottom: 14px;">
        <strong>Desarrollador:</strong> Edwin Quintero Alzate &nbsp;|&nbsp;
        <strong>Email:</strong> egqa1975@gmail.com
    </div>
    <div style="display: flex; justify-content: center; gap: 18px;">
        <a href="https://www.facebook.com/edwin.quinteroalzate" target="_blank">
            <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="#3b5998">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
            </svg>
        </a>
        <a href="https://www.linkedin.com/in/edwinquintero0329/" target="_blank">
            <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="#0A66C2">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
            </svg>
        </a>
        <a href="https://github.com/Edwin1719" target="_blank">
            <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="#000000">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)


def main():
    """Entry point para ejecutar la app: python -m sqltalk.app"""
    pass


if __name__ == "__main__":
    main()
