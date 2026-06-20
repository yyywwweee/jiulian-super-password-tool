import Cocoa
import Foundation

enum AppConstants {
    static let appName = "九联光猫获取超级密码工具"
    static let cacheURL = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".jiulian_super_password_native_cache.json")
}


enum AppVersion {
    private static func infoString(_ key: String, default fallback: String) -> String {
        let value = Bundle.main.infoDictionary?[key] as? String
        if let value, !value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return value
        }
        return fallback
    }

    static var version: String {
        infoString("CFBundleShortVersionString", default: "dev")
    }

    static var build: String {
        infoString("CFBundleVersion", default: "0")
    }

    static var gitCommit: String {
        infoString("JiulianGitCommit", default: "unknown")
    }

    static var buildTime: String {
        infoString("JiulianBuildTime", default: "unknown")
    }

    static var display: String {
        "v\(version) (Build \(build))"
    }

    static var detail: String {
        "v\(version) (Build \(build), \(gitCommit))"
    }
}

struct Cache: Codable {
    var host: String = "192.168.0.1"
    var port: String = "23"
    var user: String = "root"
    var password: String = ""
    var outputDir: String = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Downloads").path
    var cleanTmp: Bool = true
}

struct RunResult {
    var ok: Bool
    var logs: [(String, NSColor)]
    var superAccount: String = "-"
    var superPassword: String = "-"
    var outputFile: String = "-"
}

func nowText() -> String {
    let f = DateFormatter(); f.dateFormat = "HH:mm:ss"; return f.string(from: Date())
}

func shellQuote(_ s: String) -> String {
    return "'" + s.replacingOccurrences(of: "'", with: "'\\''") + "'"
}

func extractValue(_ text: String, _ name: String) -> String {
    let pattern = "<Value\\s+Name=\"" + NSRegularExpression.escapedPattern(for: name) + "\"\\s+Value=\"([^\"]*)\""
    guard let re = try? NSRegularExpression(pattern: pattern),
          let m = re.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)),
          m.numberOfRanges > 1,
          let r = Range(m.range(at: 1), in: text) else { return "" }
    return String(text[r])
}

func writeDebug(_ title: String, _ detail: String) {
    let url = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("jiulian_super_password_native_debug.log")
    let line = "\n[\(ISO8601DateFormatter().string(from: Date()))] \(title)\n\(detail)\n"
    if let data = line.data(using: .utf8) {
        if FileManager.default.fileExists(atPath: url.path), let h = try? FileHandle(forWritingTo: url) {
            try? h.seekToEnd(); try? h.write(contentsOf: data); try? h.close()
        } else {
            try? data.write(to: url)
            try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: url.path)
        }
    }
}

enum Runner {
    static func log(_ logs: inout [(String, NSColor)], _ msg: String, _ color: NSColor = .labelColor) {
        logs.append(("[\(nowText())] \(msg)", color))
    }

    static func fail(_ logs: inout [(String, NSColor)], _ msg: String) -> RunResult {
        log(&logs, "FAIL: \(msg)", .systemRed)
        log(&logs, "请检查光猫 IP、登录用户名/密码、网络连接，确认设备在线后重试。", .systemRed)
        return RunResult(ok: false, logs: logs)
    }

