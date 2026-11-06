# -*- coding: utf-8 -*-
"""Temporary Streamable HTTP MCP client for hosts without registered tools.

Only Python's standard library is required. The API key stays in memory and
the temporary cache contains only a non-reversible key fingerprint.
"""

import argparse
import hashlib
import json
import os
import socket
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from agent_source import source_headers
from config_reader import get_api_key


PROTOCOL_VERSION = "2025-06-18"
CLIENT_NAME = "nicebox-site-manager-direct"
CLIENT_VERSION = "0.4.16"
CONFIG_FILE = Path(__file__).with_name("mcp_connection.json")
TOOL_MANIFEST_FILE = Path(__file__).with_name("fallback_manifest.json")
CACHE_DIR = Path(tempfile.gettempdir()) / "nicebox-site-manager-mcp"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


class DirectMcpError(RuntimeError):
    def __init__(self, message, kind="protocol", retryable=False, allow_api_fallback=False, status=None, data=None):
        super().__init__(message)
        self.kind = kind
        self.retryable = bool(retryable)
        self.allow_api_fallback = bool(allow_api_fallback)
        self.status = status
        self.data = data


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
            return value if isinstance(value, dict) else (default or {})
    except (OSError, ValueError):
        return default or {}


def _connection_config():
    config = _read_json(CONFIG_FILE)
    primary = str(os.environ.get("NICEBOX_MCP_PRIMARY_URL") or config.get("primary_url") or "").strip()
    fallback = str(os.environ.get("NICEBOX_MCP_FALLBACK_URL") or config.get("fallback_url") or "").strip()
    urls = []
    for url in (primary, fallback):
        if url and url not in urls:
            if not url.lower().startswith("https://"):
                raise DirectMcpError("临时连接配置无效", "config", False, False)
            urls.append(url)
    if not urls:
        raise DirectMcpError("临时连接配置缺失", "config", False, True)
    return {
        "urls": urls,
        "connect_timeout": max(1, int(config.get("connect_timeout_seconds", 25))),
        "request_timeout": max(1, int(config.get("request_timeout_seconds", 600))),
        "session_ttl": max(60, int(config.get("session_ttl_seconds", 1500))),
    }


def _validate_tool_name(tool_name):
    manifest = _read_json(TOOL_MANIFEST_FILE)
    if tool_name not in manifest:
        raise DirectMcpError("当前能力未登记，无法执行", "input", False, False)


def _is_read_only_tool(tool_name):
    name = tool_name[len("nicebox_"):] if tool_name.startswith("nicebox_") else tool_name
    return name.startswith(("get_", "list_", "search_", "verify_", "diagnose_", "validate_"))


def _is_capability_error(message):
    text = str(message or "").lower()
    return ("tool " in text and ("not found" in text or "disabled" in text)) or "method not found" in text


def _fingerprint(api_key):
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _cache_file(api_key):
    return CACHE_DIR / ("session-" + _fingerprint(api_key)[:24] + ".json")


def _delete_session(api_key):
    try:
        _cache_file(api_key).unlink()
    except OSError:
        pass


def _load_session(api_key, ttl):
    session = _read_json(_cache_file(api_key))
    if not session:
        return None
    if session.get("key_fingerprint") != _fingerprint(api_key):
        _delete_session(api_key)
        return None
    created_at = float(session.get("created_at") or 0)
    if created_at <= 0 or time.time() - created_at >= ttl:
        _delete_session(api_key)
        return None
    if not session.get("session_id") or not session.get("url"):
        _delete_session(api_key)
        return None
    return session


