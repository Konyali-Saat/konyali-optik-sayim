# Konyali Optik Sayim Sistemi - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy backend requirements and install dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 5000

# Environment variables (override via Cloud Run or .env)
ENV PORT=5000
ENV FLASK_DEBUG=False
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/api/health', timeout=5)"

# Run with gunicorn (production WSGI server)
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app
