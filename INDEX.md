# Project Index & Navigation

Welcome to the iOS Anti-Revoke Profile Generator project! This document helps you navigate all project files and understand the codebase.

---

## 📚 Documentation Files (Start Here!)

| File | Purpose | Read If... |
|------|---------|-----------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute quick start | You want to get running immediately |
| [SETUP.md](SETUP.md) | Complete setup guide | You need detailed instructions |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture | You want to understand the design |
| [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md) | What was delivered | You want a project overview |
| [README.md](README.md) | Original project info | You want project context |

**👉 Start with:** [QUICKSTART.md](QUICKSTART.md) if you have 5 minutes, or [SETUP.md](SETUP.md) for comprehensive guide.

---

## 🐍 Core Python Modules

### `main.py` - Pipeline Orchestrator
**Purpose:** Main entry point that coordinates the entire pipeline

**Key Classes:**
- `AntiRevokeOrchestrator` - Main orchestrator class
  - `run(sources)` - Execute full pipeline
  - `scrape_sources(sources)` - Step 1: Scrape
  - `process_profiles(profiles)` - Step 2: Process
  - `merge_domains()` - Step 3: Merge
  - `generate_profile(domains)` - Step 4A: Generate profile
  - `generate_rules(domains)` - Step 4B: Generate rules
  - `generate_metadata()` - Create build metadata

**Usage:**
```bash
python main.py
```

**Code:** 313 lines | **Imports:** scraper, crypto_handler, rule_converter

---

### `utils/scraper.py` - HTML Scraping Module
**Purpose:** Download and parse iOS profiles from multiple sources

**Key Classes:**
- `ProfileScraper` - Scrapes profiles from sources
  - `scrape_sources(sources)` - Multi-source scraping
  - `_fetch_page(url)` - Fetch with retries
  - `_extract_download_link(html, xpath, base_url)` - XPath extraction
  - `download_profile(url)` - Download file with retries
  - `save_profiles(profiles, output_dir)` - Save to disk

**Features:**
- XPath-based link extraction
- Retry logic (configurable)
- Safe filename generation
- Comprehensive error handling

**Code:** 250 lines | **Dependencies:** requests, lxml

---

### `utils/crypto_handler.py` - Cryptography & Signing
**Purpose:** Decrypt, parse, and sign iOS profiles using OpenSSL

**Key Classes:**
- `CryptoHandler` - Handles all cryptographic operations
  - `decrypt_profile(input_file, output_file)` - DER → PList
  - `parse_plist(plist_file)` - Parse XML plist
  - `extract_domains(plist_data)` - Extract domain list
  - `create_profile(domains, output_file)` - Create new profile
  - `sign_profile(plist_file, output_file)` - Sign with certificate
  - `process_profile(input_file)` - Complete workflow

**Features:**
- OpenSSL CMS operations
- PList XML handling
- Domain extraction from PayloadContent
- Profile signing with DER output
- UUID generation

**Code:** 320 lines | **Dependencies:** subprocess, plistlib, pathlib

**OpenSSL Commands Used:**
```bash
# Decrypt
openssl smime -verify -inform DER -in input.mobileconfig -noverify -out output.plist

# Sign
openssl smime -sign -signer fullchain.pem -inkey privkey.pem -in profile.plist -out output.mobileconfig -outform DER
```

---

### `utils/rule_converter.py` - Rule Generation
**Purpose:** Generate filter rules for multiple proxy tools

**Key Classes:**
- `RuleConverter` - Static rule generation methods
  - `generate_quantumultx_rules(domains)` - QX format
  - `generate_surge_rules(domains)` - Surge format
  - `generate_loon_rules(domains)` - Loon format
  - `generate_shadowrocket_rules(domains)` - SR format
  - `generate_hosts_rules(domains, ip)` - Hosts format

- `RuleFileGenerator` - File generation and management
  - `generate_all_rules(domains)` - Generate all formats
  - Saves 6 different rule files

