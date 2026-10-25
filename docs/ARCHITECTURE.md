# Architecture

## Data flow

```text
Apple official host tables
            |
            v
 normalized candidate domains
            |
            +-----------------------------+
            |                             |
            v                             v
 normal endpoint group             enhanced endpoint
 - Khoindvn                        - Sideloading afterinstalling
 - AppleJr
 - Sideloading whileinstalling
            |                             |
            v                             v
 normal target union              enhanced endpoint targets
            |                             |
            |              partition discovered targets
            |                             |
            +---------------+-------------+
                            |
             +--------------+--------------+
             |                             |
             v                             v
 output/ normal artifacts       output/enhanced/ artifacts
 - normal proxy rules           - proxy rules: extra only
             |                             |
             +---------------+-------------+
                             |
                             v
       output/RevokeGuard.mobileconfig
       - normal DNS payload: normal domains
       - enhanced DNS payload: normal + extra domains
```

Selected DNS payloads with a non-empty domain list in `DNSSettings.SupplementalMatchDomains` contribute those domains directly to their normal or enhanced result set unless the source configures `domain_list_url` or `enhanced_domain_list_url`. In that case the downloaded plain-text list replaces the profile match-domain list for that mode. This matters for Sideloading, whose current profile uses one broad `SupplementalMatchDomains` routing scope that includes allowlist and helper domains. Lists are normalized and deduplicated; domains outside Apple's candidate tables are retained. Empty, catch-all, and invalid entries are ignored. Domain names in web clips, server addresses, or on-demand connection exceptions are not treated as target lists.

Provider-owned domains used only for upstream connectivity or status checks (for example `applejr.net`, `*.novadev.vip`, `khoindvn.com`, and `vuvankhoi.com`) are removed from discovery reports before validation and publication. The suffixes are defined in `PROVIDER_ONLY_DOMAIN_SUFFIXES` in `main.py`.

Publication reserves `ppq.apple.com` for enhanced mode, even when a normal source's explicit list or DNS response includes it. Let `N` be the normal discovery union, `E` the enhanced discovery result, and `R` the `ENHANCED_ONLY_DOMAINS` set in `main.py`. Published normal domains are `N - R`; enhanced proxy domains are `(N ∪ E) - (N - R)`; the enhanced DNS payload in the combined iOS profile contains `N ∪ E`. Reserved domains are only published when discovered in at least one source. Other overlapping domains remain normal-only proxy rules.

Payloads without an explicit domain list use the probing flow above. All NXDOMAIN or empty answers are checked against a public reference DoH resolver. A probed domain is published only when the upstream answer differs from a valid public answer, or when the upstream returns a non-global address such as `0.0.0.0`.

## Endpoint selection

The three mobileconfig files are downloaded and decoded on every run. Endpoint URLs are never hardcoded as runtime inputs; payload identifiers select the intended mode from the current profile.

| Source | Role | Selection | Target domains |
| --- | --- | --- | --- |
| Khoindvn | Normal | First DNS payload with explicit domains or a valid HTTPS endpoint | Profile `SupplementalMatchDomains` |
| AppleJr | Normal | First DNS payload with explicit domains or a valid HTTPS endpoint | Profile `SupplementalMatchDomains` |
| Sideloading | Normal | `nexsideloading.nexrevokedns.duringinstall`, then legacy `novadev.nexrevokedns.whileinstalling` and `novadev.nexdns.whileinstalling` | Upstream `denylist.txt` |
| Sideloading | Enhanced | `nexsideloading.nexrevokedns.afterinstall`, then legacy `novadev.nexrevokedns.afterinstalling` and `novadev.nexdns.afterinstalling` | Upstream `denylist-ppq.txt` |

The Sideloading profile now uses the same broad match-domain list for both modes, including allowlist and helper domains, so those match domains are not published directly. The mode-specific deny lists override them. The enhanced endpoint is intentionally excluded from the normal endpoint union. Its contribution is calculated independently so proxy users can toggle the enhanced rule set without duplicating normal rules.

## Components

`utils/scraper.py`

- Downloads Apple host data and all required source profiles.
- Extracts domains only from recognized `Host` or `主机` tables.
- Resolves page XPaths to the current mobileconfig download URLs.
- Downloads optional plain-text domain lists for sources whose profile match domains are only a routing scope.
- Fails when a required page, link, or profile cannot be retrieved.

`utils/crypto_handler.py`

- Parses unsigned plist profiles or verifies CMS-signed DER mobileconfig files.
- Extracts HTTPS DNS endpoints, explicit match-domain lists, and payload identifiers.
- Creates one unsigned iOS profile containing separately named normal and enhanced DNS payloads.
- Writes XML plists using the `.mobileconfig` extension; signing credentials are not required.

`utils/dns_probe.py`

- Sends RFC 8484 A and AAAA queries using DNS wire format over HTTPS.
- Skips upstream and reference queries for payloads with explicit domain lists and merges their domains with probed results, preserving source attribution.
- Treats non-global addresses as explicit filtering results.
- Uses the reference resolver to distinguish filtering from legitimate NODATA or NXDOMAIN.
- Rejects partial output when any required query fails after retries.

`utils/rule_converter.py`

- Preserves the existing normal filenames.
- Supports an independent output directory, filename prefix, and domain-list name for enhanced rules.

`main.py`

