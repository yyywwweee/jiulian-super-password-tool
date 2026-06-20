# 项目目录结构

本项目按“一个版本号，多平台产物”的方式组织。每次正式发布应尽量同时提供 macOS 和 Windows 产物，并预留 Android 产物位。

```text
.
├── platforms/
│   ├── macos/                                # macOS 平台目录
│   │   └── Sources/JiulianSuperPasswordTool/  # macOS Swift/AppKit 前端，SwiftPM target path
│   ├── windows/                               # Windows 图形前端源码
│   │   └── jiulian_windows_tool.py
│   └── android/                               # Android 版本预留目录
├── shared/backend/                            # 跨平台复用后端 helper
├── Assets/AppIcon/                            # App 图标设计/发布资产
├── scripts/
│   ├── build_release.sh                       # macOS 一键构建：.app + .dmg + .app.zip
│   ├── build_app.sh                           # macOS .app 构建
│   ├── package_dmg.sh                         # macOS DMG 打包
│   ├── build_windows.ps1                      # Windows exe 构建，需在 Windows 环境运行
│   ├── generate_icon.py                       # 生成 macOS 图标资源
│   ├── generate_version.sh                    # 生成 macOS 版本信息源码
│   └── install_git_hooks.sh                   # 安装构建号自增 hook
├── .github/workflows/release-builds.yml       # 多平台 CI 构建和 Release 附件上传
├── VERSION                                    # 语义版本号，所有平台共用
├── BUILD_NUMBER                               # 构建号，所有平台共用
├── Package.swift                              # macOS SwiftPM 工程入口
└── docs/                                      # 项目说明、发布流程、结构文档
```

## 设计原则

1. **版本统一**：同一次 Release 的 macOS / Windows / Android 使用同一个 `VERSION` 和 `BUILD_NUMBER`。
2. **平台隔离**：平台 UI 各自独立；公共协议、后端 helper 和设计资产尽量复用；后端 helper 放在 shared/backend。
3. **产物命名统一**：GitHub Release 附件使用英文 ASCII 文件名，避免中文文件名在 GitHub 上被截断。
4. **CI 优先**：Windows 产物由 GitHub Actions 的 Windows runner 构建；macOS 产物可本地构建，也可由 macOS runner 构建。
5. **Android 预留**：当前不实现 Android，但目录和发布命名先固定，避免后续破坏结构。

## 平台产物命名

```text
JiulianSuperPasswordTool-<version>-build<build>-macos-arm64.dmg
JiulianSuperPasswordTool-<version>-build<build>-macos-arm64.app.zip
JiulianSuperPasswordTool-<version>-build<build>-windows-x64.exe
JiulianSuperPasswordTool-<version>-build<build>-android-arm64.apk   # 未来
```