    static func runStream(host: String, port: String, user: String, password: String, outputDir: String, cleanTmp: Bool, onLog: @escaping @Sendable (String, NSColor) -> Void) -> RunResult {
        var final = RunResult(ok: false, logs: [])
        do {
            guard let helper = Bundle.main.path(forResource: "jiulian_backend_helper", ofType: "py") else {
                onLog("[\(nowText())] FAIL: App 资源缺失：jiulian_backend_helper.py。请重新安装应用。", .systemRed)
                return final
            }
            let payload: [String: Any] = [
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "output_dir": outputDir,
                "clean_tmp": cleanTmp,
                "stream": true,
            ]
            let input = try JSONSerialization.data(withJSONObject: payload, options: [])
            let p = Process()
            p.executableURL = URL(fileURLWithPath: "/usr/bin/env")
            p.arguments = ["python3", helper]
            let inPipe = Pipe()
            let outPipe = Pipe()
            let errPipe = Pipe()
            p.standardInput = inPipe
            p.standardOutput = outPipe
            p.standardError = errPipe
            try p.run()
            inPipe.fileHandleForWriting.write(input)
            try? inPipe.fileHandleForWriting.close()

            let handle = outPipe.fileHandleForReading
            var buffer = Data()
            while p.isRunning {
                let chunk = handle.availableData
                if !chunk.isEmpty {
                    buffer.append(chunk)
                    processLines(&buffer, onLog: onLog, final: &final)
                } else {
                    Thread.sleep(forTimeInterval: 0.05)
                }
            }
            let rest = handle.readDataToEndOfFile()
            if !rest.isEmpty { buffer.append(rest) }
            processLines(&buffer, flush: true, onLog: onLog, final: &final)

            let errData = errPipe.fileHandleForReading.readDataToEndOfFile()
            if !errData.isEmpty {
                writeDebug("helper stderr", String(data: errData, encoding: .utf8) ?? "")
            }
            if p.terminationStatus != 0 && !final.ok {
                onLog("[\(nowText())] FAIL: 后端执行异常，请重试。", .systemRed)
            }
            return final
        } catch {
            onLog("[\(nowText())] FAIL: 执行失败：\(error.localizedDescription)", .systemRed)
            return final
        }
    }

    static func processLines(_ buffer: inout Data, flush: Bool = false, onLog: @escaping @Sendable (String, NSColor) -> Void, final: inout RunResult) {
        while true {
            if let idx = buffer.firstIndex(of: 10) { // newline
                let lineData = buffer[..<idx]
                buffer.removeSubrange(...idx)
                handleLine(Data(lineData), onLog: onLog, final: &final)
            } else {
                break
            }
        }
        if flush && !buffer.isEmpty {
            handleLine(buffer, onLog: onLog, final: &final)
            buffer.removeAll()
        }
    }

    static func handleLine(_ data: Data, onLog: @escaping @Sendable (String, NSColor) -> Void, final: inout RunResult) {
        guard let obj = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] else {
            let raw = String(data: data, encoding: .utf8) ?? ""
            if !raw.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { writeDebug("helper non-json line", raw) }
            return
        }
        let type = obj["type"] as? String ?? ""
        if type == "log" {
            let time = obj["time"] as? String ?? nowText()
            let msg = obj["message"] as? String ?? ""
            let level = obj["level"] as? String ?? "info"
            let color: NSColor = level == "error" ? .systemRed : (level == "success" ? .systemGreen : .labelColor)
            onLog("[\(time)] \(msg)", color)
        } else if type == "result" {
            final.ok = (obj["ok"] as? Bool) == true
            final.superAccount = obj["super_account"] as? String ?? "-"
            final.superPassword = obj["super_password"] as? String ?? "-"
            final.outputFile = obj["output_file"] as? String ?? "-"
        }
    }


}

