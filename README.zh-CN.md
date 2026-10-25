# iOS-AntiRevoke-DNS-Rules

[English](README.md) | **简体中文**

[![构建状态](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/actions/workflows/daily_update.yml/badge.svg)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/actions/workflows/daily_update.yml)
[![许可证：MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![最近提交](https://img.shields.io/github/last-commit/RzMY/IOS-AntiRevoke-DNS-Rules)](https://github.com/RzMY/IOS-AntiRevoke-DNS-Rules/commits/main)

自动抓取 iOS 反撤销域名，并发布 DNS 描述文件及主流网络工具规则。

## 特性

- 每日基于 [Apple 官方主机列表](https://support.apple.com/zh-cn/101555)更新候选域名。
- 从 Khoindvn、AppleJr 与 Sideloading 的描述文件及公开列表收集域名数据。
- 一份 iOS 描述文件包含可切换的普通与增强 DNS 配置；网络工具规则仍分组发布。
- 支持 iOS/iPadOS、Quantumult X、Surge、Loon、Shadowrocket 与 Hosts。
- GitHub Actions 自动测试、校验并提交产物。

## 下载

### iOS/iPadOS 描述文件

| 平台 | 文件 |
| --- | --- |
| iOS/iPadOS | [RevokeGuard.mobileconfig — 普通 + 增强](https://reject.rzmy.dpdns.org/download) |

### 普通规则

| 平台 | 文件 |
| --- | --- |
| Quantumult X | [RevokeGuard_QuantumultX.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_QuantumultX.txt) |
| Surge | [RevokeGuard_Surge.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Surge.txt) |
| Loon | [RevokeGuard_Loon.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Loon.txt) |
| Shadowrocket | [RevokeGuard_Shadowrocket.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_Shadowrocket.txt) |
| Hosts | [RevokeGuard_hosts.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/RevokeGuard_hosts.txt) |
| 域名 | [domains.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/domains.txt) |

### 增强规则

| 平台 | 文件 |
| --- | --- |
| Quantumult X | [RevokeGuard_Enhanced_QuantumultX.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_QuantumultX.txt) |
| Surge | [RevokeGuard_Enhanced_Surge.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Surge.txt) |
| Loon | [RevokeGuard_Enhanced_Loon.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Loon.txt) |
| Shadowrocket | [RevokeGuard_Enhanced_Shadowrocket.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_Shadowrocket.txt) |
| Hosts | [RevokeGuard_Enhanced_hosts.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/RevokeGuard_Enhanced_hosts.txt) |
| 增强域名 | [enhanced-domains.txt](https://raw.githubusercontent.com/RzMY/IOS-AntiRevoke-DNS-Rules/main/output/enhanced/enhanced-domains.txt) |

## 使用说明

### 描述文件使用方法

1. 在 iPhone/iPad 的 **Safari** 中打开描述文件下载链接，允许下载。如果已安装旧版独立的普通或增强 RevokeGuard 描述文件，先到 **设置 → 通用 → VPN 与设备管理** 移除旧版，再安装合并版。
2. 打开 **设置 → 已下载描述文件**，或在 **通用 → VPN 与设备管理** 中找到已下载的描述文件，点击 **安装**，按提示输入设备密码并确认。
3. 前往 **设置 → 通用 → VPN 与设备管理 → DNS**，选择 **RevokeGuard Normal - Use during install（普通，安装时使用）**。
4. 前往 [Khoindvn Bypass](https://khoindvn.io.vn/#bypass) 下载 KSign 或 ESign，在普通模式下侧载应用并完成首次成功打开。
5. 回到 **DNS** 页面选择 **RevokeGuard Enhanced - Use after installing（增强，安装后使用）**。
6. 以后安装新应用、更新/重新签名应用或更换证书前，先切回 **Normal（普通）**，应用成功打开后再切回 **Enhanced（增强）**。

### 网络工具

1. 从上方 **普通规则** 与 **增强规则** 下载表中复制对应工具的链接，分别导入，可命名为 **RevokeGuard Normal（普通）** 与 **RevokeGuard Enhanced（增强）**，方便单独开关增强组。
2. 在配置证书或安装应用前，只启用 **普通组**。保留规则中的 **REJECT / reject（拒绝）** 动作，将规则放在可能优先匹配的 **DIRECT（直连）**、代理规则或最终兜底规则之前，保存并应用配置。启动网络工具并使用按规则分流的模式，确保规则生效。
3. 在普通模式生效后，前往 [Khoindvn Bypass](https://khoindvn.io.vn/#bypass) 下载 KSign 或 ESign，配置证书、侧载应用，并完成首次成功打开。整个过程保持增强组停用。
4. 应用成功打开后，启用 **增强组**，同时保持 **普通组** 启用。
5. 以后安装新应用、更新/重新签名应用或更换证书前，先停用 **增强组**，保持 **普通组** 启用，应用成功打开再启用 **增强组**。

### 注意事项

1. 如果已正常使用的应用无法打开，请卸载所有侧载应用并删除已信任证书，选择新证书后重新执行以上流程。
2. 推荐使用网络工具的同时也添加描述文件，防止网络状态变更造成规则意外失效
3. 重启手机之前请开启飞行模式，防止系统初始化时造成的规则意外失效

## 致谢

- [Apple 支持](https://support.apple.com/zh-cn/101555)
- [Khoindvn](https://khoindvn.io.vn/)
- [AppleJr](https://applejr.net/)
- [Sideloading / NexRevokeDNS](https://sideloading.net/dns/)

## 许可证

[MIT 许可证](LICENSE)
