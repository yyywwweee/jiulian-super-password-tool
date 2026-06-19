# 九联光猫获取超级密码工具

一个 macOS 原生小工具，用于在已知光猫 Telnet 登录账号密码的前提下，连接九联光猫并获取超级管理员账号/密码。

> 仅用于你本人拥有或被授权维护的设备。请勿用于未授权设备。

## 功能

- macOS 原生 AppKit 图形界面
- 输入光猫 IP、Telnet 端口、登录用户名和登录密码
- 自动连接设备并解析超级管理员账号/密码
- 将解密后的 XML 结果保存到用户选择的目录
- 运行日志在界面中实时显示
- 关闭窗口后进程自动退出

## 系统要求

- macOS 13.0 或更高版本
- Apple Silicon Mac（当前发布包为 arm64）
- 系统可用 `python3`
- 目标光猫 Telnet 服务可连接，且你拥有登录凭据

## 使用方法

1. 下载 Release 中的 DMG。
2. 打开 DMG，将 App 拖到 Applications。
3. 启动 App，填写光猫登录信息。
4. 点击「开始获取超级密码」。

首次保存到 Downloads 或其他受保护目录时，macOS 可能会弹出文件夹访问授权提示，点击允许即可。

## 从源码构建

```bash
./scripts/build_release.sh
```

构建产物位于 `dist/`：

- `九联光猫获取超级密码工具.app`
- `九联光猫获取超级密码工具-1.0.dmg`

## 项目结构

```text
Sources/JiulianSuperPasswordTool/main.swift   # macOS AppKit 前端
Resources/jiulian_backend_helper.py           # 后端 helper，随 App 打包
scripts/build_app.sh                          # 构建 .app
scripts/package_dmg.sh                        # 生成 DMG
scripts/build_release.sh                      # 一键构建 release
```

## 安全说明

- App 会把登录参数缓存在用户 Home 目录下的 `.jiulian_super_password_native_cache.json`，权限设置为 `0600`。
- 后端调试日志默认写入用户 Home 目录，权限设置为 `0600`。
- 发布包使用 ad-hoc 签名，不包含 Apple Developer ID 公证。首次运行可能需要在 macOS 安全设置中允许。

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
