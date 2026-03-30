from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from urllib.parse import urlencode

import requests

from .signer import SignatureResult, sign_request
from .utils import (
    build_full_url,
    canonicalize_query,
    combine_query_items,
    convert_time_values,
    parse_json_text,
)


@dataclass
class RequestDebug:
    full_url: str
    canonical_resource: str
    string_to_sign: str
    request_headers: Dict[str, str]
    request_body: str


@dataclass
class ResponseData:
    ok: bool
    status_code: int | None
    elapsed_ms: float | None
    response_headers: Dict[str, str]
    response_text: str
    error: str | None
    debug: RequestDebug | None


def _pretty_json(text: str) -> str:
    try:
        obj = json.loads(text)
    except Exception:
        return text
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _prepare_payload(method: str, params_obj: Any) -> tuple[bytes | None, str]:
    method = method.upper()
    if method in {"GET", "DELETE"}:
        return None, ""

    if params_obj is None:
        body_text = ""
        return body_text.encode("utf-8"), body_text

    body_text = json.dumps(params_obj, ensure_ascii=False)
    return body_text.encode("utf-8"), body_text


def send_request(config: Dict[str, Any]) -> ResponseData:
    method = str(config.get("method", "POST")).upper()
    scheme = str(config.get("scheme", "https")).lower()
    host = str(config.get("host", "")).strip()
    api_path = str(config.get("api_path", "")).strip()
    auto_artemis = bool(config.get("auto_artemis", True))

    if auto_artemis and api_path and not api_path.startswith(("http://", "https://")):
        normalized = api_path if api_path.startswith("/") else f"/{api_path}"
        if not (normalized == "/artemis" or normalized.startswith("/artemis/")):
            normalized = f"/artemis{normalized}"
        api_path = normalized

    app_key = str(config.get("app_key", "")).strip()
    app_secret = str(config.get("app_secret", "")).strip()

    if not app_key or not app_secret:
        return ResponseData(
            ok=False,
            status_code=None,
            elapsed_ms=None,
            response_headers={},
            response_text="",
            error="AppKey 或 AppSecret 为空",
            debug=None,
        )

    ok, params_obj, err = parse_json_text(str(config.get("params_json", "")))
    if not ok:
        return ResponseData(
            ok=False,
            status_code=None,
            elapsed_ms=None,
            response_headers={},
            response_text="",
            error=f"请求参数 JSON 解析失败: {err}",
            debug=None,
        )

    ok, headers_obj, err = parse_json_text(str(config.get("headers_json", "")))
    if not ok:
        return ResponseData(
            ok=False,
            status_code=None,
            elapsed_ms=None,
            response_headers={},
            response_text="",
            error=f"额外请求头 JSON 解析失败: {err}",
            debug=None,
        )

    headers_obj = headers_obj or {}
    if headers_obj and not isinstance(headers_obj, dict):
        return ResponseData(
            ok=False,
            status_code=None,
            elapsed_ms=None,
            response_headers={},
            response_text="",
            error="额外请求头必须是 JSON 对象",
            debug=None,
        )

    params_obj = params_obj or {}
    if method in {"GET", "DELETE"} and params_obj and not isinstance(params_obj, dict):
        return ResponseData(
            ok=False,
            status_code=None,
            elapsed_ms=None,
            response_headers={},
            response_text="",
            error="GET/DELETE 请求参数必须是 JSON 对象",
            debug=None,
        )

    if config.get("convert_time"):
        params_obj = convert_time_values(params_obj)

    full_url, path, query_items = build_full_url(scheme, host, api_path)

    use_form = bool(config.get("body_form"))
    sign_query_items = list(query_items)

    if method in {"GET", "DELETE"}:
        query_items = combine_query_items(query_items, params_obj)
        sign_query_items = list(query_items)
        body_bytes, body_text = None, ""
    else:
        if use_form:
            if params_obj and not isinstance(params_obj, dict):
                return ResponseData(
                    ok=False,
                    status_code=None,
                    elapsed_ms=None,
                    response_headers={},
                    response_text="",
                    error="表单提交需要 JSON 对象参数",
                    debug=None,
                )
            form_items = combine_query_items([], params_obj)
            sign_query_items = list(query_items) + form_items
            encoded_body = urlencode([(k, "" if v is None else str(v)) for k, v in form_items], doseq=True)
            body_text = encoded_body
            body_bytes = encoded_body.encode("utf-8")
        else:
            body_bytes, body_text = _prepare_payload(method, params_obj)

    query_string = canonicalize_query(query_items)
    if query_string:
        full_url = f"{full_url}?{query_string}"

    base_headers: Dict[str, Any] = dict(headers_obj)
    accept = str(config.get("accept", "")).strip()
    content_type = str(config.get("content_type", "")).strip()
    if accept:
        base_headers.setdefault("Accept", accept)
    else:
        base_headers.setdefault("Accept", "*/*")
    if content_type:
        base_headers.setdefault("Content-Type", content_type)
    if use_form and not content_type and "Content-Type" not in base_headers:
        base_headers["Content-Type"] = "application/x-www-form-urlencoded"
    if not use_form and not content_type and body_bytes is not None and "Content-Type" not in base_headers:
        base_headers["Content-Type"] = "application/json"

    signature: SignatureResult = sign_request(
        method=method,
        path=path,
        query_items=sign_query_items,
        headers=base_headers,
        body=body_bytes if body_bytes else None,
        app_key=app_key,
        app_secret=app_secret,
        sign_headers_override=str(config.get("sign_headers", "")) or None,
        use_date=bool(config.get("use_date")),
        compute_content_md5=not use_form,
    )

    verify_ssl = bool(config.get("verify_ssl", True))
    ca_bundle = str(config.get("ca_bundle", "")).strip()
    timeout_sec = float(config.get("timeout_sec", 10))

    start = time.perf_counter()
    try:
        verify_setting: bool | str = verify_ssl
        if verify_ssl and ca_bundle:
            verify_setting = ca_bundle
        resp = requests.request(
            method,
            full_url,
            headers=signature.headers,
            data=body_bytes if body_bytes else None,
            verify=verify_setting,
            timeout=timeout_sec,
        )
    except Exception as exc:
        return ResponseData(
            ok=False,
            status_code=None,
            elapsed_ms=None,
            response_headers={},
            response_text="",
            error=str(exc),
            debug=RequestDebug(
                full_url=full_url,
                canonical_resource=signature.canonical_resource,
                string_to_sign=signature.string_to_sign,
                request_headers=signature.headers,
                request_body=body_text,
            ),
        )

    elapsed_ms = (time.perf_counter() - start) * 1000
    response_text = resp.text
    pretty = _pretty_json(response_text)

    return ResponseData(
        ok=resp.ok,
        status_code=resp.status_code,
        elapsed_ms=elapsed_ms,
        response_headers=dict(resp.headers),
        response_text=pretty,
        error=None if resp.ok else f"HTTP {resp.status_code}",
        debug=RequestDebug(
            full_url=full_url,
            canonical_resource=signature.canonical_resource,
            string_to_sign=signature.string_to_sign,
            request_headers=signature.headers,
            request_body=body_text,
        ),
    )
