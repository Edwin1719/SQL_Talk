import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np
import re
from typing import List, Optional, Tuple, Union, Any

# Constantes
SKIP_PATTERNS = [
    'las ventas', 'son las', 'total sales', 'by sales channel', 'for the years', 'siguientes',
    'por producto son las siguientes', 'por canal son las siguientes', 'por categoría son las siguientes',
    'por región son las siguientes', 'por país son las siguientes', 'total sales for the year',
    'by category are as follows', 'by product are as follows', 'are as follows'
]

CATEGORY_PATTERNS = [
    'las ventas totales para', 'son las siguientes', 'por producto son', 'por canal son',
    'por categoría son', 'por región son', 'total sales for the year', 'by category are as follows',
    'by product are as follows', 'are as follows'
]

REGEX_PATTERNS = [
    r'([^con\n]+?)\s+con\s+ventas\s+totales\s+de\s+\$?([\d,]+(?:\.\d+)?)',
    r'([^-\n]+)\s*-\s*\$?([\d,]+(?:\.\d+)?)',
    r'([^:\n$]+):\s*\$?([\d,]+(?:\.\d+)?)',
    r'^([^:$\n]+?):\s*\$?([\d,]+(?:\.\d+)?)$'
]

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

def detect_column_names(query_text: str, text_response: str) -> Tuple[str, str]:
    query_lower = query_text.lower()
    category_mappings = {
        'pais': 'País', 'país': 'País', 'canal': 'Canal de Venta', 'producto': 'Producto',
        'categoría': 'Categoría', 'categoria': 'Categoría', 'región': 'Región', 'region': 'Región',
        'estado': 'Estado', 'ciudad': 'Ciudad', 'cliente': 'Cliente', 'vendedor': 'Vendedor',
        'marca': 'Marca', 'tienda': 'Tienda', 'sucursal': 'Sucursal'
    }
    category_name = 'Categoría'
    for key, name in category_mappings.items():
        if key in query_lower:
            category_name = name
            break
    value_name = 'Ventas'
    if 'cantidad' in query_lower:
        value_name = 'Cantidad'
    elif 'precio' in query_lower:
        value_name = 'Precio'
    return category_name, value_name

def parse_text_to_dataframe(text_response: Union[str, Any], query_text: str = "") -> Optional[pd.DataFrame]:
    if not isinstance(text_response, str):
        return None
    if 'para el canal "' in text_response.lower() and 'en 20' in text_response:
        return parse_multi_year_data(text_response, query_text)

    matches = []
    for pattern in REGEX_PATTERNS:
        matches = re.findall(pattern, text_response, re.MULTILINE)
        if matches:
            break

    if not matches:
        for line in text_response.split('\n'):
            line = line.strip()
            if not line or any(skip in line.lower() for skip in SKIP_PATTERNS):
                continue
            for pattern in REGEX_PATTERNS:
                line_matches = re.findall(pattern, line)
                if line_matches:
                    matches.extend(line_matches)

    if matches:
        categories, values = [], []
        for category, value in matches:
            clean_category = category.strip().replace('\n', '').replace('  ', ' ')
            if not clean_category or any(skip in clean_category.lower() for skip in CATEGORY_PATTERNS):
                continue
            try:
                numeric_value = float(value.replace(',', '').replace('$', '').strip())
                if (numeric_value <= 1 and
                    any(skip in clean_category.lower() for skip in ['las ventas totales', 'are as follows'])):
                    continue
                categories.append(clean_category)
                values.append(numeric_value)
            except ValueError:
                continue
        if categories and values and len(categories) == len(values):
            category_name, value_name = detect_column_names(query_text, text_response)
            return pd.DataFrame({category_name: categories, value_name: values})
    return None

def parse_multi_year_data(text_response: str, query_text: str) -> Optional[pd.DataFrame]:
    pattern = r'Para el canal\s+"([^"]+)"\s+en\s+(\d{4}),\s+las ventas[^$]*\$?([\d,]+(?:\.\d+)?)'
    matches = re.findall(pattern, text_response, re.IGNORECASE)
    if not matches:
        return None
    data_by_channel = {}
    for channel, year, value in matches:
        clean_channel = channel.strip()
        clean_value = float(value.replace(',', '').replace('$', ''))
        if clean_channel not in data_by_channel:
            data_by_channel[clean_channel] = {}
        data_by_channel[clean_channel][year] = clean_value
    df_data = []
    for channel, years_data in data_by_channel.items():
        df_data.append({
            'Canal de Venta': channel,
            'Ventas_2019': years_data.get('2019', 0),
            'Ventas_2020': years_data.get('2020', 0)
        })
    df = pd.DataFrame(df_data)
    if len(df) > 0:
        mask = (df['Ventas_2019'] > 0) & (df['Ventas_2020'] > 0)
        df.loc[mask, 'Crecimiento_%'] = (
            (df.loc[mask, 'Ventas_2020'] - df.loc[mask, 'Ventas_2019']) /
            df.loc[mask, 'Ventas_2019'] * 100
        ).round(2)
        df['Diferencia'] = df['Ventas_2020'] - df['Ventas_2019']
        df['Crecimiento_%'] = df['Crecimiento_%'].fillna(0)
    return df

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
