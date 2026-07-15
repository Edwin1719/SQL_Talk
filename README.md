# SQLTalk-AI

Asistente conversacional que traduce lenguaje natural a SQL, ejecuta consultas sobre múltiples motores de base de datos y visualiza resultados.

**Autor:** Edwin Quintero Alzate · [`egqa1975@gmail.com`](mailto:egqa1975@gmail.com) · [github.com/Edwin1719/SQL_Talk](https://github.com/Edwin1719/SQL_Talk)

---

## ¿Qué hace?

Escribís una pregunta en español o inglés, SQLTalk-AI la convierte a SQL usando un modelo de lenguaje (DeepSeek V4 Flash por defecto), ejecuta la consulta contra la base de datos y te muestra los resultados como tabla más un gráfico generado automáticamente.

### Flujo

```
Pregunta → LLM genera SQL → Ejecuta contra BD → DataFrame → Tabla + Plotly + Insights IA
                                                                            → KPIs rápidos
                                                                            → Refinamiento iterativo

Pregunta sobre esquema → LLM analiza → Recomendación de tablas/columnas

Descripción de modelo → LLM genera JSON TOM → ZIP .pbip → Power BI Desktop
```

---

## Motores soportados

| Motor | Driver | Autenticación |
|---|---|---|
| SQL Server | `pyodbc` + ODBC Driver 17 | Windows integrada (Trusted Connection) |
| PostgreSQL | `psycopg2` | usuario/contraseña |
| MySQL | `pymysql` | usuario/contraseña |
| SQLite | `sqlalchemy` nativo | ruta a archivo `.db` |

---

## Captura de pantalla

<!-- Aquí podés insertar una imagen real de la app funcionando -->
<!-- ![SQLTalk-AI en acción](screenshot.png) -->

---

## Requisitos

- Python 3.8–3.12
- API Key de [DeepSeek](https://platform.deepseek.com/api-keys) (recomendado) u OpenAI
- ODBC Driver 17 for SQL Server (solo si usás SQL Server)
- Cada motor de BD requiere su driver nativo (se instalan con `requirements.txt`)

---

## Instalación

```bash
git clone https://github.com/Edwin1719/SQL_Talk.git
cd SQL_Talk

python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac

pip install -r requirements.txt
```

---

## Configuración

```bash
cp .env.example .env
```

Editar `.env` con los valores reales. Mínimo requerido:

```ini
DEEPSEEK_API_KEY=sk-...
AI_MODEL=deepseek-v4-flash
AI_MODEL_BASE_URL=https://api.deepseek.com/v1
AI_TEMPERATURE=0.0
```

El resto de variables son opcionales (conexión por defecto a SQL Server, logging, cache, etc.).

---

## Ejecución

### Streamlit (recomendado)

```bash
streamlit run sqltalk/app.py
```

```
sqltalk/
├── app.py              # Interfaz Streamlit (UI, formularios, resultados, gráficos, KPIs)
├── sql_agent.py        # Conexión a BD, generación y limpieza de SQL vía LangChain
├── assistant.py        # Clase IntelligentAssistant: insights, tendencias, anomalías, schema Q&A
├── viz.py              # Visualización automática y personalizada con Plotly
├── pbip_builder.py     # Generación de proyectos Power BI (formato PBIP)
tests/
├── test_pbip_builder.py  # Tests para generación PBIP
├── test_viz.py
├── test_assistant.py
├── test_sql_agent.py
├── conftest.py
```

### Capas

1. **UI** — Streamlit con inputs dinámicos según el motor de BD, checkbox de KPIs, panel de insights IA, consultas sugeridas y generador de modelos Power BI.
2. **SQL Agent** — `create_sql_query_chain` de LangChain + `ChatOpenAI` (compatible con DeepSeek). Templates de prompt específicos por motor.
3. **Asistente** — `IntelligentAssistant` con análisis offline (regresión lineal para tendencias, IQR para anomalías, detección de patrones de dominio), generación de insights vía LLM y consultas sobre el esquema de BD.
4. **Visualización** — `auto_visualize()` elige tipo de gráfico según cardinalidad de columnas. Panel de gráfico personalizado con 5 opciones. Panel de KPIs rápidos con tarjetas `st.metric()`.
5. **Generación PBIP** — `pbip_builder.py` genera proyectos Power BI completos desde lenguaje natural usando DeepSeek + formato TOM.
---
## Funcionalidades principales

| Funcionalidad | Estado | Detalle |
|---|---|---|
| NL → SQL con DeepSeek/OpenAI | ✅ | Prompt templates específicos por motor |
| Multi-BD (4 motores) | ✅ | SQLAlchemy como capa de abstracción |
| Limpieza de SQL generado | ✅ | `clean_sql_query()` remueve markdown, comentarios, normaliza |
| Refinamiento iterativo | ✅ | Contexto conversacional entre consultas sucesivas |
| Panel de KPIs rápidos | ✅ | Tarjetas `st.metric()` con primeras columnas numéricas |
| Explorador de esquema inteligente | ✅ | Preguntas en lenguaje natural sobre la estructura de la BD |
| Generación de modelo Power BI (PBIP) | ✅ | DeepSeek genera JSON TOM → ZIP descargable → abrir en PBI Desktop |
| Gráfico automático | ✅ | Plotly — detecta tipo según columnas |
| Gráfico personalizado | ✅ | Selector con 5 tipos, columnas a elección |
| Insights IA | ✅ | Llamada separada al LLM con contexto de negocio |
| Detección de tendencias | ✅ | Regresión lineal offline (no requiere LLM) |
| Detección de anomalías | ✅ | Método IQR offline |
| Consultas sugeridas | ✅ | Basadas en dominio detectado (ventas, productos, clientes) |
| Historial de sesión | ✅ | Últimas 10 consultas con resumen |
| Exportar CSV / Excel | ✅ | Botones de descarga directa |
| Test suite | ✅ | 44 tests (pytest) — pbip_builder, assistant, sql_agent |
| Validación de SQL generado | ❌ | Pendiente — no rechaza DROP/DELETE/TRUNCATE |

## Dependencias principales

| Paquete | Versión | Uso |
|---|---|---|
| `streamlit` | 1.32 | Interfaz de usuario |
| `langchain` | 0.3.0 | Orquestación LLM |
| `langchain-community` | 0.3.27 | Utilidades: `SQLDatabase`, conectores |
| `langchain-openai` | 0.1.25 | Cliente ChatOpenAI (compatible DeepSeek) |
| `sqlalchemy` | 2.0.35 | Conexión a bases de datos |
| `plotly` | 5.17.0 | Visualización interactiva |
| `pandas` | 2.2.0 | Manejo de resultados |
| `python-dotenv` | 1.0.1 | Configuración vía `.env` |

---

## Licencia

MIT. Ver [LICENSE](LICENSE).

---

## Notas de desarrollo

- El proyecto usa DeepSeek V4 Flash como modelo por defecto; configurable vía `AI_MODEL`, `AI_MODEL_BASE_URL` y `AI_TEMPERATURE` en `.env`.
- `langchain_openai.ChatOpenAI` reemplazó a `langchain_community.chat_models.ChatOpenAI` (deprecado en LangChain 0.3).
- Soporte multi-schema (AdventureWorks y bases con schemas no-dbo): `SQLDatabase` se parchea post-construcción para incluir tablas de todos los schemas.
