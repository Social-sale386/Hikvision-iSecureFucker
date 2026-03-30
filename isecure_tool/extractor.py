from __future__ import annotations

import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import QThread, Signal

from .client import send_request


CATEGORY_ORDER = ["基础信息", "监控点", "人员", "组织", "停车场", "其他"]
PATH_LINE_RE = re.compile(r"^\*?\s*/api/[A-Za-z0-9_./:-]+$")
INT_KEYS = ("total", "totalCount", "totalNum", "count")


@dataclass
class ExtractAPI:
    title: str
    path: str
    method: str
    request_example: str
    disabled: bool
    category: str
    required_params: list[str]
    all_params: list[str]


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", name).strip()
    return cleaned or "unnamed_api"


def _classify_path(path: str) -> str:
    low = path.lower()
    if "/eventservice/" in low or "/nms/v1/online/" in low or "/tvms/" in low:
        return "基础信息"
    if "/resource/v1/cameras" in low or "/resource/v2/camera/" in low or "/resource/v2/door/" in low:
        return "监控点"
    if "/frs/" in low or "/person/" in low:
        return "人员"
    if "/org/" in low:
        return "组织"
    if "/pms/" in low or "/park/" in low or "/vehicle/" in low:
        return "停车场"
    return "其他"


def _parse_temp_list(temp_file: Path) -> list[dict[str, Any]]:
    lines = _read_utf8(temp_file).splitlines()
    items: list[dict[str, Any]] = []
    pending_title = ""
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        if PATH_LINE_RE.match(text):
            disabled = text.startswith("*")
            path = text.lstrip("*").strip()
            title = pending_title.lstrip("*").strip() if pending_title else path
            if pending_title.startswith("*"):
                disabled = True
            items.append(
                {
                    "title": title or path,
                    "path": path,
                    "disabled": disabled,
                }
            )
            pending_title = ""
            continue
        pending_title = text
    return items


def _load_doc_index(index_file: Path) -> dict[str, dict[str, Any]]:
    if not index_file.exists():
        return {}
    try:
        data = json.loads(_read_utf8(index_file))
    except Exception:
        return {}
    path_map: dict[str, dict[str, Any]] = {}
    if isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("doc_type", "")).lower() != "api":
                continue
            path = str(entry.get("path", "")).strip()
            if not path:
                continue
            path_map[path] = entry
    return path_map


def _load_param_meta(summary_file: Path) -> dict[str, dict[str, list[str]]]:
    if not summary_file.exists():
        return {}
    try:
        data = json.loads(_read_utf8(summary_file))
    except Exception:
        return {}

    groups: list[list[dict[str, Any]]] = []
    for key in ("A组", "B组", "group_a", "group_b"):
        value = data.get(key)
        if isinstance(value, list):
            groups.append([x for x in value if isinstance(x, dict)])

    result: dict[str, dict[str, list[str]]] = {}
    for group in groups:
        for item in group:
            path = str(item.get("path", "")).strip()
            if not path:
                continue
            result[path] = {
                "required_params": [str(x) for x in item.get("required_params", []) if str(x)],
                "all_params": [str(x) for x in item.get("all_params", []) if str(x)],
            }
    return result


def load_extract_apis(base_dir: Path) -> list[ExtractAPI]:
    temp_file = base_dir / "temp.txt"
    index_file = base_dir / "doc" / "index.json"
    summary_file = base_dir / "api_low_param_summary.json"

    raw_items = _parse_temp_list(temp_file) if temp_file.exists() else []
    doc_map = _load_doc_index(index_file)
    meta_map = _load_param_meta(summary_file)

    apis: list[tuple[int, int, ExtractAPI]] = []
    for order_idx, item in enumerate(raw_items):
        path = str(item["path"])
        doc = doc_map.get(path, {})
        title = str(item["title"] or doc.get("title") or path)
        method = str(doc.get("method", "POST")).upper().strip() or "POST"
        request_example = str(doc.get("request_example", "") or "")
        category = _classify_path(path)
        priority = CATEGORY_ORDER.index(category) if category in CATEGORY_ORDER else len(CATEGORY_ORDER)
        meta = meta_map.get(path, {})
        api = ExtractAPI(
            title=title,
            path=path,
            method=method,
            request_example=request_example,
            disabled=bool(item.get("disabled")),
            category=category,
            required_params=list(meta.get("required_params", [])),
            all_params=list(meta.get("all_params", [])),
        )
        apis.append((priority, order_idx, api))

    apis.sort(key=lambda x: (x[0], x[1]))
    return [item[2] for item in apis]


