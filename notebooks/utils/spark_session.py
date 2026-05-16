# ==============================================================================
# utils/spark_session.py
# Módulo compartido de inicialización del motor Spark.
# Importar desde cualquier notebook del proyecto:
#   from utils.spark_session import get_spark
# ==============================================================================

import warnings
import sys
import os

warnings.filterwarnings("ignore")


def get_spark(app_name: str = "EnergyAudit", log_level: str = "ERROR"):
    """
    Retorna una SparkSession activa, creándola si no existe todavía.

    La sesión se configura para el entorno de desarrollo local con 32 GB de RAM.
    Llamar a esta función desde notebooks de hipótesis carga los datos ya
    procesados desde Parquet, evitando repetir el ETL completo.

    Parameters
    ----------
    app_name : str
        Nombre de la aplicación Spark (visible en la Spark UI).
    log_level : str
        Nivel de log del SparkContext. "ERROR" mantiene la consola limpia.

    Returns
    -------
    SparkSession
    """
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .appName(app_name)
        .config("spark.driver.memory", "16g")
        .config("spark.executor.memory", "8g")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel(log_level)

    print("-" * 55)
    print(f"⚡ SPARK ENGINE READY  |  app: {app_name}")
    print(f"   Driver : {spark.conf.get('spark.driver.memory')}")
    print(f"   Executor: {spark.conf.get('spark.executor.memory')}")
    print(f"   Log level: {log_level}")
    print("-" * 55)

    return spark


def resolve_project_root() -> str:
    """
    Devuelve la ruta absoluta a la raíz del proyecto independientemente
    de si el notebook se ejecuta desde /notebooks o desde la raíz.

    Returns
    -------
    str : Ruta absoluta al directorio raíz del proyecto.
    """
    cwd = os.getcwd()
    if os.path.basename(cwd) == "notebooks":
        return os.path.dirname(cwd)
    return cwd
