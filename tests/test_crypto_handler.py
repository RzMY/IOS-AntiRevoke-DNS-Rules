import plistlib
from pathlib import Path

from main import AntiRevokeOrchestrator, PROFILE_SOURCES
from utils.crypto_handler import CryptoHandler


def test_parse_unsigned_profile_and_extract_https_endpoints():
    profile = {
        "PayloadContent": [
            {
                "PayloadDisplayName": "Primary",
                "PayloadIdentifier": "example.primary",
                "DNSSettings": {
                    "DNSProtocol": "HTTPS",
                    "ServerURL": "https://dns.example/dns-query",
                },
            },
            {
                "PayloadDisplayName": "Ignored",
                "PayloadIdentifier": "example.http",
                "DNSSettings": {
                    "DNSProtocol": "HTTPS",
                    "ServerURL": "http://dns.example/dns-query",
                },
            },
        ]
    }
    handler = CryptoHandler()

    parsed = handler.parse_profile_bytes(plistlib.dumps(profile))
    endpoints = handler.extract_dns_endpoints(parsed, "test-source")

    assert len(endpoints) == 1
    assert endpoints[0].source == "test-source"
    assert endpoints[0].url == "https://dns.example/dns-query"
    assert endpoints[0].payload_identifier == "example.primary"


def test_select_endpoint_uses_preferred_payload_identifier():
    handler = CryptoHandler()
    profile = {
        "PayloadContent": [
            {
                "PayloadIdentifier": "first",
                "DNSSettings": {
                    "DNSProtocol": "HTTPS",
                    "ServerURL": "https://first.example/dns-query",
                },
            },
            {
                "PayloadIdentifier": "preferred",
                "DNSSettings": {
                    "DNSProtocol": "HTTPS",
                    "ServerURL": "https://preferred.example/dns-query",
                },
            },
        ]
    }
    endpoints = handler.extract_dns_endpoints(profile, "source")

    selected = AntiRevokeOrchestrator._select_endpoint(
        {
            "name": "source",
            "preferred_payload_identifier": "preferred",
        },
        endpoints,
    )

    assert selected.url == "https://preferred.example/dns-query"


def test_create_profile_contains_target_domains(tmp_path: Path):
    output = tmp_path / "profile.plist"
    handler = CryptoHandler()

    created = handler.create_profile(
        ["valid.apple.com", "certs.apple.com", "certs.apple.com"],
        output_file=str(output),
        updated_utc="2026-08-28 00:00:00 UTC",
        domain_count=2,
    )

    assert created == str(output)
    data = plistlib.loads(output.read_bytes())
    dns_settings = data["PayloadContent"][0]["DNSSettings"]
    assert dns_settings["ServerURL"] == "https://reject.rzmy.dpdns.org/dns-query"
    assert dns_settings["SupplementalMatchDomains"] == [
        "certs.apple.com",
        "valid.apple.com",
    ]


def test_create_enhanced_profile_has_distinct_display_name(tmp_path: Path):
    output = tmp_path / "enhanced.plist"
    handler = CryptoHandler()

    handler.create_profile(
        ["ppq.apple.com"],
        output_file=str(output),
        updated_utc="2026-08-30 00:00:00 UTC",
        profile_name="RevokeGuard Enhanced",
    )

    data = plistlib.loads(output.read_bytes())
    assert data["PayloadDisplayName"] == "RevokeGuard Enhanced 2026-08-30"
    assert (
        data["PayloadContent"][0]["PayloadDisplayName"]
        == "RevokeGuard Enhanced DNS Settings"
    )


def test_build_enhanced_domain_sets_separates_extra_and_merged_domains():
    extra, merged = AntiRevokeOrchestrator.build_enhanced_domain_sets(
        ["certs.apple.com", "valid.apple.com"],
        ["valid.apple.com", "ppq.apple.com"],
    )

    assert extra == ("ppq.apple.com",)
    assert merged == (
        "certs.apple.com",
        "ppq.apple.com",
        "valid.apple.com",
    )


def test_sideloading_payload_modes_are_explicit():
    source = next(item for item in PROFILE_SOURCES if item["name"] == "sideloading")

    assert source["preferred_payload_identifier"] == (
        "novadev.nexdns.whileinstalling"
    )
    assert source["enhanced_payload_identifier"] == (
        "novadev.nexdns.afterinstalling"
    )
