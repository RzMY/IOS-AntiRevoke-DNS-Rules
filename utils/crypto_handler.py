"""
Cryptography and profile handling module.
Handles OpenSSL operations for decrypting, verifying, and signing .mobileconfig files.
"""

import subprocess
import plistlib
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CryptoHandler:
    """
    Handles encryption/decryption and signing of iOS .mobileconfig profiles.
    """

    def __init__(self, cert_path: str = None, key_path: str = None):
        """
        Initialize crypto handler with certificate and key paths.

        Args:
            cert_path: Path to fullchain.pem certificate
            key_path: Path to privkey.pem private key
        """
        self.cert_path = cert_path
        self.key_path = key_path

    def verify_openssl(self) -> bool:
        """
        Verify that OpenSSL is available and functional.

        Returns:
            True if OpenSSL is available, False otherwise
        """
        try:
            subprocess.run(['openssl', 'version'], capture_output=True, check=True)
            logger.info("OpenSSL is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("OpenSSL is not available or not installed")
            return False

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

    def extract_domains(self, plist_data: Dict[str, Any]) -> List[str]:
        """
        Extract domain list from parsed plist PayloadContent.

        Args:
            plist_data: Parsed plist dictionary

        Returns:
            List of domains
        """
        domains = []
        
        try:
            payload_content = plist_data.get('PayloadContent', [])
            
            if isinstance(payload_content, list):
                for payload in payload_content:
                    if isinstance(payload, dict):
                        dns_settings = payload.get('DNSSettings', {})
                        if isinstance(dns_settings, dict):
                            match_domains = dns_settings.get('SupplementalMatchDomains', [])
                            if isinstance(match_domains, list):
                                domains.extend(match_domains)
            
            logger.info(f"Extracted {len(domains)} domains from plist")
            return domains

        except Exception as e:
            logger.error(f"Domain extraction error: {e}")
            return []

    def create_profile(self, domains: List[str], output_file: str = None) -> Optional[str]:
        """
        Create a new .mobileconfig plist file with the given domains.

        Args:
            domains: List of domains to include
            output_file: Output file path (optional)

        Returns:
            Path to created plist file or None if creation fails
        """
        if output_file is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.plist')
            output_file = temp_file.name
            temp_file.close()

        try:
            # Create base mobileconfig structure
            profile = {
                'PayloadVersion': 1,
                'PayloadType': 'Configuration',
                'PayloadIdentifier': f'com.revokeGuard.{uuid.uuid4()}',
                'PayloadUUID': str(uuid.uuid4()),
                'PayloadDisplayName': 'RevokeGuard Auto-Sync',
                'PayloadDescription': 'iOS Anti-Revoke & Anti-Blacklist Configuration',
                'PayloadOrganization': 'RevokeGuard',
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
                        'PayloadDisplayName': 'DNS Settings',
                        'DNSSettings': {
                            'DNSProtocol': 'https',
                            'ServerAddresses': ['https://reject.rzmy.dpdns.org/dns-query'],
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

    def sign_profile(self, plist_file: str, output_file: str = None) -> Optional[str]:
        """
        Sign a plist profile using certificate and private key (DER format).

        Args:
            plist_file: Path to unsigned plist file
            output_file: Path to save signed .mobileconfig file

        Returns:
            Path to signed .mobileconfig file or None if signing fails
        """
        if not self.cert_path or not self.key_path:
            logger.error("Certificate or key path not configured")
            return None

        if not Path(plist_file).exists():
            logger.error(f"Plist file not found: {plist_file}")
            return None

        if not Path(self.cert_path).exists():
            logger.error(f"Certificate file not found: {self.cert_path}")
            return None

        if not Path(self.key_path).exists():
            logger.error(f"Key file not found: {self.key_path}")
            return None

        if output_file is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mobileconfig')
            output_file = temp_file.name
            temp_file.close()

        try:
            # Sign the profile using OpenSSL CMS
            cmd = [
                'openssl', 'smime',
                '-sign',
                '-signer', self.cert_path,
                '-inkey', self.key_path,
                '-in', plist_file,
                '-out', output_file,
                '-outform', 'DER',
                '-nodetach'
            ]

            logger.info(f"Signing profile {plist_file}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if Path(output_file).exists():
                logger.info(f"Successfully signed profile: {output_file}")
                return output_file
            else:
                logger.error("Signed file was not created")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"OpenSSL signing failed: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Signing error: {e}")
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
