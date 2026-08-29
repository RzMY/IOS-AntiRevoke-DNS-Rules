"""HTTP scrapers for Apple host data and upstream DNS profiles."""

from __future__ import annotations

import logging
import re
import time
from typing import Dict, Iterable, List, Optional
from urllib.parse import urljoin

import requests
from lxml import html

logger = logging.getLogger(__name__)


class ScrapeError(RuntimeError):
    """Raised when a required upstream resource cannot be retrieved or parsed."""


class ProfileScraper:
    """Download required mobileconfig profiles and Apple's official host list."""

    DOMAIN_PATTERN = re.compile(
        r"(?:\*\.)?(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
        re.IGNORECASE,
    )

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; "
                    "IOS-AntiRevoke-DNS-Rules/2.0)"
                )
            }
        )
        self.download_urls: Dict[str, str] = {}

    def _request(self, url: str) -> requests.Response:
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "Fetching %s (attempt %s/%s)",
                    url,
                    attempt,
                    self.max_retries,
                )
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("Request failed for %s: %s", url, exc)
                if attempt < self.max_retries:
                    time.sleep(0.5 * (2 ** (attempt - 1)))

        raise ScrapeError(
            f"Failed to fetch {url} after {self.max_retries} attempts: "
            f"{last_error}"
        )

    def _fetch_page(self, url: str) -> bytes:
        return self._request(url).content

    @staticmethod
    def _extract_download_link(
        html_content: bytes,
        xpath: str,
        base_url: str,
    ) -> str:
        try:
            tree = html.fromstring(html_content)
            elements = tree.xpath(xpath)
        except (ValueError, TypeError) as exc:
            raise ScrapeError(f"Invalid HTML or XPath for {base_url}: {exc}") from exc

        if not elements:
            raise ScrapeError(f"XPath did not match any element at {base_url}: {xpath}")

        href = elements[0].get("href")
        if not href:
            raise ScrapeError(f"XPath target has no href at {base_url}: {xpath}")

        return urljoin(base_url, href)

    def download_profile(self, url: str) -> bytes:
        response = self._request(url)
        content = response.content
        content_type = response.headers.get("content-type", "").lower()
        prefix = content.lstrip()[:64].lower()

        if not content:
            raise ScrapeError(f"Downloaded profile is empty: {url}")
        if "text/html" in content_type or prefix.startswith(b"<!doctype html"):
            raise ScrapeError(f"Profile URL returned HTML instead of mobileconfig: {url}")

        return content

    def scrape_sources(self, sources: Iterable[Dict[str, str]]) -> Dict[str, bytes]:
        profiles: Dict[str, bytes] = {}
        self.download_urls = {}

        for source in sources:
            name = source.get("name")
            url = source.get("url")
            xpath = source.get("xpath")
            if not name or not url or not xpath:
                raise ScrapeError("Every profile source requires name, url, and xpath")

            page = self._fetch_page(url)
            download_url = self._extract_download_link(page, xpath, url)
            profiles[name] = self.download_profile(download_url)
            self.download_urls[name] = download_url
            logger.info("Downloaded required profile from %s", name)

        return profiles

    @classmethod
    def extract_apple_domains(cls, html_content: bytes) -> List[str]:
        """Extract and normalize host names from Apple's support tables."""
        try:
            tree = html.fromstring(html_content)
        except (ValueError, TypeError) as exc:
            raise ScrapeError(f"Could not parse Apple support page: {exc}") from exc

        domains = set()
        host_tables = 0

        for table in tree.xpath("//table"):
            first_row = table.xpath(".//tr[1]/*")
            if not first_row:
                continue

            first_header = " ".join(first_row[0].itertext()).strip().lower()
            if first_header not in {"主机", "host"}:
                continue

            host_tables += 1
            for cell in table.xpath(".//tr[position() > 1]/td[1]"):
                cell_text = " ".join(cell.itertext())
                for match in cls.DOMAIN_PATTERN.findall(cell_text):
                    domain = match.lower().rstrip(".")
                    if domain.startswith("*."):
                        domain = domain[2:]
                    domains.add(domain)

        if not host_tables:
            raise ScrapeError("Apple support page contains no recognized host tables")
        if not domains:
            raise ScrapeError("Apple support page yielded no domains")

        return sorted(domains)

    def fetch_apple_domains(self, url: str) -> List[str]:
        domains = self.extract_apple_domains(self._fetch_page(url))
        logger.info("Extracted %s Apple candidate domains", len(domains))
        return domains
