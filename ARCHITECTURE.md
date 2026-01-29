# Workflow Architecture

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    iOS Anti-Revoke Pipeline                     │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────┐
                         │  START   │
                         └────┬─────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Initialize        │
                    │ Orchestrator      │
                    └────────┬─────────┘
                             │
                ┌────────────┴─────────────┐
                │                          │
                ▼                          ▼
        ┌────────────────┐      ┌──────────────────┐
        │ Load Source    │      │ Load Certificates│
        │ Definitions    │      │ (from env vars)  │
        └────────┬───────┘      └────────┬─────────┘
                 │                       │
        ┌────────┴───────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│ STEP 1: SCRAPING (scraper.py)                   │
├─────────────────────────────────────────────────┤
│ For each source:                                │
│  1. Fetch HTML content (with retries)          │
│  2. Parse HTML using XPath                     │
│  3. Extract download link                      │
│  4. Download .mobileconfig file                │
│  5. Store in temp directory                    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ profiles dict   │
            │ {name: bytes}   │
            └────────┬────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ STEP 2: PROCESSING (crypto_handler.py)          │
├─────────────────────────────────────────────────┤
│ For each profile:                               │
│  1. Decrypt DER-signed .mobileconfig           │
│     $ openssl smime -verify -inform DER ...     │
│  2. Parse plist XML                            │
│  3. Extract domains from:                      │
│     PayloadContent → DNSSettings →             │
│     SupplementalMatchDomains                   │
│  4. Accumulate domains in set()                │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  domains set    │
            │ {domain, ...}   │
            └────────┬────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ STEP 3: MERGING (main.py)                       │
├─────────────────────────────────────────────────┤
│ 1. Deduplicate domains (set → list)            │
│ 2. Sort alphabetically                         │
│ 3. Create master domain list                   │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │  merged_domains     │
            │ [domain, ...]       │
            └─────────┬───────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
┌────────────────────┐  ┌──────────────────────┐
│ STEP 4A: PROFILE   │  │ STEP 4B: RULES       │
│ GENERATION         │  │ GENERATION           │
├────────────────────┤  ├──────────────────────┤
│ 1. Create plist    │  │ 1. Quantumult X      │
│    structure       │  │    (host, d, reject) │
│ 2. Inject domains  │  │ 2. Surge             │
│ 3. Add UUIDs       │  │    (DOMAIN,d,REJECT) │
│ 4. Sign with cert  │  │ 3. Loon              │
│    $ openssl smime │  │    (DOMAIN,d,REJECT) │
│    -sign -signer   │  │ 4. Shadowrocket      │
│    ... -outform    │  │    (DOMAIN,d,REJECT) │
│    DER             │  │ 5. Hosts             │
│ 5. Output as DER   │  │    (0.0.0.0 domain)  │
│    .mobileconfig   │  │ 6. Domain list (txt) │
└────────┬───────────┘  └──────────┬───────────┘
         │                         │
         ▼                         ▼
    ┌─────────────┐          ┌──────────────────┐
    │.mobileconfig│          │ 6 Rule Files     │
    │(signed DER) │          │ + domain list    │
    └──────┬──────┘          └────────┬─────────┘
           │                          │
           └──────────┬───────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │ Generate metadata.json   │
         │ (timestamp, counts, etc) │
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │ Save to output/           │
         │ - *.mobileconfig          │
         │ - *.txt (rules)           │
         │ - domains.txt             │
         │ - metadata.json           │
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │ Commit & Push (GitHub)    │
         │ via GitHub Actions        │
         └──────────┬───────────────┘
                    │
                    ▼
                ┌─────────┐
                │ SUCCESS │
                └─────────┘
```

---

## Component Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      main.py                               │
│                 AntiRevokeOrchestrator                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  run(sources) - Main Pipeline Orchestration         │  │
│  │  - scrape_sources()                                 │  │
│  │  - process_profiles()                               │  │
│  │  - merge_domains()                                  │  │
│  │  - generate_profile()                               │  │
│  │  - generate_rules()                                 │  │
│  │  - generate_metadata()                              │  │
│  └──────────────────────────────────────────────────────┘  │
└────┬──────────────┬──────────────┬─────────────────────────┘
     │              │              │
     │              │              │
     ▼              ▼              ▼
┌──────────┐  ┌────────────┐  ┌─────────────┐
│ProfileScr│  │ CryptoHand│  │ RuleFileGen │
│aper      │  │ ler       │  │ erator      │
├──────────┤  ├────────────┤  ├─────────────┤
│ • Fetch  │  │ • Decrypt │  │ • QX Format │
│ • Parse  │  │ • Parse   │  │ • Surge     │
│ • Download│ │ • Extract │  │ • Loon      │
│ • Retry  │  │ • Create  │  │ • SR        │
│          │  │ • Sign    │  │ • Hosts     │
│          │  │ • Verify  │  │ • Domain    │
└──────────┘  └────────────┘  └─────────────┘
```

---

## GitHub Actions Workflow

```
┌──────────────────────────────────────────────────────────┐
│       GitHub Actions: daily_update.yml                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Trigger: Scheduled (0 0 * * *) + Manual Dispatch      │
│                                                          │
│  Steps:                                                 │
│  1. Checkout code                                       │
│  2. Setup Python 3.11                                   │
│  3. Cache pip dependencies                              │
│  4. Install requirements.txt                            │
│  5. Write SSL certificates from secrets                 │
│  6. Verify OpenSSL                                      │
│  7. Run: python main.py                                │
│  8. Detect changes in output/                           │
│  9. Git config (user + email)                           │
│  10. Git add output/                                    │
│  11. Git commit with message                            │
│  12. Git push to main branch                            │
│  13. Optional: Create PR                                │
│  14. Cleanup sensitive files                            │
│  15. Upload artifacts                                   │
│  16. Generate summary                                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Data Transformation

```
INPUT:
  Source A: https://khoindvn.io.vn/
  Source B: https://applejr.net/
  (Downloaded .mobileconfig files)

           │
           ▼

