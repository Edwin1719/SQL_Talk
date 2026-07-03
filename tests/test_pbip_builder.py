"""Tests para pbip_builder — generación de proyectos Power BI (PBIP)."""

import json
import zipfile
import pytest
from sqltalk.pbip_builder import build_pbip_package, build_schema_text


class TestBuildPBIpPackage:
    """Tests para build_pbip_package."""

    def test_zip_contiene_archivos_requeridos(self):
        """El ZIP debe contener definition.pbip, .pbi/localSettings.json y model/model.json."""
        modelo = {"tables": []}
        buf = build_pbip_package(modelo, "TestModel")
        with zipfile.ZipFile(buf) as zf:
            assert "definition.pbip" in zf.namelist()
            assert ".pbi/localSettings.json" in zf.namelist()
            assert "model/model.json" in zf.namelist()

    def test_model_json_tiene_estructura_valida(self):
        """model/model.json debe tener name, culture, compatibilityLevel y model."""
        modelo = {"tables": [{"name": "Test", "columns": [{"name": "x", "dataType": "int64"}]}]}
        buf = build_pbip_package(modelo, "MiModelo")
        with zipfile.ZipFile(buf) as zf:
            mj = json.loads(zf.read("model/model.json"))
        assert mj["name"] == "MiModelo"
        assert mj["culture"] == "en-US"
        assert mj["compatibilityLevel"] == 1565
        assert "model" in mj

    def test_model_json_mantiene_tablas(self):
        """Las tablas pasadas deben conservarse en model.json."""
        tables = [
            {"name": "Calendar", "columns": [{"name": "Date", "dataType": "dateTime"}]},
            {"name": "Sales", "columns": [{"name": "Amount", "dataType": "decimal"}]},
        ]
        buf = build_pbip_package({"tables": tables})
        with zipfile.ZipFile(buf) as zf:
            mj = json.loads(zf.read("model/model.json"))
        assert len(mj["model"]["tables"]) == 2
        assert mj["model"]["tables"][0]["name"] == "Calendar"

    def test_model_json_con_medidas(self):
        """Las medidas deben persistir en model.json."""
        modelo = {
            "tables": [
                {
                    "name": "Ventas",
                    "columns": [{"name": "Monto", "dataType": "decimal"}],
                    "measures": [
                        {
                            "name": "Ventas YTD",
                            "expression": "TOTALYTD(SUM(Ventas[Monto]), 'Calendar'[Date])",
                            "formatString": "#,##0.00",
                        }
                    ],
                }
            ]
        }
        buf = build_pbip_package(modelo)
        with zipfile.ZipFile(buf) as zf:
            mj = json.loads(zf.read("model/model.json"))
        medidas = mj["model"]["tables"][0]["measures"]
        assert len(medidas) == 1
        assert medidas[0]["name"] == "Ventas YTD"

    def test_model_vacio(self):
        """Modelo vacío (sin tablas) debe generar ZIP válido."""
        buf = build_pbip_package({"tables": []})
        with zipfile.ZipFile(buf) as zf:
            mj = json.loads(zf.read("model/model.json"))
        assert mj["model"]["tables"] == []

    def test_definicion_pbip_contiene_model_name(self):
        """definition.pbip debe tener el nombre del modelo."""
        buf = build_pbip_package({"tables": []}, "VentasModel")
        with zipfile.ZipFile(buf) as zf:
            dp = json.loads(zf.read("definition.pbip"))
        assert dp["model"]["name"] == "VentasModel"

    def test_zip_es_descargable(self):
        """El buffer debe ser un ZIP válido y tener tamaño > 0."""
        buf = build_pbip_package({"tables": []})
        assert buf.getvalue() is not None
        assert len(buf.getvalue()) > 0


class TestBuildSchemaText:
    """Tests para build_schema_text."""

    @pytest.fixture
    def mock_inspector(self):
        class MockInspector:
            def get_table_names(self):
                return ["Clientes", "Ventas"]

            def get_columns(self, table):
                if table == "Clientes":
                    return [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "nombre", "type": "VARCHAR(100)"},
                    ]
                return [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "cliente_id", "type": "INTEGER"},
                    {"name": "monto", "type": "DECIMAL(10,2)"},
                ]

            def get_foreign_keys(self, table):
                if table == "Ventas":
                    return [
                        {
                            "constrained_columns": ["cliente_id"],
                            "referred_table": "Clientes",
                            "referred_columns": ["id"],
                        }
                    ]
                return []

        return MockInspector()

    def test_incluye_nombres_de_tablas(self, mock_inspector):
        result = build_schema_text(mock_inspector)
        assert "Clientes" in result
        assert "Ventas" in result

    def test_incluye_columnas(self, mock_inspector):
        result = build_schema_text(mock_inspector)
        assert "id" in result
        assert "nombre" in result
        assert "monto" in result

    def test_incluye_foreign_keys(self, mock_inspector):
        result = build_schema_text(mock_inspector)
        assert "FK" in result or "cliente_id" in result

    def test_sin_foreign_keys_no_agrega_fk(self):
        class MockInspectorNoFK:
            def get_table_names(self):
                return ["Simple"]

            def get_columns(self, table):
                return [{"name": "id", "type": "INT"}]

            def get_foreign_keys(self, table):
                return []

        result = build_schema_text(MockInspectorNoFK())
        assert "FK" not in result
        assert "Simple" in result

    def test_inspector_vacio(self):
        class MockInspectorVacio:
            def get_table_names(self):
                return []

            def get_columns(self, table):
                return []

            def get_foreign_keys(self, table):
                return []

        result = build_schema_text(MockInspectorVacio())
        assert result == ""
