# ROADMAP — SQLTalk-AI

> Visión: Convertir SQLTalk-AI en una terminal automatizada de análisis de datos,
> donde el lenguaje natural sea la interfaz única para consultar, modelar, visualizar
> y distribuir información empresarial.

---

## Leyenda

| Símbolo | Significado |
|---|---|
| ✅ | Implementado |
| 🟡 | Parcial / En progreso |
| ❌ | No implementado |
| 🎯 | Prioridad alta |
| 💡 | Prioridad media |
| 🔮 | Futuro / visión |

---


## Fase 1 — Consolidación

| Feature | Estado | Descripción |
|---|---|---|
| NL → SQL con DeepSeek V4 Flash | ✅ | Pipeline vía `create_sql_query_chain` |
| Multi-BD (SQL Server, PostgreSQL, MySQL, SQLite) | ✅ | 4 motores via SQLAlchemy |
| Visualización automática | ✅ | Plotly con detección de tipo de gráfico |
| Insights IA | ✅ | Análisis de contexto + tendencias + anomalías |
| Refinamiento iterativo de consultas | ✅ | Contexto conversacional entre consultas |
| Panel de KPIs rápidos | ✅ | `st.metric()` con primeras columnas numéricas |
| Explorador de esquema inteligente | ✅ | Preguntas NL sobre estructura de BD vía LLM |
| Generación de modelo Power BI (PBIP) | ✅ | DeepSeek genera JSON TOM → ZIP .pbip descargable |
| SQL generado visible en UI | ✅ | Expander colapsado con `st.code` |
| Exportar CSV / Excel | ✅ | Botones de descarga directa |
| Explorador de esquema | ✅ | `sqlalchemy.inspect()` en sidebar |
| Test suite | ✅ | 59 tests (pytest) — sql_agent, assistant, pbip_builder |
| UI profesional con sidebar | ✅ | Material icons, gradiente, footer SVGs |

### ✅ 1.5 — Guardián SQL (solo SELECT)

SQLTalk rechaza cualquier consulta que no sea `SELECT` o `WITH ... SELECT`
antes de ejecutarla contra la BD. Detecta DROP, DELETE, TRUNCATE, UPDATE,
INSERT, ALTER, CREATE, EXEC, MERGE y tokens no reconocidos.

- **Esfuerzo:** Bajo (~60 líneas: función + hook + 21 tests) — ✅ Completado
- **Valor:** Crítico — previene pérdida o modificación accidental de datos productivos
- **Configuración:** `ENABLE_SQL_VALIDATION=false` en `.env` para desactivar
- **Personalización:** `FORBIDDEN_SQL_KEYWORDS=DROP,DELETE` en `.env`
- **Tests:** 21 casos cubriendo SELECT, CTE, DROP, DELETE, comentarios enmascarados, validación desactivada

### ✅ 1.6 — Housekeeping: dependencias muertas

Eliminar paquetes en `requirements.txt` que no se importan en ningún módulo
del proyecto. `matplotlib` y `seaborn` están presentes pero todo el renderizado
usa Plotly.

- **Esfuerzo:** Muy bajo (2 líneas en `requirements.txt`) — ✅ Completado
- **Valor:** Medio — reduce ~15 MB de instalación innecesaria
- **Dependencias:** Ninguna
- **Riesgo:** Bajo — verificar que ningún import los referencie antes de eliminar

### ✅ 1.7 — Tests de integración del pipeline completo

Tests que validan el flujo NL → SQL → DataFrame usando SQLite en memoria
y mock del LLM. Verifican SELECT, filtros, count, SQL inválido, y que el
guardián bloquee DROP/DELETE sin modificar datos en la BD.

- **Esfuerzo:** Bajo (~45 líneas: fixture con `sqlite:///:memory:` + mock) — ✅ Completado
- **Valor:** Alto — detecta regresiones en el core del proyecto antes de producción
- **Tests:** 6 tests (3 pipeline correcto + 1 error SQL + 2 verificación de guardián contra BD real)
---

