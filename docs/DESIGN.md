# 设计文档

## 1. 项目概述

九联光猫获取超级密码工具是一个面向桌面的多平台工具。用户在已获得授权并掌握光猫 Telnet 登录凭据的前提下，通过图形界面输入设备地址、端口、用户名、密码和保存目录，工具连接目标设备，解析超级管理员账号/密码，并将解密后的 XML 结果保存到本机。

当前已实现：

- macOS 原生 AppKit 图形界面。
- Windows Tkinter 图形界面。
- Python 后端 helper 作为跨平台核心逻辑。
- macOS / Windows 构建脚本与 GitHub Actions 发布流程。
- Android 目录和发布命名规则预留。

项目边界：

- 本工具只面向本人拥有或被授权维护的设备。
- 不负责开启目标设备 Telnet 服务。
- 不保证兼容所有九联设备型号和固件版本。
- 不提供云端服务，所有凭据、日志和结果均在本机处理。

## 2. 总体架构

项目采用“平台 UI 独立、核心后端复用、发布流程统一”的结构。

```text
用户
  |
  | 输入连接信息 / 选择保存目录 / 点击开始
  v
平台 UI 层
  |-- macOS: Swift + AppKit
  |-- Windows: Python + Tkinter
  |
  | JSON 参数 / 流式日志 / 最终结果
  v
共享后端层
  |-- shared/backend/jiulian_backend_helper.py
  |
  | Telnet 登录 / 远端命令 / base64 传回 / XML 解析
  v
目标光猫设备
```

核心设计原则：

- 平台隔离：macOS 和 Windows 各自维护原生 UI，不共享界面代码。
- 核心复用：设备连接、远端执行、结果解析集中在 `shared/backend`。
- 协议简单：前端与后端之间使用 JSON 字段传参和返回结果。
- 产物统一：同一次 Release 共用 `VERSION` 和 `BUILD_NUMBER`。
- 本地优先：不依赖外部服务，结果文件和缓存文件都写入用户本机。

## 3. 目录职责

```text
Package.swift
  macOS SwiftPM 工程入口。

platforms/macos/
  macOS 平台实现，包含 AppKit UI、图标资源和生成版本信息。

platforms/windows/
  Windows 平台实现，包含 Tkinter UI 和 PyInstaller 入口。

platforms/android/
  Android 平台预留目录，当前尚未实现。

shared/backend/
  跨平台复用的 Python 后端 helper。

Assets/
  共用图标源文件和生成后的图标资源。

scripts/
  构建、打包、版本生成、图标生成和 hook 安装脚本。

docs/
  项目结构、发布流程和设计文档。

.github/workflows/
  GitHub Actions 多平台构建和 Release 附件上传流程。
```

## 4. 模块设计

### 4.1 macOS 前端

入口文件：

- `platforms/macos/Sources/JiulianSuperPasswordTool/main.swift`

主要职责：

- 构建 AppKit 窗口、表单、状态区、结果区和日志区。
- 加载和保存用户输入缓存。
- 校验 IP、端口、用户名、密码等基础输入。
- 将请求参数序列化为 JSON，通过 stdin 传给 Python helper。
- 从 helper stdout 按行读取 JSON，实时刷新日志和最终结果。
- 将 helper stderr 或非 JSON 输出写入本机调试日志。

关键对象：

- `AppConstants`：应用名称、缓存文件路径。
- `Cache`：本地缓存模型。
- `RunResult`：后端运行结果模型。
- `Runner`：负责启动 Python 子进程、处理流式输出。
- `AppDelegate`：负责 UI 生命周期和用户交互。

macOS 缓存位置：

```text
~/.jiulian_super_password_native_cache.json
```

缓存文件权限会设置为 `0600`。

### 4.2 Windows 前端

入口文件：

- `platforms/windows/jiulian_windows_tool.py`

主要职责：

