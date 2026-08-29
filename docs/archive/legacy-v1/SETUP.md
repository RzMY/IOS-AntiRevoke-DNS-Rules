# iOS Anti-Revoke Profile Generator - Setup Guide

## Project Overview

This Python project automates the scraping, processing, and repacking of iOS Anti-Revoke profiles from multiple sources. It generates signed `.mobileconfig` profiles and filter rules for various proxy tools.

### Features
- ✅ Multi-source scraping with XPath support
- ✅ CMS-signed profile decryption using OpenSSL
- ✅ Domain list extraction and deduplication
- ✅ Profile regeneration with signing
- ✅ Multi-format rule generation (Quantumult X, Surge, Loon, Shadowrocket)
- ✅ Automated daily CI/CD via GitHub Actions
- ✅ Comprehensive error handling and logging

---

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── daily_update.yml          # GitHub Actions workflow
├── utils/
│   ├── __init__.py
│   ├── scraper.py                   # HTML scraping module
│   ├── crypto_handler.py            # OpenSSL operations
│   └── rule_converter.py            # Rule generation
├── output/                          # Generated files (auto-created)
├── main.py                          # Orchestrator script
├── requirements.txt                 # Python dependencies
├── fullchain.pem                    # SSL certificate (add manually)
├── privkey.pem                      # SSL private key (add manually)
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites

**System Requirements:**
- Python 3.11+
- OpenSSL (for CMS operations)
- Git (for CI/CD)

**Check if OpenSSL is installed:**
```bash
openssl version
```

**On Windows (if OpenSSL not installed):**
- Download from: https://slproweb.com/products/Win32OpenSSL.html
- Or use Git Bash which includes OpenSSL

**On macOS:**
```bash
brew install openssl
```

**On Linux:**
```bash
sudo apt-get install openssl
```

### 2. Clone & Setup

```bash
# Navigate to project directory
cd IOS-AntiRevoke-DNS-Rules

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Add SSL Certificates

Place your certificates in the project root:

```bash
# Copy your certificates
cp /path/to/fullchain.pem .
cp /path/to/privkey.pem .

# Set appropriate permissions (Linux/macOS)
chmod 600 fullchain.pem privkey.pem
```

**Note:** Keep these files secure and never commit them to git. Add to `.gitignore` if needed:
```
fullchain.pem
privkey.pem
```

---

## Usage

### Local Execution

```bash
# Run the complete pipeline
python main.py

# With custom certificate paths
SSL_CERT_PATH=/path/to/fullchain.pem SSL_KEY_PATH=/path/to/privkey.pem python main.py
```

### GitHub Actions Setup

1. **Add Secrets:**
   - Go to Repository Settings → Secrets and variables → Actions
   - Add two secrets:
     - `SSL_CERT`: Content of `fullchain.pem`
     - `SSL_KEY`: Content of `privkey.pem`

2. **Workflow Triggers:**
   - **Schedule:** Runs automatically at 00:00 UTC daily
   - **Manual:** Trigger via "Run workflow" button

3. **Output Files:**
   - `.mobileconfig` profiles in `output/`
   - Filter rules for each proxy tool
   - `domains.txt` with complete domain list
   - `metadata.json` with build information

---

## Module Documentation

### `scraper.py` - ProfileScraper
Handles HTML parsing and file downloading.

```python
from utils.scraper import ProfileScraper

scraper = ProfileScraper(timeout=10, max_retries=3)
sources = [
    {
        'url': 'https://example.com',
        'xpath': '/html/body/a[@href]',
        'name': 'source_name'
    }
]
profiles = scraper.scrape_sources(sources)
```

### `crypto_handler.py` - CryptoHandler
Manages profile encryption, decryption, and signing.

```python
from utils.crypto_handler import CryptoHandler

crypto = CryptoHandler(cert_path='fullchain.pem', key_path='privkey.pem')

# Decrypt profile
decrypted = crypto.decrypt_profile('input.mobileconfig', 'output.plist')

# Parse plist
plist_data = crypto.parse_plist(decrypted)

# Extract domains
domains = crypto.extract_domains(plist_data)

# Create and sign new profile
plist = crypto.create_profile(domains)
signed = crypto.sign_profile(plist, 'output.mobileconfig')
```

### `rule_converter.py` - RuleFileGenerator
Converts domain lists to proxy tool rule formats.

```python
from utils.rule_converter import RuleFileGenerator

generator = RuleFileGenerator(output_dir='output')
files = generator.generate_all_rules(domains)

# Generates:
# - RevokeGuard_QuantumultX.txt
# - RevokeGuard_Surge.txt
# - RevokeGuard_Loon.txt
# - RevokeGuard_Shadowrocket.txt
# - RevokeGuard_hosts.txt
# - domains.txt
```

### `main.py` - AntiRevokeOrchestrator
Orchestrates the complete pipeline.

```python
from main import AntiRevokeOrchestrator

orchestrator = AntiRevokeOrchestrator(
    cert_path='fullchain.pem',
    key_path='privkey.pem',
    output_dir='output'
)

