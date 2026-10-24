import json
import plistlib

import pytest

from main import AntiRevokeOrchestrator, PROFILE_SOURCES
from utils.dns_probe import DomainDiscoveryReport, Resolution


@pytest.mark.parametrize("enhanced_is_explicit", [False, True])
@pytest.mark.parametrize("ppq_source", ["absent", "normal", "enhanced", "both", "normal_probe"])
def test_pipeline_uses_profile_domains_and_preserves_payload_modes(
    tmp_path, monkeypatch, enhanced_is_explicit, ppq_source,
):
    normal_ppq = ["ppq.apple.com"] if ppq_source in {"normal", "both"} else []
    enhanced_ppq = ["ppq.apple.com"] if ppq_source in {"enhanced", "both"} else []
    expected_ppq = ["ppq.apple.com"] if ppq_source != "absent" else []
    sources = [
        {"name": "explicit", "url": "https://explicit.example", "xpath": "//a"},
        {
            "name": "multi", "url": "https://multi.example", "xpath": "//a",
            "preferred_payload_identifier": "normal",
            "enhanced_payload_identifier": "enhanced",
        },
    ]

    def payload(identifier, url, domains=None):
        settings = {"DNSProtocol": "HTTPS", "ServerURL": url}
        if domains is not None:
            settings["SupplementalMatchDomains"] = domains
        return {"PayloadIdentifier": identifier, "DNSSettings": settings}

    profiles = {
        "explicit": plistlib.dumps({"PayloadContent": [
            payload("explicit", "https://ordinary-website.example",
                    [" SHARED.EXAMPLE. ", "outside.example", "shared.example"] + normal_ppq),
        ]}),
        "multi": plistlib.dumps({"PayloadContent": [
            payload("unselected", "https://unused.example", ["ignored.example"]),
            payload("enhanced", "https://enhanced.example/dns-query",
                    ["extra.example", "shared.example"] + enhanced_ppq if enhanced_is_explicit else None),
            payload("normal", "https://normal.example/dns-query"),
        ]}),
    }
    candidates = ["shared.example", "blocked.example", "extra.example", "ppq.apple.com"] + [
        f"clean{i}.example" for i in range(100)
    ]
    orchestrator = AntiRevokeOrchestrator(output_dir=str(tmp_path))
    legacy_profile = tmp_path / "enhanced/RevokeGuard_Enhanced.mobileconfig"
    legacy_profile.write_bytes(b"legacy standalone profile")
    monkeypatch.setattr(orchestrator.scraper, "fetch_apple_domains", lambda _: candidates)
    monkeypatch.setattr(orchestrator.scraper, "scrape_sources", lambda _: profiles)
    orchestrator.scraper.download_urls = {s["name"]: s["url"] for s in sources}
    queries = []

    def resolve(url, domain):
        queries.append((url, domain))
        assert url in {
            "https://normal.example/dns-query", "https://enhanced.example/dns-query",
        }
        if enhanced_is_explicit:
            assert url == "https://normal.example/dns-query"
        blocked = {"shared.example", "blocked.example"} if "normal" in url else {
            "shared.example", "extra.example",
        }
        if "normal" in url and ppq_source == "normal_probe":
            blocked.add("ppq.apple.com")
        if "enhanced" in url:
            blocked.update(enhanced_ppq)
        if domain in blocked:
            return Resolution("invalid_address", ("0.0.0.0",), ("NOERROR",))
        return Resolution("valid", ("17.1.1.1",), ("NOERROR",))

    monkeypatch.setattr(orchestrator.probe, "resolve", resolve)

    assert orchestrator.run(sources)
    assert len(queries) == len(candidates) * (1 if enhanced_is_explicit else 2)

    def read_domains(path):
        return [
            line for line in path.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        ]

    assert read_domains(tmp_path / "domains.txt") == [
        "blocked.example", "outside.example", "shared.example",
    ]
    assert read_domains(tmp_path / "enhanced/enhanced-domains.txt") == [
        "extra.example",
    ] + expected_ppq
    normal = plistlib.loads((tmp_path / "RevokeGuard_Auto-Sync.mobileconfig").read_bytes())
    assert len(normal["PayloadContent"]) == 2
    assert not legacy_profile.exists()
    assert "ppq.apple.com" not in normal["PayloadContent"][0]["DNSSettings"]["SupplementalMatchDomains"]
    assert "host, ppq.apple.com, reject" not in (tmp_path / "RevokeGuard_QuantumultX.txt").read_text()
    assert ("host, ppq.apple.com, reject" in (
        tmp_path / "enhanced/RevokeGuard_Enhanced_QuantumultX.txt"
    ).read_text()) == bool(expected_ppq)
    assert normal["PayloadContent"][1]["DNSSettings"]["SupplementalMatchDomains"] == sorted([
        "blocked.example", "extra.example", "outside.example", "shared.example",
    ] + expected_ppq)
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    moved_ppq = ppq_source in {"normal", "both", "normal_probe"}
    assert metadata["schema_version"] == 4
    for mode in ("normal", "enhanced"):
        assert metadata["generated_files"][mode]["iOS Profile"] == (
            tmp_path / "RevokeGuard_Auto-Sync.mobileconfig"
        ).as_posix()
    assert metadata["normal_discovery"]["target_domains"] == 3 + int(moved_ppq)
    assert metadata["normal_discovery"]["published_target_domains"] == 3
    assert metadata["normal_discovery"]["moved_to_enhanced"] == (["ppq.apple.com"] if moved_ppq else [])
    if moved_ppq:
        assert metadata["normal_discovery"]["blocked_by"]["ppq.apple.com"] == (
            ["multi"] if ppq_source == "normal_probe" else ["explicit"]
        )
    assert metadata["enhanced_discovery"]["extra_domain_list"] == ["extra.example"] + expected_ppq
    assert metadata["enhanced_discovery"]["merged_profile_domains"] == 4 + len(expected_ppq)
    enhanced_metadata = json.loads((tmp_path / "enhanced/metadata.json").read_text(encoding="utf-8"))
    assert enhanced_metadata["extra_domains"] == ["extra.example"] + expected_ppq
    assert enhanced_metadata["merged_profile_domain_count"] == 4 + len(expected_ppq)
    assert enhanced_metadata["generated_files"]["iOS Profile"] == (
        tmp_path / "RevokeGuard_Auto-Sync.mobileconfig"
    ).as_posix()
    assert metadata["normal_discovery"]["blocked_by"]["shared.example"] == ["explicit", "multi"]
    assert metadata["normal_discovery"]["endpoint_stats"]["explicit"] == {"profile_domains": 2 + len(normal_ppq)}
    assert metadata["profile_sources"]["explicit"]["selected_endpoint"]["domains"] == sorted([
        "outside.example", "shared.example",
    ] + normal_ppq)


