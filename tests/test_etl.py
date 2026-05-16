"""
tests/test_etl.py
=================
Tests de validación del pipeline ETL.

Verifican tres contratos de calidad que deben cumplirse siempre,
independientemente del entorno de ejecución:

    1. Volumen mínimo de registros tras la limpieza de nulos.
    2. Ausencia de valores nulos en columnas críticas de medida.
    3. Ratio de standby nocturno superior al umbral de la H3 (15%).

Ejecutar con:
    pytest tests/ -v
"""

import pytest
import sys
import os

# Raíz del proyecto (un nivel por encima de tests/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# utils/ está dentro de notebooks/ — lo añadimos explícitamente
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "notebooks"))


# ---------------------------------------------------------------------------
# Fixture compartida: sesión Spark + datos limpios
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def spark_y_datos():
    """
    Inicia una sesión Spark ligera para tests y carga el dataset procesado
    desde Parquet (generado por 00_ETL_Pipeline.ipynb).

    Si el Parquet no existe, salta todos los tests con un mensaje claro.
    """
    from utils.spark_session import get_spark, resolve_project_root

    spark = get_spark(app_name="Tests_ETL", log_level="ERROR")
    raiz = resolve_project_root()
    ruta_parquet = os.path.join(raiz, "data_storage", "work", "power_data.parquet")

    if not os.path.exists(ruta_parquet):
        pytest.skip(
            f"Parquet no encontrado en '{ruta_parquet}'. "
            "Ejecuta primero el notebook 00_ETL_Pipeline.ipynb."
        )

    df = spark.read.parquet(ruta_parquet)
    df.createOrReplaceTempView("power_data")

    yield spark, df

    spark.stop()


# ---------------------------------------------------------------------------
# TEST 1: Volumen mínimo de registros
# ---------------------------------------------------------------------------

class TestVolumenDatos:
    """El dataset limpio debe contener al menos 2 millones de registros."""

    MINIMO_ESPERADO = 2_000_000

    def test_volumen_minimo(self, spark_y_datos):
        """
        Valida que el ETL no haya descartado demasiados registros.
        El dataset original tiene 2.075.259 entradas — tras limpiar nulos
        (~1.25%) deben quedar al menos 2.000.000 registros válidos.
        """
        _, df = spark_y_datos
        total = df.count()

        assert total >= self.MINIMO_ESPERADO, (
            f"Se esperaban al menos {self.MINIMO_ESPERADO:,} registros, "
            f"pero el dataset contiene solo {total:,}. "
            "Revisa el paso de limpieza de nulos en el ETL."
        )

    def test_columnas_presentes(self, spark_y_datos):
        """
        Verifica que el feature engineering generó todas las columnas
        necesarias para los análisis de hipótesis.
        """
        _, df = spark_y_datos
        columnas_requeridas = [
            "Full_Timestamp", "Hour", "Is_Weekend",
            "Global_active_power", "Sub_metering_1",
            "Sub_metering_2", "Sub_metering_3"
        ]
        columnas_presentes = df.columns

        for col in columnas_requeridas:
            assert col in columnas_presentes, (
                f"Columna obligatoria '{col}' no encontrada en el dataset. "
                "Revisa el paso de feature engineering del ETL."
            )


# ---------------------------------------------------------------------------
# TEST 2: Integridad de datos — sin nulos en columnas críticas
# ---------------------------------------------------------------------------

