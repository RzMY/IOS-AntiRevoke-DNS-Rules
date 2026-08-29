import dns.message
import dns.rcode
import dns.rrset

from utils.crypto_handler import DnsEndpoint
from utils.dns_probe import DoHDomainProbe, Resolution


def make_response(address=None, rcode=dns.rcode.NOERROR):
    query = dns.message.make_query("example.com", "A")
    response = dns.message.make_response(query)
    response.set_rcode(rcode)
    if address:
        response.answer.append(
            dns.rrset.from_text("example.com.", 60, "IN", "A", address)
        )
    return response


def test_classify_responses_distinguishes_valid_invalid_and_negative():
    valid = DoHDomainProbe.classify_responses(
        [make_response("17.253.144.10"), make_response()]
    )
    invalid = DoHDomainProbe.classify_responses(
        [make_response("0.0.0.0"), make_response()]
    )
    negative = DoHDomainProbe.classify_responses(
        [make_response(rcode=dns.rcode.NXDOMAIN), make_response()]
    )

    assert valid.state == "valid"
    assert invalid.state == "invalid_address"
    assert negative.state == "negative"


def test_discover_uses_union_and_reference_for_negative_results(monkeypatch):
    probe = DoHDomainProbe("https://reference.example/dns-query")
    endpoints = [
        DnsEndpoint("source-a", "https://a.example/dns-query", "a", "A"),
        DnsEndpoint("source-b", "https://b.example/dns-query", "b", "B"),
    ]
    domains = ["clean.example", "explicit.example", "missing.example", "ambiguous.example"]

    upstream = {
        ("source-a", "clean.example"): Resolution("valid", ("17.1.1.1",), ("NOERROR",)),
        ("source-a", "explicit.example"): Resolution("invalid_address", ("0.0.0.0",), ("NOERROR",)),
        ("source-a", "missing.example"): Resolution("negative", (), ("NXDOMAIN",)),
        ("source-a", "ambiguous.example"): Resolution("negative", (), ("NOERROR",)),
        ("source-b", "clean.example"): Resolution("valid", ("17.1.1.1",), ("NOERROR",)),
        ("source-b", "explicit.example"): Resolution("valid", ("17.1.1.1",), ("NOERROR",)),
        ("source-b", "missing.example"): Resolution("valid", ("17.1.1.1",), ("NOERROR",)),
        ("source-b", "ambiguous.example"): Resolution("valid", ("17.1.1.1",), ("NOERROR",)),
    }
    reference = {
        ("reference", "missing.example"): Resolution("valid", ("17.2.2.2",), ("NOERROR",)),
        ("reference", "ambiguous.example"): Resolution("negative", (), ("NXDOMAIN",)),
    }

    def fake_resolve_many(tasks):
        task_list = list(tasks)
        if task_list and task_list[0][0] == "reference":
            return reference
        return upstream

    monkeypatch.setattr(probe, "_resolve_many", fake_resolve_many)
    report = probe.discover(domains, endpoints)

    assert report.target_domains == ("explicit.example", "missing.example")
    assert report.blocked_by["explicit.example"] == ("source-a",)
    assert report.blocked_by["missing.example"] == ("source-a",)
    assert report.inconclusive_domains == ("ambiguous.example",)
