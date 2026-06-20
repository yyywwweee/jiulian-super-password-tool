#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""九联光猫获取超级密码工具 v1.0 - 后端 helper。
从 stdin 读取 JSON 参数，stdout 输出 JSON 结果。GUI 不显示核心技术细节。
"""

import base64
import json
import os
import pathlib
import re
import socket
import sys
import time
import traceback
from datetime import datetime

REMOTE_ENCRYPTED_FILE = "/config/workb/backup_lastgood.xml"
REMOTE_DECRYPT_SCRIPT = "/home/cli/decrypt/decrypt_file"
DEBUG_LOG_FILE = pathlib.Path.home() / "jiulian_super_password_backend_debug.log"
ANSI_RE = re.compile(rb"\x1b\[[0-9;]*[A-Za-z]")
STREAM = False

class MinimalTelnet:
    """Small Telnet client for this tool.

    Python's stdlib telnetlib was deprecated and removed in newer Python
    versions. The tool only needs a small subset of Telnet behavior, so keep a
    local implementation instead of depending on telnetlib availability.
    """

    IAC = 255
    DONT = 254
    DO = 253
    WONT = 252
    WILL = 251
    SB = 250
    SE = 240

    def __init__(self, host, port=23, timeout=6):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self._closed = False
        self._sb = False

    def get_socket(self):
        return self.sock

    def close(self):
        self._closed = True
        try:
            self.sock.close()
        except Exception:
            pass

    def write(self, data):
        if isinstance(data, str):
            data = data.encode()
        self.sock.sendall(data)

    def _reply(self, command, option):
        try:
            self.sock.sendall(bytes([self.IAC, command, option]))
        except Exception:
            pass

    def _cook(self, raw):
        out = bytearray()
        i = 0
        n = len(raw)
        while i < n:
            b = raw[i]
            if b != self.IAC:
                if not self._sb:
                    out.append(b)
                i += 1
                continue

            i += 1
            if i >= n:
                break
            cmd = raw[i]
            i += 1

            if cmd == self.IAC:
                if not self._sb:
                    out.append(self.IAC)
                continue
            if cmd in (self.DO, self.DONT, self.WILL, self.WONT):
                if i >= n:
                    break
                opt = raw[i]
                i += 1
                if cmd == self.DO:
                    self._reply(self.WONT, opt)
                elif cmd == self.WILL:
                    self._reply(self.DONT, opt)
                continue
            if cmd == self.SB:
                self._sb = True
                continue
            if cmd == self.SE:
                self._sb = False
                continue
            # Other single-byte Telnet commands are ignored.
        return bytes(out)

    def _recv_cooked(self, timeout):
        old_timeout = self.sock.gettimeout()
        try:
            self.sock.settimeout(timeout)
            data = self.sock.recv(4096)
        finally:
            try:
                self.sock.settimeout(old_timeout)
            except Exception:
                pass
        if data == b"":
            raise EOFError("Telnet connection closed")
        return self._cook(data)

    def read_until(self, expected, timeout=None):
        end = time.time() + (timeout if timeout is not None else 0)
        data = b""
        while True:
            if expected in data:
                return data
            if timeout is not None:
                remain = end - time.time()
                if remain <= 0:
                    return data
                recv_timeout = min(0.5, max(0.05, remain))
            else:
                recv_timeout = 0.5
            try:
                data += self._recv_cooked(recv_timeout)
            except socket.timeout:
                if timeout is not None and time.time() >= end:
                    return data
            except TimeoutError:
                if timeout is not None and time.time() >= end:
                    return data
            except EOFError:
                return data

    def read_very_eager(self):
        chunks = []
        while True:
            try:
                chunk = self._recv_cooked(0.01)
            except (socket.timeout, TimeoutError):
                break
            except EOFError:
                raise
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)


def emit(obj):
    if STREAM:
        try:
            print(json.dumps(obj, ensure_ascii=False), flush=True)
        except BrokenPipeError:
            # 前端提前断开时不要污染设备流程/调试输出
            pass


def debug(title, detail):
    try:
        with DEBUG_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] {title}\n")
            f.write(str(detail))
            f.write("\n")
        try:
            os.chmod(DEBUG_LOG_FILE, 0o600)
        except Exception:
            pass
    except Exception:
        pass


def log(logs, msg, level="info"):
    item = {"time": datetime.now().strftime("%H:%M:%S"), "message": msg, "level": level}
    logs.append(item)
    emit({"type": "log", **item})


def strip_ansi(data):
    return ANSI_RE.sub(b"", data)


def read_some(tn, quiet=2.0, hard=None):
    quiet_end = time.time() + quiet
    hard_end = time.time() + (hard if hard is not None else max(quiet + 2.0, 3.0))
    data = b""
    while time.time() < quiet_end and time.time() < hard_end:
        try:
            chunk = tn.read_very_eager()
            if chunk:
                data += chunk
                quiet_end = time.time() + 0.4
            else:
                time.sleep(0.08)
        except socket.timeout:
            time.sleep(0.08)
        except EOFError:
            break
    return data


def run_cmd(tn, cmd, wait=1.0, timeout=8.0):
    marker = f"__OC_MARK_{int(time.time() * 1000)}__"
    end_marker = marker + "_END"
    full_cmd = f"echo {marker}; {cmd}; echo __RET__$?; echo {end_marker}\n"
    tn.write(full_cmd.encode())
    time.sleep(wait)
    out = read_some(tn, quiet=timeout, hard=timeout + 3.0)
    if end_marker.encode() not in out:
        out += read_some(tn, quiet=2.0, hard=3.0)
    text = strip_ansi(out).decode("latin1", errors="replace")
    if end_marker not in text:
        debug("remote command timeout", {"cmd": cmd, "tail": text[-2000:]})
        raise RuntimeError("光猫响应超时，请确认连接稳定后重试。")
    return text


def is_our_tmp(path):
    return re.fullmatch(r"/tmp/oclg_[0-9]+_[0-9]+\.dec", path or "") is not None


def fetch_remote_file_base64(tn, remote_path):
    start = "__OC_B64_BEGIN__"
    end = "__OC_B64_END__"
    tn.write(f"printf '\\n{start}\\n'; base64 {remote_path}; printf '\\n{end}\\n'\n".encode())
    time.sleep(0.8)
    cap = read_some(tn, quiet=12.0, hard=18.0)
    if end.encode() not in cap:
        cap += read_some(tn, quiet=4.0, hard=6.0)
    if end.encode() not in cap:
        debug("fetch timeout", strip_ansi(cap)[-1500:].decode("latin1", errors="replace"))
        raise RuntimeError("传回结果超时，请重试。")

    cap = strip_ansi(cap)
    collecting = False
    b64_lines = []
    for line in cap.splitlines():
        s = line.strip()
        if s == start.encode():
            collecting = True
            continue
        if s == end.encode():
            break
        if collecting and re.fullmatch(rb"[A-Za-z0-9+/=]{8,}", s):
            b64_lines.append(s)
    if not b64_lines:
        debug("fetch empty", cap[:2000].decode("latin1", errors="replace"))
        raise RuntimeError("没有收到有效结果数据，请重试。")
    try:
        return base64.b64decode(b"".join(b64_lines))
    except Exception as e:
        debug("base64 decode failed", repr(e))
        raise RuntimeError("结果数据校验失败，请重试。")


def parse_value(xml_text, name):
    pattern = rf'<Value\s+Name="{re.escape(name)}"\s+Value="([^"]*)"'
    m = re.search(pattern, xml_text)
    return m.group(1) if m else ""


def run(params):
    logs = []
    host = str(params.get("host", "")).strip()
    port = int(str(params.get("port", "23")).strip() or "23")
    user = str(params.get("user", "")).strip()
    password = str(params.get("password", ""))
    output_dir = pathlib.Path(str(params.get("output_dir", str(pathlib.Path.home() / "Downloads")))).expanduser()
    clean_tmp = bool(params.get("clean_tmp", True))

    if not host:
        raise ValueError("请填写光猫 IP。")
    if not user:
        raise ValueError("请填写登录用户名。")
    if not password:
        raise ValueError("请填写登录密码。")
    output_dir.mkdir(parents=True, exist_ok=True)

    tn = None
    remote_tmp = f"/tmp/oclg_{int(time.time())}_{os.getpid()}.dec"
    try:
        log(logs, "步骤 1/5：正在连接光猫…")
        try:
            tn = MinimalTelnet(host, port, timeout=6)
            try:
                tn.get_socket().settimeout(0.5)
            except Exception:
                pass
        except Exception as e:
            raise RuntimeError(f"连接光猫失败：{e}")

        banner = tn.read_until(b"login:", timeout=5)
        if b"login:" not in banner:
            raise RuntimeError("连接成功但未进入登录流程，请确认光猫登录服务正常。")

        tn.write(user.encode() + b"\n")
        pw_prompt = tn.read_until(b"Password:", timeout=5)
        if b"Password:" not in pw_prompt:
            raise RuntimeError("用户名发送后未进入密码输入流程，请确认用户名正确。")

        tn.write(password.encode() + b"\n")
        time.sleep(1.0)
        out = read_some(tn, quiet=2.0, hard=4.0)
        # 注意：成功后可能输出 "login: can't change directory to '/root'"，不能把 login: 当失败
        if b"incorrect" in out.lower():
            raise RuntimeError("登录失败：用户名或密码不正确。")
        log(logs, "步骤 1/5：登录成功。")

        try:
            tn.write(b"stty -echo 2>/dev/null\n")
            time.sleep(0.2)
            read_some(tn, quiet=0.5, hard=1.5)
            tn.write(b"export PS1=''\n")
            time.sleep(0.2)
            read_some(tn, quiet=0.5, hard=1.5)
        except Exception:
            pass

        log(logs, "步骤 2/5：正在检查设备配置…")
        text = run_cmd(tn, f"[ -f {REMOTE_ENCRYPTED_FILE} ] && echo EXISTS && wc -c {REMOTE_ENCRYPTED_FILE} || echo MISSING", wait=0.5, timeout=4.0)
        if "EXISTS" not in text:
            raise RuntimeError("未找到配置文件，请确认设备型号/固件支持。")

        log(logs, "步骤 3/5：正在解析超级密码…")
        cmd = (
            f"rm -f {remote_tmp}; "
            f"cli {REMOTE_DECRYPT_SCRIPT} -v ifile {REMOTE_ENCRYPTED_FILE} ofile {remote_tmp}; "
            f"echo __CHECK_DEC_FILE__; "
            f"if [ -s {remote_tmp} ]; then echo __DEC_OK__; wc -c {remote_tmp}; "
            f"else echo __DEC_MISSING__; ls -l {remote_tmp} 2>&1; fi"
        )
        text = run_cmd(tn, cmd, wait=1.0, timeout=10.0)
        if "succ." not in text:
            debug("decrypt no succ", text)
            raise RuntimeError("解析失败：设备没有返回成功状态。")
        if "__DEC_OK__" not in text:
            debug("decrypt missing output", text)
            raise RuntimeError("解析失败：设备没有生成结果。")

        log(logs, "步骤 4/5：正在保存结果到电脑…")
        xml_bytes = fetch_remote_file_base64(tn, remote_tmp)
        xml_text = xml_bytes.decode("utf-8", errors="replace")
        super_account = parse_value(xml_text, "aucTeleAccountName")
        super_password = parse_value(xml_text, "aucTeleAccountPassword")
        if not super_account and not super_password:
            raise RuntimeError("未找到超级管理员账号/密码。")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_host = re.sub(r"[^0-9A-Za-z_.-]", "_", host)
        out_file = output_dir / f"jiulian_super_password_{safe_host}_{ts}.xml"
        out_file.write_bytes(xml_bytes)

        if clean_tmp:
            log(logs, "步骤 5/5：正在清理本次临时数据…")
            if is_our_tmp(remote_tmp):
                run_cmd(tn, f"rm -f {remote_tmp}; [ ! -f {remote_tmp} ] && echo CLEANED", wait=0.5, timeout=4.0)
            log(logs, "已清理本次临时数据。")
        else:
            log(logs, "已按设置保留本次临时数据。")

        log(logs, "完成：已成功获取超级密码。", "success")
        return {"ok": True, "logs": logs, "super_account": super_account or "未找到", "super_password": super_password or "未找到", "output_file": str(out_file)}
    finally:
        if tn is not None:
            try:
                tn.write(b"exit\n")
                tn.close()
            except Exception:
                pass


def main():
    global STREAM
    try:
        params = json.loads(sys.stdin.read() or "{}")
        STREAM = bool(params.get("stream"))
        result = run(params)
        if STREAM:
            final = {k: v for k, v in result.items() if k != "logs"}
            final["type"] = "result"
            emit(final)
        else:
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        debug("backend failed", traceback.format_exc())
        logs = []
        log(logs, f"FAIL: {e}", "error")
        log(logs, "请检查光猫 IP、登录用户名/密码、网络连接，确认设备在线后重试。", "error")
        result = {"ok": False, "logs": logs, "error": str(e)}
        if STREAM:
            emit({"type": "result", "ok": False, "error": str(e)})
        else:
            print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
