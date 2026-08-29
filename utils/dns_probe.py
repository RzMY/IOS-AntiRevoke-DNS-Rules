"""DNS-over-HTTPS probing and target-domain discovery."""

from __future__ import annotations

import concurrent.futures
import ipaddress
import logging
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

import dns.message
import dns.rcode
import dns.rdatatype
import dns.exception
import requests

from utils.crypto_handler import DnsEndpoint

logger = logging.getLogger(__name__)


class DnsProbeError(RuntimeError):
    """Raised when DNS transport or server errors make the run unreliable."""


@dataclass(frozen=True)
class Resolution:
    """Combined A and AAAA result for one domain and one endpoint."""

    state: str
    addresses: Tuple[str, ...]
    rcodes: Tuple[str, ...]


@dataclass(frozen=True)
class DomainDiscoveryReport:
    """Target domains plus enough diagnostics for build metadata."""

    target_domains: Tuple[str, ...]
    blocked_by: Dict[str, Tuple[str, ...]]
    inconclusive_domains: Tuple[str, ...]
    endpoint_stats: Dict[str, Dict[str, int]]
    reference_queries: int


class DoHDomainProbe:
    """Query candidate domains against upstream filtering DoH endpoints."""

    QUERY_TYPES = ("A", "AAAA")

    def __init__(
        self,
        reference_url: str,
        timeout: int = 15,
        max_retries: int = 3,
        workers: int = 20,
    ):
        self.reference_url = reference_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.workers = workers
        self._thread_local = threading.local()

    def _session(self) -> requests.Session:
        if not hasattr(self._thread_local, "session"):
            session = requests.Session()
            session.headers.update(
                {"User-Agent": "IOS-AntiRevoke-DNS-Rules/2.0"}
            )
            self._thread_local.session = session
        return self._thread_local.session

    def _query_record(self, endpoint_url: str, domain: str, query_type: str):
        query = dns.message.make_query(domain, query_type)
        payload = query.to_wire()
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._session().post(
                    endpoint_url,
                    data=payload,
                    headers={
                        "Accept": "application/dns-message",
                        "Content-Type": "application/dns-message",
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                dns_response = dns.message.from_wire(response.content)
                if not query.is_response(dns_response):
                    raise ValueError("DoH response does not match the query")

                rcode = dns_response.rcode()
                if rcode in {
                    dns.rcode.NOERROR,
                    dns.rcode.NXDOMAIN,
                }:
                    return dns_response

                raise ValueError(
                    f"DoH server returned {dns.rcode.to_text(rcode)}"
                )
            except (
                requests.RequestException,
                dns.exception.DNSException,
                ValueError,
            ) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(0.25 * (2 ** (attempt - 1)))

        raise DnsProbeError(
            f"Failed to query {domain} via {endpoint_url}: {last_error}"
        )

    @staticmethod
    def classify_responses(responses: Sequence[dns.message.Message]) -> Resolution:
        addresses: List[str] = []
        rcodes: List[str] = []

        for response in responses:
            rcodes.append(dns.rcode.to_text(response.rcode()))
            for rrset in response.answer:
                if rrset.rdtype in {dns.rdatatype.A, dns.rdatatype.AAAA}:
                    addresses.extend(str(rdata) for rdata in rrset)

        unique_addresses = tuple(sorted(set(addresses)))
        if unique_addresses:
            if any(
                not ipaddress.ip_address(address).is_global
                for address in unique_addresses
            ):
                state = "invalid_address"
            else:
                state = "valid"
        else:
            state = "negative"

        return Resolution(
            state=state,
            addresses=unique_addresses,
            rcodes=tuple(rcodes),
        )

    def resolve(self, endpoint_url: str, domain: str) -> Resolution:
        responses = [
            self._query_record(endpoint_url, domain, query_type)
            for query_type in self.QUERY_TYPES
        ]
        return self.classify_responses(responses)

    def _resolve_many(
        self,
        tasks: Iterable[Tuple[str, str, str]],
    ) -> Dict[Tuple[str, str], Resolution]:
        task_list = list(tasks)
        results: Dict[Tuple[str, str], Resolution] = {}
        errors: List[str] = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.workers
        ) as executor:
            future_map = {
                executor.submit(self.resolve, endpoint_url, domain): (
                    endpoint_name,
                    domain,
                )
                for endpoint_name, endpoint_url, domain in task_list
            }
            for future in concurrent.futures.as_completed(future_map):
                endpoint_name, domain = future_map[future]
                try:
                    results[(endpoint_name, domain)] = future.result()
                except DnsProbeError as exc:
                    errors.append(str(exc))

        if errors:
            samples = "\n".join(errors[:10])
            raise DnsProbeError(
                f"{len(errors)} DNS queries failed; refusing partial output:\n{samples}"
            )

        return results

    def discover(
        self,
        domains: Sequence[str],
        endpoints: Sequence[DnsEndpoint],
    ) -> DomainDiscoveryReport:
        if not domains:
            raise DnsProbeError("No Apple candidate domains were provided")
        if not endpoints:
            raise DnsProbeError("No upstream DoH endpoints were provided")

        logger.info(
            "Querying %s candidates against %s upstream endpoints",
            len(domains),
            len(endpoints),
        )
        upstream_results = self._resolve_many(
            (endpoint.source, endpoint.url, domain)
            for endpoint in endpoints
            for domain in domains
        )

        negative_domains = {
            domain
            for endpoint in endpoints
            for domain in domains
            if upstream_results[(endpoint.source, domain)].state == "negative"
        }
        reference_results = self._resolve_many(
            ("reference", self.reference_url, domain)
            for domain in sorted(negative_domains)
        )

        blocked_by = defaultdict(set)
        inconclusive = set()
        endpoint_counters: Dict[str, Counter] = {
            endpoint.source: Counter() for endpoint in endpoints
        }

        for endpoint in endpoints:
            for domain in domains:
                resolution = upstream_results[(endpoint.source, domain)]
                endpoint_counters[endpoint.source][resolution.state] += 1

                if resolution.state == "invalid_address":
                    blocked_by[domain].add(endpoint.source)
                    continue
                if resolution.state != "negative":
                    continue

                reference = reference_results[("reference", domain)]
                if reference.state == "valid":
                    blocked_by[domain].add(endpoint.source)
                else:
                    inconclusive.add(domain)

        report = DomainDiscoveryReport(
            target_domains=tuple(sorted(blocked_by)),
            blocked_by={
                domain: tuple(sorted(sources))
                for domain, sources in sorted(blocked_by.items())
            },
            inconclusive_domains=tuple(sorted(inconclusive - set(blocked_by))),
            endpoint_stats={
                source: dict(sorted(counter.items()))
                for source, counter in endpoint_counters.items()
            },
            reference_queries=len(reference_results),
        )
        logger.info(
            "Discovered %s target domains (%s inconclusive candidates)",
            len(report.target_domains),
            len(report.inconclusive_domains),
        )
        return report