success = orchestrator.run(sources)
```

---

## Configuration

### Sources Definition

Edit the sources in `main.py`:

```python
sources = [
    {
        'url': 'https://khoindvn.io.vn/',
        'xpath': '/html/body/main/section[2]/div[2]/div[1]/a',
        'name': 'khoindvn'
    },
    {
        'url': 'https://applejr.net/',
        'xpath': '/html/body/div[3]/div/form/div[3]/label/a',
        'name': 'applejr'
    }
]
```

**To find XPath for a download link:**
1. Open source website in browser
2. Right-click on download link → Inspect Element
3. Copy the XPath from browser developer tools

---

## Output Files

### Generated Profiles
- **RevokeGuard_Auto-Sync.mobileconfig** - Signed iOS configuration profile

### Generated Rules

#### Quantumult X Format
```
host, example.com, reject
```
File: `RevokeGuard_QuantumultX.txt`

#### Surge/Loon/Shadowrocket Format
```
DOMAIN,example.com,REJECT
```
Files: `RevokeGuard_Surge.txt`, `RevokeGuard_Loon.txt`, `RevokeGuard_Shadowrocket.txt`

#### Hosts File Format
```
0.0.0.0 example.com
```
File: `RevokeGuard_hosts.txt`

#### Domain List
```
example.com
another-domain.com
```
File: `domains.txt`

### Metadata
File: `metadata.json`
```json
{
  "timestamp": "2024-01-29T00:00:00",
  "total_domains": 1234,
  "sources_processed": 2,
  "generated_files": {...}
}
```

---

## Troubleshooting

### OpenSSL Not Found
**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'openssl'`

**Solution:**
- Install OpenSSL (see Prerequisites)
- Verify: `openssl version`
- On Windows, use Git Bash or add OpenSSL to PATH

### Certificate/Key Not Found
**Error:** `Certificate file not found` or `Key file not found`

**Solution:**
```bash
# Verify certificate exists
ls -la fullchain.pem privkey.pem

# Or set explicit paths in main.py or environment variables
SSL_CERT_PATH=/full/path/to/fullchain.pem python main.py
```

### XPath Not Matching
**Error:** `Could not extract download link from source`

**Solution:**
1. Test XPath in browser: Right-click → Inspect → Copy XPath
2. Verify the source website still has the same structure
3. Update XPath if website changed

### Network Errors
**Error:** `Failed to fetch source after 3 attempts`

**Solution:**
- Check internet connection
- Verify source URL is accessible
- Increase timeout in `ProfileScraper(timeout=20)`
- Check if source site blocks bot requests

### GitHub Actions Secrets Not Working
**Error:** Certificate/key path issues in workflows

**Solution:**
1. Verify secrets are added correctly in repository settings
2. Secret names must match: `SSL_CERT` and `SSL_KEY`
3. Check workflow logs for errors
4. Ensure newlines are preserved when copying certificate content

---

## Security Considerations

⚠️ **Important:**
- Never commit `fullchain.pem` or `privkey.pem` to git
- Use GitHub Secrets for CI/CD, never paste keys in workflows
- Limit access to your certificates
- Regenerate certificates periodically
- Use `.gitignore` to prevent accidental commits

**.gitignore entry:**
```
fullchain.pem
privkey.pem
*.key
*.pem
```

---

## Performance & Limits

- **Timeout:** 10 seconds per request (configurable)
- **Retries:** 3 attempts per request
- **Max Domains:** No hard limit (tested with 5000+)
- **Profile Size:** ~100KB average (varies with domain count)

---

## Logging

All operations are logged with timestamps and levels (INFO, WARNING, ERROR).

**Log Format:**
```
2024-01-29 12:00:00,123 - utils.scraper - INFO - Fetching https://...
```

To adjust log level, edit `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
```

---

## CI/CD Workflow Details

The GitHub Actions workflow (`daily_update.yml`):

1. ✅ Checkout code
2. ✅ Setup Python 3.11
3. ✅ Install dependencies
4. ✅ Write SSL certificates from secrets
5. ✅ Run update pipeline
6. ✅ Detect changes
7. ✅ Auto-commit and push results
8. ✅ Generate build summary
9. ✅ Upload artifacts
10. ✅ Cleanup sensitive files

**Manual Trigger:**
- Go to Actions → Daily iOS Anti-Revoke Profile Update
- Click "Run workflow"

---

## Development & Extension

### Adding New Sources

Edit `main.py`:
```python
sources = [
    # ... existing sources
    {
        'url': 'https://newsource.com',
        'xpath': '/html/body/a[@class="download"]',
        'name': 'newsource'
    }
]
```

### Adding New Rule Formats

Edit `utils/rule_converter.py`:
```python
@staticmethod
def generate_custom_rules(domains: List[str]) -> str:
    rules = []
    for domain in sorted(set(domains)):
        rules.append(f'custom,format,{domain}')
    return '\n'.join(rules)
```

### Custom OpenSSL Commands

Modify `utils/crypto_handler.py`:
```python
def custom_operation(self):
    cmd = ['openssl', 'custom', 'args']
    subprocess.run(cmd, check=True)
```

---

## Support & Contributing

For issues or improvements:
1. Check existing troubleshooting
2. Review log files
3. Test components individually
4. Create detailed bug reports

---

## License

See [LICENSE](LICENSE) file for details.

---

**Last Updated:** 2024-01-29
**Version:** 1.0.0
