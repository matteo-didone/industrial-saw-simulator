# edge-device/Dockerfile
FROM python:3.11-slim

# Installa le dipendenze di sistema necessarie
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia requirements.txt per sfruttare la cache di Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice sorgente
COPY src/ ./src/

# Configura il PYTHONPATH
ENV PYTHONPATH=/app

# Espone la porta per l'API REST
EXPOSE 5000

# Comando di avvio modificato per usare il modulo correttamente
CMD ["python", "-m", "src.main"]