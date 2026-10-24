# Operations

## Local verification

The project currently uses the existing `mine` Conda environment:

```powershell
conda run -n mine python -m pip install -r requirements-dev.txt
conda run -n mine python -m pytest tests -q
conda run -n mine python main.py --workers 20
```

Local execution writes one unsigned XML `.mobileconfig` containing normal and enhanced DNS payloads. Inspect both modes with:

```powershell
conda run -n mine python -c "import plistlib; p=plistlib.load(open('output/RevokeGuard_Auto-Sync.mobileconfig','rb')); assert len(p['PayloadContent']) == 2; print([(d['PayloadDisplayName'], len(d['DNSSettings']['SupplementalMatchDomains'])) for d in p['PayloadContent']])"
```

Inspect the enhanced extra-domain rules with:

```powershell
Get-Content output/enhanced/enhanced-domains.txt
```

## Installing and switching the profile

See [README: profile usage](../README.md#iosipados-profile-usage--描述文件使用方法) for the full bilingual guide. Download `output/RevokeGuard_Auto-Sync.mobileconfig` in Safari, install it through Settings, then open **Settings → General → VPN & Device Management → DNS**. Select **RevokeGuard Normal - Use during install** for certificate setup, app installation, and the first launch. After a successful first launch, select **RevokeGuard Enhanced - Use after installing** when enhanced protection is needed. Switch back to Normal before installing or re-signing another app; reconnect Wi-Fi or toggle cellular data after each switch.

Remove older standalone RevokeGuard profiles before migrating to this combined profile. Mode switches do not require removing or reinstalling it. Daily repository generation does not update installed match-domain lists automatically: download and install the latest combined profile to refresh them, then verify the selected mode.

## GitHub Actions

`.github/workflows/daily_update.yml` runs daily at 00:00 UTC and can also be started manually.

No signing secrets are required. The workflow produces one unsigned XML `.mobileconfig` file.

The Action performs these gates before committing:

1. Install runtime and test dependencies.
2. Run the unit test suite.
3. Run the live discovery pipeline.
4. Check that every normal and enhanced output is non-empty.
5. Parse the combined mobileconfig, verify exactly two DNS payloads and their identifiers, and compare their domains with the published normal and enhanced lists. Verify that the obsolete standalone enhanced profile is absent.
6. Commit only `output/` changes.

## Updating an upstream source

Source definitions are in `PROFILE_SOURCES` in `main.py`.

When a page changes:

1. Update its XPath only after confirming that it points to the intended `.mobileconfig` link.
2. Run `python main.py --debug` in the `mine` environment.
3. Inspect `output/metadata.json` and confirm the resolved download URL, configured domain-list URLs, and selected endpoints. A non-empty `domains` list means the payload was used directly; its `profile_domains` statistic records the domain count without DNS queries.
4. If a profile contains multiple DNS payloads, set `preferred_payload_identifiers` and `enhanced_payload_identifiers` explicitly instead of relying on page order. Lists are tried in order; keep the previous upstream identifiers as fallbacks during rebrands.
5. If `SupplementalMatchDomains` is only a routing scope that mixes deny and allow entries, configure `domain_list_url` and `enhanced_domain_list_url` to the upstream mode-specific deny lists. These lists replace the profile match domains as the published targets.
6. Add or update a unit test for any parser behavior change.

## Common failures

`XPath did not match any element`

The upstream page layout changed. Update the source XPath and verify that the target response is a mobileconfig rather than HTML.

`Profile ... contains no valid HTTPS DNS endpoint or domain list`

The downloaded profile has neither a usable `DNSSettings.SupplementalMatchDomains` list nor a valid HTTPS endpoint. Inspect the decoded plist before changing selection logic. A valid explicit list is sufficient even if the payload has no endpoint or its URL points to an ordinary website.

`DNS queries failed; refusing partial output`

At least one upstream endpoint or the local network failed after retries. Rerun later; do not convert this condition into blocked domains.

`Profile ... no longer contains any preferred payload: ...`

The Sideloading profile changed payload identifiers. Inspect the decoded profile and select both modes explicitly. As of 2026-10-23, normal mode uses `nexsideloading.nexrevokedns.duringinstall` and enhanced mode uses `nexsideloading.nexrevokedns.afterinstall`. The previous `novadev.nexrevokedns.whileinstalling` / `.afterinstalling` and `novadev.nexdns.whileinstalling` / `.afterinstalling` identifiers remain as ordered fallbacks. A failed run does not update metadata, so use the downloaded profile to inspect new identifiers rather than relying on stale `output/metadata.json`. Keep the mode-specific deny-list overrides: the broad profile routing list includes allow entries.

`Domain-list URL ...`

The configured upstream plain-text deny list moved or became unavailable. Confirm the current links on the Sideloading DNS page and update `domain_list_url` or `enhanced_domain_list_url` in `PROFILE_SOURCES`.

## Release sanity checks

After a successful run, verify:

```powershell
git diff -- output/domains.txt output/enhanced/enhanced-domains.txt output/metadata.json
conda run -n mine python -m pytest tests -q
```

Large candidate-count changes, all domains becoming targets, or one endpoint reporting mostly negative results should be treated as upstream or parser regressions rather than normal rule updates. Confirm that enhanced proxy files contain only domains absent from `output/domains.txt`, while the combined profile's normal DNS payload matches `output/domains.txt` and its enhanced DNS payload contains both sets. Both metadata groups must reference the same profile path, and `output/enhanced/RevokeGuard_Enhanced.mobileconfig` must be absent. Also confirm that provider-owned connectivity domains such as `applejr.net`, `*.novadev.vip`, `khoindvn.com`, and `vuvankhoi.com` do not appear in any generated rule or profile.

When any source discovers `ppq.apple.com`, verify that it appears only in the enhanced proxy files and the combined profile's enhanced DNS payload, never in the normal rules or normal DNS payload. Root metadata preserves raw discovery evidence: `normal_discovery.blocked_by` may contain PPQ, while `moved_to_enhanced` records its reassignment and `published_target_domains` matches the normal output count.

### PPQ classification regression (2026-10-03)

Commit `f3e1bad` added direct use of explicit profile domain lists. The first affected generated output was `29e8d80`: AppleJr's selected list included `ppq.apple.com`, so the normal union included it and the previous `enhanced - normal` calculation removed it from the enhanced files. The enhanced payload was still selected and still detected PPQ. The publication policy now reserves PPQ for enhanced mode independently of which source discovers it. Tests cover explicit lists, probed results, overlapping sources, and PPQ absent from all sources.
