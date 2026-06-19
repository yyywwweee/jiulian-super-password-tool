# 多平台发布流程

本项目发布策略：**同一个 GitHub Release 同时承载 macOS、Windows，未来再加入 Android。**

## 版本规则

- `VERSION`：语义版本号，例如 `1.0.1`、`1.1.0`。
- `BUILD_NUMBER`：构建号，提交时由本地 pre-commit hook 自动递增。
- Release tag：使用 `v<VERSION>`，例如 `v1.0.1`。

## 每次发布应包含的产物

当前：

- macOS：`.dmg`，推荐普通用户安装。
- macOS：`.app.zip`，归档版。
- Windows：`.exe`，独立可执行文件。

未来：

- Android：`.apk` 或 `.aab`。

## 标准附件命名

GitHub Release 附件统一使用英文文件名：

```text
JiulianSuperPasswordTool-<version>-build<build>-macos-arm64.dmg
JiulianSuperPasswordTool-<version>-build<build>-macos-arm64.app.zip
JiulianSuperPasswordTool-<version>-build<build>-windows-x64.exe
JiulianSuperPasswordTool-<version>-build<build>-android-arm64.apk
```

不要直接上传中文文件名，GitHub 可能会截断附件名。

## 推荐发布步骤

1. 修改 `VERSION`。
2. 提交代码，让 pre-commit hook 递增 `BUILD_NUMBER` 并生成版本信息。
3. 推送 `main`。
4. 创建 GitHub Release：

   ```bash
   gh release create v<VERSION> \
     --target main \
     --title "九联光猫获取超级密码工具 v<VERSION>" \
     --notes-file /tmp/release-notes.md
   ```

5. GitHub Actions 自动构建并上传：
   - macOS DMG / app.zip
   - Windows exe
   - Android 未来加入

6. 检查 Release 附件是否齐全、命名是否正确。

## Release 说明模板

```markdown
## 更新说明

### macOS

- ...

### Windows

- ...

### Android

- 暂未提供，已预留后续版本。

### 通用修改

- ...

### 注意事项

- macOS 发布包为 ad-hoc 签名，未进行 Apple Developer ID 公证。
- Windows exe 未进行代码签名时，SmartScreen 可能提示风险，需要用户手动允许运行。
```