- Selects normal and enhanced payloads from the decoded profiles.
- Runs normal and enhanced discovery independently.
- Partitions discovered targets, reserving `ppq.apple.com` for enhanced mode regardless of source.
- Generates normal rules and the profile's normal DNS payload from normal targets minus enhanced-only domains.
- Generates enhanced proxy rules from enhanced extras only.
- Generates the same profile's enhanced DNS payload from `normal targets + enhanced extras`.
- Removes the obsolete standalone enhanced mobileconfig after successful generation.

## Output contract

`output/` contains the existing normal rule filenames, root metadata, and the single `RevokeGuard.mobileconfig`. Users download this profile through the [dedicated download link](https://reject.rzmy.dpdns.org/download). That profile contains exactly two `com.apple.dnsSettings.managed` payloads:

| Mode | Payload identifier | Display name | Domains |
| --- | --- | --- | --- |
| Normal | `com.revokeGuard.dns.normal` | `RevokeGuard Normal - Use during install` | Published normal domains |
| Enhanced | `com.revokeGuard.dns.enhanced` | `RevokeGuard Enhanced - Use after installing` | Normal + enhanced extra domains |

Both payloads use the existing `https://reject.rzmy.dpdns.org/dns-query` backend and retain their own `SupplementalMatchDomains`. This mirrors Sideloading's two-payload structure: users select one DNS mode in iOS Settings. The enhanced payload is a superset, not an extra-only configuration. The outer identifier is stable (`com.revokeGuard`) so future downloads can replace the combined profile; each payload has a unique UUID. Users migrating from older profiles with random identifiers must remove those old profiles once. Installation and switching instructions are in [README](../README.md#iosipados-profile-usage--描述文件使用方法).

`output/enhanced/` contains:

- `RevokeGuard_Enhanced_*.txt`: enhanced extra domains only.
- `enhanced-domains.txt`: plain enhanced extra-domain list.
- `metadata.json`: enhanced endpoint, extra-domain count, and enhanced DNS payload domain count. Its `iOS Profile` path points to the combined profile in `output/`.

The former `output/enhanced/RevokeGuard_Enhanced.mobileconfig` is no longer published.

## Safety gates

- All three source profiles are required.
- Both Sideloading payload identifiers must exist.
- Configured upstream deny lists must download and contain domains.
- Provider-owned connectivity and status-check domains are removed from the final target sets.
- Apple must yield at least 100 candidate domains.
- Normal and enhanced target sets must each remain below 50% of candidates.
- Every DNS query must complete after retries.
- Normal discovery and enhanced endpoint discovery must both produce targets.
- All normal and enhanced artifacts must be generated.
- GitHub Actions verifies the single mobileconfig is a valid plist with exactly two distinct DNS payloads, checks each payload against its domain lists, and confirms the obsolete enhanced mobileconfig is absent before committing.

## Metadata

Root `output/metadata.json` uses schema version 4 and records:

- Apple source and candidate count.
- Every discovered profile endpoint.
- Each payload's normalized `domains` list (empty for payloads requiring probing).
- `domain_list_url` and `enhanced_domain_list_url` when a source overrides profile match domains.
- Selected normal endpoints and the enhanced endpoint after any domain-list override.
- Normal discovery details, including `profile_domains` counts for sources used directly without probing. Provider-only domains are absent from `target_domains` and `blocked_by`.
- Original normal discovery count (`target_domains`) and source attribution, plus the published normal count (`published_target_domains`) and domains reassigned by publication policy (`moved_to_enhanced`).
- Enhanced endpoint targets, additional domains, and enhanced DNS payload domain count (the existing `merged_profile_domains` field).
- Normal and enhanced artifact paths. Both groups' `iOS Profile` entries reference `output/RevokeGuard.mobileconfig`.


### Sideloading NexRevokeDNS migration (2026-10-20)

The Sideloading page now serves `nexrevokedns.mobileconfig` instead of `nexdns.mobileconfig` and renamed the DNS payload identifiers from `novadev.nexdns.*` to `novadev.nexrevokedns.*`. The page XPath remains valid. Both payloads now carry the same broad `SupplementalMatchDomains` routing set and new `dns.sideloading.net` DoH URLs. That routing set includes allowlist and helper domains, so it is not used as the published target list. The source configuration downloads `denylist.txt` for normal mode and `denylist-ppq.txt` for enhanced mode and uses those mode-specific sets instead. Selector configuration accepts an ordered identifier list; the current namespace wins, with the legacy namespace retained as a rollback-compatible fallback.

### Sideloading NexSideloading payload migration (2026-10-23)

The same CMS-signed `nexrevokedns.mobileconfig` now identifies its normal payload as `nexsideloading.nexrevokedns.duringinstall` and its enhanced payload as `nexsideloading.nexrevokedns.afterinstall`. Both the namespace and the mode suffixes changed; the page link, DoH URLs, and published deny-list URLs remain valid. These new identifiers take priority, with both previous generations retained as exact fallbacks. Unknown or missing modes still fail rather than selecting another payload by position. `test_current_sideloading_profile_uses_mode_lists` in `tests/test_orchestrator.py` embeds the relevant decoded upstream fields, exercises both modes independent of payload order, and verifies that routing-only domains are not published. The test is self-contained so a clean CI checkout does not depend on an untracked fixture file.