- 构建 Tkinter 窗口、连接信息表单、结果区和日志区。
- 加载和保存 `%APPDATA%` 下的用户输入缓存。
- 在后台线程运行后端逻辑，避免阻塞 UI。
- 通过队列把后端日志和结果切回主线程显示。
- 支持 PyInstaller onefile 打包后的资源路径解析。

关键对象：

- `App`：Tkinter 应用主类。
- `resource_root()`：处理源码运行和 PyInstaller 运行时资源根路径。
- `load_backend_module()`：动态加载共享后端 helper。
- `log_queue`：后端线程与 UI 主线程之间的消息队列。

Windows 缓存位置：

```text
%APPDATA%\JiulianSuperPasswordTool\cache.json
```

### 4.3 共享后端 helper

入口文件：

- `shared/backend/jiulian_backend_helper.py`

主要职责：

- 校验请求参数。
- 建立 Telnet 连接并完成登录。
- 在设备侧检查配置文件是否存在。
- 在设备侧调用解密命令生成临时 XML。
- 通过 base64 将临时 XML 传回本机。
- 解析 XML 中的超级管理员账号和密码字段。
- 将原始 XML 保存到用户指定目录。
- 根据设置清理设备侧临时文件。
- 输出结构化日志和最终结果。

重要常量：

```python
REMOTE_ENCRYPTED_FILE = "/config/workb/backup_lastgood.xml"
REMOTE_DECRYPT_SCRIPT = "/home/cli/decrypt/decrypt_file"
```

后端调试日志位置：

```text
~/jiulian_super_password_backend_debug.log
```

## 5. 前后端通信协议

### 5.1 请求参数

前端向后端传入 JSON 对象：

```json
{
  "host": "192.168.0.1",
  "port": "23",
  "user": "root",
  "password": "登录密码",
  "output_dir": "/Users/example/Downloads",
  "clean_tmp": true,
  "stream": true
}
```

字段说明：

- `host`：目标光猫 IP 或主机名。
- `port`：Telnet 端口，默认 `23`。
- `user`：Telnet 登录用户名。
- `password`：Telnet 登录密码。
- `output_dir`：本机结果保存目录。
- `clean_tmp`：完成后是否清理设备侧临时文件。
- `stream`：是否开启流式 JSON 日志输出。

### 5.2 流式日志

后端在 `stream=true` 时输出多行 JSON，每行一个对象：

```json
{
  "type": "log",
  "time": "12:00:00",
  "message": "步骤 1/5：正在连接光猫…",
  "level": "info"
}
```

日志级别：

- `info`：普通进度。
- `success`：成功完成。
- `error`：失败或异常。

### 5.3 最终结果

成功时：

```json
{
  "type": "result",
  "ok": true,
  "super_account": "账号",
  "super_password": "密码",
  "output_file": "/path/to/jiulian_super_password_192.168.0.1_20260620_120000.xml"
}
```

失败时：

```json
{
  "type": "result",
  "ok": false,
  "error": "失败原因"
}
```

## 6. 核心业务流程

```text
1. 前端校验输入
2. 前端保存缓存
3. 前端启动后端任务
4. 后端创建输出目录
5. 后端连接 Telnet 服务
6. 后端完成用户名和密码登录
7. 后端检查设备配置文件
8. 后端调用设备侧解密命令
9. 后端读取解密后的临时 XML
10. 后端解析超级管理员账号/密码
11. 后端保存 XML 到本机
12. 后端按设置清理设备侧临时文件
13. 前端展示结果并恢复按钮状态
```

远端命令执行采用 marker 包裹：

- 命令开始前输出唯一 marker。
- 命令结束后输出返回码和 end marker。
- 本机读取 Telnet 输出直到发现 end marker。
- 如果超时未发现 end marker，则记录调试日志并返回用户可理解的错误。

结果传输采用 base64：

- 设备侧执行 `base64 <remote_tmp>`。
- 输出用 `__OC_B64_BEGIN__` 和 `__OC_B64_END__` 包裹。
- 本机只收集合法 base64 行。
- 解码失败会被视为结果校验失败。

## 7. 数据与文件设计

### 7.1 用户输入缓存

