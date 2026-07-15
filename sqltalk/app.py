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
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqltalk.sql_agent import get_db_chain, consulta
from sqltalk.viz import auto_visualize, show_data_summary, parse_text_to_dataframe
from sqltalk.assistant import IntelligentAssistant
from sqltalk.pbip_builder import generate_model, build_pbip_package, build_schema_text
from dotenv import load_dotenv

# Configuración inicial
load_dotenv()

# Session state
for key, default in [('query_results', None), ('query_dataframe', None), ('last_query', ""),
                     ('last_sql', ""), ('ai_assistant', None), ('ai_insights', None),
                     ('follow_up_queries', []), ('engine', None),
                     ('conversation_history', []), ('favorites', []), ('show_kpi', True),
                     ('refined_query', False), ('is_refinement', False)]:
    if key not in st.session_state:
        st.session_state[key] = default

# Inicializar asistente IA
try:
    if st.session_state.ai_assistant is None:
        st.session_state.ai_assistant = IntelligentAssistant()
except ValueError as e:
    st.error(f"⚠️ {e}")
    st.info("Copiá `.env.example` a `.env` y completá los valores requeridos.")
    st.stop()

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

    # Explorador de esquema
    if st.session_state.engine is not None:
        st.markdown("---")
        st.markdown("##### :material/schema: Esquema de BD")
        if st.button(":material/refresh: Explorar tablas", use_container_width=True):
            try:
                inspector = __import__("sqlalchemy").inspect(st.session_state.engine)
                table_names = inspector.get_table_names()
                if table_names:
                    for table in table_names:
                        cols = inspector.get_columns(table)
                        col_list = ", ".join([f"{c['name']} ({str(c['type'])})" for c in cols[:5]])
                        if len(cols) > 5:
                            col_list += ", ..."
                        st.markdown(f"**{table}**")
                        st.caption(col_list)
                else:
                    st.caption("No se encontraron tablas")
            except Exception as e:
                st.caption(f"Error: {e}")

        # Schema Q&A — preguntar sobre la estructura
        st.markdown("##### :material/quiz: Preguntar sobre el esquema")
        schema_question = st.text_input(
            "Ej: ¿Qué tablas tienen información de clientes?",
            placeholder="Ej: ¿Qué tablas tienen información de ventas?",
            label_visibility="collapsed",
            key="schema_question"
        )
        if st.button(":material/search: Consultar esquema", use_container_width=True, key="btn_schema"):
            if schema_question.strip():
                try:
                    with st.spinner("Analizando esquema..."):
                        inspector = __import__("sqlalchemy").inspect(st.session_state.engine)
                        table_names = inspector.get_table_names()
                        schema_parts = []
                        for table in table_names:
                            cols = inspector.get_columns(table)
                            col_info = ", ".join([f"{c['name']} ({c['type']})" for c in cols])
                            # Foreign keys
                            fks = inspector.get_foreign_keys(table)
                            fk_info = ""
                            if fks:
                                fk_strs = [f"{fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}" for fk in fks]
                                fk_info = f" | FK: {'; '.join(fk_strs)}"
                            schema_parts.append(f"Tabla: {table}\nColumnas: {col_info}{fk_info}")
                        schema_text = "\n\n".join(schema_parts)
                        response = st.session_state.ai_assistant.query_schema(schema_text, schema_question)
                        st.session_state.schema_answer = response
                except Exception as e:
                    st.session_state.schema_answer = f"Error: {e}"
            else:
                st.warning("Escribí una pregunta sobre el esquema")

        if st.session_state.get('schema_answer'):
            with st.container():
                st.markdown("**Respuesta:**")
                st.markdown(st.session_state.schema_answer)
    else:
        st.caption("Conecta a una BD para ver su esquema")
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

    # Favoritos
    if st.session_state.favorites:
        st.markdown("##### :material/star: Favoritas")
        for i, fav in enumerate(st.session_state.favorites):
            label = fav["query"][:45] + ("…" if len(fav["query"]) > 45 else "")
            st.caption(fav["date"])
            if st.button(label, key=f"fav_{i}", use_container_width=True):
                st.session_state.last_query = fav["query"]
                st.session_state.last_sql = fav["sql"]
                st.session_state.query_results = None
                st.session_state.query_dataframe = None
                st.session_state.ai_insights = None
                st.rerun()
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
    mostrar_kpi = st.checkbox("Panel KPIs", value=True, help="Muestra métricas clave del resultado")

    if st.button(":material/delete: Limpiar", type="secondary"):
        for key in ['query_results', 'query_dataframe', 'last_query', 'ai_insights', 'follow_up_queries']:
            st.session_state[key] = None if key != 'last_query' else "" if key == 'last_query' else []
        st.session_state.conversation_history = []
        st.session_state.is_refinement = False
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
                st.session_state.engine = engine

                # Refinamiento iterativo: inyectar contexto de consulta anterior
                query_to_run = input_usuario
                st.session_state.is_refinement = False
                if (st.session_state.conversation_history
                    and len(input_usuario.split()) < 15
                    and not input_usuario.upper().startswith(("SELECT", "WITH"))):
                    last = st.session_state.conversation_history[-1]
                    query_to_run = (
                        f"[Contexto: consulta anterior: '{last['query']}' → "
                        f"SQL: {last['sql']}] "
                        f"{input_usuario}"
                    )
                    st.session_state.is_refinement = True

                respuesta, sql_generado = consulta(chain, engine, query_to_run, db_type)

            st.session_state.query_results = respuesta
            st.session_state.last_query = input_usuario
            st.session_state.last_sql = sql_generado

            if isinstance(respuesta, pd.DataFrame):
                st.session_state.query_dataframe = respuesta
            elif mostrar_graficos:
                df_parsed = parse_text_to_dataframe(respuesta, input_usuario)
                if df_parsed is not None:
                    st.session_state.query_dataframe = df_parsed

            # Guardar en historial conversacional
            if st.session_state.query_dataframe is not None:
                st.session_state.conversation_history.append({
                    'query': input_usuario,
                    'sql': sql_generado,
                    'rows': len(st.session_state.query_dataframe),
                    'cols': list(st.session_state.query_dataframe.columns[:5])
                })
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

