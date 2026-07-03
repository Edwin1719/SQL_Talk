"""Tests para viz.py — detección de gráficos y parsing de texto."""

import pandas as pd
import numpy as np
from sqltalk.viz import (
    get_column_types,
    detect_chart_type,
    detect_column_names,
    parse_text_to_dataframe,
    parse_multi_year_data,
)


class TestGetColumnTypes:
    def test_mixto(self, df_mixto):
        num, cat = get_column_types(df_mixto)
        assert num == ["Ventas", "Cantidad"]
        assert cat == ["Producto"]

    def test_solo_numerico(self, df_solo_numerico):
        num, cat = get_column_types(df_solo_numerico)
        assert num == ["x", "y"]
        assert cat == []

    def test_vacio(self, df_vacio):
        num, cat = get_column_types(df_vacio)
        assert num == []
        assert cat == []


class TestDetectChartType:
    def test_bar_una_cat_una_num(self, df_mixto):
        # df_mixto tiene 1 cat + 2 num → grouped_bar
        assert detect_chart_type(df_mixto) == "grouped_bar"

    def test_scatter_dos_num_sin_cat(self, df_solo_numerico):
        assert detect_chart_type(df_solo_numerico) == "scatter"

    def test_vacio_retorna_none(self, df_vacio):
        assert detect_chart_type(df_vacio) is None

    def test_una_fila_retorna_bar(self, df_una_fila):
        assert detect_chart_type(df_una_fila) == "bar"


class TestDetectColumnNames:
    def test_detecta_pais(self):
        cat, val = detect_column_names("ventas por país", "")
        assert cat == "País"

    def test_detecta_producto(self):
        cat, val = detect_column_names("productos mas vendidos", "")
        assert cat == "Producto"

    def test_detecta_cantidad(self):
        cat, val = detect_column_names("cantidad vendida por producto", "")
        assert val == "Cantidad"

    def test_detecta_precio(self):
        cat, val = detect_column_names("precio promedio", "")
        assert val == "Precio"

    def test_default_ventas(self):
        cat, val = detect_column_names("listado general", "")
        assert cat == "Categoría"
        assert val == "Ventas"

    def test_detecta_canal(self):
        cat, val = detect_column_names("ventas por canal", "")
        assert cat == "Canal de Venta"


class TestParseTextToDataframe:
    def test_parsea_formato_producto_con_ventas(self):
        texto = "Producto A con ventas totales de $1500\nProducto B con ventas totales de $2500"
        df = parse_text_to_dataframe(texto, "ventas por producto")
        assert df is not None
        assert list(df.columns) == ["Producto", "Ventas"]
        assert len(df) == 2
        assert df["Ventas"].tolist() == [1500.0, 2500.0]

    def test_parsea_formato_guion(self):
        texto = "Laptops - $50000\nTeclados - $12000"
        df = parse_text_to_dataframe(texto, "ventas por producto")
        assert df is not None
        assert len(df) == 2

    def test_parsea_formato_dos_puntos(self):
        texto = "Enero: $10000\nFebrero: $15000"
        df = parse_text_to_dataframe(texto, "ventas por mes")
        assert df is not None
        assert len(df) == 2

    def test_texto_sin_datos_retorna_none(self):
        assert parse_text_to_dataframe("No se encontraron resultados.", "") is None

    def test_no_es_string_retorna_none(self):
        assert parse_text_to_dataframe(12345, "") is None

    def test_skip_lineas_con_encabezado(self):
        texto = "las ventas totales para el año son las siguientes:\nProducto A: $1000"
        df = parse_text_to_dataframe(texto, "ventas")
        assert df is not None

    def test_valor_monetario_con_coma(self):
        texto = "Producto A: $1,500.50\nProducto B: $2,000.00"
        df = parse_text_to_dataframe(texto, "ventas")
        assert df is not None
        assert df["Ventas"].tolist() == [1500.5, 2000.0]


class TestParseMultiYearData:
    def test_parsea_dos_canales_dos_anios(self):
        texto = (
            'Para el canal "Online" en 2019, las ventas totales fueron $50000\n'
            'Para el canal "Online" en 2020, las ventas totales fueron $65000\n'
            'Para el canal "Tienda" en 2019, las ventas totales fueron $30000\n'
            'Para el canal "Tienda" en 2020, las ventas totales fueron $28000'
        )
        df = parse_multi_year_data(texto, "ventas por canal")
        assert df is not None
        assert list(df.columns) == [
            "Canal de Venta", "Ventas_2019", "Ventas_2020",
            "Crecimiento_%", "Diferencia"
        ]
        assert len(df) == 2
        # Online: (65000-50000)/50000*100 = 30%
        online = df[df["Canal de Venta"] == "Online"].iloc[0]
        assert online["Crecimiento_%"] == 30.0
        assert online["Diferencia"] == 15000.0

    def test_sin_resultados_retorna_none(self):
        assert parse_multi_year_data("sin datos", "") is None
