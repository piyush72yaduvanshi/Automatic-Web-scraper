"""Monitoring and observability configuration."""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings


def initialize_sentry():
    """Initialize Sentry error tracking if DSN is configured."""
    sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=settings.APP_ENV,
            traces_sample_rate=0.1 if settings.APP_ENV == "production" else 1.0,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
        )
        return True
    return False