def _save_session(api_key, url, session_id, protocol_version):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_file(api_key)
    value = {
        "key_fingerprint": _fingerprint(api_key),
        "url": url,
        "session_id": session_id,
        "protocol_version": protocol_version or PROTOCOL_VERSION,
        "created_at": time.time(),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return value


def _parse_sse(raw):
    messages = []
    data_lines = []
    for line in raw.replace("\r\n", "\n").split("\n") + [""]:
        if line == "":
            if data_lines:
                try:
                    messages.append(json.loads("\n".join(data_lines)))
                except ValueError as error:
                    raise DirectMcpError("临时连接返回了无法识别的数据", "protocol", True, True) from error
                data_lines = []
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if not messages:
        raise DirectMcpError("临时连接未返回结果", "protocol", True, True)
    return messages[-1]


def _parse_response(response, body):
    if not body.strip():
        return None
    content_type = (response.headers.get("Content-Type") or "").lower()
    text = body.decode("utf-8", errors="replace")
    try:
        return _parse_sse(text) if "text/event-stream" in content_type else json.loads(text)
    except ValueError as error:
        raise DirectMcpError("临时连接返回了无法识别的数据", "protocol", True, True) from error


def _http_error(error):
    status = getattr(error, "code", None)
    if status in (401, 403):
        return DirectMcpError("当前连接已失效，请重新连接", "authentication", False, False, status)
    if status == 409:
        return DirectMcpError("临时会话已失效", "session", True, True, status)
    if status is not None and status >= 500:
        return DirectMcpError("连接暂时不可用，请稍后重试", "transport", True, True, status)
    return DirectMcpError("临时连接请求未完成", "protocol", False, False, status)


def _post(url, api_key, payload, timeout, session=None):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = {
        "Authorization": "Bearer " + api_key,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "User-Agent": CLIENT_NAME + "/" + CLIENT_VERSION,
        **source_headers("/mcp", "temporary_mcp"),
    }
    if session:
        headers["Mcp-Session-Id"] = session["session_id"]
        headers["Mcp-Protocol-Version"] = session.get("protocol_version") or PROTOCOL_VERSION
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _parse_response(response, response.read()), dict(response.headers.items())
    except urllib.error.HTTPError as error:
        raise _http_error(error) from error
    except (urllib.error.URLError, socket.timeout, TimeoutError, ssl.SSLError, OSError) as error:
        raise DirectMcpError("连接暂时不可用，请稍后重试", "transport", True, True) from error


def _rpc_result(message):
    if not isinstance(message, dict):
        raise DirectMcpError("临时连接返回格式错误", "protocol", True, True)
    error = message.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        message_text = str(error.get("message") or "请求未完成")
        if code == -32601 or _is_capability_error(message_text):
            raise DirectMcpError(message_text, "capability", False, True)
        if code in (-32001, -32002) and "连接" in message_text:
            raise DirectMcpError("连接暂时不可用，请稍后重试", "transport", True, True)
        raise DirectMcpError(message_text, "business", False, False)
    if "result" not in message:
        raise DirectMcpError("临时连接缺少结果", "protocol", True, True)
    return message["result"]


def _initialize(url, api_key, timeout):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
        },
    }
    message, headers = _post(url, api_key, payload, timeout)
    result = _rpc_result(message)
    session_id = headers.get("Mcp-Session-Id") or headers.get("mcp-session-id")
    if not session_id:
        raise DirectMcpError("临时连接未建立会话", "protocol", True, True)
    protocol_version = result.get("protocolVersion") if isinstance(result, dict) else PROTOCOL_VERSION
    session = _save_session(api_key, url, session_id, protocol_version)
    _post(url, api_key, {"jsonrpc": "2.0", "method": "notifications/initialized"}, timeout, session)
    return session


def _ordered_urls(config, cached_session):
    urls = list(config["urls"])
    if cached_session and cached_session.get("url") in urls:
        selected = cached_session["url"]
        return [selected] + [url for url in urls if url != selected]
    return urls


def call_tool(tool_name, arguments):
    _validate_tool_name(tool_name)
    api_key = get_api_key()
    if not api_key:
        raise DirectMcpError("请先连接 Nicebox.AI 建站助手", "config", False, False)
    config = _connection_config()
    cached = _load_session(api_key, config["session_ttl"])
    last_error = None
    for url in _ordered_urls(config, cached):
        session = cached if cached and cached.get("url") == url else None
        for attempt in range(2):
            try:
                if session is None:
                    session = _initialize(url, api_key, config["connect_timeout"])
                request = {
                    "jsonrpc": "2.0",
                    "id": int(time.time() * 1000),
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                }
                message, _headers = _post(url, api_key, request, config["request_timeout"], session)
                result = _rpc_result(message)
                if isinstance(result, dict) and result.get("isError") is True:
                    message_text = "业务操作未完成"
                    content = result.get("content")
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                                message_text = str(item["text"])
                                break
                    if _is_capability_error(message_text):
                        raise DirectMcpError(message_text, "capability", False, True, data=result)
                    raise DirectMcpError(message_text, "business", False, False, data=result)
                return result
            except DirectMcpError as error:
                last_error = error
                if (error.kind == "session" or error.status == 400) and attempt == 0:
                    _delete_session(api_key)
                    session = None
                    continue
                if not error.allow_api_fallback:
                    raise
                if session is not None and not _is_read_only_tool(tool_name) and error.kind != "capability":
                    raise DirectMcpError(
                        "操作结果暂时无法确认，请先查询当前状态",
                        "result_unknown",
                        True,
                        False,
                    ) from error
                break
    raise last_error or DirectMcpError("连接暂时不可用，请稍后重试", "transport", True, True)


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Nicebox 临时连接客户端")
    subparsers = parser.add_subparsers(dest="command", required=True)
    call_parser = subparsers.add_parser("call", help="调用一个 Nicebox 工具")
    call_parser.add_argument("--tool", required=True)
    call_parser.add_argument("--args-json", default="{}")
    args = parser.parse_args(argv)
    try:
        arguments = json.loads(args.args_json)
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be an object")
    except ValueError:
        _print_json({"ok": False, "error": {"kind": "input", "message": "调用参数必须是 JSON 对象", "allow_api_fallback": False}})
        return 4
    try:
        _print_json({"ok": True, "result": call_tool(args.tool, arguments)})
        return 0
    except DirectMcpError as error:
        _print_json({
            "ok": False,
            "error": {
                "kind": error.kind,
                "message": str(error),
                "retryable": error.retryable,
                "allow_api_fallback": error.allow_api_fallback,
            },
            **({"result": error.data} if error.data is not None else {}),
        })
        return 2 if error.allow_api_fallback else 3


if __name__ == "__main__":
    sys.exit(main())