class TestIntegridadDatos:
    """Las columnas de medida eléctrica no pueden contener valores nulos."""

    COLUMNAS_CRITICAS = [
        "Full_Timestamp",
        "Global_active_power",
        "Sub_metering_1",
        "Sub_metering_2",
        "Sub_metering_3",
    ]

    def test_sin_nulos_en_columnas_criticas(self, spark_y_datos):
        """
        Confirma que el paso de limpieza (na.drop) eliminó correctamente
        todos los registros con lecturas fallidas del sensor.
        Un nulo en estas columnas invalida cualquier cálculo de potencia.
        """
        spark, df = spark_y_datos

        from pyspark.sql.functions import col, sum as spark_sum, isnull

        # Contamos nulos por columna de forma eficiente en una sola pasada
        expresiones_nulos = [
            spark_sum(isnull(col(c)).cast("int")).alias(c)
            for c in self.COLUMNAS_CRITICAS
        ]

        resultado = df.select(expresiones_nulos).collect()[0].asDict()

        columnas_con_nulos = {k: v for k, v in resultado.items() if v > 0}

        assert not columnas_con_nulos, (
            f"Se encontraron valores nulos en columnas críticas: {columnas_con_nulos}. "
            "El ETL debe eliminar todos los registros incompletos antes de la persistencia."
        )

    def test_voltage_en_rango_fisico(self, spark_y_datos):
        """
        Valida que los valores de tensión están dentro de rangos físicamente
        posibles para una red eléctrica monofásica europea (150V–280V).
        Valores fuera de este rango indicarían errores de sensor o corrupción.
        """
        spark, _ = spark_y_datos

        from pyspark.sql.functions import col

        fuera_de_rango = spark.sql("""
            SELECT COUNT(*) AS registros_anomalos
            FROM power_data
            WHERE CAST(Voltage AS DOUBLE) < 150
               OR CAST(Voltage AS DOUBLE) > 280
        """).collect()[0]["registros_anomalos"]

        assert fuera_de_rango == 0, (
            f"Se detectaron {fuera_de_rango:,} registros con tensión fuera del rango "
            "físico (150V–280V). Revisar el paso de validación de rangos en el ETL."
        )


# ---------------------------------------------------------------------------
# TEST 3: Validación de hipótesis H3 — ratio de standby
# ---------------------------------------------------------------------------

class TestHipotesisH3:
    """
    El consumo en standby nocturno debe superar el umbral del 15% definido
    en la hipótesis H3. Este test confirma que el hallazgo es reproducible.
    """

    UMBRAL_STANDBY_PCT = 15.0

    def test_ratio_standby_supera_umbral(self, spark_y_datos):
        """
        Calcula el ratio standby/activo y verifica que supera el 15%.
        Si este test falla, la hipótesis H3 no se sostendrá y las
        conclusiones del informe pericial deben revisarse.
        """
        spark, _ = spark_y_datos

        resultado = spark.sql("""
            SELECT
                ROUND(
                    AVG(CASE WHEN hour BETWEEN 1 AND 5 THEN Global_active_power END) /
                    AVG(CASE WHEN hour BETWEEN 6 AND 23 OR hour = 0 THEN Global_active_power END)
                    * 100, 2
                ) AS ratio_standby_pct
            FROM power_data
        """).collect()[0]["ratio_standby_pct"]

        assert resultado is not None, (
            "No se pudo calcular el ratio de standby. "
            "Verifica que el dataset contiene registros en todas las franjas horarias."
        )

        assert float(resultado) > self.UMBRAL_STANDBY_PCT, (
            f"El ratio de standby nocturno ({resultado}%) no supera el umbral del "
            f"{self.UMBRAL_STANDBY_PCT}%. La hipótesis H3 no se valida con estos datos."
        )

    def test_consumo_madrugada_no_es_cero(self, spark_y_datos):
        """
        Verifica que existe consumo medible durante la madrugada (01:00-05:59).
        Un consumo de 0 indicaría ausencia de datos o un error de filtrado.
        """
        spark, _ = spark_y_datos

        consumo_medio = spark.sql("""
            SELECT ROUND(AVG(Global_active_power), 4) AS avg_noche
            FROM power_data
            WHERE hour BETWEEN 1 AND 5
        """).collect()[0]["avg_noche"]

        assert consumo_medio is not None and float(consumo_medio) > 0.01, (
            f"El consumo medio nocturno ({consumo_medio} kW) es demasiado bajo o nulo. "
            "Revisa el filtrado temporal en el ETL."
        )