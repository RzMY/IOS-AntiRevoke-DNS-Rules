"""
Rule converter module for proxy tools.
Converts domain lists into filter rules for Quantumult X, Surge, Loon, and Shadowrocket.
"""

import logging
from typing import List
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleConverter:
    """
    Converts domain lists to different proxy tool rule formats.
    """

    PROJECT_NAME = 'iOS-AntiRevoke-DNS-Rules'
    LICENSE_NAME = 'MIT License'

    @staticmethod
    def _build_header(comment_prefix: str, author: str, updated_utc: str, domain_count: int) -> List[str]:
        """
        Build standardized header lines for rule files.

        Args:
            comment_prefix: Comment prefix for the target format (e.g., '#', '//')
            author: Author name or handle
            updated_utc: Timestamp in UTC (YYYY-MM-DD HH:MM:SS UTC)
            domain_count: Total domain count

        Returns:
            List of header lines
        """
        return [
            f'{comment_prefix} Project: {RuleConverter.PROJECT_NAME}',
            f'{comment_prefix} Author: {author}',
            f'{comment_prefix} Updated: {updated_utc}',
            f'{comment_prefix} Domain Count: {domain_count}',
            f'{comment_prefix} License: {RuleConverter.LICENSE_NAME}'
        ]

    @staticmethod
    def generate_quantumultx_rules(domains: List[str], author: str, updated_utc: str, domain_count: int) -> str:
        """
        Generate Quantumult X format rules.

        Format: host, example.com, reject

        Args:
            domains: List of domains

        Returns:
            Rule string in Quantumult X format
        """
        rules = []
        rules.extend(RuleConverter._build_header('#', author, updated_utc, domain_count))
        rules.append('# Format: host, domain, action')
        rules.append('')

        for domain in sorted(set(domains)):
            if domain.strip():
                rules.append(f'host, {domain.strip()}, reject')

        return '\n'.join(rules)

    @staticmethod
    def generate_surge_rules(domains: List[str], author: str, updated_utc: str, domain_count: int) -> str:
        """
        Generate Surge format rules.

        Format: DOMAIN,example.com,REJECT

        Args:
            domains: List of domains

        Returns:
            Rule string in Surge format
        """
        rules = []
        rules.extend(RuleConverter._build_header('#', author, updated_utc, domain_count))
        rules.append('# Format: DOMAIN,domain,action')
        rules.append('')

        for domain in sorted(set(domains)):
            if domain.strip():
                rules.append(f'DOMAIN,{domain.strip()},REJECT')

        return '\n'.join(rules)

    @staticmethod
    def generate_loon_rules(domains: List[str], author: str, updated_utc: str, domain_count: int) -> str:
        """
        Generate Loon format rules.

        Format: DOMAIN,example.com,REJECT

        Args:
            domains: List of domains

        Returns:
            Rule string in Loon format
        """
        rules = []
        rules.extend(RuleConverter._build_header('#', author, updated_utc, domain_count))
        rules.append('# Format: DOMAIN,domain,action')
        rules.append('')

        for domain in sorted(set(domains)):
            if domain.strip():
                rules.append(f'DOMAIN,{domain.strip()},REJECT')

        return '\n'.join(rules)

    @staticmethod
    def generate_shadowrocket_rules(domains: List[str], author: str, updated_utc: str, domain_count: int) -> str:
        """
        Generate Shadowrocket format rules.

        Format: DOMAIN,example.com,REJECT

        Args:
            domains: List of domains

        Returns:
            Rule string in Shadowrocket format
        """
        rules = []
        rules.extend(RuleConverter._build_header('#', author, updated_utc, domain_count))
        rules.append('# Format: DOMAIN,domain,action')
        rules.append('')

        for domain in sorted(set(domains)):
            if domain.strip():
                rules.append(f'DOMAIN,{domain.strip()},REJECT')

        return '\n'.join(rules)

    @staticmethod
    def generate_hosts_rules(
        domains: List[str],
        author: str,
        updated_utc: str,
        domain_count: int,
        ip: str = '0.0.0.0'
    ) -> str:
        """
        Generate hosts file format rules.

        Format: 0.0.0.0 example.com

        Args:
            domains: List of domains
            ip: IP address to block (default: 0.0.0.0)

        Returns:
            Rule string in hosts format
        """
        rules = []
        rules.extend(RuleConverter._build_header('#', author, updated_utc, domain_count))
        rules.append('# Format: IP domain')
        rules.append('')

        for domain in sorted(set(domains)):
            if domain.strip():
                rules.append(f'{ip} {domain.strip()}')

        return '\n'.join(rules)


