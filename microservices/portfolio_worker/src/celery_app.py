from celery import Celery
from .core.config import settings

broker_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
result_backend_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"

celery_app = Celery(
    "portfolio_worker",
    broker=broker_url,
    backend=result_backend_url,
    include=["src.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
)
