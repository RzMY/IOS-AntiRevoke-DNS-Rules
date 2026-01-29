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
            cert_path: Path to fullchain.pem certificate (可包含完整证书链)
            key_path: Path to privkey.pem private key
        """
        self.cert_path = cert_path
        self.key_path = key_path
        self.server_cert_path = None
        self.chain_cert_path = None

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

    def split_certificate_chain(self, fullchain_path: str) -> tuple[Optional[str], Optional[str]]:
        """
        将 fullchain.pem 分离为服务器证书和证书链。
        
        fullchain.pem 包含多个证书：
        - 第一个证书：服务器证书
        - 后续证书：中间证书和根证书（证书链）
        
        Args:
            fullchain_path: fullchain.pem 文件路径
            
        Returns:
            (server_cert_path, chain_cert_path) 元组，失败返回 (None, None)
        """
        if not Path(fullchain_path).exists():
            logger.error(f"证书链文件不存在: {fullchain_path}")
            return None, None
            
        try:
            with open(fullchain_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割所有证书块
            cert_blocks = []
            current_block = []
            in_cert = False
            
            for line in content.splitlines():
                if '-----BEGIN CERTIFICATE-----' in line:
                    in_cert = True
                    current_block = [line]
                elif '-----END CERTIFICATE-----' in line:
                    current_block.append(line)
                    cert_blocks.append('\n'.join(current_block))
                    current_block = []
                    in_cert = False
                elif in_cert:
                    current_block.append(line)
            
            if not cert_blocks:
                logger.error("证书链中未找到有效的证书块")
                return None, None
            
            logger.info(f"从证书链中提取到 {len(cert_blocks)} 个证书")
            
            # 第一个证书是服务器证书
            server_cert = cert_blocks[0]
            
            # 创建临时服务器证书文件
            server_cert_file = tempfile.NamedTemporaryFile(
                mode='w',
                delete=False,
                suffix='_server.pem',
                encoding='utf-8'
            )
            server_cert_file.write(server_cert + '\n')
            server_cert_file.close()
            server_cert_path = server_cert_file.name
            
            # 如果有多个证书，创建证书链文件（包含中间证书和根证书）
            chain_cert_path = None
            if len(cert_blocks) > 1:
                chain_certs = '\n'.join(cert_blocks[1:])
                chain_cert_file = tempfile.NamedTemporaryFile(
                    mode='w',
                    delete=False,
                    suffix='_chain.pem',
                    encoding='utf-8'
                )
                chain_cert_file.write(chain_certs + '\n')
                chain_cert_file.close()
                chain_cert_path = chain_cert_file.name
                logger.info(f"证书链已分离: 服务器证书={server_cert_path}, 证书链={chain_cert_path}")
            else:
                logger.info(f"仅服务器证书: {server_cert_path}")
            
            return server_cert_path, chain_cert_path
            
        except Exception as e:
            logger.error(f"证书链分离失败: {e}")
            return None, None

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

    def create_profile(
        self,
        domains: List[str],
        output_file: str = None,
        updated_utc: str = None,
        domain_count: int = None,
        backend_host: str = 'reject.rzmy.dpdns.org'
    ) -> Optional[str]:
        """
        Create a new .mobileconfig plist file with the given domains.

        Args:
            domains: List of domains to include
            output_file: Output file path (optional)
            updated_utc: Timestamp in UTC (YYYY-MM-DD HH:MM:SS UTC)
            domain_count: Total number of merged domains
            backend_host: Backend host for description metadata

        Returns:
            Path to created plist file or None if creation fails
        """
        if output_file is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.plist')
            output_file = temp_file.name
            temp_file.close()

        try:
            domain_total = domain_count if domain_count is not None else len(set(domains))
            updated_value = updated_utc or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            display_date = updated_value.split(' ')[0]

            # Create base mobileconfig structure
            profile = {
                'PayloadVersion': 1,
                'PayloadType': 'Configuration',
                'PayloadIdentifier': f'com.revokeGuard.{uuid.uuid4()}',
                'PayloadUUID': str(uuid.uuid4()),
                'PayloadDisplayName': f'RevokeGuard {display_date}',
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
                        'PayloadDisplayName': 'DNS Settings',
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

    def sign_profile(self, plist_file: str, output_file: str = None) -> Optional[str]:
        """
        Sign a plist profile using certificate and private key (DER format).
        支持完整证书链签名，确保 iOS 设备能够验证证书。

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
            # 分离证书链
            server_cert, chain_cert = self.split_certificate_chain(self.cert_path)
            
            if not server_cert:
                logger.error("无法提取服务器证书，尝试直接使用原始证书文件")
                server_cert = self.cert_path
                chain_cert = None
            else:
                self.server_cert_path = server_cert
                self.chain_cert_path = chain_cert

            # 构建 OpenSSL 签名命令
            cmd = [
                'openssl', 'smime',
                '-sign',
                '-signer', server_cert,
                '-inkey', self.key_path,
                '-in', plist_file,
                '-out', output_file,
                '-outform', 'DER',
                '-nodetach'
            ]
            
            # 如果有证书链，添加 -certfile 参数
            # 这会将中间证书包含在签名中，确保 iOS 设备能够验证完整的信任链
            if chain_cert:
                cmd.extend(['-certfile', chain_cert])
                logger.info(f"使用完整证书链签名: 服务器证书 + {chain_cert}")
            else:
                logger.info("使用单个证书签名（可能是自签名或已包含完整链）")

            logger.info(f"Signing profile {plist_file}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if Path(output_file).exists():
                logger.info(f"Successfully signed profile: {output_file}")
                
                # 清理临时证书文件
                if self.server_cert_path and self.server_cert_path != self.cert_path:
                    try:
                        Path(self.server_cert_path).unlink()
                        logger.debug(f"已清理临时服务器证书: {self.server_cert_path}")
                    except Exception as e:
                        logger.warning(f"清理临时文件失败: {e}")
                
                if self.chain_cert_path:
                    try:
                        Path(self.chain_cert_path).unlink()
                        logger.debug(f"已清理临时证书链: {self.chain_cert_path}")
                    except Exception as e:
                        logger.warning(f"清理临时文件失败: {e}")
                
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