def _parse_request_example(request_example: str) -> dict[str, Any]:
    text = (request_example or "").strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
        return {}
    except Exception:
        return {}


def _extract_int_value(data: dict[str, Any]) -> int | None:
    for key in INT_KEYS:
        value = data.get(key)
        try:
            if value is None:
                continue
            return int(value)
        except Exception:
            continue
    return None


def _extract_page_records(payload: Any) -> list[dict[str, Any]]:
    def normalize_row(row: Any) -> dict[str, Any]:
        if isinstance(row, dict):
            return row
        return {"value": row}

    if isinstance(payload, list):
        return [normalize_row(row) for row in payload]

    if isinstance(payload, dict):
        for key in ("list", "rows", "records", "items", "detail", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return [normalize_row(row) for row in value]
        list_values = [value for value in payload.values() if isinstance(value, list)]
        if len(list_values) == 1:
            return [normalize_row(row) for row in list_values[0]]
        return [payload]

    return [{"value": payload}]


def _flatten_row(row: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        field = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            out.update(_flatten_row(value, field))
        elif isinstance(value, list):
            out[field] = json.dumps(value, ensure_ascii=False)
        else:
            out[field] = value
    return out


def save_rows_to_xlsx(file_path: Path, rows: list[dict[str, Any]]) -> None:
    try:
        from openpyxl import Workbook
    except Exception as exc:
        raise RuntimeError("未安装 openpyxl，无法导出 xlsx，请先安装依赖。") from exc

    normalized = [_flatten_row(row) for row in rows] if rows else [{"message": "empty"}]
    headers: list[str] = []
    seen: set[str] = set()
    for row in normalized:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                headers.append(key)

    wb = Workbook()
    ws = wb.active
    ws.title = "data"
    ws.append(headers)
    for row in normalized:
        ws.append([row.get(key, "") for key in headers])
    ws.freeze_panes = "A2"
    wb.save(file_path)


class ExtractionWorker(QThread):
    log = Signal(str)
    api_progress = Signal(int, int, str)
    all_progress = Signal(int, int, str)
    speed_eta = Signal(str)
    api_saved = Signal(str, str, int)
    done = Signal(bool, str)

    def __init__(
        self,
        tasks: list[ExtractAPI],
        base_config: dict[str, Any],
        output_dir: Path,
    ) -> None:
        super().__init__()
        self.tasks = tasks
        self.base_config = base_config
        self.output_dir = output_dir
        self.max_pages = 2000
        self._started_ts = 0.0
        self._processed_pages = 0

    def _emit_speed(self, done_apis: int, total_apis: int) -> None:
        elapsed = max(time.time() - self._started_ts, 0.001)
        page_speed = self._processed_pages / elapsed
        api_speed = done_apis / elapsed if done_apis > 0 else 0.0
        if api_speed > 0 and total_apis > done_apis:
            eta_seconds = (total_apis - done_apis) / api_speed
            eta_text = f"{eta_seconds:.1f}s"
        else:
            eta_text = "--"
        text = (
            f"速度: {page_speed:.2f} 页/秒 | {api_speed:.2f} 接口/秒 | "
            f"预计剩余: {eta_text}"
        )
        self.speed_eta.emit(text)

    def _build_request_config(self, task: ExtractAPI, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "app_key": self.base_config.get("app_key", ""),
            "app_secret": self.base_config.get("app_secret", ""),
            "scheme": self.base_config.get("scheme", "https"),
            "method": method,
            "host": self.base_config.get("host", ""),
            "api_path": task.path,
            "auto_artemis": True,
            "params_json": json.dumps(payload, ensure_ascii=False),
            "headers_json": self.base_config.get("headers_json", "{}"),
            "sign_headers": self.base_config.get("sign_headers", ""),
            "accept": self.base_config.get("accept", "*/*"),
            "content_type": self.base_config.get("content_type", "application/json"),
            "use_date": bool(self.base_config.get("use_date", False)),
            "verify_ssl": bool(self.base_config.get("verify_ssl", True)),
            "ca_bundle": self.base_config.get("ca_bundle", ""),
            "timeout_sec": self.base_config.get("timeout_sec", 20),
            "convert_time": False,
            "show_signing": False,
            "body_form": False,
            "auto_pretty_params": False,
        }

    def _method_for_task(self, task: ExtractAPI) -> str:
        override = str(self.base_config.get("method_override", "AUTO")).upper().strip()
        if override and override != "AUTO":
            return override
        return task.method or "POST"

    def _should_paginate(self, task: ExtractAPI, payload: dict[str, Any]) -> bool:
        keys = set(payload.keys())
        required = set(task.required_params)
        all_params = set(task.all_params)
        if "pageNo" in keys or "pageSize" in keys:
            return True
        if "pageNo" in required or "pageSize" in required:
            return True
        if "pageNo" in all_params and "pageSize" in all_params:
            return True
        path = task.path.lower()
        if "/page" in path:
            return True
        return False

    def _extract_single(self, task: ExtractAPI, done_apis: int, total_apis: int) -> tuple[int, int]:
        method = self._method_for_task(task)
        payload = _parse_request_example(task.request_example)
        paginate = self._should_paginate(task, payload)
        if paginate:
            payload["pageNo"] = 1
            payload["pageSize"] = 1000

        current_page = int(payload.get("pageNo", 1) or 1)
        total_pages = 0
        total_rows: list[dict[str, Any]] = []
        seen_responses: set[int] = set()

        while True:
            if paginate:
                payload["pageNo"] = current_page

            req_cfg = self._build_request_config(task, method, payload)
            resp = send_request(req_cfg)
            if not resp.ok and resp.error and not resp.response_text:
                raise RuntimeError(resp.error)
            if not resp.response_text:
                raise RuntimeError("响应为空，无法解析")

            try:
                body = json.loads(resp.response_text)
            except Exception as exc:
                raise RuntimeError(f"响应不是合法 JSON: {exc}") from exc

            if isinstance(body, dict):
                code = body.get("code")
                if code not in (None, 0, "0"):
                    self.log.emit(f"{task.title}: 返回 code={code}, msg={body.get('msg', '')}")
                data = body.get("data")
            else:
                data = body

            rows = _extract_page_records(data)
            total_rows.extend(rows)

            self._processed_pages += 1
            self.log.emit(
                f"{task.title}: 第 {current_page} 页完成, 本页 {len(rows)} 条, 累计 {len(total_rows)} 条"
            )
            self._emit_speed(done_apis, total_apis)

            data_dict = data if isinstance(data, dict) else {}
            total = _extract_int_value(data_dict)
            if total is not None and paginate:
                page_size = int(payload.get("pageSize", 1000) or 1000)
                if page_size > 0:
                    total_pages = max(1, math.ceil(total / page_size))

            self.api_progress.emit(current_page, total_pages, task.title)
            response_hash = hash(resp.response_text)
            if response_hash in seen_responses and paginate:
                self.log.emit(f"{task.title}: 检测到重复页面响应，提前结束翻页")
                break
            seen_responses.add(response_hash)

            if not paginate:
                break
            if total_pages > 0 and current_page >= total_pages:
                break
            if isinstance(data_dict.get("lastPage"), bool) and data_dict["lastPage"]:
                break
            if len(rows) == 0:
                break
            if len(rows) < int(payload.get("pageSize", 1000) or 1000) and total_pages == 0:
                break
            if current_page >= self.max_pages:
                self.log.emit(f"{task.title}: 已达最大翻页限制 {self.max_pages}，停止")
                break

            current_page += 1

        if not total_rows:
            total_rows = [{"message": "empty"}]

        self.output_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{_safe_filename(task.title)}.xlsx"
        out_file = self.output_dir / file_name
        save_rows_to_xlsx(out_file, total_rows)
        self.api_saved.emit(task.title, str(out_file), len(total_rows))
        return len(total_rows), current_page

    def run(self) -> None:
        enabled_tasks = [task for task in self.tasks if not task.disabled]
        if not enabled_tasks:
            self.done.emit(False, "没有可执行的提取任务。")
            return

        self._started_ts = time.time()
        total_apis = len(enabled_tasks)
        self.all_progress.emit(0, total_apis, "")
        self._emit_speed(0, total_apis)

        try:
            for index, task in enumerate(enabled_tasks, start=1):
                self.log.emit(f"开始 {task.title} 信息提取")
                self._extract_single(task, index - 1, total_apis)
                self.all_progress.emit(index, total_apis, task.title)
                self._emit_speed(index, total_apis)
            self.done.emit(True, f"提取完成，共处理 {total_apis} 个接口")
        except Exception as exc:
            self.done.emit(False, f"提取失败: {exc}")
