# iOS-AntiRevoke-DNS-Rules

[![Build Status](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/workflows/Daily%20iOS%20Anti-Revoke%20Profile%20Update/badge.svg)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/RzMY/IOS-AntiRevoke-DNS-Rules)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/commits/main)
[![GitHub Stars](https://img.shields.io/github/stars/RzMY/IOS-AntiRevoke-DNS-Rules?style=social)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/stargazers)

> 🛡️ An automated, stateless iOS Anti-Revoke & Anti-Blacklist solution powered by Cloudflare Workers DoH.  
> 🛡️ 基于 Cloudflare Workers DoH 的自动化、无状态 iOS 防撤销与防黑名单解决方案。

---

## ✨ Features | 特性

### 🚀 **Auto-Sync | 自动同步**
- Daily automated scraping from **Khoindvn** & **AppleJr** via GitHub Actions
- 每日自动从 **Khoindvn** 与 **AppleJr** 抓取最新规则（GitHub Actions）

### ⚡ **Stateless Backend | 无状态后端**
- Uses a high-performance **"Always-NXDOMAIN"** DNS-over-HTTPS server: `reject.rzmy.dpdns.org`
- **Zero logging, zero latency overhead** for blocked domains - instant rejection
- 采用高性能"永久 NXDOMAIN"DoH 服务器：`reject.rzmy.dpdns.org`
- **无日志、零延迟开销** - 被阻止域名立即返回不存在

### ✅ **Signed Profile | 签名配置文件**
- Automatically signed with a valid certificate for **green "Verified"** status on iOS
- 使用有效证书自动签名，在 iOS 上显示**绿色"已验证"**状态

### 📦 **Multi-Format Output | 多格式输出**
- iOS Native: `.mobileconfig` profile
- Quantumult X, Loon, Surge, Shadowrocket: Rule files
- 支持多种代理工具规则格式

### 🔒 **Privacy First | 隐私优先**
- **No logging, no tracking** - Backend is a stateless Cloudflare Worker
- Works alongside VPN in most configurations
- **无日志、无跟踪** - 后端为无状态 Cloudflare Worker
- 大多数配置下可与 VPN 并存

---

## 📥 Usage | 使用方法

### 🎯 Quick Install | 快速安装

<div align="center">

<a href="https://reject.rzmy.dpdns.org/download">
  <img src="https://img.shields.io/badge/📲_Install_Profile-007AFF?style=for-the-badge&logo=apple&logoColor=white" alt="Install iOS Profile">
</a>

**Tap the button above on your iOS device to install directly**  
**在 iOS 设备上点击上方按钮直接安装**

</div>

---

### 📋 Platform-Specific Downloads | 平台专用下载

| Platform<br/>平台 | Format<br/>格式 | Link<br/>链接 | Description<br/>说明 |
|:---|:---|:---|:---|
| **🍎 iOS Native** | `.mobileconfig` (Signed) | [📲 Install Profile](https://reject.rzmy.dpdns.org/download) | Native DNS profile<br/>原生 DNS 配置文件 |
| **Ⓠ Quantumult X** | Rule Snippet | [📄 View Rules](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_QuantumultX.txt) | `host, domain, reject`<br/>主机规则格式 |
| **🦁 Loon** | Rule Plugin | [📄 View Rules](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Loon.txt) | `DOMAIN,domain,REJECT`<br/>域名规则格式 |
| **🌊 Surge** | Domain Set | [📄 View Rules](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Surge.txt) | `DOMAIN,domain,REJECT`<br/>域名规则格式 |
| **🚀 Shadowrocket** | Rule List | [📄 View Rules](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Shadowrocket.txt) | `DOMAIN,domain,REJECT`<br/>域名规则格式 |
| **🗂️ Hosts Format** | Hosts File | [📄 View Hosts](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_hosts.txt) | `0.0.0.0 domain`<br/>Hosts 文件格式 |
| **📝 Plain List** | Domain List | [📄 View Domains](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/domains.txt) | Plain domain list<br/>纯域名列表 |

---

### 📱 Installation Guide | 安装指南

#### For iOS Native Profile | iOS 原生配置文件安装

1. **Safari Download** | **Safari 下载**
   - Tap the **Install Profile** button above on your iOS device
   - 在 iOS 设备上使用 Safari 点击上方的**安装配置文件**按钮

2. **Open Settings** | **打开设置**
   - Go to: **Settings** → **Profile Downloaded** (or **VPN & Device Management**)
   - 前往：**设置** → **已下载描述文件**（或 **VPN 与设备管理**）

3. **Install** | **安装**
   - Tap **Install** in the top right corner
   - Enter your passcode if prompted
   - Tap **Install** again to confirm
   - 点击右上角的**安装**
   - 如提示，输入设备密码
   - 再次点击**安装**确认

4. **Verification** | **验证**
   - Look for the **green "Verified"** badge ✅
   - Profile name: **RevokeGuard [YYYY-MM-DD]**
   - 查看配置文件是否显示**绿色"已验证"**标识 ✅
   - 配置文件名称：**RevokeGuard [YYYY-MM-DD]**

#### For Proxy Tools | 代理工具配置

**Quantumult X:**
```
[filter_remote]
https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_QuantumultX.txt, tag=Anti-Revoke, enabled=true
```

**Loon:**
```
[Remote Rule]
https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Loon.txt, policy=REJECT, tag=Anti-Revoke, enabled=true
```

**Surge:**
```
[Rule]
RULE-SET,https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Surge.txt,REJECT
```

**Shadowrocket:**
```
[Remote Rule]
https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Shadowrocket.txt
```

> 💡 **Tip | 提示**: Import these rules into your **"REJECT"** policy group for best results.  
> 💡 **提示**: 将这些规则导入到您的 **"拒绝"** 策略组以获得最佳效果。

> ⚠️ **Important for Proxy Tool Users | 代理工具用户重要提示**:  
> Even if you use proxy tools like Quantumult X (which take over system DNS), **we still recommend installing the iOS native profile as well**. This provides redundant protection and prevents blocking failures when you toggle the proxy app on/off or during network state changes (WiFi ↔ Cellular, VPN switching, etc.).
> 
> 即使您使用 Quantumult X 等代理工具（会接管系统 DNS），**仍然建议同时安装 iOS 原生配置文件**。这提供了冗余保护，可以防止在开关代理软件或网络状态变更时（WiFi ↔ 蜂窝数据、VPN 切换等）造成的拦截失效。

---

## 🏗️ Architecture | 架构

### How It Works | 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                    Daily Automation Flow                     │
│                      每日自动化流程                           │
└─────────────────────────────────────────────────────────────┘

1️⃣  GitHub Actions (Daily 00:00 UTC)
    │
    ├──► Scrapes Khoindvn.io.vn
    ├──► Scrapes AppleJr.net
    └──► Extracts & Merges Domain Lists
         │
         ▼
2️⃣  Profile Generation
    │
    ├──► Creates .mobileconfig pointing to:
    │    https://reject.rzmy.dpdns.org/dns-query
    ├──► Signs with valid certificate
    └──► Generates proxy tool rules
         │
         ▼
3️⃣  Commit & Push to Repository
    │
    └──► Users download latest files via raw.githubusercontent.com

┌─────────────────────────────────────────────────────────────┐
│                     Runtime Flow (iOS)                       │
│                   运行时流程 (iOS 端)                         │
└─────────────────────────────────────────────────────────────┘

iOS Device Queries Blocked Domain
         │
         ▼
DNS Request → reject.rzmy.dpdns.org (DoH)
         │
         ▼
Cloudflare Worker (Stateless)
         │
         ├──► No logging ❌
         ├──► No IP tracking ❌
         └──► Returns: NXDOMAIN (RCODE 3) ⚡
              │
              ▼
iOS: "Domain does not exist" → App fails to validate → ✅ Success!
```

### Backend Details | 后端详情

- **Service | 服务**: Cloudflare Workers DNS-over-HTTPS
- **Endpoint | 端点**: `https://reject.rzmy.dpdns.org/dns-query`
- **Response | 响应**: Always `NXDOMAIN` (RCODE 3) for ALL queries
- **Logging | 日志**: **None** - Completely stateless
- **Performance | 性能**: <10ms latency, globally distributed CDN
- **Privacy | 隐私**: Zero data retention, no IP tracking

---

## 🔒 Privacy Statement | 隐私声明

### English

**Your privacy is our priority.**

The backend DNS-over-HTTPS service (`reject.rzmy.dpdns.org`) is powered by a **stateless Cloudflare Worker**:

- ✅ **No logging** - Zero query logs, zero user IP logs
- ✅ **No tracking** - No analytics, no identifiers, no cookies
- ✅ **Blind rejection** - Returns `NXDOMAIN` to all requests without inspection
- ✅ **Open source** - All code is available in this repository
- ✅ **Edge computing** - Runs on Cloudflare's global network (200+ data centers)

**What data is collected?** **NONE.**

The Worker script is designed to immediately return a negative response without processing, storing, or transmitting any query data.

### 中文

**您的隐私是我们的首要任务。**

后端 DNS-over-HTTPS 服务（`reject.rzmy.dpdns.org`）基于**无状态 Cloudflare Worker** 运行：

- ✅ **无日志** - 零查询日志、零用户 IP 日志
- ✅ **无跟踪** - 无分析、无标识符、无 Cookie
- ✅ **盲拒绝** - 对所有请求返回 `NXDOMAIN`，无需检查内容
- ✅ **开源** - 所有代码均在本仓库中公开
- ✅ **边缘计算** - 运行在 Cloudflare 全球网络（200+ 数据中心）

**会收集什么数据？** **没有任何数据。**

Worker 脚本被设计为立即返回否定响应，不处理、存储或传输任何查询数据。

---

## ⚠️ Important Notes | 重要说明

### Compatibility | 兼容性

- ✅ **iOS 14.0+** - Full support for DNS Settings payload
- ✅ **iPadOS 14.0+** - Full support
- ⚠️ **VPN Compatibility** - May work alongside some VPNs, but not guaranteed (DNS profiles have priority in some configurations)
- ⚠️ **VPN 兼容性** - 可能与某些 VPN 共存，但不保证（某些配置下 DNS 配置文件优先级更高）

### Limitations | 局限性

- This profile only affects DNS queries for the specified domains
- Apps using hard-coded IP addresses may bypass this protection
- Certificate trust apps (e.g., TrollStore) are unaffected
- 此配置文件仅影响指定域名的 DNS 查询
- 使用硬编码 IP 地址的应用可能绕过此保护
- 证书信任类应用（如 TrollStore）不受影响

### Removal | 卸载

To remove the profile:
1. Go to **Settings** → **General** → **VPN & Device Management**
2. Select the **RevokeGuard** profile
3. Tap **Remove Profile**

卸载配置文件：
1. 前往 **设置** → **通用** → **VPN 与设备管理**
2. 选择 **RevokeGuard** 配置文件
3. 点击**移除描述文件**

---

## 🙏 Credits & References | 致谢与参考

### Domain Sources | 域名来源

- [**Khoindvn**](https://khoindvn.io.vn/) - iOS Anti-Revoke domain list
- [**AppleJr**](https://applejr.net/) - iOS Anti-Blacklist domain list

### Technology Stack | 技术栈

- **Backend** | **后端**: Cloudflare Workers (DNS-over-HTTPS)
- **Automation** | **自动化**: GitHub Actions
- **Signing** | **签名**: OpenSSL CMS/PKCS#7
- **Language** | **语言**: Python 3.11+

### Acknowledgments | 鸣谢

Special thanks to:
- All contributors who maintain the upstream domain lists
- The open-source community for tools and libraries
- Cloudflare for providing free edge computing infrastructure

特别感谢：
- 所有维护上游域名列表的贡献者
- 提供工具和库的开源社区
- Cloudflare 提供的免费边缘计算基础设施

---

## 📊 Statistics | 统计信息

- **Update Frequency** | **更新频率**: Daily at 00:00 UTC | 每日 UTC 00:00
- **Domain Count** | **域名数量**: See `metadata.json` in `output/` folder | 查看 `output/` 文件夹中的 `metadata.json`
- **Last Update** | **最后更新**: Check commit history | 查看提交历史

---

## 🤝 Contributing | 贡献

Contributions are welcome! Please feel free to submit a Pull Request.

欢迎贡献！请随时提交 Pull Request。

### Development Setup | 开发环境设置

```bash
# Clone repository | 克隆仓库
git clone https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules.git
cd IOS-AntiRevoke-DNS-Rules

# Install dependencies | 安装依赖
pip install -r requirements.txt

# Run pipeline | 运行流水线
python main.py
```

For detailed documentation, see:
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide | 快速入门
- [SETUP.md](SETUP.md) - Detailed setup | 详细设置
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture | 系统架构

---

## 📄 License | 许可证

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

本项目采用 **MIT 许可证** - 详见 [LICENSE](LICENSE) 文件。

---

## ⭐ Star History | 星标历史

[![Star History Chart](https://api.star-history.com/svg?repos=RzMY/IOS-AntiRevoke-DNS-Rules&type=Date)](https://star-history.com/#RzMY/IOS-AntiRevoke-DNS-Rules&Date)

---

## 📞 Support | 支持

- **Issues** | **问题反馈**: [GitHub Issues](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/issues)
- **Discussions** | **讨论**: [GitHub Discussions](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/discussions)

---

<div align="center">

### Made with ❤️ by RzMY

**If this project helps you, please consider giving it a ⭐!**  
**如果这个项目对您有帮助，请考虑给它一个 ⭐！**

[⬆ Back to Top | 返回顶部](#ios-antirevoke-dns-rules)

</div>