@pytest.mark.parametrize("fmt", [plistlib.FMT_XML, plistlib.FMT_BINARY])
def test_current_sideloading_profile_uses_mode_lists(tmp_path, monkeypatch, fmt):
    """Replay relevant decoded upstream fields without an external fixture file."""
    source = next(item for item in PROFILE_SOURCES if item["name"] == "sideloading")
    # Snapshot of the 2026-10-23 payload identifiers, endpoints, and shared
    # routing scope. Keep this in the tracked test so clean CI checkouts work.
    routing_domains = [
        "appattest.apple.com", "certs.apple.com", "crl.apple.com",
        "ocsp.apple.com", "ocsp2.apple.com", "ocsp3.apple.com",
        "ocsp4.apple.com", "valid.apple.com", "vpp.itunes.apple.com",
        "ppq.apple.com", "ppq-ext.apple.com", "use1-ppq-ext-prod.apple.com",
        "usw2-ppq-ext-prod.apple.com", "ppq-ext.v.aaplimg.com",
        "ppq-st-ext.itunes.apple.com", "dns-check.novadev.vip",
        "ppq-check.novadev.vip", "app.localhost.direct",
        "register.appattest.apple.com", "backloop.dev",
    ]
    # Enhanced comes first to ensure selection does not depend on page order.
    profile = {"PayloadContent": [
        {
            "PayloadType": "com.apple.dnsSettings.managed",
            "PayloadIdentifier": identifier,
            "DNSSettings": {
                "DNSProtocol": "HTTPS",
                "ServerURL": url,
                "SupplementalMatchDomains": routing_domains,
            },
        }
        for identifier, url in (
            (
                "nexsideloading.nexrevokedns.afterinstall",
                "https://dns.sideloading.net/ppq/dns-query",
            ),
            (
                "nexsideloading.nexrevokedns.duringinstall",
                "https://dns.sideloading.net/dns-query",
            ),
        )
    ]}
    orchestrator = AntiRevokeOrchestrator(output_dir=str(tmp_path))
    monkeypatch.setattr(
        orchestrator.scraper, "fetch_apple_domains",
        lambda _: [f"clean{i}.example" for i in range(100)],
    )
    monkeypatch.setattr(
        orchestrator.scraper, "scrape_sources",
        lambda _: {"sideloading": plistlib.dumps(profile, fmt=fmt)},
    )
    orchestrator.scraper.download_urls = {
        "sideloading": "https://sideloading.net/dns/nexrevokedns.mobileconfig"
    }
    orchestrator.scraper.domain_lists = {
        "sideloading": ("ocsp.apple.com", "dns-check.novadev.vip")
    }
    orchestrator.scraper.enhanced_domain_lists = {
        "sideloading": (
            "ocsp.apple.com", "ppq.apple.com", "ppq-check.novadev.vip",
        )
    }

    def unexpected_query(*args):
        raise AssertionError("Explicit deny lists must not require DNS probing")

    monkeypatch.setattr(orchestrator.probe, "resolve", unexpected_query)

    assert orchestrator.run([source])
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    normal = metadata["profile_sources"]["sideloading"]["selected_endpoint"]
    enhanced = metadata["enhanced_dns_endpoint"]
    assert normal["payload_identifier"] == "nexsideloading.nexrevokedns.duringinstall"
    assert normal["url"] == "https://dns.sideloading.net/dns-query"
    assert normal["domains"] == ["ocsp.apple.com"]
    assert enhanced["payload_identifier"] == "nexsideloading.nexrevokedns.afterinstall"
    assert enhanced["url"] == "https://dns.sideloading.net/ppq/dns-query"
    assert enhanced["domains"] == ["ocsp.apple.com", "ppq.apple.com"]
    assert metadata["enhanced_discovery"]["extra_domain_list"] == ["ppq.apple.com"]
    normal_profile = plistlib.loads((tmp_path / "RevokeGuard_Auto-Sync.mobileconfig").read_bytes())
    assert len(normal_profile["PayloadContent"]) == 2
    assert normal_profile["PayloadContent"][0]["DNSSettings"]["SupplementalMatchDomains"] == [
        "ocsp.apple.com",
    ]
    assert normal_profile["PayloadContent"][1]["DNSSettings"]["SupplementalMatchDomains"] == [
        "ocsp.apple.com", "ppq.apple.com",
    ]


