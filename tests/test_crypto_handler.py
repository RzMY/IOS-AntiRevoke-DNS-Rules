import plistlib
from pathlib import Path

import pytest

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
    assert endpoints[0].domains == ()


@pytest.mark.parametrize("fmt", [plistlib.FMT_XML, plistlib.FMT_BINARY])
def test_extract_explicit_domains_without_https_endpoint(fmt):
    profile = {
        "PayloadContent": [{
            "PayloadIdentifier": "explicit",
            "DNSSettings": {
                "SupplementalMatchDomains": [
                    " OCSP.APPLE.COM. ", "*.certs.apple.com", "ocsp.apple.com",
                    "outside.example", "", "*", "https://not-a-domain.example",
                    "1.1.1.1", "::1", "-invalid.example", 123,
                ],
                "ServerAddresses": ["resolver.example"],
            },
            "OnDemandRules": [{"Domains": ["unrelated.example"]}],
        }],
    }
    handler = CryptoHandler()
    parsed = handler.parse_profile_bytes(plistlib.dumps(profile, fmt=fmt))

    endpoint, = handler.extract_dns_endpoints(parsed, "source")

    assert endpoint.url == ""
    assert endpoint.payload_identifier == "explicit"
    assert endpoint.domains == (
        "certs.apple.com", "ocsp.apple.com", "outside.example",
    )


@pytest.mark.parametrize("values", [[], ["", "*"], "ocsp.apple.com"])
def test_empty_or_malformed_domain_list_keeps_https_probe_path(values):
    profile = {"DNSSettings": {
        "DNSProtocol": "HTTPS",
        "ServerURL": "https://dns.example/dns-query",
        "SupplementalMatchDomains": values,
    }}

    endpoint, = CryptoHandler().extract_dns_endpoints(profile, "source")

    assert endpoint.domains == ()
    assert endpoint.url == "https://dns.example/dns-query"


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


def test_sideloading_payload_modes_are_explicit_and_accept_legacy_ids():
    source = next(item for item in PROFILE_SOURCES if item["name"] == "sideloading")

    assert source["preferred_payload_identifiers"] == [
        "nexsideloading.nexrevokedns.duringinstall",
        "novadev.nexrevokedns.whileinstalling",
        "novadev.nexdns.whileinstalling",
    ]
    assert source["enhanced_payload_identifiers"] == [
        "nexsideloading.nexrevokedns.afterinstall",
        "novadev.nexrevokedns.afterinstalling",
        "novadev.nexdns.afterinstalling",
    ]


@pytest.mark.parametrize("mode", ["preferred", "enhanced"])
@pytest.mark.parametrize("generation", [0, 1, 2])
def test_select_endpoint_prefers_newest_available_sideloading_identifier(
    mode, generation,
):
    source = next(item for item in PROFILE_SOURCES if item["name"] == "sideloading")
    identifiers = source[f"{mode}_payload_identifiers"]
    # Put the oldest payload first to ensure profile order cannot choose a mode.
    profile = {"PayloadContent": [
        {
            "PayloadIdentifier": identifier,
            "DNSSettings": {
                "DNSProtocol": "HTTPS",
                "ServerURL": f"https://dns.example/{identifier}/dns-query",
            },
        }
        for identifier in reversed(identifiers[generation:])
    ]}
    endpoints = CryptoHandler().extract_dns_endpoints(profile, "sideloading")

    selected = AntiRevokeOrchestrator._select_endpoint(
        source,
        endpoints,
        mode=mode,
    )

    assert selected.payload_identifier == identifiers[generation]


@pytest.mark.parametrize("mode", ["preferred", "enhanced"])
def test_sideloading_missing_mode_refuses_another_payload(mode):
    source = next(item for item in PROFILE_SOURCES if item["name"] == "sideloading")
    other_mode = "enhanced" if mode == "preferred" else "preferred"
    profile = {"PayloadContent": [{
        "PayloadIdentifier": source[f"{other_mode}_payload_identifiers"][0],
        "DNSSettings": {
            "DNSProtocol": "HTTPS",
            "ServerURL": "https://dns.example/dns-query",
        },
    }]}
    endpoints = CryptoHandler().extract_dns_endpoints(profile, "sideloading")

    with pytest.raises(RuntimeError, match="no longer contains any preferred payload"):
        AntiRevokeOrchestrator._select_endpoint(source, endpoints, mode=mode)
