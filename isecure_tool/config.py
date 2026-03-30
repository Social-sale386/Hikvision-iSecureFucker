from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path(__file__).resolve().parent.parent / "isecure_tool_config.ini"

DEFAULT_CONFIG: Dict[str, Any] = {
    "app_key": "",
    "app_secret": "",
    "scheme": "https",
    "method": "POST",
    "host": "127.0.0.1:443",
    "api_path": "/api/resource/v1/org/advance/orgList",
    "auto_artemis": True,
    "params_json": '{\n  "pageNo": 1,\n  "pageSize": 100\n}',
    "headers_json": "{}",
    "sign_headers": "",
    "accept": "*/*",
    "content_type": "application/json",
    "use_date": False,
    "verify_ssl": False,
    "ca_bundle": "",
    "timeout_sec": 20,
    "convert_time": True,
    "show_signing": True,
    "body_form": False,
    "auto_pretty_params": True,
}

COMMENTS: Dict[str, str] = {
    "app_key": "AK/SK 鉴权中的 AppKey",
    "app_secret": "AK/SK 鉴权中的 AppSecret",
    "scheme": "请求协议: https 或 http",
    "method": "HTTP 方法: GET/POST/PUT/DELETE",
    "host": "平台地址与端口，例如 10.1.10.1:443",
    "api_path": "接口 URL 路径，例如 /api/resource/v1/org/advance/orgList",
    "auto_artemis": "是否自动补全 /artemis 前缀",
    "params_json": "请求参数(JSON 字符串，换行会转义保存)",
    "headers_json": "额外请求头(JSON 字符串，换行会转义保存)",
    "sign_headers": "自定义签名头列表，英文逗号分隔",
    "accept": "Accept 请求头",
    "content_type": "Content-Type 请求头",
    "use_date": "是否在签名中带 Date 头",
    "verify_ssl": "是否校验证书",
    "ca_bundle": "CA 证书文件路径",
    "timeout_sec": "请求超时(秒)",
    "convert_time": "是否将时间戳自动转 ISO8601",
    "show_signing": "是否在调试页显示签名字符串",
    "body_form": "是否使用表单提交(body form)",
    "auto_pretty_params": "发送前是否自动格式化请求参数 JSON",
}

MULTILINE_KEYS = {"params_json", "headers_json"}


def _parse_bool(value: str, default: bool) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_value(key: str, raw: str, default: Any) -> Any:
    text = raw.strip()
    if key in MULTILINE_KEYS:
        text = text.replace("\\n", "\n")

    if isinstance(default, bool):
        return _parse_bool(text, default)
    if isinstance(default, int):
        try:
            return int(text)
        except Exception:
            return default
    if isinstance(default, float):
        try:
            return float(text)
        except Exception:
            return default
    return text


def _format_value(key: str, value: Any, default: Any) -> str:
    if isinstance(default, bool):
        return "true" if bool(value) else "false"
    text = str(value)
    if key in MULTILINE_KEYS:
        text = text.replace("\r\n", "\n").replace("\n", "\\n")
    return text


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    merged = DEFAULT_CONFIG.copy()
    current_key: str | None = None

    try:
        lines = CONFIG_PATH.read_text(encoding="utf-8").splitlines()
    except Exception:
        return merged

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(";"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current_key = None
            continue
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key in merged:
                merged[key] = _parse_value(key, value, DEFAULT_CONFIG[key])
                current_key = key
            else:
                current_key = None
            continue
        if current_key in MULTILINE_KEYS:
            appended = stripped
            existing = str(merged[current_key])
            merged[current_key] = existing + "\n" + appended

    return merged


def save_config(config: Dict[str, Any]) -> None:
    merged = DEFAULT_CONFIG.copy()
    for key in merged:
        if key in config:
            merged[key] = config[key]

    lines = [
        "# iSecure Center local configuration",
        "# 保存位置: 与 main.py 同级目录",
        "# 注意: 修改后会在下一次发送请求时生效",
        "",
        "[settings]",
    ]

    for key, default in DEFAULT_CONFIG.items():
        comment = COMMENTS.get(key, "")
        if comment:
            lines.append(f"# {comment}")
        value = _format_value(key, merged.get(key, default), default)
        lines.append(f"{key} = {value}")
        lines.append("")

    CONFIG_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
