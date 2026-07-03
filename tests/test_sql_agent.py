"""Tests para sql_agent.py — limpieza de SQL generado."""

from sqltalk.sql_agent import clean_sql_query


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
