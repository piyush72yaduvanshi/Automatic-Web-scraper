"""Local Google Maps Scraper Provider.

Integrates the autonomous local Google Maps Scraper Kit (engine/serve.py) via REST API.
Operates on localhost (default http://localhost:8080) with headless Chrome over CDP.
Provides unlimited, zero-cost business discovery with direct website, email, and social profile extraction.
"""

import logging
import asyncio
import re
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.providers.discovery.base import BaseDiscoveryProvider

logger = logging.getLogger(__name__)


class LocalMapsScraperProvider(BaseDiscoveryProvider):
    """
    Discovery provider for the local Google Maps Scraper Engine.
    Communicates with http://localhost:8080 (or configured LOCAL_MAPS_SCRAPER_URL).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.LOCAL_MAPS_SCRAPER_URL or "http://localhost:8080").rstrip("/")
        self.timeout = timeout or settings.LOCAL_MAPS_SCRAPER_TIMEOUT
        self.api_key = api_key if api_key is not None else settings.LOCAL_MAPS_SCRAPER_API_KEY

    def get_name(self) -> str:
        return "local_maps_scraper"

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def is_configured(self) -> bool:
        """
        Check if the local engine is reachable and identifies as gmskit-engine.
        """
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/v1/jobs", headers=self._get_headers())
                engine_header = res.headers.get("X-Engine", "")
                return bool(engine_header.startswith("gmskit-engine/") or res.status_code in (200, 401))
        except Exception:
            return False

    async def is_available(self) -> bool:
        """Async health check for orchestrator pre-flight."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/v1/jobs", headers=self._get_headers())
                engine_header = res.headers.get("X-Engine", "")
                return bool(engine_header.startswith("gmskit-engine/") or res.status_code in (200, 401))
        except Exception:
            return False

    async def _geocode_location(self, client: httpx.AsyncClient, location: str) -> tuple[Optional[str], Optional[str]]:
        """Look up coordinates for city/location using local engine's cities preset."""
        if not location:
            return None, None
        try:
            first_term = location.split(",")[0].strip()
            res = await client.get(f"{self.base_url}/api/v1/cities", params={"q": first_term}, headers=self._get_headers())
            if res.status_code == 200:
                cities = res.json()
                if cities and isinstance(cities, list) and len(cities) > 0:
                    best = cities[0]
                    return str(best.get("lat")), str(best.get("lon"))
        except Exception as e:
            logger.debug(f"[LocalMapsScraper] Geocoding lookup error: {e}")
        return None, None

    async def discover_businesses(
        self,
        query: str,
        location: str,
        radius_km: Optional[float] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Execute Google Maps business discovery via the local engine.
        Creates a job, polls until completion, and downloads structured JSON records.
        """
        search_query = f"{query} in {location}" if location else query

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1. Geocode location for viewport centering
            lat, lon = await self._geocode_location(client, location)

            # 2. Compute depth (1 depth batch ~ 20 places on Google Maps)
            depth = max(1, min((limit + 19) // 20, 5))

            job_payload = {
                "name": f"CRM Discovery: {search_query}"[:60],
                "keywords": [search_query],
                "lang": "en",
                "max_time": min(self.timeout, 300),
                "depth": depth,
                "email": True,
                "socials": True,
            }
            if lat and lon:
                job_payload["lat"] = lat
                job_payload["lon"] = lon

            logger.info(f"Submitting job to Local Maps Scraper: {job_payload['name']} (depth={depth})")
            create_res = await client.post(f"{self.base_url}/api/v1/jobs", json=job_payload, headers=self._get_headers())
            if create_res.status_code not in (200, 201):
                raise RuntimeError(f"Local Maps Scraper refused job: HTTP {create_res.status_code} - {create_res.text}")

            job_info = create_res.json()
            job_id = job_info.get("id")
            if not job_id:
                raise RuntimeError(f"Local Maps Scraper did not return job ID: {job_info}")

            # 3. Poll for job completion or partial results
            poll_interval = 2.0
            max_polls = int(self.timeout / poll_interval)
            raw_places: List[Dict[str, Any]] = []

            for poll_idx in range(max_polls):
                await asyncio.sleep(poll_interval)
                try:
                    status_res = await client.get(f"{self.base_url}/api/v1/jobs/{job_id}", headers=self._get_headers())
                    if status_res.status_code == 200:
                        job_status = status_res.json()
                        state = str(job_status.get("Status", "")).lower()
                        progress = job_status.get("Progress") or {}
                        places_count = progress.get("places", 0)

                        logger.debug(f"[LocalMapsScraper] Job {job_id}: status={state}, places={places_count}")

                        if state in ("ok", "done", "completed"):
                            break
                        if state in ("failed", "error"):
                            err_msg = job_status.get("Error") or "Scrape job failed"
                            logger.warning(f"[LocalMapsScraper] Job {job_id} failed: {err_msg}")
                            break
                        # If we already have enough places while still working, can proceed
                        if places_count >= limit and poll_idx >= 5:
                            break
                except Exception as e:
                    logger.debug(f"[LocalMapsScraper] Poll error: {e}")

            # 4. Download structured results (format=json)
            try:
                dl_res = await client.get(f"{self.base_url}/api/v1/jobs/{job_id}/download", params={"format": "json"}, headers=self._get_headers())
                if dl_res.status_code == 200:
                    data = dl_res.json()
                    if isinstance(data, list):
                        raw_places = data
            except Exception as e:
                logger.error(f"[LocalMapsScraper] Failed to download results for {job_id}: {e}")

            # 5. Normalize items into standard schema
            businesses = [self.normalize_business(p, location) for p in raw_places[:limit]]

            return {
                "businesses": businesses,
                "provider_job_id": f"local_maps:{job_id}",
                "total_found": len(businesses),
            }

    def normalize_business(self, raw_data: Dict[str, Any], default_location: str = "") -> Dict[str, Any]:
        """
        Normalize engine output row into common business lead schema.
        Maps reviews, phone, direct emails, website, and social media handles.
        """
        title = raw_data.get("title") or raw_data.get("name") or "Unknown Business"
        raw_address = raw_data.get("complete_address") or raw_data.get("address") or default_location
        city, state, country = self._parse_location(raw_address, default_location)

        # Rating and description
        rating = raw_data.get("review_rating")
        reviews = raw_data.get("review_count")
        desc_parts = []
        if rating:
            desc_parts.append(f"Rating: {rating}★ ({reviews or 0} reviews)")
        if raw_data.get("category"):
            desc_parts.append(f"Category: {raw_data.get('category')}")
        if raw_data.get("descriptions"):
            desc_parts.append(str(raw_data.get("descriptions")))
        description = " • ".join(desc_parts) if desc_parts else None

        # Clean website
        website = raw_data.get("website")
        if website and "google.com/url?" in website:
            match = re.search(r'url=([^&]+)', website)
            if match:
                from urllib.parse import unquote
                website = unquote(match.group(1))

        # Direct phone
        phone = raw_data.get("phone")

        # Parse emails collected during the website pass
        raw_emails = raw_data.get("emails") or []
        email_list: List[Dict[str, Any]] = []
        if isinstance(raw_emails, str):
            # Comma-separated or whitespace
            raw_emails = [e.strip() for e in re.split(r'[,;\s]+', raw_emails) if e.strip() and "@" in e]
        if isinstance(raw_emails, list):
            for em in raw_emails:
                if isinstance(em, str) and "@" in em:
                    clean_em = em.strip().lower()
                    if clean_em not in [x["email"] for x in email_list]:
                        email_list.append({
                            "email": clean_em,
                            "verification_status": "unverified",
                            "source_url": website or "https://maps.google.com",
                        })

        # Parse social media profiles collected during website pass
        social_profiles: List[Dict[str, Any]] = []
        social_keys = [
            ("instagram", "INSTAGRAM"),
            ("facebook", "FACEBOOK"),
            ("linkedin", "LINKEDIN"),
            ("x", "X"),
            ("twitter", "X"),
        ]
        for key, platform in social_keys:
            url = raw_data.get(key)
            if url and isinstance(url, str) and url.startswith("http"):
                social_profiles.append({
                    "platform": platform,
                    "profile_url": url.strip(),
                    "verification_status": "verified",
                    "source_url": website or "https://maps.google.com",
                })

        return {
            "business_name": title,
            "category": raw_data.get("category") or "Local Business",
            "description": description,
            "address": raw_address or None,
            "city": city,
            "state": state,
            "country": country,
            "website": website,
            "phone": phone,
            "emails": email_list,
            "social_profiles": social_profiles,
            "source_provider": "local_maps_scraper",
            "provider_external_id": raw_data.get("place_id") or raw_data.get("cid") or raw_data.get("data_id") or f"local_{title}_{city}",
        }

    def _parse_location(self, address: str, default_location: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse city, state, country from address string."""
        city = None
        state = None
        country = None

        if address:
            parts = [p.strip() for p in address.split(",") if p.strip()]
            if len(parts) >= 3:
                country = parts[-1]
                state_zip = parts[-2]
                state = re.sub(r'\d+', '', state_zip).strip() or state_zip
                city = parts[-3]
            elif len(parts) == 2:
                city = parts[0]
                country = parts[1]
            elif len(parts) == 1:
                city = parts[0]

        if not city and default_location:
            loc_parts = [p.strip() for p in default_location.split(",") if p.strip()]
            city = loc_parts[0]
            if len(loc_parts) > 1:
                country = loc_parts[-1]

        return city, state, country
