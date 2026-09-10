#!/usr/bin/env python3
"""Daily iOS Anti-Revoke domain discovery and artifact generation."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from utils.crypto_handler import CryptoHandler, DnsEndpoint
from utils.dns_probe import DoHDomainProbe, DomainDiscoveryReport
from utils.rule_converter import RuleFileGenerator
from utils.scraper import ProfileScraper

APPLE_SOURCE_URL = "https://support.apple.com/zh-cn/101555"
REFERENCE_DOH_URL = "https://cloudflare-dns.com/dns-query"
MIN_APPLE_CANDIDATES = 100
MAX_TARGET_RATIO = 0.5

PROFILE_SOURCES = [
    {
        "url": "https://khoindvn.io.vn/",
        "xpath": "/html/body/main/div[1]/div/a[5]",
        "name": "khoindvn",
    },
    {
        "url": "https://applejr.net/",
        "xpath": '//*[@id="cat-esign"]/div[1]/a',
        "name": "applejr",
    },
    {
        "url": "https://sideloading.net/dns/",
        "xpath": "/html/body/main/div/section[1]/div[1]/a[1]",
        "name": "sideloading",
        "preferred_payload_identifier": "novadev.nexdns.whileinstalling",
        "enhanced_payload_identifier": "novadev.nexdns.afterinstalling",
    },
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AntiRevokeOrchestrator:
    """Coordinate candidate collection, DNS probing, and output generation."""

    def __init__(
        self,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        output_dir: str = "output",
        timeout: int = 30,
        workers: int = 20,
        reference_doh_url: str = REFERENCE_DOH_URL,
    ):
        self.cert_path = cert_path
        self.key_path = key_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.enhanced_output_dir = self.output_dir / "enhanced"
        self.enhanced_output_dir.mkdir(parents=True, exist_ok=True)

        self.scraper = ProfileScraper(timeout=timeout)
        self.crypto = CryptoHandler(cert_path, key_path)
        self.probe = DoHDomainProbe(
            reference_url=reference_doh_url,
            timeout=min(timeout, 20),
            workers=workers,
        )
        self.rule_generator = RuleFileGenerator(output_dir)
        self.enhanced_rule_generator = RuleFileGenerator(
            str(self.enhanced_output_dir),
            file_prefix="RevokeGuard_Enhanced",
            domain_filename="enhanced-domains.txt",
        )
        self.reference_doh_url = reference_doh_url
        self.source_details: Dict[str, Dict[str, object]] = {}

    @staticmethod
    def _select_endpoint(
        source: Dict[str, str],
        endpoints: Sequence[DnsEndpoint],
    ) -> DnsEndpoint:
        if not endpoints:
            raise RuntimeError(
                f"Profile {source['name']} contains no valid HTTPS DNS endpoint"
            )

        preferred_identifier = source.get("preferred_payload_identifier")
        if preferred_identifier:
            for endpoint in endpoints:
                if endpoint.payload_identifier == preferred_identifier:
                    return endpoint
            raise RuntimeError(
                f"Profile {source['name']} no longer contains preferred payload "
                f"{preferred_identifier}"
            )

        if len(endpoints) > 1:
            logger.warning(
                "Profile %s has %s endpoints; selecting the first payload",
                source["name"],
                len(endpoints),
            )
        return endpoints[0]

    def extract_selected_endpoints(
        self,
        profiles: Dict[str, bytes],
        sources: Sequence[Dict[str, str]],
    ) -> Tuple[List[DnsEndpoint], DnsEndpoint]:
        selected: List[DnsEndpoint] = []
        enhanced_endpoint: Optional[DnsEndpoint] = None
        self.source_details = {}

        for source in sources:
            name = source["name"]
            profile = self.crypto.parse_profile_bytes(profiles[name])
            discovered = self.crypto.extract_dns_endpoints(profile, name)
            endpoint = self._select_endpoint(source, discovered)
            selected.append(endpoint)
            enhanced_identifier = source.get("enhanced_payload_identifier")
            if enhanced_identifier:
                enhanced_endpoint = self._select_endpoint(
                    {
                        "name": f"{name} enhanced",
                        "preferred_payload_identifier": enhanced_identifier,
                    },
                    discovered,
                )
            self.source_details[name] = {
                "page_url": source["url"],
                "xpath": source["xpath"],
                "download_url": self.scraper.download_urls[name],
                "profile_size": len(profiles[name]),
                "discovered_endpoints": [asdict(item) for item in discovered],
                "selected_endpoint": asdict(endpoint),
                "enhanced_endpoint": (
                    asdict(enhanced_endpoint) if enhanced_identifier else None
                ),
            }
            logger.info("Selected %s endpoint: %s", name, endpoint.url)

        if len(selected) != len(sources):
            raise RuntimeError("Not every required profile yielded a DNS endpoint")
        if enhanced_endpoint is None:
            raise RuntimeError("No enhanced DNS endpoint was selected")
        logger.info("Selected enhanced endpoint: %s", enhanced_endpoint.url)
        return selected, enhanced_endpoint

    def generate_profile(
        self,
        domains: Sequence[str],
        updated_utc: str,
        output_path: Path,
        profile_name: str,
    ) -> str:
        if bool(self.cert_path) != bool(self.key_path):
            raise RuntimeError("Both SSL_CERT_PATH and SSL_KEY_PATH are required")

        with tempfile.TemporaryDirectory() as temp_dir:
            plist_path = Path(temp_dir) / f"{output_path.stem}.plist"
            created = self.crypto.create_profile(
                list(domains),
                output_file=str(plist_path),
                updated_utc=updated_utc,
                domain_count=len(domains),
                backend_host="reject.rzmy.dpdns.org",
                profile_name=profile_name,
            )
            if not created:
                raise RuntimeError("Failed to create the iOS configuration profile")

            if self.cert_path and self.key_path:
                if not Path(self.cert_path).is_file() or not Path(self.key_path).is_file():
                    raise RuntimeError("Configured signing certificate or key is missing")
                signed = self.crypto.sign_profile(created, str(output_path))
                if not signed:
                    raise RuntimeError("Failed to sign the iOS configuration profile")
            else:
                shutil.copyfile(created, output_path)
                logger.warning("No signing credentials configured; wrote unsigned mobileconfig")

        return str(output_path)

    def generate_metadata(
        self,
        candidate_domains: Sequence[str],
        selected_endpoints: Sequence[DnsEndpoint],
        enhanced_endpoint: DnsEndpoint,
        normal_report: DomainDiscoveryReport,
        enhanced_report: DomainDiscoveryReport,
        enhanced_extra_domains: Sequence[str],
        normal_files: Dict[str, str],
        enhanced_files: Dict[str, str],
        timestamp: str,
    ) -> str:
        metadata = {
            "schema_version": 3,
            "timestamp": timestamp,
            "apple_source": {
                "url": APPLE_SOURCE_URL,
                "candidate_domains": len(candidate_domains),
            },
            "profile_sources": self.source_details,
            "selected_dns_endpoints": [
                asdict(endpoint) for endpoint in selected_endpoints
            ],
            "enhanced_dns_endpoint": asdict(enhanced_endpoint),
            "reference_doh_url": self.reference_doh_url,
            "normal_discovery": {
                "target_domains": len(normal_report.target_domains),
                "blocked_by": normal_report.blocked_by,
                "inconclusive_domains": list(normal_report.inconclusive_domains),
                "endpoint_stats": normal_report.endpoint_stats,
                "reference_queries": normal_report.reference_queries,
            },
            "enhanced_discovery": {
                "endpoint_target_domains": len(enhanced_report.target_domains),
                "extra_domains": len(enhanced_extra_domains),
                "extra_domain_list": list(enhanced_extra_domains),
                "merged_profile_domains": len(
                    set(normal_report.target_domains) | set(enhanced_extra_domains)
                ),
                "blocked_by": enhanced_report.blocked_by,
                "inconclusive_domains": list(enhanced_report.inconclusive_domains),
                "endpoint_stats": enhanced_report.endpoint_stats,
                "reference_queries": enhanced_report.reference_queries,
            },
            "generated_files": {
                "normal": normal_files,
                "enhanced": enhanced_files,
            },
        }
        metadata_file = self.output_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as file_handle:
            json.dump(metadata, file_handle, indent=2, ensure_ascii=False)
            file_handle.write("\n")
        return str(metadata_file)

    def generate_enhanced_metadata(
        self,
        enhanced_endpoint: DnsEndpoint,
        enhanced_extra_domains: Sequence[str],
        merged_domains: Sequence[str],
        generated_files: Dict[str, str],
        timestamp: str,
    ) -> str:
        metadata = {
            "schema_version": 1,
            "timestamp": timestamp,
            "dns_endpoint": asdict(enhanced_endpoint),
            "extra_domains": list(enhanced_extra_domains),
            "extra_domain_count": len(enhanced_extra_domains),
            "merged_profile_domain_count": len(merged_domains),
            "generated_files": generated_files,
        }
        metadata_file = self.enhanced_output_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as file_handle:
            json.dump(metadata, file_handle, indent=2, ensure_ascii=False)
            file_handle.write("\n")
        return str(metadata_file)

    @staticmethod
    def _validate_report(
        label: str,
        candidate_domains: Sequence[str],
        report: DomainDiscoveryReport,
    ) -> None:
        if not report.target_domains:
            raise RuntimeError(f"{label} DNS discovery produced no target domains")
        if len(report.target_domains) / len(candidate_domains) > MAX_TARGET_RATIO:
            raise RuntimeError(
                f"{label} target-domain ratio exceeded the safety threshold: "
                f"{len(report.target_domains)}/{len(candidate_domains)}"
            )

    @staticmethod
    def build_enhanced_domain_sets(
        normal_domains: Sequence[str],
        enhanced_endpoint_domains: Sequence[str],
    ) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
        normal_set = set(normal_domains)
        enhanced_extra = tuple(
            sorted(set(enhanced_endpoint_domains) - normal_set)
        )
        merged = tuple(sorted(normal_set | set(enhanced_extra)))
        return enhanced_extra, merged

    def run(self, sources: Sequence[Dict[str, str]] = PROFILE_SOURCES) -> bool:
        try:
            logger.info("Starting DNS-based iOS Anti-Revoke discovery")
            candidate_domains = self.scraper.fetch_apple_domains(APPLE_SOURCE_URL)
            if len(candidate_domains) < MIN_APPLE_CANDIDATES:
                raise RuntimeError(
                    f"Apple candidate count dropped below {MIN_APPLE_CANDIDATES}: "
                    f"{len(candidate_domains)}"
                )
            profiles = self.scraper.scrape_sources(sources)
            selected_endpoints, enhanced_endpoint = self.extract_selected_endpoints(
                profiles, sources
            )
            normal_report = self.probe.discover(candidate_domains, selected_endpoints)
            enhanced_report = self.probe.discover(
                candidate_domains, [enhanced_endpoint]
            )
            self._validate_report("Normal", candidate_domains, normal_report)
            self._validate_report("Enhanced", candidate_domains, enhanced_report)

            enhanced_extra_domains, merged_enhanced_domains = (
                self.build_enhanced_domain_sets(
                    normal_report.target_domains,
                    enhanced_report.target_domains,
                )
            )

            now = datetime.now(timezone.utc)
            updated_utc = now.strftime("%Y-%m-%d %H:%M:%S UTC")
            normal_profile_path = self.generate_profile(
                normal_report.target_domains,
                updated_utc,
                self.output_dir / "RevokeGuard_Auto-Sync.mobileconfig",
                "RevokeGuard",
            )
            normal_files = self.rule_generator.generate_all_rules(
                list(normal_report.target_domains),
                author="RzMY",
                updated_utc=updated_utc,
                domain_count=len(normal_report.target_domains),
            )
            if len(normal_files) != 6:
                raise RuntimeError(
                    f"Expected 6 normal rule artifacts, generated {len(normal_files)}"
                )

            enhanced_profile_path = self.generate_profile(
                merged_enhanced_domains,
                updated_utc,
                self.enhanced_output_dir / "RevokeGuard_Enhanced.mobileconfig",
                "RevokeGuard Enhanced",
            )
            enhanced_files = self.enhanced_rule_generator.generate_all_rules(
                list(enhanced_extra_domains),
                author="RzMY",
                updated_utc=updated_utc,
                domain_count=len(enhanced_extra_domains),
            )
            if len(enhanced_files) != 6:
                raise RuntimeError(
                    "Expected 6 enhanced rule artifacts, "
                    f"generated {len(enhanced_files)}"
                )

            normal_files["iOS Profile"] = normal_profile_path
            enhanced_files["iOS Profile"] = enhanced_profile_path
            timestamp = now.isoformat().replace("+00:00", "Z")
            enhanced_metadata_path = self.generate_enhanced_metadata(
                enhanced_endpoint,
                enhanced_extra_domains,
                merged_enhanced_domains,
                enhanced_files,
                timestamp,
            )
            enhanced_files["Metadata"] = enhanced_metadata_path
            metadata_path = self.generate_metadata(
                candidate_domains,
                selected_endpoints,
                enhanced_endpoint,
                normal_report,
                enhanced_report,
                enhanced_extra_domains,
                normal_files,
                enhanced_files,
                timestamp,
            )
            logger.info(
                "Pipeline complete: %s candidates, %s normal targets, "
                "%s enhanced extras, metadata=%s",
                len(candidate_domains),
                len(normal_report.target_domains),
                len(enhanced_extra_domains),
                metadata_path,
            )
            return True
        except Exception:
            logger.exception("Pipeline failed")
            return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--reference-doh-url", default=REFERENCE_DOH_URL)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    orchestrator = AntiRevokeOrchestrator(
        cert_path=os.getenv("SSL_CERT_PATH"),
        key_path=os.getenv("SSL_KEY_PATH"),
        output_dir=args.output_dir,
        timeout=args.timeout,
        workers=args.workers,
        reference_doh_url=args.reference_doh_url,
    )
    return 0 if orchestrator.run() else 1


if __name__ == "__main__":
    sys.exit(main())
