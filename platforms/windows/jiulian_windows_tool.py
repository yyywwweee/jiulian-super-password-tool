#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows GUI for 九联光猫获取超级密码工具."""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import queue
import sys
import threading
import time
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ctypes

# Windows 任务栏图标需要设置 AppUserModelID
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.jiulian.superpassword-tool")
    except Exception:
        pass

APP_NAME = "九联光猫获取超级密码工具"
ORG_DIR_NAME = "JiulianSuperPasswordTool"


def resource_root() -> pathlib.Path:
    if hasattr(sys, "_MEIPASS"):
        return pathlib.Path(getattr(sys, "_MEIPASS"))
    # Source tree layout: repo/platforms/windows/jiulian_windows_tool.py
    return pathlib.Path(__file__).resolve().parents[2]


def read_text_resource(name: str, default: str) -> str:
    candidates = [resource_root() / name, pathlib.Path(__file__).resolve().parents[1] / name]
    for path in candidates:
        try:
            return path.read_text(encoding="utf-8").strip() or default
        except Exception:
            pass
    return default


VERSION = read_text_resource("VERSION", "1.0.1")
BUILD = read_text_resource("BUILD_NUMBER", "0")
DISPLAY_VERSION = f"v{VERSION} (Build {BUILD})"


def app_data_dir() -> pathlib.Path:
    base = os.environ.get("APPDATA") or str(pathlib.Path.home() / "AppData" / "Roaming")
    path = pathlib.Path(base) / ORG_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


CACHE_FILE = app_data_dir() / "cache.json"
DEBUG_LOG_FILE = app_data_dir() / "windows_debug.log"


def write_debug(title: str, detail: str) -> None:
    try:
        with DEBUG_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {title}\n{detail}\n")
    except Exception:
        pass


