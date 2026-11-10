"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "crm_lead_discovery",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks", "app.workers.scheduled_discovery"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Check for due discovery schedules every 5 minutes
    'check-scheduled-discoveries': {
        'task': 'app.workers.scheduled_discovery.check_and_run_scheduled_discoveries',
        'schedule': 300.0,  # Every 5 minutes (in seconds)
    },
    # Publish scheduled social posts every minute
    'publish-scheduled-social-posts': {
        'task': 'app.workers.tasks.publish_scheduled_social_posts',
        'schedule': 60.0,  # Every minute
    },
    # Sync social metrics every 30 minutes
    'sync-social-metrics': {
        'task': 'app.workers.tasks.sync_social_metrics_task',
        'schedule': 1800.0,  # Every 30 minutes
    },
}
