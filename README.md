# SQLTalk-AI

Asistente conversacional que traduce lenguaje natural a SQL, ejecuta consultas sobre múltiples motores de base de datos y visualiza resultados.

**Autor:** Edwin Quintero Alzate · [`egqa1975@gmail.com`](mailto:egqa1975@gmail.com) · [github.com/Edwin1719/SQL_Talk](https://github.com/Edwin1719/SQL_Talk)

---

## ¿Qué hace?

Escribís una pregunta en español o inglés, SQLTalk-AI la convierte a SQL usando un modelo de lenguaje (DeepSeek V4 Flash por defecto), ejecuta la consulta contra la base de datos y te muestra los resultados como tabla más un gráfico generado automáticamente.

### Flujo

```
Pregunta → LLM genera SQL → Ejecuta contra BD → DataFrame → Tabla + Plotly + Insights IA
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

> **Alternativa:** `pip install -e .` instala el paquete y deja disponible el comando `sqltalk-cli` (ver más abajo).

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

### CLI (consulta hardcodeada de ejemplo)

```bash
python -m scripts.cli
# o si instalaste con pip install -e .
sqltalk-cli
```

> El CLI ejecuta una consulta fija de ejemplo. No es interactivo.

---

## Estructura del proyecto

```
sqltalk/
├── app.py          # Interfaz Streamlit (UI, formularios, resultados, gráficos)
├── sql_agent.py    # Conexión a BD, generación y limpieza de SQL vía LangChain
├── assistant.py    # Clase IntelligentAssistant: análisis de contexto, detección de
│                   # tendencias/anomalías, insights vía LLM, consultas sugeridas
├── viz.py          # Visualización automática y personalizada con Plotly
scripts/
├── cli.py          # Entry point de consola (consulta fija)
tests/
├── __init__.py     # Vacío — pendiente de implementar
```

### Capas

1. **UI** — Streamlit con inputs dinámicos según el motor de BD, selector de gráfico personalizado, panel de insights IA y consultas sugeridas.
2. **SQL Agent** — `SQLDatabaseChain` de LangChain + `ChatOpenAI` (compatible con API de OpenAI y DeepSeek). Templates de prompt específicos por motor (corchetes `[]` para SQL Server, dobles comillas `""` para PostgreSQL, backticks para MySQL).
3. **Asistente** — `IntelligentAssistant` con análisis offline (regresión lineal para tendencias, IQR para anomalías, detección de patrones de dominio) y generación de insights vía LLM.
4. **Visualización** — `auto_visualize()` elige tipo de gráfico según cardinalidad de columnas. Panel de gráfico personalizado con 5 opciones (barras, torta, dispersión, histograma, líneas).

---

## Funcionalidades principales

| Funcionalidad | Estado | Detalle |
|---|---|---|
| NL → SQL con DeepSeek/OpenAI | ✅ | Prompt templates específicos por motor |
| Multi-BD (4 motores) | ✅ | SQLAlchemy como capa de abstracción |
| Limpieza de SQL generado | ✅ | `clean_sql_query()` remueve markdown, comentarios, normaliza |
| Gráfico automático | ✅ | Plotly — detecta tipo según columnas |
| Gráfico personalizado | ✅ | Selector con 5 tipos, columnas a elección |
| Insights IA | ✅ | Llamada separada al LLM con contexto de negocio |
| Detección de tendencias | ✅ | Regresión lineal offline (no requiere LLM) |
| Detección de anomalías | ✅ | Método IQR offline |
| Consultas sugeridas | ✅ | Basadas en dominio detectado (ventas, productos, clientes) |
| Historial de sesión | ✅ | Últimas 10 consultas con resumen |
| CLI | 🟡 | Consulta fija hardcodeada, no interactivo |
| Tests | ❌ | No implementados |
| Rate limiting / retry | ❌ | Sin manejo de errores de API |
| Límite de filas en consultas | ❌ | Sin protección contra tablas grandes |
| Validación de SQL generado | ❌ | No rechaza DROP/DELETE/TRUNCATE |

---

## Dependencias principales

| Paquete | Versión | Uso |
|---|---|---|
| `streamlit` | 1.32 | Interfaz de usuario |
| `langchain` | 0.3.0 | Orquestación LLM |
| `langchain-experimental` | 0.0.6 | `SQLDatabaseChain` (deprecado — pendiente migrar a `langchain-sql`) |
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

- El proyecto migró de OpenAI GPT a DeepSeek V4 Flash como modelo por defecto (2026-07-02).
- Las variables de entorno `AI_MODEL`, `AI_MODEL_BASE_URL` y `AI_TEMPERATURE` controlan el modelo sin tocar código.
- `langchain-experimental` está deprecado; la próxima refactorización debería migrar a `langchain-sql` / `create_sql_query_chain`.
- El README anterior contenía benchmarks y roadmaps expirados. Este README describe solo lo que el código realmente hace. Si algo falta, está en la lista de funcionalidades pendientes, no en una promesa futura.
