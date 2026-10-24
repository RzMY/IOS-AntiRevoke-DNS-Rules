# iOS-AntiRevoke-DNS-Rules

[![Build Status](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/actions/workflows/daily_update.yml/badge.svg)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/actions/workflows/daily_update.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/RzMY/IOS-AntiRevoke-DNS-Rules)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/commits/main)

Automatically discovers iOS anti-revoke domains and publishes DNS profiles plus rules for major network tools.

自动抓取 iOS 反撤销域名，并发布 DNS 描述文件及主流网络工具规则。

## Features | 特性

- Daily discovery based on [Apple's official host list](https://support.apple.com/zh-cn/101555). / 每日基于 [Apple 官方主机列表](https://support.apple.com/zh-cn/101555)更新候选域名。
- Domain data is collected from Khoindvn, AppleJr and Sideloading profiles and published lists. / 从 Khoindvn、AppleJr 与 Sideloading 的描述文件及公开列表收集域名数据。
- One iOS profile contains selectable normal and enhanced DNS configurations; network-tool rules are published separately. / 一份 iOS 描述文件包含可切换的普通与增强 DNS 配置；网络工具规则仍分组发布。
- Supports iOS/iPadOS, Quantumult X, Surge, Loon, Shadowrocket and Hosts. / 支持 iOS/iPadOS、Quantumult X、Surge、Loon、Shadowrocket 与 Hosts。
- GitHub Actions tests, validates and commits all generated artifacts. / GitHub Actions 自动测试、校验并提交产物。

## Downloads | 下载

### iOS/iPadOS Profile | iOS/iPadOS 描述文件

| Platform / 平台 | File / 文件 |
| --- | --- |
| iOS/iPadOS | [RevokeGuard_Auto-Sync.mobileconfig — Normal + Enhanced / 普通 + 增强](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Auto-Sync.mobileconfig) |

### Normal Rules | 普通规则

| Platform / 平台 | File / 文件 |
| --- | --- |
| Quantumult X | [RevokeGuard_QuantumultX.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_QuantumultX.txt) |
| Surge | [RevokeGuard_Surge.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Surge.txt) |
| Loon | [RevokeGuard_Loon.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Loon.txt) |
| Shadowrocket | [RevokeGuard_Shadowrocket.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Shadowrocket.txt) |
| Hosts | [RevokeGuard_hosts.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_hosts.txt) |
| Domains / 域名 | [domains.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/domains.txt) |

### Enhanced Rules | 增强规则

| Platform / 平台 | File / 文件 |
| --- | --- |
| Quantumult X | [RevokeGuard_Enhanced_QuantumultX.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_QuantumultX.txt) |
| Surge | [RevokeGuard_Enhanced_Surge.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Surge.txt) |
| Loon | [RevokeGuard_Enhanced_Loon.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Loon.txt) |
| Shadowrocket | [RevokeGuard_Enhanced_Shadowrocket.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Shadowrocket.txt) |
| Hosts | [RevokeGuard_Enhanced_hosts.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_hosts.txt) |
| Extra domains / 增强域名 | [enhanced-domains.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/enhanced-domains.txt) |

## Usage | 使用说明

### iOS/iPadOS Profile Usage | 描述文件使用方法

1. Open the profile download link in **Safari** on your iPhone/iPad and allow the download. If you already have the old standalone normal or enhanced RevokeGuard profiles, remove them in **Settings → General → VPN & Device Management** before installing this combined profile.
   在 iPhone/iPad 的 **Safari** 中打开描述文件下载链接，允许下载。如果已安装旧版独立的普通或增强 RevokeGuard 描述文件，先到 **设置 → 通用 → VPN 与设备管理** 移除旧版，再安装合并版。
2. Open **Settings → Profile Downloaded**, or find the downloaded profile under **General → VPN & Device Management**. Tap **Install**, enter your device passcode if prompted, and confirm.
   打开 **设置 → 已下载描述文件**，或在 **通用 → VPN 与设备管理** 中找到已下载的描述文件，点击 **安装**，按提示输入设备密码并确认。
3. Go to **Settings → General → VPN & Device Management → DNS** and select **RevokeGuard Normal - Use during install**. The two DNS entries belong to the same installed profile; select one mode at a time.
   前往 **设置 → 通用 → VPN 与设备管理 → DNS**，选择 **RevokeGuard Normal - Use during install（普通，安装时使用）**。两项 DNS 属于同一份已安装描述文件，每次选择一种模式。
4. Download KSign or ESign from [Khoindvn Bypass](https://khoindvn.io.vn/#bypass), sideload your apps, and open them successfully for the first time while normal mode is selected.
   前往 [Khoindvn Bypass](https://khoindvn.io.vn/#bypass) 下载 KSign 或 ESign，在普通模式下侧载应用并完成首次成功打开。
5. Return to the **DNS** page and select **RevokeGuard Enhanced - Use after installing**. Before installing another app, updating/re-signing an app, or changing certificates, switch back to **Normal**; return to **Enhanced** after the app opens successfully. Reconnect the network after each switch. 
   回到 **DNS** 页面选择 **RevokeGuard Enhanced - Use after installing（增强，安装后使用）**。以后安装新应用、更新/重新签名应用或更换证书前，先切回 **Normal（普通）**；应用成功打开后再切回 **Enhanced（增强）**。

### Network Tools | 网络工具

Import the matching normal rule file into Quantumult X, Surge, Loon, Shadowrocket or Hosts. For enhanced protection, also enable its enhanced rule set after the first successful app launch. Disable the enhanced set before installing or re-signing apps, while keeping normal rules enabled.

将对应的普通规则导入 Quantumult X、Surge、Loon、Shadowrocket 或 Hosts。需要增强保护时，在应用首次成功打开后启用对应增强规则组；安装或重新签名应用前停用增强规则组，同时保持普通规则启用。

### Note | 注意事项

If a normally working application becomes unable to open, remove all sideloaded apps and the trusted certificate, select a new certificate, then repeat the steps above.

如果已正常使用的应用无法打开，请卸载所有侧载应用并删除已信任证书，选择新证书后重新执行以上流程。

## Credits | 致谢

- [Apple Support](https://support.apple.com/zh-cn/101555)
- [Khoindvn](https://khoindvn.io.vn/)
- [AppleJr](https://applejr.net/)
- [Sideloading / NexRevokeDNS](https://sideloading.net/dns/)

## License | 许可证

[MIT License](LICENSE)
