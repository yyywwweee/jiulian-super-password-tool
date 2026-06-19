# 九联光猫获取超级密码工具

一个桌面小工具，用于在已知光猫 Telnet 登录账号密码的前提下，连接九联光猫并获取超级管理员账号/密码。当前提供 macOS 原生版和 Windows 图形版，并按后续 Android 版扩展进行目录和发布流程设计。

> 仅用于你本人拥有或被授权维护的设备。请勿用于未授权设备。

## 功能

- 自定义光猫/路由器风格 App 图标
- macOS 原生 AppKit 图形界面
- Windows Tkinter 图形界面，打包为独立 exe 后无需用户安装 Python
- 预留 Android 版本目录和发布命名规则
- 输入光猫 IP、Telnet 端口、登录用户名和登录密码
- 自动连接设备并解析超级管理员账号/密码
- 将解密后的 XML 结果保存到用户选择的目录
- 运行日志在界面中实时显示
- 关闭窗口后进程自动退出

## 系统要求

### macOS

- macOS 13.0 或更高版本
- Apple Silicon Mac（当前发布包为 arm64）
- 系统可用 `python3`
- 目标光猫 Telnet 服务可连接，且你拥有登录凭据

### Windows

- Windows 10/11 x64
- 使用 Release 中的 Windows exe 时无需安装 Python
- 目标光猫 Telnet 服务可连接，且你拥有登录凭据

## 使用方法

### macOS

1. 下载 Release 中的 DMG。
2. 打开 DMG，将 App 拖到 Applications。
3. 启动 App，填写光猫登录信息。
4. 点击「开始获取超级密码」。

### Windows

1. 下载 Release 或 GitHub Actions 构建产物中的 Windows exe。
2. 双击启动，填写光猫登录信息。
3. 点击「开始获取超级密码」。

首次保存到 Downloads 或其他受保护目录时，macOS 可能会弹出文件夹访问授权提示，点击允许即可。

## 从源码构建

```bash
./scripts/build_release.sh
```

Windows 版在 Windows 环境中构建：

```powershell
./scripts/build_windows.ps1
```

构建产物位于 `dist/`。正式 GitHub Release 附件统一使用英文命名，例如：

- `JiulianSuperPasswordTool-<version>-build<build>-macos-arm64.dmg`
- `JiulianSuperPasswordTool-<version>-build<build>-macos-arm64.app.zip`
- `JiulianSuperPasswordTool-<version>-build<build>-windows-x64.exe`
- `JiulianSuperPasswordTool-<version>-build<build>-android-arm64.apk`（未来）

## 项目结构

项目已按多平台发布思路整理：

```text
Sources/JiulianSuperPasswordTool/          # macOS Swift/AppKit 前端
Resources/                                 # macOS 打包资源
platforms/windows/                         # Windows 图形前端
platforms/android/                         # Android 预留目录
Assets/                                    # 共用视觉资产和图标源文件
scripts/                                   # 各平台构建脚本
.github/workflows/release-builds.yml       # 多平台 CI 构建和 Release 附件上传
docs/                                      # 项目结构和发布流程说明
```

详细说明见：

- [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md)
- [`docs/RELEASE_PROCESS.md`](docs/RELEASE_PROCESS.md)

## 安全说明

- macOS App 会把登录参数缓存在用户 Home 目录下的 `.jiulian_super_password_native_cache.json`，权限设置为 `0600`。
- Windows App 会把登录参数缓存在 `%APPDATA%\JiulianSuperPasswordTool\cache.json`。
- 后端调试日志默认写入用户 Home 目录，Windows 前端调试日志写入 `%APPDATA%\JiulianSuperPasswordTool\windows_debug.log`。
- 发布包使用 ad-hoc 签名，不包含 Apple Developer ID 公证。首次运行可能需要在 macOS 安全设置中允许。

## 多平台发布策略

后续每次正式发布按同一版本号同时规划多个平台产物：

- macOS：`.dmg` + `.app.zip`
- Windows：`.exe`
- Android：未来 `.apk` / `.aab`

同一次 Release 共用 `VERSION` 和 `BUILD_NUMBER`。Release 附件统一使用英文文件名，避免 GitHub 对中文附件名截断。

## 版本机制

项目使用两层版本号：

- `VERSION`：人工维护的语义版本号，例如 `1.0.0`。
- `BUILD_NUMBER`：构建号，每次执行 `git commit` 时由本地 `pre-commit` hook 自动递增。

版本信息会自动生成到：

```text
Sources/JiulianSuperPasswordTool/GeneratedVersion.swift
```

App 界面和运行日志会显示：

```text
v1.0.0 (Build 2)
```

首次 clone 或重新配置仓库后，请执行：

```bash
./scripts/install_git_hooks.sh
```

之后每次提交时会自动：

1. 递增 `BUILD_NUMBER`
2. 重新生成 `GeneratedVersion.swift`
3. 将版本文件加入本次 commit

发布新功能版本时，手动修改 `VERSION`，例如从 `1.0.0` 改为 `1.1.0`，然后正常 commit 即可。
