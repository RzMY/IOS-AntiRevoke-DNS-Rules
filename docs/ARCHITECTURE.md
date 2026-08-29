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
            |              extra = enhanced - normal
            |                             |
            +---------------+-------------+
                            |
             +--------------+--------------+
             |                             |
             v                             v
 output/ normal artifacts       output/enhanced/ artifacts
 - normal proxy rules           - proxy rules: extra only
 - normal iOS profile           - iOS profile: normal + extra
```

All NXDOMAIN or empty answers are checked against a public reference DoH resolver. A domain is published only when the upstream answer differs from a valid public answer, or when the upstream returns a non-global address such as `0.0.0.0`.

## Endpoint selection

The three mobileconfig files are downloaded and decoded on every run. Endpoint URLs are never hardcoded as runtime inputs; payload identifiers select the intended mode from the current profile.

| Source | Role | Selection |
| --- | --- | --- |
| Khoindvn | Normal | First HTTPS DNS payload |
| AppleJr | Normal | First HTTPS DNS payload |
| Sideloading | Normal | `novadev.nexdns.whileinstalling` |
| Sideloading | Enhanced | `novadev.nexdns.afterinstalling` |

The enhanced endpoint is intentionally excluded from the normal endpoint union. Its contribution is calculated independently so proxy users can toggle the enhanced rule set without duplicating normal rules.

## Components

`utils/scraper.py`

- Downloads Apple host data and all required source profiles.
- Extracts domains only from recognized `Host` or `主机` tables.
- Resolves page XPaths to the current mobileconfig download URLs.
- Fails when a required page, link, or profile cannot be retrieved.

`utils/crypto_handler.py`

- Parses unsigned plist profiles or verifies CMS-signed DER mobileconfig files.
- Extracts HTTPS DNS endpoints and payload identifiers.
- Creates separately named normal and enhanced iOS profiles.
- Signs generated profiles with the configured certificate chain.

`utils/dns_probe.py`

- Sends RFC 8484 A and AAAA queries using DNS wire format over HTTPS.
- Treats non-global addresses as explicit filtering results.
- Uses the reference resolver to distinguish filtering from legitimate NODATA or NXDOMAIN.
- Rejects partial output when any required query fails after retries.

`utils/rule_converter.py`

- Preserves the existing normal filenames.
- Supports an independent output directory, filename prefix, and domain-list name for enhanced rules.

`main.py`

- Selects normal and enhanced payloads from the decoded profiles.
- Runs normal and enhanced discovery independently.
- Computes `enhanced extra = enhanced endpoint targets - normal targets`.
- Generates normal rules from normal targets.
- Generates enhanced proxy rules from enhanced extras only.
- Generates the enhanced iOS profile from `normal targets + enhanced extras`.

## Output contract

`output/` contains the backward-compatible normal files and root metadata.

`output/enhanced/` contains:

- `RevokeGuard_Enhanced.mobileconfig`: merged normal and enhanced domains.
- `RevokeGuard_Enhanced_*.txt`: enhanced extra domains only.
- `enhanced-domains.txt`: plain enhanced extra-domain list.
- `metadata.json`: enhanced endpoint, extra-domain count, and merged profile count.

## Safety gates

- All three source profiles are required.
- Both Sideloading payload identifiers must exist.
- Apple must yield at least 100 candidate domains.
- Normal and enhanced target sets must each remain below 50% of candidates.
- Every DNS query must complete after retries.
- Normal discovery and enhanced endpoint discovery must both produce targets.
- All normal and enhanced artifacts must be generated.
- GitHub Actions verifies both CMS signatures before committing.

## Metadata

Root `output/metadata.json` uses schema version 3 and records:

- Apple source and candidate count.
- Every discovered profile endpoint.
- Selected normal endpoints and the enhanced endpoint.
- Normal discovery details.
- Enhanced endpoint targets, additional domains, and merged profile count.
- Normal and enhanced artifact paths.
