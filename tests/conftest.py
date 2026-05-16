# tests/conftest.py
# =================
# Configuración global de pytest para el proyecto.
# Define marcadores personalizados y comportamiento compartido.

import pytest


def pytest_configure(config):
    """Registra marcadores personalizados para evitar advertencias de pytest."""
    config.addinivalue_line(
        "markers",
        "spark: tests que requieren una sesión Spark activa (lentos)"
    )
    config.addinivalue_line(
        "markers",
        "hipotesis: tests de validación de hipótesis de negocio"
    )