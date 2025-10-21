FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 9808
CMD ["python", "-m", "prometheus_exporter_celery", "--broker", "redis://redis:6379/0", "--port", "9808"]