**Output Formats:**
- **Quantumult X:** `host, example.com, reject`
- **Surge:** `DOMAIN,example.com,REJECT`
- **Loon:** `DOMAIN,example.com,REJECT`
- **Shadowrocket:** `DOMAIN,example.com,REJECT`
- **Hosts:** `0.0.0.0 example.com`
- **Domain List:** Plain text, one per line

**Code:** 280 lines | **Dependencies:** pathlib, logging

---

## 🔧 Configuration Files

### `requirements.txt` - Python Dependencies
```
requests>=2.28.0        # HTTP client for scraping
lxml>=4.9.0            # HTML/XML parsing
pycryptodome>=3.16.0   # Cryptographic operations
```

**Install:** `pip install -r requirements.txt`

---

### `.gitignore` - Version Control Security
**Protects:**
- SSL certificates (fullchain.pem, privkey.pem)
- Python cache (__pycache__, *.pyc)
- Virtual environments (venv/, env/)
- IDE settings (.vscode/, .idea/)
- OS files (Thumbs.db, .DS_Store)
- Environment variables (.env)

**Allows:** Source code, documentation, workflow files

---

### `.github/workflows/daily_update.yml` - CI/CD Automation
**Triggers:**
- Schedule: `0 0 * * *` (Daily at 00:00 UTC)
- Manual: Via GitHub Actions UI

**Steps:**
1. Checkout code
2. Setup Python 3.11
3. Install dependencies
4. Write SSL certificates from secrets
5. Run pipeline
6. Detect changes
7. Auto-commit & push
8. Upload artifacts
9. Generate summary

**Secrets Required:**
- `SSL_CERT` - Content of fullchain.pem
- `SSL_KEY` - Content of privkey.pem

---

## 📁 Directory Structure

```
.
├── main.py                          ← Run this
├── requirements.txt                 ← Install these
├── utils/
│   ├── __init__.py
│   ├── scraper.py                  ← Fetch profiles
│   ├── crypto_handler.py           ← Decrypt/sign
│   └── rule_converter.py           ← Generate rules
├── .github/
│   └── workflows/
│       └── daily_update.yml        ← CI/CD automation
├── output/                         ← Generated files
│   ├── RevokeGuard_Auto-Sync.mobileconfig
│   ├── RevokeGuard_QuantumultX.txt
│   ├── RevokeGuard_Surge.txt
│   ├── RevokeGuard_Loon.txt
│   ├── RevokeGuard_Shadowrocket.txt
│   ├── RevokeGuard_hosts.txt
│   ├── domains.txt
│   └── metadata.json
├── fullchain.pem                   ← Add your certificate
├── privkey.pem                     ← Add your private key
└── Documentation/
    ├── QUICKSTART.md               ← Start here (5 min)
    ├── SETUP.md                    ← Detailed setup
    ├── ARCHITECTURE.md             ← System design
    ├── DELIVERY_SUMMARY.md         ← Project summary
    ├── README.md                   ← Project overview
    └── INDEX.md                    ← This file
```

---

## 🚀 Quick Navigation

### I want to...

#### **Get running in 5 minutes**
→ Read [QUICKSTART.md](QUICKSTART.md)

#### **Understand the system design**
→ Read [ARCHITECTURE.md](ARCHITECTURE.md)

#### **Set up detailed configuration**
→ Read [SETUP.md](SETUP.md)

#### **Run the pipeline locally**
→ See [QUICKSTART.md](QUICKSTART.md) Steps 1-4

#### **Deploy to GitHub**
→ See [QUICKSTART.md](QUICKSTART.md) GitHub Actions Setup

#### **Customize sources**
→ Edit sources list in [main.py](main.py) lines ~280

#### **Add a new rule format**
→ Add method to `RuleConverter` in [utils/rule_converter.py](utils/rule_converter.py)

#### **Modify scraping logic**
→ Edit `ProfileScraper` in [utils/scraper.py](utils/scraper.py)

