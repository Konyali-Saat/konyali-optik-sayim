# Python 3.11 base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy backend requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend code into the container
# Assumes the build context is the project root directory
COPY backend/ .
COPY frontend/ ./frontend

# Set the port environment variable
ENV PORT=8080
EXPOSE 8080

# Run the application using Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app