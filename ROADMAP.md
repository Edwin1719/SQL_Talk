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

## Fase 1 — Consolidación (actual)

La base actual del proyecto.

| Feature | Estado | Descripción |
|---|---|---|
| NL → SQL con DeepSeek V4 Flash | ✅ | Pipeline vía `create_sql_query_chain` |
| Multi-BD (SQL Server, PostgreSQL, MySQL, SQLite) | ✅ | 4 motores via SQLAlchemy |
| Visualización automática | ✅ | Plotly con detección de tipo de gráfico |
| Insights IA | ✅ | Análisis de contexto + tendencias + anomalías |
| SQL generado visible en UI | ✅ | Expander colapsado con `st.code` |
| Exportar CSV / Excel | ✅ | Botones de descarga directa |
| Explorador de esquema | ✅ | `sqlalchemy.inspect()` en sidebar |
| Test suite (54 tests) | ✅ | pytest sobre core lógico |
| UI profesional con sidebar | ✅ | Material icons, gradiente, footer SVGs |

---

## Fase 2 — Integración con Power BI (próximo)

### 🎯 2.1 — Misma BD como puente

SQLTalk y Power BI apuntan a la misma base de datos. Power BI en DirectQuery o Import.
El gerente usa SQLTalk para explorar y validar, Power BI para dashboards formales.

- **Esfuerzo:** 0 (solo configurar el origen de datos en Power BI Desktop)
- **Valor:** Alto — el usuario ya puede hacerlo hoy
- **Dependencias:** Ninguna

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

### 🎯 2.3 — Publicación en modelo semántico vía MCP

Integración con **Power BI Modeling MCP** para que SQLTalk pueda crear tablas,
medidas y relaciones directamente en un modelo semántico de Power BI Desktop o Fabric.

```text
Usuario: "Agrega una tabla calendario al modelo con medidas de ventas YTD y PY"
SQLTalk → Power BI Modeling MCP → Modelo semántico actualizado
```

- **Esfuerzo:** Medio (servidor MCP + trigger desde SQLTalk)
- **Valor:** Alto — construcción automatizada del modelo desde NL
- **Dependencias:** Power BI Desktop abierto o Fabric workspace configurado

### 💡 2.4 — Generación de dashboard PBIR

SQLTalk genera archivos de definición de página/visual Power BI (formato PBIR/PBIP)
y los despliega en un workspace de Fabric.

```text
Usuario: "Crea un dashboard de ventas por región con mapa y KPI de cumplimiento"
SQLTalk → archivos PBIR → Fabric API → Dashboard publicado
```

- **Esfuerzo:** Alto (requiere conocimiento del formato PBIR + Fabric REST API)
- **Valor:** Máximo — dashboard completo desde una frase
- **Dependencias:** Fabric workspace, permiso de despliegue

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

### 💡 3.4 — Query favoritas / guardadas

El usuario puede marcar consultas como favoritas y ejecutarlas con un clic.

- **Esfuerzo:** Bajo (~15 líneas)
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

---

## Fase 5 — Experiencia de usuario (futuro)

### 🔮 5.1 — App empaquetada (.exe)

SQLTalk se empaqueta como ejecutable independiente con PyInstaller.
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

---

## Resumen visual del roadmap

```
FASE 1 ─── Consolidación ───────────────────────────────────────────── ✅ hoy
FASE 2 ─── Power BI ─── BD puente → DAX → MCP Modelo → PBIR dashboard
FASE 3 ─── Automatización ─── Reportes → Alertas → Historial → Favoritos
FASE 4 ─── Análisis avanzado ─── JOIN auto → Multi-período → Debug SQL → Narración
FASE 5 ─── UX ─── .exe → Chat conversacional
```

---

## Notas

- Este roadmap es **vivo** — las prioridades cambian según el uso real.
- Cada feature incluye su esfuerzo estimado para que puedas decidir qué
  tiene más valor para tu caso de uso específico.
- No hay fechas compromiso — el proyecto es una herramienta personal/gerencial
  y crece a tu ritmo.
- Las features marcadas como 🔮 son visión a futuro y pueden requerir
  cambios arquitectónicos más profundos.

---

*Última actualización: Julio 2026*
