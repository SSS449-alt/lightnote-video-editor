"""
Celery application for async background video processing.

Uses Redis as both broker and result backend.
"""

from celery import Celery
from config import settings


celery_app = Celery(
    "lightnote_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.pipeline"]
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    timezone="UTC",
    enable_utc=True,

    task_track_started=True,

    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    task_time_limit=600,
    task_soft_time_limit=540,

)

if settings.REDIS_URL.startswith("rediss://"):
    celery_app.conf.update(
        broker_use_ssl={"ssl_cert_reqs": "none"},
        redis_backend_use_ssl={"ssl_cert_reqs": "none"},
    )