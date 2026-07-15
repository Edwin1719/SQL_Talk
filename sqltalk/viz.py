import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np
import re
from typing import List, Optional, Tuple, Union, Any

import json


def get_column_types(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    return (
        df.select_dtypes(include=[np.number]).columns.tolist(),
        df.select_dtypes(include=['object', 'category']).columns.tolist()
    )

def detect_chart_type(df: pd.DataFrame) -> Optional[str]:
    if df.empty:
        return None
    numeric_cols, categorical_cols = get_column_types(df)
    if len(numeric_cols) == 0:
        return None
    elif len(categorical_cols) == 1 and len(numeric_cols) == 1:
        return 'bar'
    elif len(numeric_cols) >= 2 and len(categorical_cols) == 0:
        return 'scatter'
    elif len(categorical_cols) == 1 and len(numeric_cols) > 1:
        return 'grouped_bar'
    elif len(numeric_cols) >= 1 and len(categorical_cols) == 0:
        return 'histogram'
    return None

def create_chart(df: pd.DataFrame, chart_type: str) -> Optional[go.Figure]:
    numeric_cols, categorical_cols = get_column_types(df)
    try:
        if chart_type == 'bar':
            x_col = categorical_cols[0] if categorical_cols else df.columns[0]
            y_col = numeric_cols[0] if numeric_cols else df.columns[1]
            fig = px.bar(df, x=x_col, y=y_col, title=f'{y_col} por {x_col}')
            fig.update_layout(xaxis_tickangle=-45, height=500, showlegend=False)
            return fig
        elif chart_type == 'scatter':
            x_col, y_col = numeric_cols[0], numeric_cols[1]
            return px.scatter(df, x=x_col, y=y_col, title=f'{y_col} vs {x_col}')
        elif chart_type == 'histogram':
            col = numeric_cols[0]
            return px.histogram(df, x=col, title=f'Distribución de {col}')
        elif chart_type == 'grouped_bar':
            x_col = categorical_cols[0]
            fig = go.Figure()
            for y_col in numeric_cols[:3]:
                fig.add_trace(go.Bar(name=y_col, x=df[x_col], y=df[y_col]))
            fig.update_layout(
                barmode='group', title=f'Comparación por {x_col}',
                xaxis_title=x_col, yaxis_title='Valores', height=500, xaxis_tickangle=-45
            )
            return fig
    except Exception as e:
        st.error(f"Error al crear gráfico: {e}")
    return None

def auto_visualize(df: pd.DataFrame) -> Optional[go.Figure]:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return None
    chart_type = detect_chart_type(df)
    return create_chart(df, chart_type) if chart_type else None

def parse_text_to_dataframe(text_response: Union[str, Any], query_text: str = "") -> Optional[pd.DataFrame]:
    """Convierte respuesta del LLM a DataFrame. Intenta JSON primero, regex como fallback."""
    if not isinstance(text_response, str):
        return None

    # Ruta principal: JSON estructurado
    try:
        data = json.loads(text_response)
        if isinstance(data, list) and len(data) > 0:
            return pd.DataFrame(data)
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # Fallback: regex para respuestas en texto libre (compatibilidad hacia atrás)
    try:
        lines = [l.strip() for l in text_response.split('\n') if l.strip()]
        rows = []
        for line in lines:
            parts = re.split(r'\s{2,}|\t', line)
            if len(parts) >= 2:
                row = []
                for p in parts:
                    p = p.strip().rstrip(',').replace('$', '').replace(',', '')
                    try:
                        row.append(float(p))
                    except ValueError:
                        row.append(p)
                rows.append(row)
        if len(rows) >= 2:
            return pd.DataFrame(rows[1:], columns=rows[0])
    except Exception:
        pass

    return None


def show_data_summary(df: pd.DataFrame) -> None:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return
    numeric_cols, categorical_cols = get_column_types(df)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Resumen de Datos")
        st.write(f"**Filas:** {len(df)}")
        st.write(f"**Columnas:** {len(df.columns)}")
        st.write(f"**Numéricas:** {len(numeric_cols)}")
        st.write(f"**Categóricas:** {len(categorical_cols)}")
    with col2:
        if numeric_cols:
            st.subheader("📈 Estadísticas")
            st.dataframe(df[numeric_cols].describe())
