"""
Celery application configuration.
"""

from celery import Celery

from config.settings import settings

app = Celery(
    "asusu",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task discovery
    include=["workers.pipeline"],

    # Time limits (seconds)
    task_soft_time_limit=1800,   # 30 minutes soft
    task_time_limit=3600,        # 60 minutes hard

    # Result expiry
    result_expires=86400,  # 24 hours

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,

    # Track task progress
    task_track_started=True,
)
