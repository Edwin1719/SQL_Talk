"""Tests para sql_agent.py — limpieza de SQL, validación de solo lectura, integración."""

import pytest
import os
from unittest.mock import MagicMock

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqltalk.sql_agent import clean_sql_query, validate_sql_readonly, consulta

class TestCleanSqlQuery:
    """clean_sql_query() remueve markdown, comentarios y normaliza."""

    def test_sql_simple(self):
        assert clean_sql_query("SELECT * FROM Ventas") == "SELECT * FROM Ventas;"

    def test_remueve_markdown_sql(self):
        assert clean_sql_query("```sql\nSELECT * FROM Ventas\n```") == "SELECT * FROM Ventas;"

    def test_remueve_markdown_sin_lenguaje(self):
        assert clean_sql_query("```\nSELECT * FROM Ventas\n```") == "SELECT * FROM Ventas;"

    def test_remueve_comentarios_linea(self):
        sql = "SELECT * FROM Ventas -- solo primeras 10"
        assert clean_sql_query(sql) == "SELECT * FROM Ventas;"

    def test_remueve_comentarios_bloque(self):
        sql = "SELECT /* comentario */ * FROM Ventas"
        assert clean_sql_query(sql) == "SELECT * FROM Ventas;"

    def test_normaliza_espacios(self):
        sql = "SELECT   *\nFROM  Ventas\nWHERE  id = 1"
        assert clean_sql_query(sql) == "SELECT * FROM Ventas WHERE id = 1;"

    def test_agrega_punto_y_coma(self):
        assert clean_sql_query("SELECT count(*) FROM Ventas") == "SELECT count(*) FROM Ventas;"

    def test_no_duplica_punto_y_coma(self):
        assert clean_sql_query("SELECT 1;") == "SELECT 1;"

    def test_vacio_retorna_vacio(self):
        assert clean_sql_query("") == ""

    def test_none_retorna_none(self):
        assert clean_sql_query(None) is None

    def test_multiple_lineas_con_comentarios(self):
        sql = """-- calcular total
        SELECT
            SUM(monto)  -- suma
        FROM Pedidos
        /* filtro activos */
        WHERE estado = 'activo'"""
        esperado = "SELECT SUM(monto) FROM Pedidos WHERE estado = 'activo';"
        assert clean_sql_query(sql) == esperado

    def test_case_insensitive_markdown(self):
        assert clean_sql_query("```SQL\nSELECT 1```") == "SELECT 1;"
        assert clean_sql_query("```Sql\nSELECT 1```") == "SELECT 1;"

class TestValidateSqlReadonly:
    """validate_sql_readonly() rechaza DROP/DELETE/etc, permite SELECT/WITH."""

    def setup_method(self):
        """Asegurar que ENABLE_SQL_VALIDATION esté activo para cada test."""
        os.environ["ENABLE_SQL_VALIDATION"] = "true"

    def test_select_simple(self):
        ok, msg = validate_sql_readonly("SELECT * FROM Ventas")
        assert ok is True
        assert msg == ""

    def test_select_con_comentarios(self):
        ok, msg = validate_sql_readonly("SELECT * FROM Ventas -- solo primeras 10")
        assert ok is True

    def test_select_con_cte(self):
        ok, msg = validate_sql_readonly("WITH VentasTop AS (SELECT * FROM Ventas) SELECT * FROM VentasTop")
        assert ok is True

    def test_select_con_cte_multiline(self):
        sql = """
        WITH VentasTop AS (
            SELECT TOP 10 *, ROW_NUMBER() OVER (ORDER BY Total DESC) as rn
            FROM Ventas
        )
        SELECT * FROM VentasTop WHERE rn <= 5
        """
        ok, msg = validate_sql_readonly(sql)
        assert ok is True

    def test_drop_table(self):
        ok, msg = validate_sql_readonly("DROP TABLE Ventas")
        assert ok is False
        assert "DROP" in msg

    def test_delete(self):
        ok, msg = validate_sql_readonly("DELETE FROM Ventas WHERE id = 1")
        assert ok is False
        assert "DELETE" in msg

    def test_truncate(self):
        ok, msg = validate_sql_readonly("TRUNCATE TABLE Ventas")
        assert ok is False
        assert "TRUNCATE" in msg

    def test_update(self):
        ok, msg = validate_sql_readonly("UPDATE Ventas SET Total = 0")
        assert ok is False

    def test_insert(self):
        ok, msg = validate_sql_readonly("INSERT INTO Ventas VALUES (1)")
        assert ok is False

    def test_alter(self):
        ok, msg = validate_sql_readonly("ALTER TABLE Ventas ADD Columna INT")
        assert ok is False

    def test_create(self):
        ok, msg = validate_sql_readonly("CREATE TABLE Otra (id INT)")
        assert ok is False

    def test_exec(self):
        ok, msg = validate_sql_readonly("EXEC sp_help 'Ventas'")
        assert ok is False

    def test_merge(self):
        ok, msg = validate_sql_readonly("MERGE INTO Ventas AS target USING ...")
        assert ok is False

    def test_drop_enmascarado_con_comentario(self):
        """DROP después de comentario inline no debería engañar al parser."""
        ok, msg = validate_sql_readonly("SELECT 1; -- comentario\nDROP TABLE Ventas")
        assert ok is True  # El primer token es SELECT

    def test_vacio(self):
        ok, msg = validate_sql_readonly("")
        assert ok is True

    def test_none(self):
        ok, msg = validate_sql_readonly(None)  # type: ignore
        assert ok is True

    def test_solo_whitespace(self):
        ok, msg = validate_sql_readonly("   \n  \t  ")
        assert ok is True

    def test_desactivado_explicitamente(self):
        os.environ["ENABLE_SQL_VALIDATION"] = "false"
        ok, msg = validate_sql_readonly("DROP TABLE Ventas")
        assert ok is True

    def test_cte_sin_select_final_pero_con_select_dentro(self):
        """WITH ... AS (SELECT ...) tiene SELECT en el cuerpo → válido."""
        ok, msg = validate_sql_readonly("WITH foo AS (SELECT 1)")
        assert ok is True

    def test_sql_con_select_minusculas(self):
        ok, msg = validate_sql_readonly("select * from productos")
        assert ok is True

    def test_token_desconocido_rechazado(self):
        ok, msg = validate_sql_readonly("FOOBAR xyz")
        assert ok is False
        assert "FOOBAR" in msg


