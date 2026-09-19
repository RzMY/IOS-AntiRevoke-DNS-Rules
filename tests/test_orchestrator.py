import json
import plistlib

import pytest

from main import AntiRevokeOrchestrator
from utils.dns_probe import Resolution


@pytest.mark.parametrize("enhanced_is_explicit", [False, True])
def test_pipeline_uses_profile_domains_and_preserves_payload_modes(
    tmp_path, monkeypatch, enhanced_is_explicit,
):
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
                    [" SHARED.EXAMPLE. ", "outside.example", "shared.example"]),
        ]}),
        "multi": plistlib.dumps({"PayloadContent": [
            payload("unselected", "https://unused.example", ["ignored.example"]),
            payload("enhanced", "https://enhanced.example/dns-query",
                    ["extra.example", "shared.example"] if enhanced_is_explicit else None),
            payload("normal", "https://normal.example/dns-query"),
        ]}),
    }
    candidates = ["shared.example", "blocked.example", "extra.example"] + [
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
    ]
    enhanced = plistlib.loads((tmp_path / "enhanced/RevokeGuard_Enhanced.mobileconfig").read_bytes())
    assert enhanced["PayloadContent"][0]["DNSSettings"]["SupplementalMatchDomains"] == [
        "blocked.example", "extra.example", "outside.example", "shared.example",
    ]
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["normal_discovery"]["blocked_by"]["shared.example"] == ["explicit", "multi"]
    assert metadata["normal_discovery"]["endpoint_stats"]["explicit"] == {"profile_domains": 2}
    assert metadata["profile_sources"]["explicit"]["selected_endpoint"]["domains"] == [
        "outside.example", "shared.example",
    ]
