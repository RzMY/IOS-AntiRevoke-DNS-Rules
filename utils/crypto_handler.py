"""
Profile parsing and generation for iOS .mobileconfig files.
Handles OpenSSL decoding of upstream CMS profiles and unsigned plist generation.
"""

import subprocess
import plistlib
import logging
import ipaddress
import re
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DnsEndpoint:
    """A DNS payload with explicit domains or an endpoint to probe."""

    source: str
    url: str
    payload_identifier: str
    display_name: str
    domains: Tuple[str, ...] = ()


class CryptoHandler:
    """Decode upstream profiles and create unsigned iOS DNS profiles."""

    def decrypt_profile(self, input_file: str, output_file: str = None) -> Optional[str]:
        """
        Decrypt a CMS-signed .mobileconfig file (DER format) to extract raw plist.

        Args:
            input_file: Path to encrypted .mobileconfig file
            output_file: Path to save decrypted plist (optional)

        Returns:
            Path to decrypted plist file or None if decryption fails
        """
        if not Path(input_file).exists():
            logger.error(f"Input file not found: {input_file}")
            return None

        # Create temporary output file if not specified
        if output_file is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.plist')
            output_file = temp_file.name
            temp_file.close()

        try:
            # Use openssl to decrypt CMS-signed file
            cmd = [
                'openssl', 'smime',
                '-verify',
                '-inform', 'DER',
                '-in', input_file,
                '-noverify',
                '-out', output_file
            ]
            
            logger.info(f"Decrypting {input_file} to {output_file}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if Path(output_file).exists():
                logger.info(f"Successfully decrypted profile to {output_file}")
                return output_file
            else:
                logger.error("Decrypted file was not created")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"OpenSSL decryption failed: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None

    def parse_plist(self, plist_file: str) -> Optional[Dict[str, Any]]:
        """
        Parse a plist file into a Python dictionary.

        Args:
            plist_file: Path to plist file

        Returns:
            Parsed plist dictionary or None if parsing fails
        """
        if not Path(plist_file).exists():
            logger.error(f"Plist file not found: {plist_file}")
            return None

        try:
            with open(plist_file, 'rb') as f:
                plist_data = plistlib.load(f)
            logger.info(f"Successfully parsed plist: {plist_file}")
            return plist_data
        except Exception as e:
            logger.error(f"Plist parsing error: {e}")
            return None

    def parse_profile_bytes(self, content: bytes) -> Dict[str, Any]:
        """Parse an unsigned plist or verify and decode a CMS mobileconfig."""
        try:
            return plistlib.loads(content)
        except (plistlib.InvalidFileException, ValueError):
            pass

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "profile.mobileconfig"
            output_file = Path(temp_dir) / "profile.plist"
            input_file.write_bytes(content)

            cmd = [
                "openssl",
                "smime",
                "-verify",
                "-inform",
                "DER",
                "-in",
                str(input_file),
                "-noverify",
                "-out",
                str(output_file),
            ]
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                details = getattr(exc, "stderr", "") or str(exc)
                raise ValueError(f"Could not decode mobileconfig: {details}") from exc

            try:
                return plistlib.loads(output_file.read_bytes())
            except (plistlib.InvalidFileException, ValueError) as exc:
                raise ValueError("Decoded mobileconfig is not a valid plist") from exc

    @staticmethod
    def _extract_match_domains(dns_settings: Dict[str, Any]) -> Tuple[str, ...]:
        """Normalize explicit DNS match domains, excluding catch-all entries."""
        values = dns_settings.get("SupplementalMatchDomains", [])
        if not isinstance(values, list):
            return ()

        domains = set()
        for value in values:
            if not isinstance(value, str):
                continue
            domain = value.strip().lower().rstrip(".")
            if domain.startswith("*."):
                domain = domain[2:]
            if len(domain) > 253 or not re.fullmatch(
                r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
                r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
                domain,
            ):
                continue
            try:
                ipaddress.ip_address(domain)
            except ValueError:
                domains.add(domain)
        return tuple(sorted(domains))

    def extract_dns_endpoints(
        self,
        plist_data: Dict[str, Any],
        source: str,
    ) -> List[DnsEndpoint]:
        """Extract DNS payloads with explicit domains or a valid HTTPS endpoint."""
        endpoints: List[DnsEndpoint] = []

        def visit(value: Any) -> None:
            if isinstance(value, list):
                for child in value:
                    visit(child)
                return
            if not isinstance(value, dict):
                return

            dns_settings = value.get("DNSSettings")
            if isinstance(dns_settings, dict):
                domains = self._extract_match_domains(dns_settings)
                protocol = str(dns_settings.get("DNSProtocol", "")).upper()
                server_url = dns_settings.get("ServerURL")
                endpoint_url = server_url if domains and isinstance(server_url, str) else ""
                if not domains and protocol == "HTTPS" and isinstance(server_url, str):
                    parsed = urlparse(server_url)
                    if (
                        parsed.scheme == "https"
                        and parsed.hostname
                        and not parsed.username
                        and not parsed.password
                    ):
                        endpoint_url = server_url
                if domains or endpoint_url:
                    endpoints.append(
                        DnsEndpoint(
                            source=source,
                            url=endpoint_url,
                            payload_identifier=str(value.get("PayloadIdentifier", "")),
                            display_name=str(value.get("PayloadDisplayName", "")),
                            domains=domains,
                        )
                    )

            for child in value.values():
                visit(child)

        visit(plist_data)
        unique = list(dict.fromkeys(endpoints))
        logger.info("Extracted %s DNS payloads from %s", len(unique), source)
        return unique

    def create_profile(
        self,
        domains: List[str],
        output_file: str = None,
        updated_utc: str = None,
        domain_count: int = None,
        backend_host: str = 'reject.rzmy.dpdns.org',
        profile_name: str = 'RevokeGuard'
    ) -> Optional[str]:
        """
        Create a new .mobileconfig plist file with the given domains.

        Args:
            domains: List of domains to include
            output_file: Output file path (optional)
            updated_utc: Timestamp in UTC (YYYY-MM-DD HH:MM:SS UTC)
            domain_count: Total number of merged domains
            backend_host: Backend host for description metadata
            profile_name: Display name prefix for the generated profile

        Returns:
            Path to created plist file or None if creation fails
        """
        if output_file is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.plist')
            output_file = temp_file.name
            temp_file.close()

        try:
            domain_total = domain_count if domain_count is not None else len(set(domains))
            updated_value = updated_utc or datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            display_date = updated_value.split(' ')[0]

            # Create base mobileconfig structure
            profile = {
                'PayloadVersion': 1,
                'PayloadType': 'Configuration',
                'PayloadIdentifier': f'com.revokeGuard.{uuid.uuid4()}',
                'PayloadUUID': str(uuid.uuid4()),
                'PayloadDisplayName': f'{profile_name} {display_date}',
                'PayloadDescription': (
                    f'Auto-generated on {updated_value}. '
                    f'Blocked Domains: {domain_total}. '
                    f'Backend: {backend_host}.'
                ),
                'PayloadOrganization': 'iOS-AntiRevoke-DNS-Rules',
                'PayloadRemovalDisallowed': False,
                'ConsentText': {
                    'default': 'This profile provides protection against revocation and blacklisting.'
                },
                'PayloadContent': [
                    {
                        'PayloadVersion': 1,
                        'PayloadType': 'com.apple.dnsSettings.managed',
                        'PayloadIdentifier': f'com.revokeGuard.dns.{uuid.uuid4()}',
                        'PayloadUUID': str(uuid.uuid4()),
                        'PayloadDisplayName': f'{profile_name} DNS Settings',
                        'DNSSettings': {
                            'DNSProtocol': 'HTTPS',
                            'ServerURL': 'https://reject.rzmy.dpdns.org/dns-query',
                            'SupplementalMatchDomains': sorted(list(set(domains)))
                        }
                    }
                ]
            }

            with open(output_file, 'wb') as f:
                plistlib.dump(profile, f)

            logger.info(f"Created profile with {len(set(domains))} domains at {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Profile creation error: {e}")
            return None

    def process_profile(self, input_file: str, output_plist: str = None) -> Optional[Dict[str, Any]]:
        """
        Complete workflow: decrypt -> parse a profile.

        Args:
            input_file: Path to encrypted .mobileconfig
            output_plist: Path to save decrypted plist (optional)

        Returns:
            Parsed plist dictionary or None if processing fails
        """
        # Decrypt
        decrypted_plist = self.decrypt_profile(input_file, output_plist)
        if not decrypted_plist:
            return None

        # Parse
        plist_data = self.parse_plist(decrypted_plist)
        return plist_data