### 🎯 1.8 — Autodetección de ODBC Driver

`sql_agent.py` hardcodea `ODBC Driver 17 for SQL Server`. Detectar
automáticamente el driver disponible desde el registro de Windows
o probando conectividad con `pyodbc.drivers()`.

- **Esfuerzo:** Muy bajo (~10 líneas)
- **Valor:** Medio — elimina error de conexión en máquinas con Driver 18
- **Dependencias:** `pyodbc`

### 💡 1.9 — Logging estructurado

Los warnings de SQLAlchemy (tipos no reconocidos: `hierarchyid`,
`geography`) y errores de conexión se mezclan con stdout de Streamlit.
Migrar a `logging` con archivo rotativo y nivel configurable.

- **Esfuerzo:** Bajo (~20 líneas)
- **Valor:** Medio — facilita debugging en producción

### 💡 1.10 — Fix test_viz.py

`test_viz.py` importa `detect_column_names` que fue eliminado de
`viz.py`. Reparar o eliminar el archivo para suite completo en verde.

- **Esfuerzo:** Muy bajo (~5 líneas)
- **Valor:** Medio — elimina falso negativo en el suite

### 💡 1.11 — Tests con mock del LLM para assistant.py

`generate_insights()` y `suggest_follow_up_queries()` usan LLM real y
no tienen tests unitarios. Mockear respuestas conocidas del asistente.

- **Esfuerzo:** Bajo (~30 líneas: fixture + 4 tests)
- **Valor:** Alto — detecta regresiones en generación de insights
- **Dependencias:** `pytest`, `unittest.mock`

## Fase 2 — Integración con Power BI (próximo)

### 📌 2.1 — Misma BD como puente

SQLTalk y Power BI apuntan a la misma base de datos. Power BI en DirectQuery o Import.
El gerente usa SQLTalk para explorar y validar, Power BI para dashboards formales.

- **Esfuerzo:** 0 (solo configurar el origen de datos en Power BI Desktop)
- **Valor:** Alto
- **Nota:** No es una tarea, es una decisión de configuración ya disponible hoy.

### 🎯 2.2 — Generación de medidas DAX

SQLTalk recibe comandos como:

> "Crea una medida de ventas acumuladas YTD comparada con el año anterior"

Y el LLM genera el código DAX listo para copiar a Power BI.

```dax
Ventas YTD = TOTALYTD( SUM(Ventas[Monto]), 'Calendario'[Fecha] )
Ventas PY = CALCULATE( SUM(Ventas[Monto]), SAMEPERIODLASTYEAR('Calendario'[Fecha]) )
```

- **Esfuerzo:** Bajo (~20 líneas en `app.py`: nuevo input + template de prompt DAX)
- **Valor:** Medio — educativo, acelera la creación de medidas
- **Dependencias:** Prompt engineering para DAX

### ✅ 2.3 — Generación de modelo semántico PBIP ⭐

SQLTalk genera un proyecto Power BI completo (formato PBIP) a partir del esquema
de la BD conectada y las instrucciones del usuario. DeepSeek produce el JSON del modelo
(tablas, medidas, relaciones) y la app lo empaqueta como archivo descargable.

```text
Usuario: "Agrega una tabla calendario 2020-2026 con medidas de ventas YTD, PY y YoY%"
SQLTalk → DeepSeek genera JSON del modelo → archivo .pbip → descarga → abrir en Power BI Desktop
```

**Lo que puede generar:**
- Tabla calendario con año, mes, trimestre, días hábiles
- Medidas DAX: YTD, PY, YoY%, promedios, rankings
- Relaciones entre tablas detectadas del esquema
- Métricas de negocio según el dominio (ventas, inventario, clientes)