def test_sideloading_mode_lists_override_routing_match_domains(tmp_path):
    """NexRevokeDNS uses one routing list; publish only its deny lists."""
    sources = [{
        "name": "sideloading",
        "url": "https://sideloading.example/dns/",
        "xpath": "//a",
        "preferred_payload_identifiers": [
            "novadev.nexrevokedns.whileinstalling",
            "novadev.nexdns.whileinstalling",
        ],
        "enhanced_payload_identifiers": [
            "novadev.nexrevokedns.afterinstalling",
            "novadev.nexdns.afterinstalling",
        ],
        "domain_list_url": "https://sideloading.example/dns/denylist.txt",
        "enhanced_domain_list_url": (
            "https://sideloading.example/dns/denylist-ppq.txt"
        ),
    }]
    routing_domains = ["allowed.example", "blocked.example"]
    profiles = {"sideloading": plistlib.dumps({"PayloadContent": [
        {
            "PayloadIdentifier": "novadev.nexrevokedns.whileinstalling",
            "DNSSettings": {
                "DNSProtocol": "HTTPS",
                "ServerURL": "https://dns.example/dns-query",
                "SupplementalMatchDomains": routing_domains,
            },
        },
        {
            "PayloadIdentifier": "novadev.nexrevokedns.afterinstalling",
            "DNSSettings": {
                "DNSProtocol": "HTTPS",
                "ServerURL": "https://dns.example/ppq/dns-query",
                "SupplementalMatchDomains": routing_domains,
            },
        },
    ]})}

    orchestrator = AntiRevokeOrchestrator(output_dir=str(tmp_path))
    orchestrator.scraper.download_urls = {
        "sideloading": "https://sideloading.example/dns/profile.mobileconfig"
    }
    orchestrator.scraper.domain_lists = {
        "sideloading": ("blocked.example", "dns-check.novadev.vip")
    }
    orchestrator.scraper.enhanced_domain_lists = {
        "sideloading": (
            "blocked.example",
            "ppq.apple.com",
            "ppq-check.novadev.vip",
        )
    }

    selected, enhanced = orchestrator.extract_selected_endpoints(profiles, sources)

    assert selected[0].domains == ("blocked.example",)
    assert enhanced.domains == ("blocked.example", "ppq.apple.com")
    details = orchestrator.source_details["sideloading"]
    assert details["download_url"].endswith("profile.mobileconfig")
    assert details["domain_list_url"].endswith("denylist.txt")
    assert details["enhanced_domain_list_url"].endswith("denylist-ppq.txt")
    assert details["selected_endpoint"]["domains"] == ("blocked.example",)
    assert details["enhanced_endpoint"]["domains"] == (
        "blocked.example",
        "ppq.apple.com",
    )
    assert "dns-check.novadev.vip" not in details["selected_endpoint"]["domains"]
    assert "ppq-check.novadev.vip" not in details["enhanced_endpoint"]["domains"]
    assert "dns-check.novadev.vip" not in details["selected_endpoint"]["domains"]
    assert "ppq-check.novadev.vip" not in details["enhanced_endpoint"]["domains"]
    assert "dns-check.novadev.vip" not in details["selected_endpoint"]["domains"]
    assert "ppq-check.novadev.vip" not in details["enhanced_endpoint"]["domains"]
    assert "dns-check.novadev.vip" not in details["selected_endpoint"]["domains"]
    assert "ppq-check.novadev.vip" not in details["enhanced_endpoint"]["domains"]
    assert "dns-check.novadev.vip" not in details["selected_endpoint"]["domains"]
    assert "ppq-check.novadev.vip" not in details["enhanced_endpoint"]["domains"]