缓存内容包含：

- 光猫地址。
- Telnet 端口。
- 登录用户名。
- 登录密码。
- 保存目录。
- 是否清理临时数据。

注意：当前登录密码以明文写入本机缓存，UI 也明文展示。README 和界面文案已提示这一点。

### 7.2 输出结果文件

输出文件命名：

```text
jiulian_super_password_<safe_host>_<yyyyMMdd_HHmmss>.xml
```

其中 `safe_host` 会替换不适合文件名的字符，降低路径和文件名风险。

### 7.3 调试日志

调试日志只用于排查异常，不进入 UI 主日志：

- macOS 前端：`~/jiulian_super_password_native_debug.log`
- 共享后端：`~/jiulian_super_password_backend_debug.log`
- Windows 前端：`%APPDATA%\JiulianSuperPasswordTool\windows_debug.log`

## 8. 构建与发布设计

### 8.1 版本机制

版本文件：

- `VERSION`：人工维护的语义版本号。
- `BUILD_NUMBER`：构建号。

macOS 版本源码：

- `platforms/macos/Sources/JiulianSuperPasswordTool/GeneratedVersion.swift`

生成脚本：

- `scripts/generate_version.sh`

提交时可通过 `hooks/pre-commit` 自动递增构建号并重新生成版本源码。

### 8.2 macOS 构建

构建脚本：

- `scripts/build_app.sh`
- `scripts/package_dmg.sh`
- `scripts/build_release.sh`

主要步骤：

1. 生成 `GeneratedVersion.swift`。
2. 使用 SwiftPM 构建 release 可执行文件。
3. 组装 `.app` bundle。
4. 拷贝 Python helper 和图标资源到 bundle。
5. 生成 `Info.plist`。
6. 使用 ad-hoc codesign 签名。
7. 生成 `.app.zip` 和 `.dmg`。

### 8.3 Windows 构建

构建脚本：

- `scripts/build_windows.ps1`

主要步骤：

1. 安装 PyInstaller 和 Pillow。
2. 从 PNG 生成 Windows `.ico`。
3. 使用 PyInstaller `--onefile --windowed` 打包。
4. 将共享后端、`VERSION`、`BUILD_NUMBER` 加入资源。
5. 输出独立 exe。

### 8.4 CI 发布

工作流：

- `.github/workflows/release-builds.yml`

触发方式：

- 手动触发。
- 推送到 `main` 且改动命中指定路径。
- GitHub Release published。

构建产物：

- macOS `.dmg`
- macOS `.app.zip`
- Windows `.exe`
- Android 当前仅占位提示。

Release 附件统一使用英文 ASCII 文件名，避免 GitHub 截断中文附件名。

## 9. 安全与权限约束

安全假设：

- 用户拥有目标设备或已获得明确授权。
- 用户已经知道设备 Telnet 登录凭据。
- 工具运行在用户可信本机环境。

当前安全措施：

- 不上传任何数据到外部服务。
- 设备侧临时文件默认在完成后删除。
- macOS 缓存和后端调试日志尽量设置为 `0600`。
- 后端只删除符合 `/tmp/oclg_<timestamp>_<pid>.dec` 格式的本次临时文件。
- Release 附件命名稳定，降低分发混乱。

当前限制：

- 登录密码和超级密码均可能明文显示在 UI 中。
- 登录参数缓存当前未做系统钥匙串或凭据管理器加密。
- Telnet 本身是明文协议，网络链路不具备加密保护。
- Windows 缓存文件当前未显式设置 ACL。

建议后续增强：

- macOS 使用 Keychain 保存密码。
- Windows 使用 Credential Manager 或 DPAPI 保存密码。
- 给“保存密码”增加显式开关。
- 在文档中继续强调授权边界和 Telnet 明文风险。

## 10. 错误处理设计

错误分为三类：