- **Esfuerzo:** Medio (~80 líneas: serialización PBIP + template de prompt)
- **Valor:** Alto — el usuario obtiene un modelo funcional sin abrir Power BI
- **Dependencias:** Ninguna (solo Python + DeepSeek)

### 🔮 2.4 — Publicación en vivo vía MCP (futuro)

Cuando 2.3 esté maduro y el usuario necesite aplicar los cambios directamente
sin descargar archivos, se agrega un servidor MCP que escribe en el modelo vivo
de Power BI Desktop (vía Tabular Editor CLI) o Fabric (vía XMLA Endpoint).

```text
Usuario: "Agrega la medida de ventas YTD al modelo"
SQLTalk → MCP Power Modeling Server → Power BI Desktop / Fabric → modelo actualizado
```

- **Esfuerzo:** Medio (servidor MCP + conector a TE o XMLA)
- **Valor:** Alto — feedback inmediato sobre el modelo vivo
- **Dependencias:** Power BI Desktop abierto (TE) o Fabric workspace (XMLA)
- **Requiere:** 2.3 implementado primero (el MCP server reusa la lógica de generación)

### 🔮 2.5 — Generación de dashboard (futuro lejano)

SQLTalk genera un reporte completo con páginas, visuales y filtros, ya sea como
archivos descargables o publicado directo a Fabric.

```text
Usuario: "Crea un dashboard de ventas por región con mapa y KPI de cumplimiento"
SQLTalk → JSON de definición de reporte → descarga PBIP o publish a Fabric
```

- **Esfuerzo:** Alto (requiere conocimiento del formato de visuales PBIP)
- **Valor:** Máximo — dashboard completo desde una frase
- **Dependencias:** Fabric workspace para publish automático
- **Requiere:** 2.3 y 2.4 implementados
---

## Fase 3 — Automatización del análisis (siguiente)

### 🎯 3.1 — Reportes programados

SQLTalk ejecuta consultas en segundo plano y envía resultados por email
en horarios definidos.

```text
Usuario: "Todos los lunes a las 8am, envíame el reporte de ventas semanal"
```

- **Esfuerzo:** Medio (tarea programada + email SMTP)
- **Valor:** Alto — el gerente recibe los datos sin abrir la app
- **Dependencias:** Servidor SMTP, scheduler

### 🎯 3.2 — Alertas inteligentes

SQLTalk monitorea la BD y notifica cuando se cumplen condiciones definidas.

```text
Usuario: "Avísame si las ventas del día caen más del 20% vs el mismo día del mes pasado"
```

- **Esfuerzo:** Medio (servicio de monitoreo + evaluación de condiciones)
- **Valor:** Alto — detección proactiva de anomalías
- **Dependencias:** Servicio background, conexión persistente a BD

### 💡 3.3 — Historial de consultas persistente

Las consultas anteriores se guardan en un archivo JSON local para poder
re-ejecutarlas, compartirlas o usarlas como base para nuevas preguntas.

- **Esfuerzo:** Bajo (~20 líneas, JSON + `st.session_state`)
- **Valor:** Medio — evita re-escribir consultas frecuentes
- **Dependencias:** Ninguna

### ✅ 3.4 — Query favoritas / guardadas

El usuario puede marcar consultas como favoritas y ejecutarlas con un clic.

- **Esfuerzo:** Bajo (~15 líneas) — ✅ Completado
- **Valor:** Medio — las 5 consultas que el gerente repite semanalmente
- **Dependencias:** Historial persistente (3.3)

---

## Fase 4 — Análisis avanzado (futuro)

### 🔮 4.1 — Análisis multi-tabla con JOIN automático

SQLTalk detecta relaciones entre tablas (por foreign keys o coincidencia de
columnas) y genera JOINs automáticos sin que el usuario los especifique.

```text
Usuario: "Dame ventas por cliente con su segmento y región"
SQLTalk detecta: Ventas → Clientes → Segmentos → Regiones
```