# =====================================================
# RESULTADOS
# =====================================================
if st.session_state.query_results is not None:
    st.markdown(f"##### :material/search_insights: {st.session_state.last_query}")

    # Indicador de refinamiento contextual
    if st.session_state.is_refinement:
        st.caption("🔗 Usando contexto de la consulta anterior — podés seguir refinando")

    # SQL generado (colapsado)
    if st.session_state.last_sql:
        with st.expander(":material/code: Ver SQL generado", expanded=False):
            st.code(st.session_state.last_sql, language="sql")

    # =====================================================
    # PANEL DE KPIS (primeras columnas numéricas)
    # =====================================================
    if (mostrar_kpi
        and st.session_state.query_dataframe is not None
        and len(st.session_state.query_dataframe) > 0):
        df = st.session_state.query_dataframe
        kpi_cols = df.select_dtypes(include=['number']).columns[:6].tolist()
        if kpi_cols:
            st.markdown("##### :material/metrics: KPIs Rápidos")
            cols = st.columns(len(kpi_cols))
            first = df.iloc[0]
            for i, col in enumerate(kpi_cols):
                with cols[i]:
                    val = first[col]
                    if isinstance(val, (int, float)):
                        if abs(val) >= 1_000_000:
                            display = f"${val/1_000_000:,.2f}M" if "monto" in col.lower() or "venta" in col.lower() or "precio" in col.lower() else f"{val/1_000_000:,.2f}M"
                        elif abs(val) >= 1_000:
                            display = f"${val/1_000:,.1f}K" if "monto" in col.lower() or "venta" in col.lower() or "precio" in col.lower() else f"{val/1_000:,.1f}K"
                        else:
                            display = f"${val:,.0f}" if "monto" in col.lower() or "venta" in col.lower() or "precio" in col.lower() else f"{val:,.0f}"
                    else:
                        display = str(val)
                    st.metric(label=col.replace("_", " ").title(), value=display)

    if isinstance(st.session_state.query_results, pd.DataFrame):
        st.dataframe(st.session_state.query_results, use_container_width=True)

        # Exportar resultados
        df_exp = st.session_state.query_results
        csv_data = df_exp.to_csv(index=False).encode("utf-8")
        col_csv, col_xlsx = st.columns(2)
        with col_csv:
            st.download_button(
                ":material/download: Exportar CSV",
                data=csv_data,
                file_name="sqltalk_resultados.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_xlsx:
            try:
                import io
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    df_exp.to_excel(writer, index=False, sheet_name="Resultados")
                st.download_button(
                    ":material/table: Exportar Excel",
                    data=buf.getvalue(),
                    file_name="sqltalk_resultados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception:
                st.caption("Excel no disponible (instala openpyxl: pip install openpyxl)")

    # Botón guardar como favorita
    already_saved = st.session_state.last_sql in [f["sql"] for f in st.session_state.favorites]
    if not already_saved and st.session_state.last_sql:
        if st.button(":material/star: Guardar consulta", key="save_fav", use_container_width=True):
            st.session_state.favorites.append({
                "query": st.session_state.last_query,
                "sql": st.session_state.last_sql,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success("Consulta guardada en favoritos")
            st.rerun()
    else:
        st.markdown(st.session_state.query_results)
        if st.session_state.query_dataframe is not None:
            st.markdown("##### :material/table_chart: Datos extraídos para visualización")
            st.dataframe(st.session_state.query_dataframe, use_container_width=True)

# Visualizaciones
if (st.session_state.query_dataframe is not None and
    len(st.session_state.query_dataframe) > 0 and mostrar_graficos):

    df = st.session_state.query_dataframe

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


# =====================================================
# GENERADOR DE MODELO POWER BI (PBIP)
# =====================================================
with st.expander(":material/table_chart: Generar modelo Power BI", expanded=False):
    if st.session_state.engine is None:
        st.info(":material/info: Conectá a una base de datos primero")
    else:
        st.markdown("Describí qué querés incluir en el modelo semántico:")
        pbip_request = st.text_area(
            "Solicitud",
            placeholder="Ej: Crea una tabla calendario 2020-2026 con medidas de ventas YTD, PY y YoY%. Agrega relaciones entre tablas.",
            label_visibility="collapsed",
            key="pbip_request"
        )

        col_btn, col_status = st.columns([2, 3])
        with col_btn:
            generar_modelo_btn = st.button(
                ":material/auto_fix: Generar modelo",
                use_container_width=True,
                disabled=not pbip_request
            )

        if generar_modelo_btn:
            if pbip_request.strip():
                with st.spinner("🧠 Generando modelo semántico con IA..."):
                    try:
                        inspector = __import__("sqlalchemy").inspect(st.session_state.engine)
                        schema_text = build_schema_text(inspector)
                        llm = st.session_state.ai_assistant.llm
                        model_json = generate_model(schema_text, pbip_request, llm)
                        if model_json:
                            st.session_state.pbip_model = model_json
                            st.success("✅ Modelo generado correctamente")
                        else:
                            st.error("❌ El modelo generado no es válido. Reformulá la solicitud.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Escribí qué querés incluir en el modelo")

        if st.session_state.get("pbip_model"):
            zip_buf = build_pbip_package(st.session_state.pbip_model)
            st.download_button(
                ":material/download: Descargar proyecto Power BI (.pbip)",
                data=zip_buf,
                file_name="sqltalk_modelo.pbip.zip",
                mime="application/zip",
                use_container_width=True
            )
            st.caption(":material/info: Descomprimí la carpeta y abrila con Power BI Desktop")

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
