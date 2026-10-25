# iOS-AntiRevoke-DNS-Rules

**English** | [简体中文](README.zh-CN.md)

[![Build Status](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/actions/workflows/daily_update.yml/badge.svg)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/actions/workflows/daily_update.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/RzMY/IOS-AntiRevoke-DNS-Rules)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/commits/main)

Automatically discovers iOS anti-revoke domains and publishes DNS profiles plus rules for major network tools.

## Features

- Daily discovery based on [Apple's official host list](https://support.apple.com/en-us/101555).
- Domain data is collected from Khoindvn, AppleJr and Sideloading profiles and published lists.
- One iOS profile contains selectable normal and enhanced DNS configurations; network-tool rules are published separately.
- Supports iOS/iPadOS, Quantumult X, Surge, Loon, Shadowrocket and Hosts.
- GitHub Actions tests, validates and commits all generated artifacts.

## Downloads

### iOS/iPadOS Profile

| Platform | File |
| --- | --- |
| iOS/iPadOS | [RevokeGuard.mobileconfig — Normal + Enhanced](https://reject.rzmy.dpdns.org/download) |

### Normal Rules

| Platform | File |
| --- | --- |
| Quantumult X | [RevokeGuard_QuantumultX.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_QuantumultX.txt) |
| Surge | [RevokeGuard_Surge.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Surge.txt) |
| Loon | [RevokeGuard_Loon.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Loon.txt) |
| Shadowrocket | [RevokeGuard_Shadowrocket.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Shadowrocket.txt) |
| Hosts | [RevokeGuard_hosts.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_hosts.txt) |
| Domains | [domains.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/domains.txt) |

### Enhanced Rules

| Platform | File |
| --- | --- |
| Quantumult X | [RevokeGuard_Enhanced_QuantumultX.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_QuantumultX.txt) |
| Surge | [RevokeGuard_Enhanced_Surge.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Surge.txt) |
| Loon | [RevokeGuard_Enhanced_Loon.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Loon.txt) |
| Shadowrocket | [RevokeGuard_Enhanced_Shadowrocket.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Shadowrocket.txt) |
| Hosts | [RevokeGuard_Enhanced_hosts.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_hosts.txt) |
| Extra domains | [enhanced-domains.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/enhanced-domains.txt) |

## Usage

### iOS/iPadOS Profile Usage

1. Open the profile download link in **Safari** on your iPhone/iPad and allow the download. If you already have the old standalone normal or enhanced RevokeGuard profiles, remove them in **Settings → General → VPN & Device Management** before installing this combined profile.
2. Open **Settings → Profile Downloaded**, or find the downloaded profile under **General → VPN & Device Management**. Tap **Install**, enter your device passcode if prompted, and confirm.
3. Go to **Settings → General → VPN & Device Management → DNS** and select **RevokeGuard Normal - Use during install**.
4. Download KSign or ESign from [Khoindvn Bypass](https://khoindvn.io.vn/#bypass), sideload your apps, and open them successfully for the first time while normal mode is selected.
5. Return to the **DNS** page and select **RevokeGuard Enhanced - Use after installing**. 
6. Before installing another app, updating/re-signing an app, or changing certificates, switch back to **Normal**，return to **Enhanced** after the app opens successfully.

### Network Tools

1. Copy the matching tool's links from **Normal Rules** and **Enhanced Rules** above. Import them separately and name them, for example, **RevokeGuard Normal** and **RevokeGuard Enhanced**, so the enhanced set can be toggled independently.
2. Enable only **Normal** before certificate setup or app installation. Keep the imported actions as **REJECT / reject**, place these rules before any matching **DIRECT**, proxy or final fallback rule, and save/apply the configuration. Start the network tool and use its rule-based routing mode so the rules can take effect.
3. With normal mode active, download KSign or ESign from [Khoindvn Bypass](https://khoindvn.io.vn/#bypass), configure your certificate, sideload the apps, and open them successfully for the first time. Keep the enhanced set disabled throughout these steps.
4. After the apps open successfully, enable **Enhanced**, keeping **Normal** enabled.
5. Before installing another app, updating/re-signing an app, or changing certificates, disable **Enhanced** while leaving **Normal** enabled， then re-enable **Enhanced** after the app opens successfully.

### Note

1. If a normally working application becomes unable to open, remove all sideloaded apps and the trusted certificate, select a new certificate, then repeat the steps above.
2. It is recommended to use network tools along with profiles to unexpected prevent rule failures caused by changes in network status.
3. Please enable airplane mode before restarting your phone to prevent unexpected rule failures during system initialization.

## Credits

- [Apple Support](https://support.apple.com/en-us/101555)
- [Khoindvn](https://khoindvn.io.vn/)
- [AppleJr](https://applejr.net/)
- [Sideloading / NexRevokeDNS](https://sideloading.net/dns/)

## License

[MIT License](LICENSE)
