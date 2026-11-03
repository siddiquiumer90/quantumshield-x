# QUANTUMSHIELD X backend image.
# git + cmake + a C compiler are required because liboqs-python builds the
# liboqs C library on first import.
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    git cmake gcc g++ make libssl-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
# Render (and other hosts) assign the port through $PORT; default to 8000
# for local docker-compose runs.
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