@MainActor
class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var hostField = NSTextField(string: "192.168.0.1")
    var portField = NSTextField(string: "23")
    var userField = NSTextField(string: "root")
    var passField = NSTextField(string: "")
    var outField = NSTextField(string: FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Downloads").path)
    var cleanBox = NSButton(checkboxWithTitle: "完成后清理本次临时数据（推荐）", target: nil, action: nil)
    var startButton = NSButton(title: "开始获取超级密码", target: nil, action: nil)
    var clearButton = NSButton(title: "清空日志", target: nil, action: nil)
    var chooseButton = NSButton(title: "选择…", target: nil, action: nil)
    var statusLabel = NSTextField(labelWithString: "就绪")
    var accountLabel = NSTextField(labelWithString: "-")
    var passwordLabel = NSTextField(labelWithString: "-")
    var outputLabel = NSTextField(labelWithString: "-")
    var logView = NSTextView()

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        loadCache()
        buildWindow()
        NSApp.activate(ignoringOtherApps: true)
    }

    func loadCache() {
        guard let data = try? Data(contentsOf: AppConstants.cacheURL), let c = try? JSONDecoder().decode(Cache.self, from: data) else { return }
        hostField.stringValue = c.host; portField.stringValue = c.port; userField.stringValue = c.user; passField.stringValue = c.password; outField.stringValue = c.outputDir; cleanBox.state = c.cleanTmp ? .on : .off
    }

    func saveCache() {
        let c = Cache(host: hostField.stringValue, port: portField.stringValue, user: userField.stringValue, password: passField.stringValue, outputDir: outField.stringValue, cleanTmp: cleanBox.state == .on)
        if let data = try? JSONEncoder().encode(c) { try? data.write(to: AppConstants.cacheURL); try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: AppConstants.cacheURL.path) }
    }

    func label(_ text: String, x: CGFloat, y: CGFloat, w: CGFloat = 120) -> NSTextField {
        let l = NSTextField(labelWithString: text); l.frame = NSRect(x: x, y: y, width: w, height: 24); l.alignment = .right; l.font = .boldSystemFont(ofSize: 14); return l
    }
    func hint(_ text: String, x: CGFloat, y: CGFloat, w: CGFloat = 180) -> NSTextField {
        let l = NSTextField(labelWithString: text); l.frame = NSRect(x: x, y: y, width: w, height: 22); l.textColor = .secondaryLabelColor; l.font = .systemFont(ofSize: 12); return l
    }
    func setupField(_ f: NSTextField, x: CGFloat, y: CGFloat, w: CGFloat = 390) { f.frame = NSRect(x: x, y: y, width: w, height: 26); f.font = .systemFont(ofSize: 14); f.isBezeled = true; f.backgroundColor = .textBackgroundColor }

    func buildWindow() {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 880, height: 650), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "\(AppConstants.appName) \(AppVersion.display)"
        window.center()
        let v = NSView(frame: window.contentView!.bounds); v.autoresizingMask = [.width, .height]; v.wantsLayer = true; v.layer?.backgroundColor = NSColor.windowBackgroundColor.cgColor; window.contentView = v

        let title = NSTextField(labelWithString: "\(AppConstants.appName) \(AppVersion.display)"); title.frame = NSRect(x: 28, y: 595, width: 700, height: 34); title.font = .boldSystemFont(ofSize: 28); v.addSubview(title)
        let sub = NSTextField(labelWithString: "本工具只获取超级管理员账号和密码。登录密码明文显示，并会缓存在本机，便于下次自动填入。"); sub.frame = NSRect(x: 30, y: 568, width: 760, height: 22); sub.textColor = .secondaryLabelColor; v.addSubview(sub)
        let versionLabel = NSTextField(labelWithString: "版本：\(AppVersion.detail)"); versionLabel.frame = NSRect(x: 30, y: 548, width: 760, height: 20); versionLabel.textColor = .tertiaryLabelColor; versionLabel.font = .systemFont(ofSize: 12); v.addSubview(versionLabel)

        let x1: CGFloat = 30, x2: CGFloat = 165, x3: CGFloat = 570
        var y: CGFloat = 510
        for (name, field, h) in [("光猫 IP：", hostField, "例如 192.168.0.1"), ("登录端口：", portField, "默认 23"), ("登录用户名：", userField, "例如 root"), ("登录密码：", passField, "明文显示"), ("保存目录：", outField, "") ] {
            v.addSubview(label(name, x: x1, y: y)); setupField(field, x: x2, y: y, w: name == "保存目录：" ? 500 : 390); v.addSubview(field); if !h.isEmpty { v.addSubview(hint(h, x: x3, y: y)) }; y -= 39
        }
        chooseButton.frame = NSRect(x: 675, y: 354, width: 78, height: 30); chooseButton.target = self; chooseButton.action = #selector(chooseDir); v.addSubview(chooseButton)
        cleanBox.frame = NSRect(x: x2, y: 315, width: 300, height: 24); cleanBox.state = cleanBox.state == .off ? .on : cleanBox.state; v.addSubview(cleanBox)

        startButton.frame = NSRect(x: x2, y: 271, width: 160, height: 34); startButton.bezelStyle = .rounded; startButton.target = self; startButton.action = #selector(start); v.addSubview(startButton)
        clearButton.frame = NSRect(x: 340, y: 271, width: 90, height: 34); clearButton.target = self; clearButton.action = #selector(clearLogs); v.addSubview(clearButton)
        statusLabel.frame = NSRect(x: 485, y: 271, width: 260, height: 34); statusLabel.font = .boldSystemFont(ofSize: 22); statusLabel.textColor = .systemBlue; v.addSubview(statusLabel)

        let box = NSBox(frame: NSRect(x: 30, y: 150, width: 820, height: 105)); box.title = "解密结果"; v.addSubview(box)
        accountLabel.frame = NSRect(x: 145, y: 217, width: 650, height: 22); passwordLabel.frame = NSRect(x: 145, y: 190, width: 650, height: 22); outputLabel.frame = NSRect(x: 145, y: 163, width: 650, height: 22)
        for (t, yy) in [("超级账号：", 217 as CGFloat), ("超级密码：", 190 as CGFloat), ("保存位置：", 163 as CGFloat)] { v.addSubview(label(t, x: 40, y: yy, w: 95)) }
        for l in [accountLabel, passwordLabel, outputLabel] { l.isSelectable = true; v.addSubview(l) }

        let logBox = NSBox(frame: NSRect(x: 30, y: 20, width: 820, height: 118)); logBox.title = "运行日志"; v.addSubview(logBox)
        let scroll = NSScrollView(frame: NSRect(x: 42, y: 33, width: 796, height: 85)); scroll.hasVerticalScroller = true; logView.isEditable = false; logView.font = .monospacedSystemFont(ofSize: 12, weight: .regular); logView.backgroundColor = .textBackgroundColor; scroll.documentView = logView; v.addSubview(scroll)

        appendLog("当前软件：\(AppConstants.appName) \(AppVersion.detail)")
        appendLog("如果失败，日志会用红色显示原因；修正信息后可以直接重试。")
        window.makeKeyAndOrderFront(nil)
    }

    func appendLog(_ text: String, color: NSColor = .labelColor) {
        let attr = NSAttributedString(string: text + "\n", attributes: [.foregroundColor: color, .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .regular)])
        logView.textStorage?.append(attr)
        logView.scrollToEndOfDocument(nil)
    }

    @objc func clearLogs() { logView.string = "" }
    @objc func chooseDir() { let p = NSOpenPanel(); p.canChooseDirectories = true; p.canChooseFiles = false; p.allowsMultipleSelection = false; if p.runModal() == .OK, let u = p.url { outField.stringValue = u.path } }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    @objc func start() {
        if hostField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { appendLog("FAIL: 请填写光猫 IP。", color: .systemRed); return }
        if userField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { appendLog("FAIL: 请填写登录用户名。", color: .systemRed); return }
        if passField.stringValue.isEmpty { appendLog("FAIL: 请填写登录密码。", color: .systemRed); return }
        guard Int(portField.stringValue) != nil else { appendLog("FAIL: 登录端口必须是数字。", color: .systemRed); return }
        saveCache(); startButton.isEnabled = false; statusLabel.stringValue = "运行中…"; statusLabel.textColor = .systemBlue; accountLabel.stringValue = "-"; passwordLabel.stringValue = "-"; outputLabel.stringValue = "-"; appendLog("已开始，请稍候。")
        let params = (hostField.stringValue, portField.stringValue, userField.stringValue, passField.stringValue, outField.stringValue, cleanBox.state == .on)
        DispatchQueue.global(qos: .userInitiated).async {
            let r = Runner.runStream(host: params.0, port: params.1, user: params.2, password: params.3, outputDir: params.4, cleanTmp: params.5, onLog: { text, color in
                DispatchQueue.main.async { self.appendLog(text, color: color) }
            })
            DispatchQueue.main.async {
                self.startButton.isEnabled = true
                if r.ok { self.statusLabel.stringValue = "✅ 完成"; self.statusLabel.textColor = .systemGreen; self.accountLabel.stringValue = r.superAccount; self.passwordLabel.stringValue = r.superPassword; self.outputLabel.stringValue = r.outputFile }
                else { self.statusLabel.stringValue = "❌ 失败"; self.statusLabel.textColor = .systemRed }
            }
        }
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
