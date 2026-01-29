# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Add SSL Certificates
```bash
# Copy your certificates to project root
cp /path/to/fullchain.pem .
cp /path/to/privkey.pem .
```

### Step 3: Verify OpenSSL
```bash
openssl version
```

### Step 4: Run Pipeline
```bash
python main.py
```

### Step 5: Check Output
```bash
ls -la output/
```

Generated files:
- `RevokeGuard_Auto-Sync.mobileconfig` - iOS profile
- `RevokeGuard_QuantumultX.txt` - Quantumult X rules
- `RevokeGuard_Surge.txt` - Surge rules
- `RevokeGuard_Loon.txt` - Loon rules
- `RevokeGuard_Shadowrocket.txt` - Shadowrocket rules
- `domains.txt` - Plain domain list
- `metadata.json` - Build metadata

---

## GitHub Actions Setup

### Step 1: Add Secrets
Go to: Repository → Settings → Secrets and variables → Actions

Add two secrets:
1. **SSL_CERT**
   - Name: `SSL_CERT`
   - Secret: (copy content of fullchain.pem)

2. **SSL_KEY**
   - Name: `SSL_KEY`
   - Secret: (copy content of privkey.pem)

### Step 2: Enable Workflow
- Go to Actions tab
- Select "Daily iOS Anti-Revoke Profile Update"
- Click "Enable workflow"

### Step 3: Manual Trigger (Optional)
- Click "Run workflow"
- Select "main" branch
- Click "Run workflow"

The workflow will:
- Run daily at 00:00 UTC
- Scrape profiles from sources
- Extract domains
- Generate new profile and rules
- Auto-commit changes to repository

---

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| `openssl not found` | Install OpenSSL (see SETUP.md) |
| `Certificate not found` | Place fullchain.pem & privkey.pem in root |
| `XPath not matching` | Update XPath in main.py for changed websites |
| `Network timeout` | Check internet, increase timeout value |
| `GitHub workflow fails` | Verify SSL_CERT and SSL_KEY secrets are added |

---

## File Explanation

```
main.py                   # Run this to start the pipeline
├─ scraper.py           # Downloads profiles from sources
├─ crypto_handler.py     # Decrypts and signs profiles
└─ rule_converter.py     # Generates proxy tool rules

.github/workflows/
└─ daily_update.yml      # GitHub Actions automation

output/                  # Generated files (auto-created)
├─ *.mobileconfig        # Signed iOS profile
├─ *.txt                 # Rule files for each tool
├─ domains.txt          # Complete domain list
└─ metadata.json        # Build information
```

---

## Next Steps

1. **Customize Sources:** Edit sources in `main.py` if needed
2. **Test Locally:** Run `python main.py` to verify
3. **Deploy to GitHub:** Push code and add secrets
4. **Monitor:** Check workflow runs in Actions tab
5. **Share:** Distribute generated files to users

---

**Need more help?** See [SETUP.md](SETUP.md) for detailed documentation.