- **Esfuerzo:** Medio (leer foreign keys del esquema + construir JOINs)
- **Valor:** Alto — el usuario no necesita conocer la estructura de la BD
- **Dependencias:** Esquema con foreign keys o heurísticas de matching

### 🔮 4.2 — Análisis comparativo multi-período

SQLTalk detecta automáticamente columnas de fecha y genera análisis
comparativos: mes actual vs mes anterior, mismo mes año anterior, YTD, etc.

- **Esfuerzo:** Medio (detección de columnas fecha + generación de ventanas)
- **Valor:** Alto — el análisis temporal es el más común en gerencia
- **Dependencias:** Columna de fecha detectable en el esquema

### 🔮 4.3 — Corrección automática de consultas fallidas

Cuando una consulta SQL falla, SQLTalk envía el error al LLM junto con
la consulta original y el esquema, y el LLM genera una versión corregida
que se ejecuta automáticamente.

- **Esfuerzo:** Bajo (~15 líneas, ciclo de reintento)
- **Valor:** Alto — reduce la fricción cuando el SQL generado tiene errores
- **Dependencias:** LLM con capacidad de debug SQL

### 🔮 4.4 — Narración automática de resultados

SQLTalk genera un párrafo ejecutivo que resume los resultados en lenguaje
natural, destacando hallazgos clave, variaciones porcentuales y conclusiones.

```text
"Las ventas de Marzo 2024 fueron $1.2M, un 15% más que Febrero.
El producto estrella fue el SKU-452 con $340K. La región Norte
lidera con un 32% del total."
```

- **Esfuerzo:** Medio (template de prompt + post-procesamiento de métricas)
- **Valor:** Alto — el gerente obtiene el resumen sin leer tablas
- **Dependencias:** LLM con contexto de resultados numéricos

### ✅ 4.5 — Parsing robusto de resultados del LLM

Parseo de respuestas del LLM migrado de regex frágil a `json.loads()` sobre
JSON estructurado. Los prompts de los 4 motores SQL instruyen al LLM a devolver
un array JSON de objetos cuando no puede generar un SELECT. `parse_multi_year_data()`
eliminada. Regex mantenido como fallback de compatibilidad.

- **Esfuerzo:** Bajo — ✅ Completado

---

## Fase 5 — Experiencia de usuario (futuro)

### 🔮 5.1 — App empaquetada (.exe)

El usuario descarga, hace doble clic y la app se abre en el navegador.

- **Esfuerzo:** Bajo (script de PyInstaller + ícono)
- **Valor:** Medio — elimina la necesidad de Python y terminal
- **Dependencias:** PyInstaller

### 🔮 5.2 — Chat conversacional tipo ChatGPT

La interfaz pasa de inputs + botones a un chat continuo donde cada
consulta y respuesta se muestra como mensajes. El contexto se mantiene
entre turnos.

- **Esfuerzo:** Medio (reemplazar flujo actual por `st.chat_message`)
- **Valor:** Alto — experiencia más natural e intuitiva
- **Dependencias:** Streamlit 1.32+

### 💡 5.3 — Refactor de UI a componentes

`app.py` tiene ~550 líneas mezclando UI, lógica de negocio y manejo de
estado en un solo archivo. Extraer la interfaz en componentes separados
para mejorar mantenibilidad y preparar el terreno para el chat conversacional (5.2).

**Componentes propuestos:**
- `SidebarConnection` — formulario de conexión a BD (hoy ~100 líneas en sidebar)
- `ResultsPanel` — tabla de resultados + exportación CSV/Excel
- `InsightsPanel` — insights IA + KPIs + consultas sugeridas
- `PbipGenerator` — generador de modelos Power BI

- **Esfuerzo:** Medio (~2h: extraer lógica a archivos separados + pruebas manuales)
- **Valor:** Alto — el código se vuelve testeable, navegable y preparado para 5.2
- **Dependencias:** Ninguna