def test_generate_profile_writes_unsigned_xml_mobileconfig(tmp_path):
    orchestrator = AntiRevokeOrchestrator(output_dir=str(tmp_path))
    output_path = tmp_path / "RevokeGuard_Test.mobileconfig"

    generated = orchestrator.generate_profile(
        ["certs.apple.com"],
        "2026-10-20 00:00:00 UTC",
        output_path,
        "RevokeGuard Test",
    )

    assert generated == output_path.as_posix()
    assert output_path.read_bytes().lstrip().startswith(b"<?xml")
    profile = plistlib.loads(output_path.read_bytes())
    assert profile["PayloadType"] == "Configuration"
    assert profile["PayloadContent"][0]["DNSSettings"][
        "SupplementalMatchDomains"
    ] == ["certs.apple.com"]


def test_provider_infrastructure_domains_are_removed_from_reports():
    provider_domains = (
        "applejr.net",
        "dns-check.novadev.vip",
        "ppq-check.novadev.vip",
        "khoindvn.com",
        "vuvankhoi.com",
    )
    report = DomainDiscoveryReport(
        target_domains=(
            "certs.apple.com",
            *provider_domains,
            "ppq.apple.com",
        ),
        blocked_by={
            "certs.apple.com": ("applejr",),
            **{domain: ("source",) for domain in provider_domains},
            "ppq.apple.com": ("sideloading",),
        },
        inconclusive_domains=(),
        endpoint_stats={},
        reference_queries=0,
    )

    filtered, removed = AntiRevokeOrchestrator._filter_provider_domains(report)

    assert removed == provider_domains
    assert filtered.target_domains == ("certs.apple.com", "ppq.apple.com")
    assert filtered.blocked_by == {
        "certs.apple.com": ("applejr",),
        "ppq.apple.com": ("sideloading",),
    }
    assert AntiRevokeOrchestrator._is_provider_domain("applejr.net")
    assert AntiRevokeOrchestrator._is_provider_domain("dns-check.novadev.vip")
    assert not AntiRevokeOrchestrator._is_provider_domain("certs.apple.com")
    assert not AntiRevokeOrchestrator._is_provider_domain("crl.digicert.com")


