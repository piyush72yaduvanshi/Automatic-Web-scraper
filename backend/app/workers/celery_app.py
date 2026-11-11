"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "crm_lead_discovery",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks",
        "app.workers.scheduled_discovery",
        "app.workers.social_polling_tasks",
        "app.workers.inbound_tasks"
    ]
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
    # Instagram polling - every 5 minutes
    'poll-instagram-engagements': {
        'task': 'app.workers.social_polling_tasks.poll_instagram_engagements',
        'schedule': 300.0,  # 5 minutes
        'options': {'expires': 240}
    },
    # Facebook polling - every 5 minutes
    'poll-facebook-engagements': {
        'task': 'app.workers.social_polling_tasks.poll_facebook_engagements',
        'schedule': 300.0,
        'options': {'expires': 240}
    },
    # Twitter polling - every 5 minutes
    'poll-twitter-mentions': {
        'task': 'app.workers.social_polling_tasks.poll_twitter_mentions',
        'schedule': 300.0,
        'options': {'expires': 240}
    },
    # LinkedIn polling - every 10 minutes (lower rate limits)
    'poll-linkedin-engagements': {
        'task': 'app.workers.social_polling_tasks.poll_linkedin_engagements',
        'schedule': 600.0,  # 10 minutes
        'options': {'expires': 540}
    },
    # Process unprocessed inbound messages - every 2 minutes
    'process-inbound-messages': {
        'task': 'app.workers.inbound_tasks.process_inbound_messages',
        'schedule': 120.0,  # 2 minutes
        'options': {'expires': 100}
    },
    # Process unprocessed social leads - every 3 minutes
    'process-social-leads': {
        'task': 'app.workers.inbound_tasks.process_social_media_leads',
        'schedule': 180.0,
        'options': {'expires': 150}
    },
}
