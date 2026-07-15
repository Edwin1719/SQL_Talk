import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple, Optional, Any, Union
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json
from dotenv import load_dotenv

load_dotenv()

class IntelligentAssistant:
    """
    Asistente inteligente que analiza consultas, resultados y genera insights automáticos
    para ayudar en la toma de decisiones empresariales.
    """

    def __init__(self, model_name: Optional[str] = None, temperature: Optional[float] = None) -> None:
        """
        Inicializa el asistente inteligente

        Args:
            model_name: Nombre del modelo (ej: deepseek-chat, gpt-4).
                       Por defecto lee AI_MODEL del .env.
            temperature: Temperatura (0.0 = determinístico, 1.0 = creativo).
                        Por defecto lee AI_TEMPERATURE del .env.
        """
        # Leer configuración del .env (sin defaults ocultos en código)
        env_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        env_model = os.getenv("AI_MODEL")
        env_base_url = os.getenv("AI_MODEL_BASE_URL")
        env_temp = os.getenv("AI_TEMPERATURE")

        model = model_name or env_model
        temp = temperature if temperature is not None else env_temp

        missing = []
        if not env_key:
            missing.append("DEEPSEEK_API_KEY (u OPENAI_API_KEY como fallback)")
        if not model:
            missing.append("AI_MODEL")
        if not env_base_url:
            missing.append("AI_MODEL_BASE_URL")
        if temp is None:
            missing.append("AI_TEMPERATURE")
        if missing:
            raise ValueError(
                "Faltan variables en el archivo .env:\n  - " + "\n  - ".join(missing) +
                "\nCopia .env.example a .env y completa los valores."
            )

        self.llm = ChatOpenAI(
            model=model,
            temperature=float(temp),
            openai_api_key=env_key,
            openai_api_base=env_base_url
        )
        self.session_history = []
        self.context_memory = {}

        # Patrones de contexto empresarial
        self.business_contexts = {
            'ventas': ['ventas', 'revenue', 'ingresos', 'facturación', 'sales'],
            'productos': ['producto', 'item', 'articulo', 'sku', 'inventario'],
            'clientes': ['cliente', 'customer', 'comprador', 'usuario'],
            'tiempo': ['mes', 'año', 'trimestre', 'fecha', 'periodo'],
            'geografico': ['región', 'país', 'ciudad', 'zona', 'territorio'],
            'rendimiento': ['top', 'mejor', 'peor', 'ranking', 'performance']
        }

        # Métricas KPI comunes
        self.kpi_patterns = {
            'growth': r'crecimiento|growth|aumento|incremento',
            'decline': r'disminución|decline|caída|reducción',
            'comparison': r'comparar|vs|versus|diferencia',
            'trend': r'tendencia|trend|evolución|patrón'
        }

    def analyze_query_context(self, query: str) -> Dict[str, Any]:
        """Analiza el contexto y intención de la consulta del usuario"""
        query_lower = query.lower()

        context = {
            'business_domain': [],
            'query_type': 'informational',
            'time_sensitivity': False,
            'comparison_intent': False,
            'kpi_focus': [],
            'urgency_level': 'normal'
        }

        for domain, keywords in self.business_contexts.items():
            if any(keyword in query_lower for keyword in keywords):
                context['business_domain'].append(domain)

        if any(word in query_lower for word in ['¿cuál', 'cuánto', 'qué', 'what', 'how much']):
            context['query_type'] = 'quantitative'
        elif any(word in query_lower for word in ['por qué', 'why', 'cómo', 'how']):
            context['query_type'] = 'analytical'
        elif any(word in query_lower for word in ['predice', 'forecast', 'futuro']):
            context['query_type'] = 'predictive'

        time_words = ['hoy', 'ayer', 'mes', 'año', 'trimestre', 'recent', 'último']
        context['time_sensitivity'] = any(word in query_lower for word in time_words)

        comparison_words = ['vs', 'versus', 'comparar', 'diferencia', 'mejor', 'peor']
        context['comparison_intent'] = any(word in query_lower for word in comparison_words)

        for kpi, pattern in self.kpi_patterns.items():
            if re.search(pattern, query_lower):
                context['kpi_focus'].append(kpi)

        urgent_words = ['urgente', 'inmediato', 'ahora', 'crítico']
        if any(word in query_lower for word in urgent_words):
            context['urgency_level'] = 'high'

        return context

    def analyze_data_results(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Analiza los resultados de datos para encontrar patrones e insights"""
        if not isinstance(df, pd.DataFrame) or df.empty:
            return {}

        insights = {
            'data_summary': {},
            'patterns': [],
            'anomalies': [],
            'trends': [],
            'recommendations': []
        }

        insights['data_summary'] = {
            'total_records': len(df),
            'columns': list(df.columns),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist()
        }

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                if len(col_data) > 1:
                    trend = self._detect_trend(col_data.values)
                    if trend != 'stable':
                        insights['trends'].append({
                            'column': col,
                            'trend': trend,
                            'magnitude': abs(col_data.iloc[-1] - col_data.iloc[0]) if len(col_data) > 1 else 0
                        })
                anomalies = self._detect_anomalies(col_data.values)
                if anomalies:
                    insights['anomalies'].extend([{
                        'column': col,
                        'type': 'outlier',
                        'value': val,
                        'index': idx
                    } for idx, val in anomalies])

        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            value_counts = df[col].value_counts()
            if len(value_counts) > 1:
                top_percentage = value_counts.iloc[0] / len(df) * 100
                if top_percentage > 70:
                    insights['patterns'].append({
                        'type': 'dominance',
                        'column': col,
                        'dominant_value': value_counts.index[0],
                        'percentage': round(top_percentage, 2)
                    })

        return insights

    def _detect_trend(self, values: np.ndarray) -> str:
        """Detecta tendencia en serie de valores"""
        if len(values) < 2:
            return 'stable'
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        threshold = np.std(values) * 0.1
        if slope > threshold:
            return 'increasing'
        elif slope < -threshold:
            return 'decreasing'
        else:
            return 'stable'

    def _detect_anomalies(self, values: np.ndarray) -> List[Tuple[int, float]]:
        """Detecta valores anómalos usando método IQR"""
        if len(values) < 4:
            return []
        Q1 = np.percentile(values, 25)
        Q3 = np.percentile(values, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        anomalies = []
        for i, val in enumerate(values):
            if val < lower_bound or val > upper_bound:
                anomalies.append((i, val))
        return anomalies

    def generate_insights(self, query: str, results: pd.DataFrame, query_context: Dict[str, Any], data_analysis: Dict[str, Any]) -> str:
        """Genera insights inteligentes usando el LLM configurado"""
        system_prompt = """Eres un consultor de business intelligence experto. Tu trabajo es analizar consultas SQL,
        resultados de datos y generar insights accionables para la toma de decisiones empresariales.

        Debes proporcionar:
        1. Resumen ejecutivo del análisis
        2. Insights clave encontrados
        3. Recomendaciones específicas y accionables
        4. Preguntas de seguimiento sugeridas
        5. Alertas o puntos de atención

        Usa un lenguaje profesional pero accesible. Enfócate en el valor empresarial."""

        context_info = f"""
        CONSULTA ORIGINAL: {query}

        CONTEXTO DE LA CONSULTA:
        - Dominio empresarial: {', '.join(query_context.get('business_domain', []))}
        - Tipo de consulta: {query_context.get('query_type', 'N/A')}
        - Sensibilidad temporal: {'Sí' if query_context.get('time_sensitivity') else 'No'}
        - Intención de comparación: {'Sí' if query_context.get('comparison_intent') else 'No'}
        - Nivel de urgencia: {query_context.get('urgency_level', 'normal')}

        ANÁLISIS DE DATOS:
        - Total de registros: {data_analysis.get('data_summary', {}).get('total_records', 0)}
        - Columnas numéricas: {data_analysis.get('data_summary', {}).get('numeric_columns', [])}
        - Tendencias detectadas: {len(data_analysis.get('trends', []))}
        - Anomalías encontradas: {len(data_analysis.get('anomalies', []))}
        - Patrones identificados: {len(data_analysis.get('patterns', []))}
        """

        if isinstance(results, pd.DataFrame) and not results.empty:
            sample_data = results.head(5).to_string()
            context_info += f"\n\nMUESTRA DE DATOS:\n{sample_data}"

        if data_analysis.get('trends'):
            trends_info = "\n\nTENDENCIAS DETECTADAS:\n"
            for trend in data_analysis['trends']:
                trends_info += f"- {trend['column']}: {trend['trend']} (magnitud: {trend['magnitude']})\n"
            context_info += trends_info

        if data_analysis.get('anomalies'):
            anomalies_info = "\n\nANOMALÍAS DETECTADAS:\n"
            for anomaly in data_analysis['anomalies'][:3]:
                anomalies_info += f"- {anomaly['column']}: Valor {anomaly['value']} es anómalo\n"
            context_info += anomalies_info

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context_info)
        ]

        try:
            response = self.llm(messages)
            return response.content
        except Exception as e:
            return f"Error generando insights: {str(e)}"

    def suggest_follow_up_queries(self, query: str, results: pd.DataFrame, context: Dict[str, Any]) -> List[str]:
        """Sugiere consultas de seguimiento relevantes"""
        suggestions = []
        domains = context.get('business_domain', [])

        if 'ventas' in domains:
            suggestions.extend([
                "¿Cuál es la tendencia de ventas en los últimos 6 meses?",
                "¿Qué productos tienen mejor margen de ganancia?",
                "¿Cuáles son los clientes más rentables?"
            ])
        if 'productos' in domains:
            suggestions.extend([
                "¿Qué productos tienen menor rotación?",
                "¿Cuál es el análisis ABC de productos?",
                "¿Qué productos están por debajo del stock mínimo?"
            ])
        if 'clientes' in domains:
            suggestions.extend([
                "¿Cuál es la segmentación de clientes por valor?",
                "¿Qué clientes tienen riesgo de churn?",
                "¿Cuál es el ticket promedio por cliente?"
            ])

        query_type = context.get('query_type')
        if query_type == 'quantitative':
            suggestions.append("¿Cómo se compara esto con el periodo anterior?")
        elif query_type == 'analytical':
            suggestions.append("¿Qué factores están influyendo en estos resultados?")

        return suggestions[:5]

    def update_session_memory(self, query: str, results: pd.DataFrame, insights: str) -> None:
        """Actualiza la memoria de la sesión para mantener contexto"""
        session_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'results_summary': {
                'total_records': len(results) if isinstance(results, pd.DataFrame) else 0,
                'columns': list(results.columns) if isinstance(results, pd.DataFrame) else []
            },
            'insights': insights[:500]
        }
        self.session_history.append(session_entry)
        if len(self.session_history) > 10:
            self.session_history.pop(0)

    def get_full_analysis(self, query: str, results: pd.DataFrame) -> Dict[str, Any]:
        """Método principal que ejecuta análisis completo"""
        query_context = self.analyze_query_context(query)
        data_analysis = self.analyze_data_results(results, query)
        insights = self.generate_insights(query, results, query_context, data_analysis)
        follow_up_queries = self.suggest_follow_up_queries(query, results, query_context)
        self.update_session_memory(query, results, insights)

        return {
            'query_context': query_context,
            'data_analysis': data_analysis,
            'insights': insights,
            'follow_up_queries': follow_up_queries,
            'session_context': len(self.session_history)
        }

    def query_schema(self, schema_text: str, question: str) -> str:
        """Responde preguntas sobre el esquema de la base de datos usando el LLM"""
        system_prompt = """Eres un experto en bases de datos relacionales. Tu trabajo es analizar
el esquema de una base de datos y responder preguntas del usuario de forma clara y concisa.

Debes:
- Identificar qué tablas y columnas son relevantes para la pregunta
- Explicar relaciones entre tablas si aplica
- Sugerir cómo usar esa información para consultas
- Usar un lenguaje claro, el usuario no es técnico

Ejemplo:
Usuario: "¿Qué tablas tienen información de clientes?"
Respuesta: "La tabla 'Clientes' tiene los datos principales (nombre, dirección, teléfono).
También hay una tabla 'Ventas' que se relaciona con Clientes por el campo 'cliente_id'.
Si necesitas consultar clientes, podés usar la tabla Clientes. Si querés ver qué compraron,
podés combinar Clientes con Ventas." """

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Esquema de la base de datos:\n{schema_text}\n\nPregunta: {question}")
            ]
            response = self.llm(messages)
            return response.content
        except Exception as e:
            return f"Error consultando el esquema: {str(e)}"
