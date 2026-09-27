"""Double-click entry point for the self-contained Windows desktop edition."""

import ctypes
import json
import os
import secrets
import threading
import time
import traceback
import urllib.request
import webbrowser
from ctypes import wintypes

from app.state import APP_DATA_ROOT, TEMPLATE
from app.web import Handler, ThreadingHTTPServer
from app.tools.provider_settings import public_settings


URL_FILE = APP_DATA_ROOT / "desktop-url.txt"


def _windows_mutex() -> tuple[object | None, bool]:
    if os.name != "nt":
        return None, False
    kernel = ctypes.windll.kernel32
    kernel.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
    kernel.CreateMutexW.restype = wintypes.HANDLE
    handle = kernel.CreateMutexW(None, False, "Local\\ASWProject01ContactSheet")
    if not handle:
        raise OSError("无法创建单实例锁")
    return handle, kernel.GetLastError() == 183


def _open_running_page() -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(30):
        try:
            address = URL_FILE.read_text(encoding="utf-8").strip()
            if address.startswith("http://127.0.0.1:"):
                with opener.open(address + "api/config", timeout=1) as response:
                    if json.load(response).get("desktop_mode"):
                        webbrowser.open(address)
                        return
        except (OSError, ValueError):
            pass
        time.sleep(0.1)


class DesktopHandler(Handler):
    def log_message(self, format: str, *args) -> None:
        """The windowed exe has no stderr for the standard HTTP request log."""

    def do_GET(self) -> None:
        if self.path == "/api/config":
            self.send_json(200, {**public_settings(), "template_ready": TEMPLATE.exists(),
                                 "desktop_mode": True, "quit_token": self.server.quit_token})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/desktop/quit":
            if self.headers.get("X-ASW-Desktop-Token") != self.server.quit_token:
                self.send_json(403, {"error": "无权退出程序"})
                return
            self.send_json(200, {"ok": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        super().do_POST()


class DesktopServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address) -> None:
        """Keep request failures diagnosable when the exe has no console."""
        try:
            APP_DATA_ROOT.mkdir(parents=True, exist_ok=True)
            with (APP_DATA_ROOT / "desktop-error.log").open("a", encoding="utf-8") as output:
                traceback.print_exc(file=output)
        except OSError:
            pass


def main() -> None:
    handle, already_running = _windows_mutex()
    try:
        if already_running:
            _open_running_page()
            return
        try:
            server = DesktopServer(("127.0.0.1", 0), DesktopHandler)
        except OSError as error:
            APP_DATA_ROOT.mkdir(parents=True, exist_ok=True)
            (APP_DATA_ROOT / "desktop-error.log").write_text(f"启动失败：{error}\n", encoding="utf-8")
            return
        server.quit_token = secrets.token_urlsafe(32)
        address = f"http://127.0.0.1:{server.server_address[1]}/"
        APP_DATA_ROOT.mkdir(parents=True, exist_ok=True)
        URL_FILE.write_text(address, encoding="utf-8")
        browser_timer = threading.Timer(0.3, lambda: webbrowser.open(address))
        browser_timer.daemon = True
        browser_timer.start()
        try:
            server.serve_forever()
        finally:
            server.server_close()
            if URL_FILE.exists() and URL_FILE.read_text(encoding="utf-8").strip() == address:
                URL_FILE.unlink(missing_ok=True)
    finally:
        if handle is not None:
            ctypes.windll.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
