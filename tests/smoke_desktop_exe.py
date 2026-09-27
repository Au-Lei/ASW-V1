"""Exercise a running desktop exe with a local, fake AI service."""

import base64
import io
import json
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.state import FIELDS


class FakeAI(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt = request["messages"][0]["content"]
        if prompt.startswith("只输出 JSON 对象"):
            answer = {"ok": True}
        else:
            answer = {key: {name: "" for name in ("value", "evidence", "source", "source_label", "review_reason")} for key in FIELDS}
            answer["sailing_date"].update(value="08-Sep-2026", evidence="PROFORMA ETD:08-Sep-2026", source="sample.xlsx", source_label="PROFORMA ETD")
            answer["destination"].update(value="HAMAD;QATAR", evidence="卸货港: HAMAD;QATAR", source="sample.xlsx", source_label="卸货港")
        body = json.dumps({"choices": [{"message": {"content": json.dumps(answer, ensure_ascii=False)}}]}, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:
        pass


def post(opener, url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    return json.load(opener.open(request, timeout=15))


def main(app_url: str) -> None:
    service = ThreadingHTTPServer(("127.0.0.1", 0), FakeAI)
    thread = threading.Thread(target=service.serve_forever, daemon=True)
    thread.start()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        config = post(opener, app_url + "/api/config", {
            "action": "test", "base_url": f"http://127.0.0.1:{service.server_port}/v1",
            "api_key": "local-test-only", "model": "mock-model",
        })
        assert config["ai_available"] is True
        workbook = openpyxl.Workbook()
        workbook.active["A1"] = "PROFORMA ETD:08-Sep-2026; 卸货港: HAMAD;QATAR"
        buffer = io.BytesIO()
        workbook.save(buffer)
        result = post(opener, app_url + "/api/extract", {
            "mode": "ai", "documents": [{"name": "sample.xlsx", "role": "入货通知", "data": base64.b64encode(buffer.getvalue()).decode()}],
        })
        assert result["fields"]["sailing_date"]["value"] == "9.8", result
        assert result["fields"]["destination"]["value"] == "HAMAD", result
        print("Packaged AI connection and extraction: OK")
    finally:
        try:
            post(opener, app_url + "/api/config", {"action": "clear"})
        finally:
            service.shutdown()
            service.server_close()


if __name__ == "__main__":
    main(sys.argv[1].rstrip("/"))
