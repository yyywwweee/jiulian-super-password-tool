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

1. 确认本地 Git hook 已安装：`./scripts/install_git_hooks.sh`。
2. 修改 `VERSION`，不要手写或猜测最终 `BUILD_NUMBER`。
3. 提交代码，让 pre-commit hook 自动递增 `BUILD_NUMBER` 并把版本文件加入本次 commit。
4. 推送 `main`。
5. 创建 GitHub Release：

   ```bash
   gh release create v<VERSION> \
     --target main \
     --title "九联光猫获取超级密码工具 v<VERSION>" \
     --notes-file /tmp/release-notes.md
   ```

6. GitHub Actions 自动构建并上传：
   - macOS DMG / app.zip
   - Windows exe
   - Android 未来加入

7. 检查 Release 附件是否齐全、命名是否正确。
8. 如需本地/NAS 归档，Release 完成后把 GitHub Actions 或 Release 中生成的 Windows exe 回拷到本机 `dist/windows/`，并复制到 NAS 对应版本目录。不要只归档本地 macOS DMG/ZIP。

## Release 说明模板

Release 页面已经有标题，notes 文件不要再重复写一级标题；正文统一使用 `## 更新说明`。

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

## 发布后本地/NAS 归档

`build_release.sh` 只会归档本机生成的 macOS `.dmg` 和 `.app.zip`。正式发布后，Windows exe 由 GitHub Actions 的 Windows runner 生成，需要从 GitHub Release 或 Actions artifact 下载回本机，再放入同一个 NAS 版本目录。

示例：

```text
dist/windows/JiulianSuperPasswordTool-<version>-build<build>-windows-x64.exe
/Volumes/西数紫盘4T/jiulian-super-password-tool-releases/v<version>/build<build>/
```

## 本地构建归档

本机执行：

```bash
./scripts/build_release.sh
```

除了生成 `dist/` 下的本地 macOS 产物外，如果 NAS 磁盘已挂载，还会自动复制一份到：

```text
/Volumes/西数紫盘4T/jiulian-super-password-tool-releases/v<VERSION>/build<BUILD_NUMBER>/
```

可通过环境变量覆盖归档根目录：

```bash
JIULIAN_RELEASE_ARCHIVE_ROOT=/path/to/archive ./scripts/build_release.sh
```

如果 NAS 未挂载，归档步骤会跳过，不影响本地构建成功。GitHub Actions 环境会明确跳过该 NAS 归档步骤。
