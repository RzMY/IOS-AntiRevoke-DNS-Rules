"""
Scraper module for iOS Anti-Revoke profiles.
Fetches .mobileconfig files from multiple sources using specified XPaths.
"""

import requests
import tempfile
import logging
from pathlib import Path
from lxml import html
from typing import List, Dict, Optional
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProfileScraper:
    """
    Scrapes iOS .mobileconfig profiles from multiple sources.
    """

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize the scraper.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a URL with retry logic.

        Args:
            url: Target URL

        Returns:
            HTML content or None if fetch fails
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
        return None

    def _extract_download_link(self, html_content: str, xpath: str, base_url: str) -> Optional[str]:
        """
        Extract download link from HTML using XPath.

        Args:
            html_content: HTML content as string
            xpath: XPath expression to find the link
            base_url: Base URL for resolving relative links

        Returns:
            Absolute URL of the download link or None
        """
        try:
            tree = html.fromstring(html_content)
            elements = tree.xpath(xpath)
            if elements:
                link = elements[0].get('href')
                if link:
                    # Convert relative URLs to absolute
                    return urljoin(base_url, link)
            logger.warning(f"No element found for XPath: {xpath}")
        except Exception as e:
            logger.error(f"XPath parsing error: {e}")
        return None

    def download_profile(self, url: str) -> Optional[bytes]:
        """
        Download a .mobileconfig file.

        Args:
            url: Download URL

        Returns:
            File content as bytes or None if download fails
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Downloading {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to download {url} after {self.max_retries} attempts")
                    return None
        return None

    def scrape_sources(self, sources: List[Dict[str, str]]) -> Dict[str, bytes]:
        """
        Scrape profiles from multiple sources.

        Args:
            sources: List of dicts with 'url' and 'xpath' keys

        Returns:
            Dictionary mapping source names to profile content
        """
        profiles = {}

        for source in sources:
            url = source.get('url')
            xpath = source.get('xpath')
            name = source.get('name', url)

            if not url or not xpath:
                logger.warning(f"Skipping source: missing url or xpath")
                continue

            # Fetch the page
            html_content = self._fetch_page(url)
            if not html_content:
                continue

            # Extract download link
            download_url = self._extract_download_link(html_content, xpath, url)
            if not download_url:
                logger.warning(f"Could not extract download link from {url}")
                continue

            # Download the profile
            profile_content = self.download_profile(download_url)
            if profile_content:
                profiles[name] = profile_content
                logger.info(f"Successfully scraped profile from {name}")
            else:
                logger.warning(f"Failed to download profile from {name}")

        return profiles

    def save_profiles(self, profiles: Dict[str, bytes], output_dir: str) -> List[str]:
        """
        Save downloaded profiles to disk.

        Args:
            profiles: Dictionary mapping names to content
            output_dir: Output directory path

        Returns:
            List of saved file paths
        """
        saved_files = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for name, content in profiles.items():
            try:
                # Create safe filename
                safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).lower()
                file_path = output_path / f"{safe_name}.mobileconfig"
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                saved_files.append(str(file_path))
                logger.info(f"Saved profile to {file_path}")
            except Exception as e:
                logger.error(f"Failed to save profile {name}: {e}")

        return saved_files
