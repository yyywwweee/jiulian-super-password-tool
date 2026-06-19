# macOS 平台

macOS 版本使用 Swift / AppKit 实现，SwiftPM target 源码位于：

```text
platforms/macos/Sources/JiulianSuperPasswordTool/
```

macOS 平台资源位于：

```text
platforms/macos/Resources/
```

后端 helper 不再放在 macOS 资源目录，而是统一放在：

```text
shared/backend/jiulian_backend_helper.py
```

构建脚本：

```bash
./scripts/build_release.sh
```
