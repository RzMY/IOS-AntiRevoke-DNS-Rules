# Operations

## Local verification

The project currently uses the existing `mine` Conda environment:

```powershell
conda run -n mine python -m pip install -r requirements-dev.txt
conda run -n mine python -m pytest -q
conda run -n mine python main.py --workers 20
```

Without signing credentials, local execution writes an unsigned XML plist using the `.mobileconfig` extension. Inspect it with:

```powershell
conda run -n mine python -c "import plistlib; p=plistlib.load(open('output/RevokeGuard_Auto-Sync.mobileconfig','rb')); print(len(p['PayloadContent'][0]['DNSSettings']['SupplementalMatchDomains']))"
```

Inspect enhanced output with:

```powershell
conda run -n mine python -c "import plistlib; p=plistlib.load(open('output/enhanced/RevokeGuard_Enhanced.mobileconfig','rb')); print(p['PayloadDisplayName']); print(len(p['PayloadContent'][0]['DNSSettings']['SupplementalMatchDomains']))"
Get-Content output/enhanced/enhanced-domains.txt
```

## GitHub Actions

`.github/workflows/daily_update.yml` runs daily at 00:00 UTC and can also be started manually.

Required repository Secrets:

| Secret | Content |
| --- | --- |
| `SSL_CERT` | PEM certificate followed by any intermediate chain certificates |
| `SSL_KEY` | Matching PEM private key |

The Action performs these gates before committing:

1. Install runtime and test dependencies.
2. Run the unit test suite.
3. Validate the certificate and private key with OpenSSL.
4. Run the live discovery pipeline.
5. Check that every normal and enhanced output is non-empty.
6. Verify both generated mobileconfig CMS signatures.
7. Commit only `output/` changes.

## Updating an upstream source

Source definitions are in `PROFILE_SOURCES` in `main.py`.

When a page changes:

1. Update its XPath only after confirming that it points to the intended `.mobileconfig` link.
2. Run `python main.py --debug` in the `mine` environment.
3. Inspect `output/metadata.json` and confirm the resolved download URL and selected endpoints. A non-empty `domains` list means the payload was used directly; its `profile_domains` statistic records the domain count without DNS queries.
4. If a profile contains multiple DNS payloads, set `preferred_payload_identifier` and `enhanced_payload_identifier` explicitly instead of relying on page order.
5. Add or update a unit test for any parser behavior change.

## Common failures

`XPath did not match any element`

The upstream page layout changed. Update the source XPath and verify that the target response is a mobileconfig rather than HTML.

`Profile ... contains no valid HTTPS DNS endpoint or domain list`

The downloaded profile has neither a usable `DNSSettings.SupplementalMatchDomains` list nor a valid HTTPS endpoint. Inspect the decoded plist before changing selection logic. A valid explicit list is sufficient even if the payload has no endpoint or its URL points to an ordinary website.

`DNS queries failed; refusing partial output`

At least one upstream endpoint or the local network failed after retries. Rerun later; do not convert this condition into blocked domains.

`preferred payload ... no longer exists`

The Sideloading profile changed payload identifiers. Inspect all `discovered_endpoints` and select both the `whileinstalling` normal mode and `afterinstalling` enhanced mode explicitly.

`Failed to sign the iOS configuration profile`

Confirm that `SSL_CERT` and `SSL_KEY` match, the certificate is PEM encoded, and the full chain order places the leaf certificate first.

## Release sanity checks

After a successful run, verify:

```powershell
git diff -- output/domains.txt output/enhanced/enhanced-domains.txt output/metadata.json
conda run -n mine python -m pytest -q
```

Large candidate-count changes, all domains becoming targets, or one endpoint reporting mostly negative results should be treated as upstream or parser regressions rather than normal rule updates. Confirm that enhanced proxy files contain only domains absent from `output/domains.txt`, while the enhanced iOS profile contains both sets.
