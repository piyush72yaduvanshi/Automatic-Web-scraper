"""Celery configuration file for the CRM Lead Discovery system.

This module provides centralized Celery configuration including:
- Broker and backend settings
- Task serialization
- Beat schedule for periodic tasks
- Worker configuration
"""

from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Redis configuration from environment
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery app instance
celery_app = Celery('crm_leads')

# Core Celery configuration
celery_app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone and datetime handling
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Task discovery
    imports=[
        'app.workers.tasks',
        'app.workers.scheduled_discovery',
    ],
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Scheduled discovery automation - checks every 5 minutes
    'check-scheduled-discoveries': {
        'task': 'app.workers.scheduled_discovery.check_and_run_scheduled_discoveries',
        'schedule': 300.0,  # Every 5 minutes
        'options': {
            'expires': 240,  # Task expires after 4 minutes
        }
    },
    
    # Social media scheduled posts - checks every minute
    'publish-scheduled-social-posts': {
        'task': 'app.workers.tasks.publish_scheduled_social_posts',
        'schedule': 60.0,  # Every minute
        'options': {
            'expires': 50,
        }
    },
    
    # Sync social platform metrics - every 30 minutes
    'sync-social-metrics': {
        'task': 'app.workers.tasks.sync_social_metrics_task',
        'schedule': 1800.0,  # Every 30 minutes
        'options': {
            'expires': 1700,
        }
    },
}

if __name__ == '__main__':
    celery_app.start()
