# iOS-AntiRevoke-DNS-Rules

[![Build Status](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/actions/workflows/daily_update.yml/badge.svg)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/actions/workflows/daily_update.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/RzMY/IOS-AntiRevoke-DNS-Rules)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/commits/main)

Automatically discovers iOS anti-revoke domains and publishes DNS profiles plus rules for major network tools.

自动抓取 iOS 反撤销域名，并发布 DNS 描述文件及主流网络工具规则。

## Features | 特性

- Daily discovery based on [Apple's official host list](https://support.apple.com/zh-cn/101555). / 每日基于 [Apple 官方主机列表](https://support.apple.com/zh-cn/101555)更新候选域名。
- Domain data is collected from Khoindvn, AppleJr and Sideloading profiles and published lists. / 从 Khoindvn、AppleJr 与 Sideloading 的描述文件及公开列表收集域名数据。
- Publishes normal and enhanced configurations separately. / 分别发布正常配置与增强配置。
- Supports iOS/iPadOS, Quantumult X, Surge, Loon, Shadowrocket and Hosts. / 支持 iOS/iPadOS、Quantumult X、Surge、Loon、Shadowrocket 与 Hosts。
- GitHub Actions tests, validates and commits all generated artifacts. / GitHub Actions 自动测试、校验并提交产物。

## Downloads | 下载

### Normal Configuration | 正常配置

Use the normal configuration for installation and daily sideloading.

正常配置用于安装证书、签名工具及日常侧载。

| Platform / 平台 | File / 文件 |
| --- | --- |
| iOS/iPadOS | [Install profile / 安装描述文件](https://reject.rzmy.dpdns.org/download) |
| Quantumult X | [RevokeGuard_QuantumultX.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_QuantumultX.txt) |
| Surge | [RevokeGuard_Surge.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Surge.txt) |
| Loon | [RevokeGuard_Loon.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Loon.txt) |
| Shadowrocket | [RevokeGuard_Shadowrocket.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Shadowrocket.txt) |
| Hosts | [RevokeGuard_hosts.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_hosts.txt) |
| Domains / 域名 | [domains.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/domains.txt) |

### Enhanced Configuration | 增强配置

| Platform / 平台 | File / 文件 |
| --- | --- |
| iOS/iPadOS | [Install profile / 安装描述文件](https://reject.rzmy.dpdns.org/download2) |
| Quantumult X | [RevokeGuard_Enhanced_QuantumultX.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_QuantumultX.txt) |
| Surge | [RevokeGuard_Enhanced_Surge.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Surge.txt) |
| Loon | [RevokeGuard_Enhanced_Loon.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Loon.txt) |
| Shadowrocket | [RevokeGuard_Enhanced_Shadowrocket.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Shadowrocket.txt) |
| Hosts | [RevokeGuard_Enhanced_hosts.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_hosts.txt) |
| Extra domains / 增强域名 | [enhanced-domains.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/enhanced-domains.txt) |

## Usage | 使用说明

1. Install the normal anti-revoke DNS profile, or import the matching rule file into your network tool.
   安装正常反撤销 DNS 描述文件，或将对应规则导入网络工具。
2. Download KSign or ESign from [Khoindvn Bypass](https://khoindvn.io.vn/#bypass).
   前往 [Khoindvn Bypass](https://khoindvn.io.vn/#bypass) 下载 KSign 或 ESign。
3. Sideload your apps.
   侧载你的应用。

**Note 1:** If a normally working application becomes unable to open, remove all sideloaded apps and the trusted certificate, select a new certificate, then repeat the steps above.

**Note 1：** 如果已正常使用的应用无法打开，请卸载所有侧载应用并删除已信任证书，选择新证书后重新执行以上流程。

**Note 2:** If the above problems frequently occur, install or enable the enhanced configuration after the app opens successfully for the first time. Temporarily remove or disable the enhanced configuration whenever you need to sideload another app.

**Note 2：** 如果经常出现上述问题，请在应用第一次成功打开后安装或启用增强配置；之后每次需要侧载新应用时，先暂时移除或停用增强配置。

Do not enable the normal and enhanced iOS profiles at the same time. The enhanced profile already includes all normal domains. Network-tool users should keep the normal rules enabled and toggle the separate enhanced rule set as required.

请勿同时安装正常与增强 iOS 描述文件；增强描述文件已经包含全部正常域名。网络工具用户应保持正常规则启用，并按需单独开关增强规则组。

## Discovery | 规则发现

The daily workflow performs the following operations:

每日工作流执行以下操作：

1. Read candidate domains from Apple's official enterprise network page. / 从 Apple 官方企业网络页面读取候选域名。
2. Download and decode the three upstream DNS profiles. / 下载并解析三个上游 DNS 描述文件。
3. Use `DNSSettings.SupplementalMatchDomains` as target domains when no separate mode list is configured; otherwise use the configured plain-text deny list. / 未配置独立模式列表时，将 `DNSSettings.SupplementalMatchDomains` 直接作为目标域名；配置了纯文本 denylist 时优先使用该列表。
4. Process Sideloading with its mode-specific `denylist.txt` and `denylist-ppq.txt` lists. The new profile’s match-domain list is a routing scope and includes allowlist entries, so it is not published directly. / 使用 Sideloading 的 `denylist.txt` 与 `denylist-ppq.txt` 分别处理普通和增强模式。新版描述文件的 match-domain 列表只是路由范围，包含 allowlist 条目，因此不会直接发布。
5. Remove provider-owned connectivity and status-check domains, then generate normal outputs and the isolated `output/enhanced/` set. / 先移除提供商自有连通性/状态检查域名，再生成正常产物及隔离的 `output/enhanced/` 增强产物。

| Source / 来源 | Mode / 模式 | Payload identifier |
| --- | --- | --- |
| Khoindvn | Normal / 正常 | First DNS payload with a domain list or HTTPS endpoint / 首个包含域名列表或 HTTPS 端点的 DNS payload |
| AppleJr | Normal / 正常 | First DNS payload with a domain list or HTTPS endpoint / 首个包含域名列表或 HTTPS 端点的 DNS payload |
| Sideloading | Normal / 正常 | `novadev.nexrevokedns.whileinstalling`|
| Sideloading | Enhanced / 增强 | `novadev.nexrevokedns.afterinstalling`|

## Credits | 致谢

- [Apple Support](https://support.apple.com/zh-cn/101555)
- [Khoindvn](https://khoindvn.io.vn/)
- [AppleJr](https://applejr.net/)
- [Sideloading / NexRevokeDNS](https://sideloading.net/dns/)

## License | 许可证

[MIT License](LICENSE)