def load_backend_module():
    root = resource_root()
    candidates = [
        root / "shared" / "backend" / "jiulian_backend_helper.py",
        root / "Resources" / "jiulian_backend_helper.py",  # compatibility with older bundles
        root / "jiulian_backend_helper.py",
        pathlib.Path(__file__).resolve().parents[2] / "shared" / "backend" / "jiulian_backend_helper.py",
    ]
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location("jiulian_backend_helper", path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore[union-attr]
                return module
    raise RuntimeError("程序资源缺失：jiulian_backend_helper.py。请重新下载安装。")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {DISPLAY_VERSION}")
        self._set_app_icon()
        self.geometry("900x800")
        self.minsize(840, 700)
        self.log_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self.worker: threading.Thread | None = None
        self.backend = None

        self.host_var = tk.StringVar(value="192.168.0.1")
        self.port_var = tk.StringVar(value="23")
        self.user_var = tk.StringVar(value="root")
        self.password_var = tk.StringVar(value="")
        self.output_var = tk.StringVar(value=str(pathlib.Path.home() / "Downloads"))
        self.clean_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="就绪")
        self.account_var = tk.StringVar(value="-")
        self.super_password_var = tk.StringVar(value="-")
        self.output_file_var = tk.StringVar(value="-")

        self._load_cache()
        self._build_ui()
        self._fit_initial_window()
        self.after(80, self._drain_queue)

    def _resolve_icon_path(self) -> str | None:
        candidates = [
            resource_root() / "Assets" / "AppIcon" / "windows" / "AppIcon.ico",
            resource_root() / "AppIcon.ico",
            pathlib.Path(__file__).resolve().parents[2] / "Assets" / "AppIcon" / "windows" / "AppIcon.ico",
        ]
        for path in candidates:
            if path.is_file():
                return str(path)
        return None

    def _set_app_icon(self) -> None:
        icon_path = self._resolve_icon_path()
        if not icon_path:
            return
        # tkinter iconbitmap 设置标题栏小图标
        try:
            self.iconbitmap(default=icon_path)
        except Exception:
            pass
        # Windows: 用 WM_SETICON 指定尺寸分别设置
        if sys.platform == "win32":
            try:
                import ctypes as _ct
                hwnd = int(self.frame(), 16)
                icon_win = icon_path.replace("/", "\\")
                # ICON_BIG: 48x48 用于任务栏
                hicon_big = _ct.windll.user32.LoadImageW(0, icon_win, 1, 48, 48, 0x00000010)
                if hicon_big:
                    _ct.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_big)
                # ICON_SMALL: 32x32 用于标题栏
                hicon_small = _ct.windll.user32.LoadImageW(0, icon_win, 1, 32, 32, 0x00000010)
                if hicon_small:
                    _ct.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon_small)
            except Exception:
                pass

    def _load_cache(self) -> None:
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            self.host_var.set(data.get("host", self.host_var.get()))
            self.port_var.set(data.get("port", self.port_var.get()))
            self.user_var.set(data.get("user", self.user_var.get()))
            self.password_var.set(data.get("password", self.password_var.get()))
            self.output_var.set(data.get("output_dir", self.output_var.get()))
            self.clean_var.set(bool(data.get("clean_tmp", True)))
        except Exception:
            pass

    def _save_cache(self) -> None:
        data = {
            "host": self.host_var.get(),
            "port": self.port_var.get(),
            "user": self.user_var.get(),
            "password": self.password_var.get(),
            "output_dir": self.output_var.get(),
            "clean_tmp": self.clean_var.get(),
        }
        try:
            CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            write_debug("cache write failed", repr(exc))

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root = ttk.Frame(self, padding=18)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(1, weight=1)
        root.rowconfigure(6, weight=1)

        title = ttk.Label(root, text=f"{APP_NAME} {DISPLAY_VERSION}", font=("Microsoft YaHei UI", 20, "bold"))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))
        subtitle = ttk.Label(root, text="本工具只获取超级管理员账号和密码。登录密码明文显示，并会缓存在本机，便于下次自动填入。", foreground="#666666")
        subtitle.grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 2))
        version = ttk.Label(root, text=f"版本：{DISPLAY_VERSION}", foreground="#888888")
        version.grid(row=2, column=0, columnspan=4, sticky="w", pady=(0, 14))

        form = ttk.LabelFrame(root, text="连接信息", padding=12)
        form.grid(row=3, column=0, columnspan=4, sticky="ew")
        form.columnconfigure(1, weight=1)

        rows = [
            ("光猫 IP：", self.host_var, "例如 192.168.0.1"),
            ("登录端口：", self.port_var, "默认 23"),
            ("登录用户名：", self.user_var, "例如 root"),
            ("登录密码：", self.password_var, "明文显示"),
            ("保存目录：", self.output_var, ""),
        ]
        for r, (label, var, hint) in enumerate(rows):
            ttk.Label(form, text=label).grid(row=r, column=0, sticky="e", padx=(0, 8), pady=5)
            entry = ttk.Entry(form, textvariable=var)
            entry.grid(row=r, column=1, sticky="ew", pady=5)
            if label == "保存目录：":
                ttk.Button(form, text="选择…", command=self._choose_dir).grid(row=r, column=2, padx=(8, 0), pady=5)
            elif hint:
                ttk.Label(form, text=hint, foreground="#777777").grid(row=r, column=2, sticky="w", padx=(8, 0), pady=5)

        ttk.Checkbutton(form, text="完成后清理本次临时数据（推荐）", variable=self.clean_var).grid(row=5, column=1, sticky="w", pady=(8, 0))

        actions = ttk.Frame(root)
        actions.grid(row=4, column=0, columnspan=4, sticky="ew", pady=14)
        self.start_btn = ttk.Button(actions, text="开始获取超级密码", command=self._start)
        self.start_btn.pack(side="left")
        ttk.Button(actions, text="清空日志", command=self._clear_logs).pack(side="left", padx=(10, 0))
        ttk.Label(actions, textvariable=self.status_var, foreground="#0067c0", font=("Microsoft YaHei UI", 13, "bold")).pack(side="left", padx=(22, 0))

        result_box = ttk.LabelFrame(root, text="解密结果", padding=12)
        result_box.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(0, 12))
        result_box.columnconfigure(1, weight=1)
        for r, (label, var) in enumerate([
            ("超级账号：", self.account_var),
            ("超级密码：", self.super_password_var),
            ("保存位置：", self.output_file_var),
        ]):
            ttk.Label(result_box, text=label).grid(row=r, column=0, sticky="e", padx=(0, 8), pady=3)
            e = ttk.Entry(result_box, textvariable=var, state="readonly")
            e.grid(row=r, column=1, sticky="ew", pady=3)

        log_box = ttk.LabelFrame(root, text="运行日志", padding=8)
        log_box.grid(row=6, column=0, columnspan=4, sticky="nsew")
        log_box.columnconfigure(0, weight=1)
        log_box.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_box, height=10, wrap="word", font=("Consolas", 10))
        scroll = ttk.Scrollbar(log_box, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.tag_configure("error", foreground="#c00000")
        self.log_text.tag_configure("success", foreground="#008000")
        self.log_text.tag_configure("info", foreground="#222222")

        self._append_log(f"当前软件：{APP_NAME} {DISPLAY_VERSION}")
        self._append_log("如果失败，日志会用红色显示原因；修正信息后可以直接重试。")

    def _fit_initial_window(self) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = max(900, self.winfo_reqwidth())
        height = max(800, self.winfo_reqheight())
        width = min(width, max(840, screen_w - 80))
        height = min(height, max(700, screen_h - 120))
        self.geometry(f"{width}x{height}")

    def _choose_dir(self) -> None:
        path = filedialog.askdirectory(initialdir=self.output_var.get() or str(pathlib.Path.home()))
        if path:
            self.output_var.set(path)

    def _append_log(self, text: str, level: str = "info") -> None:
        self.log_text.insert("end", text + "\n", level)
        self.log_text.see("end")

    def _clear_logs(self) -> None:
        self.log_text.delete("1.0", "end")

    def _validate(self) -> bool:
        if not self.host_var.get().strip():
            messagebox.showerror(APP_NAME, "请填写光猫 IP。")
            return False
        if not self.user_var.get().strip():
            messagebox.showerror(APP_NAME, "请填写登录用户名。")
            return False
        if not self.password_var.get():
            messagebox.showerror(APP_NAME, "请填写登录密码。")
            return False
        try:
            int(self.port_var.get().strip() or "23")
        except ValueError:
            messagebox.showerror(APP_NAME, "登录端口必须是数字。")
            return False
        return True

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self._validate():
            return
        self._save_cache()
        self.status_var.set("运行中…")
        self.start_btn.configure(state="disabled")
        self.account_var.set("-")
        self.super_password_var.set("-")
        self.output_file_var.set("-")

        params = {
            "host": self.host_var.get().strip(),
            "port": self.port_var.get().strip() or "23",
            "user": self.user_var.get().strip(),
            "password": self.password_var.get(),
            "output_dir": self.output_var.get().strip() or str(pathlib.Path.home() / "Downloads"),
            "clean_tmp": self.clean_var.get(),
            "stream": True,
            "debug_dir": str(app_data_dir() / "Logs"),
        }
        self.worker = threading.Thread(target=self._run_backend, args=(params,), daemon=True)
        self.worker.start()

    def _run_backend(self, params: dict) -> None:
        try:
            backend = self.backend or load_backend_module()
            self.backend = backend

            def emit(obj: dict) -> None:
                if obj.get("type") == "log":
                    level = str(obj.get("level", "info"))
                    self.log_queue.put(("log", f"[{obj.get('time', time.strftime('%H:%M:%S'))}] {obj.get('message', '')}", level))
                elif obj.get("type") == "credentials":
                    self.log_queue.put(("credentials", obj))
                elif obj.get("type") == "result":
                    self.log_queue.put(("result", obj))

            backend.STREAM = True
            backend.emit = emit
            result = backend.run(params)
            result = {k: v for k, v in result.items() if k != "logs"}
            self.log_queue.put(("result", result))
        except Exception as exc:
            write_debug("windows backend failed", traceback.format_exc())
            self.log_queue.put(("log", f"[{time.strftime('%H:%M:%S')}] FAIL: {exc}", "error"))
            self.log_queue.put(("log", f"[{time.strftime('%H:%M:%S')}] 请检查光猫 IP、登录用户名/密码、网络连接，确认设备在线后重试。", "error"))
            self.log_queue.put(("result", {"ok": False, "error": str(exc)}))

    def _drain_queue(self) -> None:
        try:
            while True:
                item = self.log_queue.get_nowait()
                kind = item[0]
                if kind == "log":
                    _, text, level = item
                    self._append_log(str(text), str(level))
                elif kind == "credentials":
                    _, creds = item
                    self.account_var.set(str(creds.get("super_account", "-")))
                    self.super_password_var.set(str(creds.get("super_password", "-")))
                elif kind == "result":
                    _, result = item
                    if isinstance(result, dict):
                        if result.get("ok"):
                            self.status_var.set("完成")
                            self.account_var.set(str(result.get("super_account", "-")))
                            self.super_password_var.set(str(result.get("super_password", "-")))
                            self.output_file_var.set(str(result.get("output_file", "-")))
                        else:
                            self.status_var.set("失败")
                    self.start_btn.configure(state="normal")
        except queue.Empty:
            pass
        self.after(80, self._drain_queue)


def main() -> None:
    try:
        app = App()
        app.mainloop()
    except Exception:
        write_debug("fatal", traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