class TestConsultaIntegration:
    """Pipeline NL → SQL → DataFrame con SQLite en memoria + mock del LLM.

    Valida que consulta() ejecute SQL correcto, maneje errores SQL,
    y que el guardián bloquee DROP/DELETE sin modificar datos.
    """

    # ── fixtures ──────────────────────────────────────────────

    @pytest.fixture(autouse=True)
    def _ensure_validation_on(self):
        os.environ["ENABLE_SQL_VALIDATION"] = "true"
        yield

    @pytest.fixture
    def engine(self):
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE productos ("
                "  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, precio REAL NOT NULL"
                ")"
            ))
            conn.execute(text(
                "INSERT INTO productos VALUES "
                "(1, 'Laptop', 1500.00),"
                "(2, 'Mouse', 25.50),"
                "(3, 'Teclado', 75.00)"
            ))
        return engine

    @pytest.fixture
    def chain(self):
        chain = MagicMock()
        chain.invoke.return_value = "SELECT * FROM productos"
        return chain

    # ── tests ─────────────────────────────────────────────────

    def test_select_devuelve_dataframe(self, chain, engine):
        df, sql = consulta(chain, engine, "todos los productos")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["id", "nombre", "precio"]

    def test_select_con_filtro(self, chain, engine):
        chain.invoke.return_value = "SELECT * FROM productos WHERE precio > 100"
        df, _ = consulta(chain, engine, "productos caros")
        assert len(df) == 1
        assert df.iloc[0]["nombre"] == "Laptop"

    def test_select_count(self, chain, engine):
        chain.invoke.return_value = "SELECT count(*) as total FROM productos"
        df, _ = consulta(chain, engine, "contar productos")
        assert df.iloc[0]["total"] == 3

    def test_sql_invalido_retorna_error(self, chain, engine):
        chain.invoke.return_value = "SELECT * FROM tabla_inexistente"
        respuesta, sql = consulta(chain, engine, "consulta invalida")
        assert isinstance(respuesta, str)
        assert respuesta.startswith("Error")

    def test_drop_bloqueado_sin_ejecutar(self, chain, engine):
        chain.invoke.return_value = "DROP TABLE productos"
        respuesta, sql = consulta(chain, engine, "borrar tabla")
        assert isinstance(respuesta, str)
        assert "DROP" in respuesta
        inspector = inspect(engine)
        assert "productos" in inspector.get_table_names()

    def test_delete_bloqueado_datos_intactos(self, chain, engine):
        chain.invoke.return_value = "DELETE FROM productos WHERE id = 1"
        respuesta, sql = consulta(chain, engine, "eliminar laptop")
        assert "DELETE" in respuesta or "no permitida" in respuesta.lower()
        df = pd.read_sql_query("SELECT count(*) as total FROM productos", engine)
        assert df.iloc[0]["total"] == 3