DECRYPT:  openssl smime -verify -inform DER -in input -noverify -out output.plist
          (DER Format) → (PList XML Format)

           │
           ▼

PARSE:    plistlib.load(file)
          (XML PList) → (Python Dict)

           │
           ▼

EXTRACT:  PayloadContent[0].DNSSettings.SupplementalMatchDomains
          (Dict) → (List[domains])

           │
           ▼

MERGE:    set(domains_a + domains_b)
          (Multiple lists) → (Deduplicated set)

           │
           ▼

GENERATE: plistlib.dump(profile_dict, file)
          (Dict) → (PList XML)

           │
           ▼

SIGN:     openssl smime -sign -signer cert -inkey key -outform DER
          (PList XML) → (DER Signed .mobileconfig)

           │
           ▼

RULE CONVERT: For each domain: "host, domain, reject"
              (Domain list) → (Multiple rule formats)

           │
           ▼

OUTPUT:   output/RevokeGuard_Auto-Sync.mobileconfig
          output/RevokeGuard_QuantumultX.txt
          output/RevokeGuard_Surge.txt
          output/RevokeGuard_Loon.txt
          output/RevokeGuard_Shadowrocket.txt
          output/RevokeGuard_hosts.txt
          output/domains.txt
          output/metadata.json
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────┐
│           Error Detection & Recovery                    │
└─────────────────────────────────────────────────────────┘

Network Error
  ├─ Retry with exponential backoff (max 3 times)
  ├─ Log warning at each attempt
  └─ Skip source if all attempts fail

Parse Error (XPath/Plist)
  ├─ Log detailed error with context
  ├─ Try next source
  └─ Continue if other sources available

Crypto Error (Decrypt/Sign)
  ├─ Log error details
  ├─ Fallback to unsigned profile (if decrypt fails)
  ├─ Stop pipeline (if sign fails, cert required)
  └─ Alert user to verify certificates

File Error (Read/Write)
  ├─ Verify file permissions
  ├─ Create directories if needed
  ├─ Log with full path
  └─ Exit gracefully

No Domains Extracted
  ├─ Log warning
  ├─ Continue with previous data (if available)
  └─ Alert in metadata

All errors logged with:
  - Timestamp
  - Component name
  - Error message
  - Suggested action
```

---

## Deployment Sequence

```
LOCAL SETUP:
  1. git clone <repo>
  2. pip install -r requirements.txt
  3. cp fullchain.pem privkey.pem .
  4. python main.py
  5. Check output/ directory

GITHUB DEPLOYMENT:
  1. Push code to GitHub
  2. Repository Settings → Secrets
  3. Add SSL_CERT secret (fullchain.pem content)
  4. Add SSL_KEY secret (privkey.pem content)
  5. Go to Actions tab
  6. Select "Daily iOS Anti-Revoke Profile Update"
  7. Click "Enable workflow"
  8. Workflow runs automatically at scheduled time
  9. Or manually click "Run workflow"
  10. Check "output/" directory for generated files
  11. Commit history shows automated commits
  12. Generated profiles ready for distribution
```

---

## File Dependency Graph

```
main.py (Orchestrator)
  ├─ utils/scraper.py
  │   ├─ requests (HTTP)
  │   ├─ lxml (HTML parsing)
  │   └─ tempfile (temp storage)
  │
  ├─ utils/crypto_handler.py
  │   ├─ subprocess (OpenSSL)
  │   ├─ plistlib (PList parsing)
  │   ├─ tempfile (temp files)
  │   └─ pycryptodome (crypto)
  │
  ├─ utils/rule_converter.py
  │   ├─ pathlib (file paths)
  │   └─ logging (output)
  │
  └─ Standard Library
      ├─ logging
      ├─ json
      ├─ pathlib
      └─ datetime

requirements.txt
  ├─ requests>=2.28.0
  ├─ lxml>=4.9.0
  └─ pycryptodome>=3.16.0

.github/workflows/daily_update.yml
  ├─ Ubuntu Latest
  ├─ Python 3.11
  ├─ pip (package install)
  ├─ git (version control)
  ├─ openssl (CLI tool)
  └─ GitHub Actions (runners)
```

---

## Timeline Diagram

```
Day 1:
  00:00:00 UTC - Workflow triggered (scheduled)
  00:00:15 UTC - Checkout code
  00:00:30 UTC - Setup Python
  00:00:45 UTC - Install dependencies
  00:01:00 UTC - Write certificates
  00:01:15 UTC - Start scraping
  00:02:00 UTC - Finish scraping (depends on network)
  00:02:15 UTC - Decrypt profiles
  00:02:30 UTC - Extract domains
  00:02:45 UTC - Merge domains
  00:03:00 UTC - Generate signed profile
  00:03:15 UTC - Generate rule files
  00:03:30 UTC - Commit changes
  00:03:45 UTC - Push to main
  00:04:00 UTC - Workflow complete

Total execution time: ~4 minutes (estimated)

Day 2:
  (Workflow repeats)

Whenever manual trigger:
  - Same process as scheduled execution
```

---

This architecture provides:
- ✅ Clear separation of concerns
- ✅ Modular, reusable components
- ✅ Robust error handling
- ✅ Comprehensive logging
- ✅ Automated deployment
- ✅ Scalable design
