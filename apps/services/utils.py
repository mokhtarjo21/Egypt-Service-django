"""
Utility functions for the services app.
Includes SEO helpers like search engine ping notifications.
"""

import urllib.request
import urllib.error
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def notify_search_engines():
    """
    Ping Google and Bing to re-crawl the sitemap.
    Called automatically when a service is approved.
    """
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    sitemap_url = f"{site_url}/sitemap.xml"

    ping_urls = [
        f"https://www.google.com/ping?sitemap={sitemap_url}",
        f"https://www.bing.com/ping?sitemap={sitemap_url}",
    ]

    for url in ping_urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'EgyptServiceMarketplace/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                logger.info(f"[SEO] Pinged {url} — status: {response.status}")
        except urllib.error.URLError as e:
            logger.warning(f"[SEO] Failed to ping {url}: {e.reason}")
        except Exception as e:
            logger.warning(f"[SEO] Unexpected error pinging {url}: {e}")