class RuleFileGenerator:
    """
    Generates and saves rule files for different proxy tools.
    """

    def __init__(self, output_dir: str = 'output'):
        """
        Initialize rule file generator.

        Args:
            output_dir: Output directory for rule files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.converter = RuleConverter()

    def generate_all_rules(self, domains: List[str], author: str, updated_utc: str, domain_count: int) -> dict:
        """
        Generate all supported rule formats and save to files.

        Args:
            domains: List of domains to convert

        Returns:
            Dictionary mapping rule names to file paths
        """
        generated_files = {}

        try:
            # Generate Quantumult X rules
            qx_rules = self.converter.generate_quantumultx_rules(domains, author, updated_utc, domain_count)
            qx_file = self.output_dir / 'RevokeGuard_QuantumultX.txt'
            with open(qx_file, 'w', encoding='utf-8') as f:
                f.write(qx_rules)
            generated_files['Quantumult X'] = str(qx_file)
            logger.info(f"Generated Quantumult X rules: {qx_file}")

        except Exception as e:
            logger.error(f"Failed to generate Quantumult X rules: {e}")

        try:
            # Generate Surge rules
            surge_rules = self.converter.generate_surge_rules(domains, author, updated_utc, domain_count)
            surge_file = self.output_dir / 'RevokeGuard_Surge.txt'
            with open(surge_file, 'w', encoding='utf-8') as f:
                f.write(surge_rules)
            generated_files['Surge'] = str(surge_file)
            logger.info(f"Generated Surge rules: {surge_file}")

        except Exception as e:
            logger.error(f"Failed to generate Surge rules: {e}")

        try:
            # Generate Loon rules
            loon_rules = self.converter.generate_loon_rules(domains, author, updated_utc, domain_count)
            loon_file = self.output_dir / 'RevokeGuard_Loon.txt'
            with open(loon_file, 'w', encoding='utf-8') as f:
                f.write(loon_rules)
            generated_files['Loon'] = str(loon_file)
            logger.info(f"Generated Loon rules: {loon_file}")

        except Exception as e:
            logger.error(f"Failed to generate Loon rules: {e}")

        try:
            # Generate Shadowrocket rules
            sr_rules = self.converter.generate_shadowrocket_rules(domains, author, updated_utc, domain_count)
            sr_file = self.output_dir / 'RevokeGuard_Shadowrocket.txt'
            with open(sr_file, 'w', encoding='utf-8') as f:
                f.write(sr_rules)
            generated_files['Shadowrocket'] = str(sr_file)
            logger.info(f"Generated Shadowrocket rules: {sr_file}")

        except Exception as e:
            logger.error(f"Failed to generate Shadowrocket rules: {e}")

        try:
            # Generate hosts file rules
            hosts_rules = self.converter.generate_hosts_rules(domains, author, updated_utc, domain_count)
            hosts_file = self.output_dir / 'RevokeGuard_hosts.txt'
            with open(hosts_file, 'w', encoding='utf-8') as f:
                f.write(hosts_rules)
            generated_files['Hosts'] = str(hosts_file)
            logger.info(f"Generated Hosts file rules: {hosts_file}")

        except Exception as e:
            logger.error(f"Failed to generate Hosts rules: {e}")

        # Generate domain list file
        try:
            domain_file = self.output_dir / 'domains.txt'
            with open(domain_file, 'w', encoding='utf-8') as f:
                header_lines = RuleConverter._build_header('#', author, updated_utc, domain_count)
                for line in header_lines:
                    f.write(f'{line}\n')
                f.write('\n')
                for domain in sorted(set(domains)):
                    if domain.strip():
                        f.write(f'{domain.strip()}\n')
            generated_files['Domain List'] = str(domain_file)
            logger.info(f"Generated domain list: {domain_file}")

        except Exception as e:
            logger.error(f"Failed to generate domain list: {e}")

        return generated_files
