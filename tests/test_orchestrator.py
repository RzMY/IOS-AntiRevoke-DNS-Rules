import json
import plistlib

import pytest

from main import AntiRevokeOrchestrator
from utils.dns_probe import Resolution


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
    assert "ppq.apple.com" not in normal["PayloadContent"][0]["DNSSettings"]["SupplementalMatchDomains"]
    assert "host, ppq.apple.com, reject" not in (tmp_path / "RevokeGuard_QuantumultX.txt").read_text()
    assert ("host, ppq.apple.com, reject" in (
        tmp_path / "enhanced/RevokeGuard_Enhanced_QuantumultX.txt"
    ).read_text()) == bool(expected_ppq)
    enhanced = plistlib.loads((tmp_path / "enhanced/RevokeGuard_Enhanced.mobileconfig").read_bytes())
    assert enhanced["PayloadContent"][0]["DNSSettings"]["SupplementalMatchDomains"] == sorted([
        "blocked.example", "extra.example", "outside.example", "shared.example",
    ] + expected_ppq)
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    moved_ppq = ppq_source in {"normal", "both", "normal_probe"}
    assert metadata["schema_version"] == 4
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
    assert metadata["normal_discovery"]["blocked_by"]["shared.example"] == ["explicit", "multi"]
    assert metadata["normal_discovery"]["endpoint_stats"]["explicit"] == {"profile_domains": 2 + len(normal_ppq)}
    assert metadata["profile_sources"]["explicit"]["selected_endpoint"]["domains"] == sorted([
        "outside.example", "shared.example",
    ] + normal_ppq)
