#!/bin/bash
trap "kill 0" SIGINT SIGTERM

echo "Starting Kafka Consumer in the background..."
python -m src.main &

echo "Starting Celery Worker in the foreground..."
celery -A src.celery_app worker --loglevel=INFO -P eventlet