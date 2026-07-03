"""
PBIP Builder — Genera proyectos Power BI (formato PBIP) desde lenguaje natural.

Flujo:
  1. Recolectar esquema de la BD (sqlalchemy inspect)
  2. Enviar esquema + solicitud del usuario a DeepSeek
  3. DeepSeek devuelve JSON del modelo (formato TOM)
  4. Empaquetar como ZIP con estructura PBIP
  5. Usuario descarga y abre en Power BI Desktop
"""

import json
import zipfile
from io import BytesIO
from typing import Any, Optional

# ──────────────────────────────────────────────
# Templates de archivos PBIP
# ──────────────────────────────────────────────

DEFINITION_PBIP = {
    "version": "1.0",
    "culture": "en-US",
    "compatibilityLevel": 1565,
    "model": {
        "type": "model",
        "name": "SQLTalk Model",
    },
}

LOCAL_SETTINGS = {
    "version": "1.0",
    "culture": "en-US",
    "report": {"name": "Report"},
}

# ──────────────────────────────────────────────
# Prompt del sistema para DeepSeek
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un experto en modelos tabulares de Power BI (Tabular Object Model).
Genera ÚNICAMENTE JSON válido para la propiedad 'model' de un archivo model.json.

El JSON debe seguir esta estructura exacta:
{
  "tables": [
    {
      "name": "Nombre Tabla",
      "columns": [
        {"name": "Columna", "dataType": "int64|string|decimal|dateTime|boolean",
         "dataType": "columna string"}
      ],
      "measures": [
        {
          "name": "Nombre Medida",
          "expression": "Expresión DAX",
          "formatString": "#,##0.00"
        }
      ],
      "partitions": [
        {
          "name": "Particion",
          "source": {
            "type": "calculated",
            "expression": "Expresión DAX o consulta SQL"
          }
        }
      ]
    }
  ],
  "relationships": [
    {
      "name": "Nombre Relacion",
      "fromTable": "Tabla Origen",
      "fromColumn": "Columna Origen",
      "toTable": "Tabla Destino",
      "toColumn": "Columna Destino"
    }
  ]
}

REGLAS:
- Solo devuelve el JSON, sin markdown, sin explicaciones, sin bloques ```json
- Tablas reales de la BD: NUNCA incluyas partition (Power BI las importa automaticamente)
  Solo tablas calculadas (como Calendar) llevan partition con type "calculated"
- Medidas: usa DAX valido. Nombres claros en espanol
- Relaciones: usa las foreign keys del esquema como guia
- FormatString: "#,##0" para enteros, "#,##0.00" para decimales, "0.00%" para porcentajes
- No inventes tablas que no existen en el esquema
- No incluyas columnas que no existen en el esquema
- Los nombres en el modelo deben coincidir exactamente con los del esquema"""


def build_pbip_package(
    model_json: dict, model_name: str = "SQLTalk Model"
) -> BytesIO:
    """Crea estructura PBIP como ZIP en memoria.

    Args:
        model_json: Dict con la propiedad 'model' del model.json TOM.
        model_name: Nombre del modelo semántico.

    Returns:
        BytesIO con el ZIP listo para descargar.
    """
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # definition.pbip
        def_pbip = dict(DEFINITION_PBIP)
        def_pbip["model"]["name"] = model_name
        zf.writestr("definition.pbip", json.dumps(def_pbip, indent=2))

        # .pbi/localSettings.json
        zf.writestr(".pbi/localSettings.json", json.dumps(LOCAL_SETTINGS, indent=2))

        # model/model.json
        model_file = {
            "name": model_name,
            "culture": "en-US",
            "compatibilityLevel": 1565,
            "model": model_json,
        }
        zf.writestr("model/model.json", json.dumps(model_file, indent=2))

    buf.seek(0)
    return buf


def generate_model(
    schema_text: str, user_request: str, llm: Any
) -> Optional[dict]:
    """Genera el modelo semantico TOM llamando a DeepSeek.

    Args:
        schema_text: Texto con tablas, columnas, tipos y FK del esquema.
        user_request: Descripcion del usuario de lo que quiere en el modelo.
        llm: Instancia de ChatOpenAI configurada (desde IntelligentAssistant).

    Returns:
        Dict del modelo (propiedad 'model') o None si falla.
    """
    from langchain.schema import HumanMessage, SystemMessage

    user_prompt = (
        f"Basado en el siguiente esquema de base de datos y la solicitud del usuario, "
        f"genera el modelo semantico de Power BI.\n\n"
        f"ESQUEMA DE BASE DE DATOS:\n{schema_text}\n\n"
        f"SOLICITUD DEL USUARIO:\n{user_request}\n\n"
        f"Genera UNICAMENTE el JSON del modelo, sin explicaciones adicionales."
    )

    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = llm(messages)
        content = response.content.strip()

        # Extraer JSON de bloques markdown si DeepSeek los incluye
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return None


def build_schema_text(inspector) -> str:
    """Construye texto descriptivo del esquema desde un inspector SQLAlchemy.

    Args:
        inspector: sqlalchemy Inspector de la BD conectada.

    Returns:
        Texto formateado con tablas, columnas, tipos y FK.
    """
    table_names = inspector.get_table_names()
    schema_parts = []
    for table in table_names:
        cols = inspector.get_columns(table)
        col_info = ", ".join([f"{c['name']} ({c['type']})" for c in cols])
        fks = inspector.get_foreign_keys(table)
        fk_info = ""
        if fks:
            fk_strs = [
                f"{fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
                for fk in fks
            ]
            fk_info = f" | FK: {'; '.join(fk_strs)}"
        schema_parts.append(f"Tabla: {table}\nColumnas: {col_info}{fk_info}")
    return "\n\n".join(schema_parts)
