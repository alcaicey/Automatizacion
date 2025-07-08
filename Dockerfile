# Usa una imagen oficial de Python
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia solo los archivos necesarios para las dependencias
COPY requirementsTest.txt .

# Instala las dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev && \
    pip install --upgrade pip && \
    pip install -r requirementsTest.txt
    RUN playwright install
# Expone el puerto por donde corre Flask (o SocketIO)
EXPOSE 5000

# Comando para correr la app
CMD ["python", "-m", "src.main", "--skip-checks"]