### 💡 5.4 — Guía de usuario para no-técnicos

Manual en PDF/HTML con screenshots: cómo obtener API key, conectar a BD,
primeros pasos, solución de problemas comunes. Escrito para el perfil real
del producto (gerentes, administrativos).

- **Esfuerzo:** Medio (~2h: escribir + capturas)
- **Valor:** Alto — reduce soporte técnico en distribución comercial

### 🔮 5.5 — Soporte multi-idioma (inglés)

Traducir prompts, insights y UI a inglés para mercado global.
Configurable vía variable de entorno `APP_LANG=en`.

- **Esfuerzo:** Medio (~1h: extraer strings a archivo de traducción)
- **Valor:** Alto — abre mercado internacional

---

## Fase 6 — Seguridad y operaciones

### 🎯 6.1 — Cifrado de API keys en disco

El archivo `.env` contiene API keys en texto plano. Cifrar la sección
de credenciales con una clave derivada de la sesión del usuario.

- **Esfuerzo:** Bajo (~15 líneas: `cryptography.fernet` + helper)
- **Valor:** Alto — requisito para distribución comercial
- **Dependencias:** `cryptography`

### 🎯 6.2 — Rate limiting

Proteger la app contra consultas masivas accidentales o maliciosas.
Límite por ventana de tiempo configurable desde `.env`.

- **Esfuerzo:** Bajo (~15 líneas: decorador + `st.session_state` contador)
- **Valor:** Alto — evita sobrecarga a la BD y consumo excesivo de API

### 💡 6.3 — Autenticación básica de usuarios

Pantalla de login con usuario/contraseña antes de acceder a la app.
Configurable desde `.env` (desactivado por defecto para desarrollo).

- **Esfuerzo:** Bajo (~20 líneas: formulario + validación)
- **Valor:** Alto — requisito para entornos productivos

### 🔮 6.4 — Auditoría de consultas

Registro persistente de quién ejecutó cada consulta, timestamp, SQL
generado y resultado (filas devueltas o error). Exportable a CSV.

- **Esfuerzo:** Medio (~40 líneas: modelo de datos + UI de consulta)
- **Valor:** Alto — trazabilidad para cumplimiento normativo

### 🔮 6.5 — Multi-tenant

Cada usuario con su propia configuración de BD, historial y favoritos.
Aislamiento total entre inquilinos.

- **Esfuerzo:** Alto (requiere 6.3 primero + refactor de estado)
- **Valor:** Máximo — modelo SaaS con clientes independientes
- **Requiere:** 6.3 implementado

---

## Resumen visual del roadmap

```
FASE 1 ─── Consolidación ─── Guardián SQL → Housekeeping → Tests integración → ODBC auto → Logging → Fix tests → Mock assistant
FASE 2 ─── Power BI ─── BD puente → DAX → Modelo PBIP ⭐ → MCP en vivo → Dashboard
FASE 3 ─── Automatización ─── Reportes → Alertas → Historial → Favoritos
FASE 4 ─── Análisis avanzado ─── JOIN auto → Multi-período → Debug SQL → Narración → Parsing robusto
FASE 5 ─── UX ─── .exe → Chat conversacional → Refactor UI → Guía usuario → Multi-idioma
FASE 6 ─── Seguridad ─── Cifrado keys → Rate limit → Auth básica → Auditoría → Multi-tenant
```

## Notas

- Este roadmap es **vivo** — las prioridades cambian según el uso real.
- Cada feature incluye su esfuerzo estimado para que puedas decidir qué
  tiene más valor para tu caso de uso específico.
- No hay fechas compromiso — el proyecto es una herramienta personal/gerencial
  y crece a tu ritmo.
- Las features marcadas como 🔮 son visión a futuro y pueden requerir
  cambios arquitectónicos más profundos.

*Última actualización: Julio 2026*

