# Python 3.11 base image
FROM python:3.11-slim

# Çalışma dizini
WORKDIR /app

# Python bağımlılıkları
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend kodunu kopyala
COPY backend/ ./

# Frontend'i kopyala
COPY frontend/ ./frontend/

# Port
ENV PORT=8080
EXPOSE 8080

# Gunicorn ile çalıştır
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
