FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY start.sh .
RUN chmod +x ./start.sh

# --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
COPY ./src . 

CMD ["./start.sh"]