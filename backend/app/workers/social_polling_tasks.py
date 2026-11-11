"""Celery tasks for polling social media platforms for leads."""

import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.workers.tasks import DatabaseTask
from app.core.database import SessionLocal
from app.services.social_capture.instagram_service import InstagramLeadExtractor
from app.services.social_capture.facebook_service import FacebookLeadExtractor
from app.services.social_capture.twitter_service import TwitterLeadExtractor
from app.services.social_capture.linkedin_service import LinkedInLeadExtractor
from app.services.social_capture.exceptions import RateLimitError, AuthenticationError
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.social_polling_tasks.poll_instagram_engagements",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def poll_instagram_engagements(self):
    """Poll Instagram for new comments, DMs, and mentions every 5 minutes."""
    db = self.session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting Instagram engagement polling")
        
        # Create extractor
        extractor = InstagramLeadExtractor()
        
        # Fetch engagements from last 10 minutes
        since_timestamp = datetime.utcnow() - timedelta(minutes=10)
        
        # Fetch engagements
        engagements = loop.run_until_complete(
            extractor.fetch_engagements(since_timestamp)
        )
        
        # Store engagements
        result = loop.run_until_complete(
            extractor.store_engagements(engagements, db)
        )
        
        logger.info(
            f"Instagram polling completed: {result['created']} created, "
            f"{result['duplicates']} duplicates, {result['errors']} errors"
        )
        
        return {
            "status": "success",
            "platform": "INSTAGRAM",
            "engagements_found": len(engagements),
            "created": result["created"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except RateLimitError as e:
        logger.warning(f"Instagram rate limit: {e}. Retrying in {e.retry_after} seconds")
        raise self.retry(countdown=e.retry_after or 3600)
    
    except AuthenticationError as e:
        logger.error(f"Instagram auth failed: {e}. Disabling polling.")
        return {"status": "auth_failed", "error": str(e)}
    
    except Exception as e:
        logger.error(f"Error polling Instagram: {e}", exc_info=True)
        raise self.retry(exc=e)
    
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.social_polling_tasks.poll_facebook_engagements",
    max_retries=3,
    default_retry_delay=300,
)
def poll_facebook_engagements(self):
    """Poll Facebook for new page comments and messages every 5 minutes."""
    db = self.session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting Facebook engagement polling")
        
        extractor = FacebookLeadExtractor()
        since_timestamp = datetime.utcnow() - timedelta(minutes=10)
        
        engagements = loop.run_until_complete(
            extractor.fetch_engagements(since_timestamp)
        )
        
        result = loop.run_until_complete(
            extractor.store_engagements(engagements, db)
        )
        
        logger.info(
            f"Facebook polling completed: {result['created']} created, "
            f"{result['duplicates']} duplicates"
        )
        
        return {
            "status": "success",
            "platform": "FACEBOOK",
            "engagements_found": len(engagements),
            "created": result["created"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except RateLimitError as e:
        logger.warning(f"Facebook rate limit: {e}")
        raise self.retry(countdown=e.retry_after or 3600)
    
    except AuthenticationError as e:
        logger.error(f"Facebook auth failed: {e}")
        return {"status": "auth_failed", "error": str(e)}
    
    except Exception as e:
        logger.error(f"Error polling Facebook: {e}", exc_info=True)
        raise self.retry(exc=e)
    
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.social_polling_tasks.poll_twitter_mentions",
    max_retries=3,
    default_retry_delay=300,
)
def poll_twitter_mentions(self):
    """Poll Twitter for new mentions and replies every 5 minutes."""
    db = self.session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting Twitter mention polling")
        
        extractor = TwitterLeadExtractor()
        since_timestamp = datetime.utcnow() - timedelta(minutes=10)
        
        # Get Twitter user ID from settings
        twitter_user_id = getattr(settings, "TWITTER_USER_ID", None)
        
        engagements = loop.run_until_complete(
            extractor.fetch_engagements(since_timestamp, user_id=twitter_user_id)
        )
        
        result = loop.run_until_complete(
            extractor.store_engagements(engagements, db)
        )
        
        logger.info(
            f"Twitter polling completed: {result['created']} created, "
            f"{result['duplicates']} duplicates"
        )
        
        return {
            "status": "success",
            "platform": "TWITTER",
            "engagements_found": len(engagements),
            "created": result["created"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except RateLimitError as e:
        logger.warning(f"Twitter rate limit: {e}")
        raise self.retry(countdown=e.retry_after or 900)
    
    except AuthenticationError as e:
        logger.error(f"Twitter auth failed: {e}")
        return {"status": "auth_failed", "error": str(e)}
    
    except Exception as e:
        logger.error(f"Error polling Twitter: {e}", exc_info=True)
        raise self.retry(exc=e)
    
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.social_polling_tasks.poll_linkedin_engagements",
    max_retries=3,
    default_retry_delay=600,
)
def poll_linkedin_engagements(self):
    """Poll LinkedIn for new post comments every 10 minutes."""
    db = self.session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting LinkedIn engagement polling")
        
        extractor = LinkedInLeadExtractor()
        since_timestamp = datetime.utcnow() - timedelta(minutes=15)
        
        engagements = loop.run_until_complete(
            extractor.fetch_engagements(since_timestamp)
        )
        
        result = loop.run_until_complete(
            extractor.store_engagements(engagements, db)
        )
        
        logger.info(
            f"LinkedIn polling completed: {result['created']} created, "
            f"{result['duplicates']} duplicates"
        )
        
        return {
            "status": "success",
            "platform": "LINKEDIN",
            "engagements_found": len(engagements),
            "created": result["created"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except RateLimitError as e:
        logger.warning(f"LinkedIn rate limit: {e}")
        raise self.retry(countdown=e.retry_after or 86400)
    
    except AuthenticationError as e:
        logger.error(f"LinkedIn auth failed: {e}")
        return {"status": "auth_failed", "error": str(e)}
    
    except Exception as e:
        logger.error(f"Error polling LinkedIn: {e}", exc_info=True)
        raise self.retry(exc=e)
    
    finally:
        loop.close()
