# Usa una imagen oficial de Python
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para playwright y psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    # Dependencias para Playwright
    libnss3 \
    libnspr4 \
    libdbus-glib-1-2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copia los archivos de requerimientos primero para aprovechar el cache de Docker
COPY requirements.txt requirementsTest.txt ./

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirementsTest.txt

# Descarga e instala los navegadores que Playwright necesita
RUN playwright install --with-deps

# Copia el resto del código de la aplicación
COPY . .

# Expone el puerto por donde corre la app
EXPOSE 5000

# Comando para correr la app
CMD ["python", "-m", "src.main", "--skip-checks"]
