
# Usamos una imagen que ya tiene Spark y Python configurados.
# Versión fijada para garantizar reproducibilidad del entorno.
FROM jupyter/pyspark-notebook:spark-3.5.0
 
# Cambiamos al directorio de trabajo
WORKDIR /home/jovyan/work
 
# Copiamos los requerimientos primero para aprovechar el caché de Docker.
# Si requirements.txt no cambia, esta capa no se reconstruye.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# El contenedor expondrá JupyterLab y la Spark UI
EXPOSE 8888 4040