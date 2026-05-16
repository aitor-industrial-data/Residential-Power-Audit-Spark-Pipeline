"""
src/dataset_loader.py
=====================
Verificación y descarga automática del dataset desde el repositorio oficial.

Uso desde cualquier notebook:
    from src.dataset_loader import verify_dataset
    verify_dataset(dataset_path)
"""

import os
import zipfile
import urllib.request
import urllib.error


# --- CONFIGURACIÓN ---
# Fuente oficial: UCI Machine Learning Repository (licencia CC BY 4.0)
# DOI: https://doi.org/10.24432/C58K54
_UCI_ZIP_URL = (
    "https://archive.ics.uci.edu/static/public/235/"
    "individual+household+electric+power+consumption.zip"
)

_DATASET_FILENAME = "household_power_consumption.txt"


# -----------------------------------------------------------------------
# Función principal
# -----------------------------------------------------------------------

def verify_dataset(dataset_path: str) -> bool:
    """
    Comprueba si el dataset existe en la ruta indicada.

    Si no existe, intenta descargarlo desde el repositorio oficial de UCI.
    Si la descarga falla, muestra instrucciones detalladas para hacerlo
    manualmente y devuelve False para detener la ejecución del notebook.

    Parameters
    ----------
    dataset_path : str
        Ruta completa al archivo .txt del dataset.

    Returns
    -------
    bool
        True si el archivo está disponible.
        False si no se pudo obtener.
    """

    # -------------------------------------------------------------------
    # CASO 1: El archivo ya existe → todo correcto
    # -------------------------------------------------------------------
    if os.path.isfile(dataset_path):
        size_mb = os.path.getsize(dataset_path) / (1024 ** 2)
        print("-" * 60)
        print("✅ DATASET ENCONTRADO")
        print(f"   Ruta    : {dataset_path}")
        print(f"   Tamaño  : {size_mb:.1f} MB")
        print("-" * 60)
        return True

    # -------------------------------------------------------------------
    # CASO 2: El archivo NO existe → intentar descarga automática
    # -------------------------------------------------------------------
    print("-" * 60)
    print("⚠️  DATASET NO ENCONTRADO")
    print(f"   Ruta esperada: {dataset_path}")
    print("\n🌐 Intentando descarga automática desde UCI ML Repository...")
    print(f"   Fuente: {_UCI_ZIP_URL}")
    print("-" * 60)

    target_dir = os.path.dirname(dataset_path)
    os.makedirs(target_dir, exist_ok=True)

    if _download_and_extract(target_dir, dataset_path):
        return True

    # -------------------------------------------------------------------
    # CASO 3: La descarga falló → instrucciones manuales
    # -------------------------------------------------------------------
    _show_manual_instructions(dataset_path)
    return False


# -----------------------------------------------------------------------
# Funciones auxiliares (privadas)
# -----------------------------------------------------------------------

def _download_and_extract(target_dir: str, final_path: str) -> bool:
    """
    Descarga el ZIP oficial de UCI, extrae el .txt y elimina el ZIP temporal.
    Devuelve True si el archivo queda disponible en final_path.
    """
    temp_zip = os.path.join(target_dir, "_temp_uci_dataset.zip")

    try:
        print("   Descargando... (el archivo pesa ~132 MB, puede tardar unos minutos)")
        urllib.request.urlretrieve(_UCI_ZIP_URL, temp_zip, reporthook=_progress_hook)
        print()  # Salto de línea tras la barra de progreso

        print("   Extrayendo archivo ZIP...")
        with zipfile.ZipFile(temp_zip, "r") as zip_ref:
            # Buscar el .txt del dataset dentro del ZIP
            txt_files = [
                f for f in zip_ref.namelist()
                if f.endswith(".txt") and "household" in f.lower()
            ]
            if not txt_files:
                print("   ❌ El ZIP no contiene el archivo esperado.")
                return False

            zip_ref.extract(txt_files[0], target_dir)

            # Renombrar al nombre estándar si el ZIP lo anida en subcarpeta
            extracted_path = os.path.join(target_dir, txt_files[0])
            if extracted_path != final_path:
                os.rename(extracted_path, final_path)

        os.remove(temp_zip)

        if os.path.isfile(final_path):
            size_mb = os.path.getsize(final_path) / (1024 ** 2)
            print(f"\n✅ DESCARGA COMPLETADA")
            print(f"   Archivo : {final_path}")
            print(f"   Tamaño  : {size_mb:.1f} MB")
            return True

    except urllib.error.URLError as e:
        print(f"\n   ❌ Error de red: {e.reason}")
    except zipfile.BadZipFile:
        print("   ❌ El archivo descargado no es un ZIP válido.")
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)

    return False


def _progress_hook(block_count: int, block_size: int, total_size: int):
    """Muestra una barra de progreso simple durante la descarga."""
    if total_size > 0:
        downloaded = block_count * block_size
        pct = min(downloaded / total_size * 100, 100)
        mb_done = downloaded / (1024 ** 2)
        mb_total = total_size / (1024 ** 2)
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"\r   [{bar}] {pct:.1f}%  ({mb_done:.1f}/{mb_total:.1f} MB)", end="")


def _show_manual_instructions(dataset_path: str):
    """Muestra un mensaje de error con pasos claros para descarga manual."""
    target_dir = os.path.dirname(dataset_path)

    print("\n" + "=" * 60)
    print("❌  DESCARGA AUTOMÁTICA FALLIDA — ACCIÓN MANUAL REQUERIDA")
    print("=" * 60)
    print()
    print("  Este notebook no puede ejecutarse sin el dataset.")
    print()
    print("  PASOS PARA DESCARGA MANUAL:")
    print()
    print("  1. Accede a la página oficial del dataset en UCI:")
    print("     https://archive.ics.uci.edu/dataset/235/")
    print("     individual+household+electric+power+consumption")
    print()
    print("  2. Pulsa el botón 'Download' para obtener el ZIP.")
    print()
    print("  3. Extrae el contenido y coloca el archivo .txt en:")
    print(f"     {dataset_path}")
    print()
    print("  La estructura esperada del proyecto es:")
    print(f"     {target_dir}/")
    print(f"     └── {os.path.basename(dataset_path)}  (~132 MB)")
    print()
    print("  Licencia: CC BY 4.0")
    print("  Fuente  : Hebrail, G. & Berard, A. (2006). UCI ML Repository.")
    print("  DOI     : https://doi.org/10.24432/C58K54")
    print("=" * 60)