"""Fixtures compartidos para los tests de SQLTalk-AI."""

import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def df_mixto():
    """DataFrame con columnas numéricas y categóricas."""
    return pd.DataFrame({
        "Producto": ["A", "B", "C", "D"],
        "Ventas": [100, 250, 180, 90],
        "Cantidad": [10, 25, 18, 9],
    })


@pytest.fixture
def df_solo_numerico():
    """DataFrame con solo columnas numéricas."""
    return pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [10, 20, 15, 25, 30],
    })


@pytest.fixture
def df_vacio():
    """DataFrame vacío."""
    return pd.DataFrame()


@pytest.fixture
def df_una_fila():
    """DataFrame con una sola fila."""
    return pd.DataFrame({"Producto": ["A"], "Ventas": [100]})