- 输入错误：前端直接阻止执行，例如空 IP、空用户名、空密码、端口非数字。
- 可恢复运行错误：后端返回用户可理解的错误，例如连接失败、登录失败、配置文件不存在、设备响应超时。
- 调试错误：原始 stderr、非 JSON 输出、远端命令尾部内容写入调试日志，避免污染普通用户界面。

UI 行为：

- 任务运行时禁用开始按钮。
- 日志实时追加。
- 成功时展示超级账号、超级密码和保存路径。
- 失败时状态显示失败，并允许用户修改信息后重试。

## 11. 可扩展性设计

### 11.1 新增设备型号

当前设备路径和字段名写在共享后端中：

- 配置文件路径。
- 设备侧解密命令路径。
- XML 字段名。

如果后续支持更多型号，建议抽象为设备 profile：

```text
profile
  |-- encrypted_file
  |-- decrypt_script
  |-- account_field
  |-- password_field
  |-- capability_check
```

UI 可增加型号选择，后端按 profile 执行。

### 11.2 新增 Android

Android 版建议继续沿用“UI 独立、核心协议复用”的原则：

- UI 使用原生 Android 或跨平台框架。
- 核心流程可以复用 Python 逻辑的协议设计，也可以重写为 Kotlin。
- Release 继续共用 `VERSION` / `BUILD_NUMBER`。
- 权限说明需要覆盖网络访问、文件保存和本地凭据存储。

### 11.3 后端协议演进

建议保持 JSON 行协议向后兼容：

- 新增字段可以可选。
- 保持 `type=log` 和 `type=result` 不变。
- 错误信息继续使用用户可理解文案。
- 调试细节继续写入本地 debug log。

## 12. 当前风险与改进建议

1. Python `telnetlib` 兼容性风险

   后端依赖 `telnetlib`。该模块在较新的 Python 版本中已不可用。本地当前 Python 3.14 环境执行 `import telnetlib` 会报 `ModuleNotFoundError`。CI 当前使用 Python 3.12，Windows 打包产物风险较低；macOS 运行时依赖系统 `python3`，需要确认目标用户环境是否仍包含 `telnetlib`。建议后续改为 vendored telnet 实现或第三方兼容库。

2. XML 解析较简单

   当前使用正则提取 XML 字段。若设备输出格式变化、字段顺序变化或 XML 转义更复杂，可能解析失败。建议后续使用 XML parser，并兼容字段缺失场景。

3. 设备兼容性硬编码

   配置文件路径、解密命令路径和 XML 字段名固定，适合当前目标型号，但扩展多个固件版本时需要 profile 化。

4. 密码明文缓存

   当前为使用便利牺牲了本地凭据安全。建议新增“不保存密码”选项，并接入系统安全存储。

5. macOS UI 布局固定

   macOS 界面大量使用固定 frame。窗口可调整大小，但控件布局不会充分响应式变化。后续可改为 Auto Layout 或 NSStackView。

6. Git 工具依赖

   本地当前环境无法识别 `git` 命令，因此 `git status`、pre-commit hook、`generate_version.sh` 中的 git commit 获取等能力在该环境不可用。项目脚本本身有 unknown fallback，但本地提交和 hook 依赖需要安装 Git。

## 13. 验证策略

建议分层验证：

- 静态检查：Python 文件使用 `python -m py_compile` 做语法检查。
- 后端单元测试：对 `parse_value`、`is_our_tmp`、base64 解析、错误路径做测试。
- 后端集成测试：使用 Telnet mock server 模拟登录、命令返回和超时。
- UI 冒烟测试：检查启动、输入校验、日志追加、按钮状态恢复。
- 打包验证：macOS 检查 `.app` 内 helper 和图标资源；Windows 检查 PyInstaller onefile 是否能定位资源。
- 发布验证：检查 Release 附件名称、版本号、构建号和产物可运行性。

本次解析时已执行：

```text
python -m py_compile shared/backend/jiulian_backend_helper.py platforms/windows/jiulian_windows_tool.py
```

语法检查通过。

同时确认：

```text
python -c "import telnetlib"
```

在当前 Python 3.14 环境失败，属于运行时兼容性风险。
