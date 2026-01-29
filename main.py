#!/usr/bin/env python3
"""
Main orchestrator script for iOS Anti-Revoke profile generation.
Coordinates scraping, processing, merging, and generating configurations.
"""

import logging
import sys
import tempfile
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Import utilities
from utils.scraper import ProfileScraper
from utils.crypto_handler import CryptoHandler
from utils.rule_converter import RuleFileGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AntiRevokeOrchestrator:
    """
    Main orchestrator for iOS Anti-Revoke profile generation pipeline.
    """

    def __init__(
        self,
        cert_path: str = None,
        key_path: str = None,
        output_dir: str = 'output'
    ):
        """
        Initialize orchestrator.

        Args:
            cert_path: Path to fullchain.pem certificate
            key_path: Path to privkey.pem private key
            output_dir: Output directory for generated files
        """
        self.cert_path = cert_path
        self.key_path = key_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scraper = ProfileScraper()
        self.crypto = CryptoHandler(cert_path, key_path)
        self.rule_generator = RuleFileGenerator(output_dir)
        
        self.all_domains = set()
        self.processing_results = {}

    def scrape_sources(self, sources: List[Dict[str, str]]) -> Dict[str, bytes]:
        """
        Step 1: Scrape profiles from multiple sources.

        Args:
            sources: List of source configurations

        Returns:
            Dictionary of scraped profiles
        """
        logger.info("=" * 60)
        logger.info("STEP 1: Scraping profiles from sources")
        logger.info("=" * 60)

        profiles = self.scraper.scrape_sources(sources)
        
        logger.info(f"Successfully scraped {len(profiles)} profiles")
        return profiles

    def process_profiles(self, profiles: Dict[str, bytes]) -> None:
        """
        Step 2: Decrypt and extract domains from profiles.

        Args:
            profiles: Dictionary of scraped profiles
        """
        logger.info("=" * 60)
        logger.info("STEP 2: Processing profiles (decrypt & extract)")
        logger.info("=" * 60)

        temp_dir = tempfile.mkdtemp()
        
        for name, content in profiles.items():
            try:
                logger.info(f"Processing profile: {name}")
                
                # Save profile temporarily
                temp_profile = Path(temp_dir) / f"{name}.mobileconfig"
                with open(temp_profile, 'wb') as f:
                    f.write(content)

                # Decrypt profile
                decrypted_plist = self.crypto.decrypt_profile(str(temp_profile))
                if not decrypted_plist:
                    logger.warning(f"Failed to decrypt profile: {name}")
                    continue

                # Parse plist and extract domains
                plist_data = self.crypto.parse_plist(decrypted_plist)
                if not plist_data:
                    logger.warning(f"Failed to parse profile: {name}")
                    continue

                domains = self.crypto.extract_domains(plist_data)
                logger.info(f"Extracted {len(domains)} domains from {name}")
                
                self.all_domains.update(domains)
                self.processing_results[name] = {
                    'domains_count': len(domains),
                    'domains_sample': list(domains)[:5]  # Store first 5 for reference
                }

            except Exception as e:
                logger.error(f"Error processing profile {name}: {e}")
                continue

    def merge_domains(self) -> List[str]:
        """
        Step 3: Merge and deduplicate domains from all sources.

        Returns:
            Merged domain list
        """
        logger.info("=" * 60)
        logger.info("STEP 3: Merging and deduplicating domains")
        logger.info("=" * 60)

        merged_domains = sorted(list(self.all_domains))
        logger.info(f"Total unique domains: {len(merged_domains)}")
        
        return merged_domains

    def generate_profile(self, domains: List[str], updated_utc: str, domain_count: int) -> Optional[str]:
        """
        Step 4A: Generate signed .mobileconfig profile.

        Args:
            domains: Merged domain list

        Returns:
            Path to generated profile or None
        """
        logger.info("=" * 60)
        logger.info("STEP 4A: Generating signed .mobileconfig profile")
        logger.info("=" * 60)

        # Create unsigned plist
        plist_file = self.crypto.create_profile(
            domains,
            updated_utc=updated_utc,
            domain_count=domain_count,
            backend_host='reject.rzmy.dpdns.org'
        )
        if not plist_file:
            logger.error("Failed to create profile plist")
            return None

        # Sign the profile
        if self.cert_path and self.key_path:
            signed_profile = self.crypto.sign_profile(
                plist_file,
                str(self.output_dir / 'RevokeGuard_Auto-Sync.mobileconfig')
            )
            if signed_profile:
                logger.info(f"Profile generated: {signed_profile}")
                return signed_profile
            else:
                logger.warning("Failed to sign profile, saving unsigned version")
        else:
            logger.warning("Certificate or key not configured, saving unsigned plist")

        # Fallback: save unsigned plist
        unsigned_path = self.output_dir / 'RevokeGuard_Auto-Sync.plist'
        import shutil
        shutil.copy(plist_file, unsigned_path)
        logger.info(f"Saved unsigned plist: {unsigned_path}")
        return str(unsigned_path)

    def generate_rules(self, domains: List[str], author: str, updated_utc: str, domain_count: int) -> Dict[str, str]:
        """
        Step 4B: Generate filter rules for proxy tools.

        Args:
            domains: Merged domain list

        Returns:
            Dictionary mapping tool names to file paths
        """
        logger.info("=" * 60)
        logger.info("STEP 4B: Generating filter rules")
        logger.info("=" * 60)

        generated_files = self.rule_generator.generate_all_rules(domains, author, updated_utc, domain_count)
        
        for tool_name, file_path in generated_files.items():
            logger.info(f"Generated {tool_name} rules: {file_path}")

        return generated_files

    def generate_metadata(self, domains: List[str], generated_files: Dict[str, str]) -> str:
        """
        Generate metadata JSON file with build information.

        Args:
            domains: Domain list
            generated_files: Generated output files

        Returns:
            Path to metadata file
        """
        metadata = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_domains': len(set(domains)),
            'sources_processed': len(self.processing_results),
            'generated_files': generated_files,
            'source_details': self.processing_results
        }

        metadata_file = self.output_dir / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated metadata: {metadata_file}")
        return str(metadata_file)

    def run(self, sources: List[Dict[str, str]]) -> bool:
        """
        Execute the complete pipeline.

        Args:
            sources: List of source configurations with 'url', 'xpath', and 'name'

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting iOS Anti-Revoke Profile Generation Pipeline")
            logger.info(f"Output directory: {self.output_dir.absolute()}")

            # Step 1: Scrape
            profiles = self.scrape_sources(sources)
            if not profiles:
                logger.error("No profiles were scraped successfully")
                return False

            # Step 2: Process
            self.process_profiles(profiles)
            if not self.all_domains:
                logger.error("No domains extracted from profiles")
                return False

            # Step 3: Merge
            merged_domains = self.merge_domains()
            domain_count = len(merged_domains)
            updated_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            author = 'RzMY'

            # Step 4A: Generate Profile
            profile_path = self.generate_profile(merged_domains, updated_utc, domain_count)

            # Step 4B: Generate Rules
            generated_files = self.generate_rules(merged_domains, author, updated_utc, domain_count)

            # Generate metadata
            metadata_file = self.generate_metadata(merged_domains, generated_files)

            logger.info("=" * 60)
            logger.info("Pipeline completed successfully!")
            logger.info("=" * 60)
            logger.info(f"Profile: {profile_path}")
            logger.info(f"Output files: {len(generated_files)}")
            logger.info(f"Total domains: {len(merged_domains)}")

            return True

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return False


def main():
    """
    Main entry point.
    """
    # Define sources
    sources = [
        {
            'url': 'https://khoindvn.io.vn/',
            'xpath': '/html/body/main/section[2]/div[2]/div[1]/a',
            'name': 'khoindvn'
        },
        {
            'url': 'https://applejr.net/',
            'xpath': '/html/body/div[3]/div/form/div[3]/label/a',
            'name': 'applejr'
        }
    ]

    # Certificate paths (can be set from environment variables)
    import os
    cert_path = os.getenv('SSL_CERT_PATH', 'fullchain.pem')
    key_path = os.getenv('SSL_KEY_PATH', 'privkey.pem')

    # Create and run orchestrator
    orchestrator = AntiRevokeOrchestrator(cert_path, key_path)
    success = orchestrator.run(sources)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
