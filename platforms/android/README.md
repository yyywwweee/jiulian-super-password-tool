# Android 平台预留

这里预留 Android 版本目录。

未来 Android 版建议原则：

- 与 macOS / Windows 使用同一个 `VERSION` 版本号。
- 每次正式 Release 同步产出 Android 安装包，建议命名：
  - `JiulianSuperPasswordTool-<version>-build<build>-android-arm64.apk`
  - 如需要上架或分发多 ABI，可再补充 `.aab` 或 universal apk。
- 尽量复用核心业务协议和解析逻辑；UI 层独立实现。
- Release 说明中单独列出 Android 已知限制和权限说明。

当前状态：尚未实现。