#### **Change certificate paths**
→ Use environment variables `SSL_CERT_PATH` and `SSL_KEY_PATH`

#### **Understand the pipeline steps**
→ See [ARCHITECTURE.md](ARCHITECTURE.md) "Data Flow Diagram"

#### **See what was delivered**
→ Read [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md)

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| Total Python Code | ~1,200 lines |
| Total Documentation | ~2,000 lines |
| Core Modules | 3 (scraper, crypto, rules) |
| Rule Formats Supported | 6 |
| Data Sources | 2 (configurable) |
| CI/CD Workflow Steps | 16 |
| Error Handling Points | 15+ |
| Logging Statements | 50+ |
| Python Version | 3.11+ |
| External Dependencies | 3 (requests, lxml, pycryptodome) |
| External Tools | 1 (OpenSSL) |

---

## 🔍 Key Functions Quick Reference

### Scraping
```python
ProfileScraper.scrape_sources(sources: List[Dict]) → Dict[str, bytes]
```

### Processing
```python
CryptoHandler.decrypt_profile(input_file: str) → str
CryptoHandler.extract_domains(plist_data: Dict) → List[str]
```

### Profile Generation
```python
CryptoHandler.create_profile(domains: List[str]) → str
CryptoHandler.sign_profile(plist_file: str) → str
```

### Rule Generation
```python
RuleFileGenerator.generate_all_rules(domains: List[str]) → Dict[str, str]
```

### Orchestration
```python
AntiRevokeOrchestrator.run(sources: List[Dict]) → bool
```

---

## 🔐 Security Checklist

- ✅ SSL certificates in .gitignore
- ✅ GitHub Secrets for certificates
- ✅ No hardcoded credentials
- ✅ Environment variable support
- ✅ Sensitive file cleanup in workflows
- ✅ Comprehensive error handling
- ✅ Audit logging
- ✅ Safe filename generation

---

## 📈 Performance & Limits

| Aspect | Value |
|--------|-------|
| Request Timeout | 10 seconds (configurable) |
| Max Retries | 3 attempts |
| Supported Domains | 10,000+ (no hard limit) |
| Profile Size | ~100KB (varies) |
| Pipeline Duration | ~4 minutes (varies) |
| Rule File Size | ~1-5 MB (domain count dependent) |

---

## 🐛 Debugging

### Enable Debug Logging
Edit `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

### View Logs
```bash
python main.py 2>&1 | tee pipeline.log
```

### Test Individual Modules
```python
from utils.scraper import ProfileScraper
scraper = ProfileScraper()
# Test scraping...
```

---

## 🔗 Related Resources

- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [Apple Configuration Profile Documentation](https://developer.apple.com/documentation/devicemanagement/configurationprofilepayload)
- [requests Library](https://requests.readthedocs.io/)
- [lxml Documentation](https://lxml.de/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## ✅ File Checklist

- [x] main.py - Orchestrator
- [x] requirements.txt - Dependencies
- [x] utils/scraper.py - Scraping module
- [x] utils/crypto_handler.py - Crypto module
- [x] utils/rule_converter.py - Rules module
- [x] .github/workflows/daily_update.yml - CI/CD
- [x] QUICKSTART.md - Quick guide
- [x] SETUP.md - Detailed setup
- [x] ARCHITECTURE.md - Design docs
- [x] DELIVERY_SUMMARY.md - Project summary
- [x] .gitignore - Security config
- [x] INDEX.md - This file

---

## 📞 Support

For each type of issue:

| Issue | Check |
|-------|-------|
| Installation | [SETUP.md](SETUP.md) Prerequisites section |
| Configuration | [SETUP.md](SETUP.md) Configuration section |
| Errors | [SETUP.md](SETUP.md) Troubleshooting section |
| Design questions | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Quick help | [QUICKSTART.md](QUICKSTART.md) |

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-29  
**Status:** ✅ Production Ready

For comprehensive information, see [SETUP.md](SETUP.md).
