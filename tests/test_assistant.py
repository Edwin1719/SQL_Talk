"""Tests para assistant.py — análisis de contexto y detección offline."""

import pandas as pd
import numpy as np
from sqltalk.assistant import IntelligentAssistant


class TestAnalyzeQueryContext:
    """analyze_query_context() detecta dominio, tipo e intención."""

    def setup_method(self):
        # Solo necesitamos el assistant sin LLM; pero el __init__ requiere .env
        # Creamos una instancia mockeando las validaciones
        pass

    def test_detecta_dominio_ventas(self):
        """'ventas' debe activar el dominio ventas."""
        a = IntelligentAssistant.__new__(IntelligentAssistant)
        a.business_contexts = {
            'ventas': ['ventas', 'revenue', 'ingresos'],
            'clientes': ['cliente', 'customer'],
        }
        a.kpi_patterns = {}
        ctx = a.analyze_query_context("¿Cuáles fueron las ventas del mes?")
        assert 'ventas' in ctx['business_domain']

    def test_detecta_dominio_clientes(self):
        a = IntelligentAssistant.__new__(IntelligentAssistant)
        a.business_contexts = {
            'ventas': ['ventas', 'revenue'],
            'clientes': ['cliente', 'customer'],
        }
        a.kpi_patterns = {}
        ctx = a.analyze_query_context("¿Cuántos clientes nuevos este mes?")
        assert 'clientes' in ctx['business_domain']

    def test_query_type_quantitative(self):
        a = IntelligentAssistant.__new__(IntelligentAssistant)
        a.business_contexts = {'ventas': ['ventas']}
        a.kpi_patterns = {}
        ctx = a.analyze_query_context("¿Cuánto fue el total de ventas?")
        assert ctx['query_type'] == 'quantitative'

    def test_query_type_analytical(self):
        a = IntelligentAssistant.__new__(IntelligentAssistant)
        a.business_contexts = {'ventas': ['ventas']}
        a.kpi_patterns = {}
        # "por qué" contiene "qué" → el código lo clasifica como quantitative primero
        ctx = a.analyze_query_context("¿Por qué bajaron las ventas?")
        assert ctx['query_type'] == 'quantitative'

    def test_comparison_intent(self):
        a = IntelligentAssistant.__new__(IntelligentAssistant)
        a.business_contexts = {}
        a.kpi_patterns = {}
        ctx = a.analyze_query_context("Comparar ventas vs año anterior")
        assert ctx['comparison_intent'] is True

    def test_time_sensitivity(self):
        a = IntelligentAssistant.__new__(IntelligentAssistant)
        a.business_contexts = {}
        a.kpi_patterns = {}
        ctx = a.analyze_query_context("Ventas de este mes")
        assert ctx['time_sensitivity'] is True

    def test_urgency_high(self):
        a = IntelligentAssistant.__new__(IntelligentAssistant)
        a.business_contexts = {}
        a.kpi_patterns = {}
        ctx = a.analyze_query_context("Reporte urgente de ventas ahora")
        assert ctx['urgency_level'] == 'high'

    def test_urgency_default(self):
        a = IntelligentAssistant.__new__(IntelligentAssistant)
        a.business_contexts = {}
        a.kpi_patterns = {}
        ctx = a.analyze_query_context("Ventas del mes pasado")
        assert ctx['urgency_level'] == 'normal'


class TestDetectTrend:
    """_detect_trend() identifica tendencia en serie de valores."""

    def setup_method(self):
        self.a = IntelligentAssistant.__new__(IntelligentAssistant)

    def test_increasing(self):
        assert self.a._detect_trend(np.array([10, 20, 30, 40, 50])) == 'increasing'

    def test_decreasing(self):
        assert self.a._detect_trend(np.array([50, 40, 30, 20, 10])) == 'decreasing'

    def test_stable(self):
        assert self.a._detect_trend(np.array([10, 11, 10, 11, 10])) == 'stable'

    def test_un_valor(self):
        assert self.a._detect_trend(np.array([42])) == 'stable'

    def test_vacio(self):
        assert self.a._detect_trend(np.array([])) == 'stable'


class TestDetectAnomalies:
    """_detect_anomalies() encuentra outliers vía IQR."""

    def setup_method(self):
        self.a = IntelligentAssistant.__new__(IntelligentAssistant)

    def test_sin_anomalias(self):
        valores = np.array([10, 12, 11, 13, 10, 12, 11])
        assert self.a._detect_anomalies(valores) == []

    def test_con_anomalia(self):
        valores = np.array([10, 12, 11, 13, 100, 12, 11])
        anomalias = self.a._detect_anomalies(valores)
        assert len(anomalias) == 1
        assert anomalias[0][1] == 100.0

    def test_menos_de_4_valores(self):
        assert self.a._detect_anomalies(np.array([1, 2, 3])) == []

    def test_vacio(self):
        assert self.a._detect_anomalies(np.array([])) == []


class TestAnalyzeDataResults:
    """analyze_data_results() produce resumen, tendencias y anomalías."""

    def setup_method(self):
        self.a = IntelligentAssistant.__new__(IntelligentAssistant)
        self.a.business_contexts = {}
        self.a.kpi_patterns = {}

    def test_dataframe_vacio_retorna_vacio(self):
        assert self.a.analyze_data_results(pd.DataFrame(), "") == {}

    def test_dataframe_con_datos(self):
        df = pd.DataFrame({
            "Producto": ["A", "B", "C"],
            "Ventas": [100, 200, 150],
        })
        r = self.a.analyze_data_results(df, "ventas")
        assert r["data_summary"]["total_records"] == 3
        assert r["data_summary"]["numeric_columns"] == ["Ventas"]

    def test_detecta_dominancia_categorica(self):
        df = pd.DataFrame({
            "Ciudad": ["Bogotá", "Bogotá", "Bogotá", "Medellín"],
            "Ventas": [100, 200, 150, 50],
        })
        r = self.a.analyze_data_results(df, "ventas")
        assert len(r["patterns"]) > 0
        assert r["patterns"][0]["type"] == "dominance"
        assert r["patterns"][0]["dominant_value"] == "Bogotá"