def test_generate_profile_writes_unsigned_xml_mobileconfig(tmp_path):
    orchestrator = AntiRevokeOrchestrator(output_dir=str(tmp_path))
    output_path = tmp_path / "RevokeGuard_Test.mobileconfig"

    generated = orchestrator.generate_profile(
        ["certs.apple.com"],
        "2026-10-20 00:00:00 UTC",
        output_path,
        "RevokeGuard Test",
    )

    assert generated == output_path.as_posix()
    assert output_path.read_bytes().lstrip().startswith(b"<?xml")
    profile = plistlib.loads(output_path.read_bytes())
    assert profile["PayloadType"] == "Configuration"
    assert profile["PayloadContent"][0]["DNSSettings"][
        "SupplementalMatchDomains"
    ] == ["certs.apple.com"]


def test_generate_profile_writes_unsigned_xml_mobileconfig(tmp_path):
    orchestrator = AntiRevokeOrchestrator(output_dir=str(tmp_path))
    output_path = tmp_path / "RevokeGuard_Test.mobileconfig"

    generated = orchestrator.generate_profile(
        ["certs.apple.com"],
        "2026-10-20 00:00:00 UTC",
        output_path,
        "RevokeGuard Test",
    )

    assert generated == output_path.as_posix()
    assert output_path.read_bytes().lstrip().startswith(b"<?xml")
    profile = plistlib.loads(output_path.read_bytes())
    assert profile["PayloadType"] == "Configuration"
    assert profile["PayloadContent"][0]["DNSSettings"][
        "SupplementalMatchDomains"
    ] == ["certs.apple.com"]


def test_generate_profile_writes_unsigned_xml_mobileconfig(tmp_path):
    orchestrator = AntiRevokeOrchestrator(output_dir=str(tmp_path))
    output_path = tmp_path / "RevokeGuard_Test.mobileconfig"

    generated = orchestrator.generate_profile(
        ["certs.apple.com"],
        "2026-10-20 00:00:00 UTC",
        output_path,
        "RevokeGuard Test",
    )

    assert generated == output_path.as_posix()
    assert output_path.read_bytes().lstrip().startswith(b"<?xml")
    profile = plistlib.loads(output_path.read_bytes())
    assert profile["PayloadType"] == "Configuration"
    assert profile["PayloadContent"][0]["DNSSettings"][
        "SupplementalMatchDomains"
    ] == ["certs.apple.com"]


def test_generate_profile_writes_unsigned_xml_mobileconfig(tmp_path):
    orchestrator = AntiRevokeOrchestrator(output_dir=str(tmp_path))
    output_path = tmp_path / "RevokeGuard_Test.mobileconfig"

    generated = orchestrator.generate_profile(
        ["certs.apple.com"],
        "2026-10-20 00:00:00 UTC",
        output_path,
        "RevokeGuard Test",
    )

    assert generated == output_path.as_posix()
    assert output_path.read_bytes().lstrip().startswith(b"<?xml")
    profile = plistlib.loads(output_path.read_bytes())
    assert profile["PayloadType"] == "Configuration"
    assert profile["PayloadContent"][0]["DNSSettings"][
        "SupplementalMatchDomains"
    ] == ["certs.apple.com"]
