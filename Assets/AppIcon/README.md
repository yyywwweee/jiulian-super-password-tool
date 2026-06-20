# App 图标资产

图标属于设计/发布资产，不是普通构建中间产物。

## 目录

```text
Assets/AppIcon/
├── source/AppIcon-1024.png          # 图标源图 / 母版
├── macos/AppIcon.icns               # macOS App 打包使用
├── macos/AppIcon.iconset/           # macOS 多尺寸图标资产
└── windows/AppIcon.ico              # Windows exe 打包使用
```

## 规则

- 普通构建脚本只复制或引用这里已经提交的图标资产。
- 普通构建不应重新生成图标，也不应修改本目录。
- 只有需要修改图标设计时，才运行：

```bash
python3 scripts/generate_icon.py
```

然后检查生成结果，并把更新后的图标资产一起提交。

## 平台使用

- macOS：`scripts/build_app.sh` 复制 `Assets/AppIcon/macos/AppIcon.icns` 到 `.app/Contents/Resources/AppIcon.icns`。
- Windows：`scripts/build_windows.ps1` 将 `Assets/AppIcon/windows/AppIcon.ico` 传给 PyInstaller 的 `--icon`。
- Android：未来从同一源图导出 Android 所需 mipmap/adaptive icon 资产。
