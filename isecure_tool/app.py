from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .client import ResponseData, send_request
from .utils import parse_json_text
from .config import DEFAULT_CONFIG, load_config, save_config
from .extractor import CATEGORY_ORDER, ExtractAPI, ExtractionWorker, load_extract_apis


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("iSecueFucker - iSecure Center AK/SK 利用工具")
        self.resize(1080, 760)
        self._config: Dict[str, Any] = load_config()
        self._doc_entries: list[dict[str, Any]] = []
        self._extract_apis: list[ExtractAPI] = []
        self._extract_worker: ExtractionWorker | None = None
        self._extract_under_development = True

        self._build_ui()
        self._apply_config()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_test_tab(), "接口测试")
        self.tabs.addTab(self._build_extract_tab(), "信息提取(开发中)")
        self.tabs.addTab(self._build_docs_tab(), "API 文档")
        self.tabs.addTab(self._build_reserved_tab(), "其他功能(预留)")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        root_layout.addWidget(self.tabs, 1)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")

        self.setCentralWidget(root)
        self._apply_styles()

    def _row(self, *widgets: QWidget) -> QWidget:
        box = QWidget()
        layout = QHBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch(1)
        return box

    def _build_test_tab(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        base_group = QGroupBox("基础配置")
        base_form = QGridLayout(base_group)
        base_form.setHorizontalSpacing(10)
        base_form.setVerticalSpacing(8)
        base_form.setColumnStretch(1, 1)
        base_form.setColumnStretch(3, 1)

        self.app_key_edit = QLineEdit()
        self.app_key_edit.setPlaceholderText("AppKey")
        self.app_key_edit.setMinimumWidth(180)
        self.app_key_edit.setMaximumWidth(260)
        self.app_secret_edit = QLineEdit()
        self.app_secret_edit.setEchoMode(QLineEdit.Password)
        self.app_secret_edit.setPlaceholderText("AppSecret")
        self.app_secret_edit.setMinimumWidth(360)
        self.show_secret_check = QCheckBox("显示")
        self.show_secret_check.stateChanged.connect(self._toggle_secret)

        base_form.addWidget(QLabel("AppKey"), 0, 0)
        base_form.addWidget(self.app_key_edit, 0, 1)
        base_form.addWidget(QLabel("AppSecret"), 0, 2)
        base_form.addWidget(self._row(self.app_secret_edit, self.show_secret_check), 0, 3)

        self.scheme_combo = QComboBox()
        self.scheme_combo.addItems(["https", "http"])
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE"])
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("10.112.1.8:443")
        base_form.addWidget(QLabel("协议/方法"), 1, 0)
        base_form.addWidget(self._row(self.scheme_combo, self.method_combo), 1, 1)
        base_form.addWidget(QLabel("平台地址"), 1, 2)
        base_form.addWidget(self.host_edit, 1, 3)

        self.api_path_edit = QLineEdit()
        self.api_path_edit.setPlaceholderText("/api/resource/v1/org/advance/orgList")
        self.auto_artemis_check = QCheckBox("自动补 /artemis")
        self.auto_artemis_check.setToolTip("开启后，如果请求 URL 不以 /artemis 开头，将自动补全。")
        base_form.addWidget(QLabel("请求 URL"), 2, 0)
        base_form.addWidget(self.api_path_edit, 2, 1)
        base_form.addWidget(QLabel("Artemis"), 2, 2)
        base_form.addWidget(self.auto_artemis_check, 2, 3)

        self.accept_edit = QLineEdit()
        self.accept_edit.setPlaceholderText("*/*")
        self.content_type_edit = QLineEdit()
        self.content_type_edit.setPlaceholderText("application/json")
        base_form.addWidget(QLabel("Accept"), 3, 0)
        base_form.addWidget(self.accept_edit, 3, 1)
        base_form.addWidget(QLabel("Content-Type"), 3, 2)
        base_form.addWidget(self.content_type_edit, 3, 3)

        self.verify_ssl_check = QCheckBox("校验证书")
        self.verify_ssl_check.stateChanged.connect(self._toggle_ca_widgets)
        self.ca_path_edit = QLineEdit()
        self.ca_path_edit.setPlaceholderText("CA 证书路径(可选)")
        self.ca_path_edit.setReadOnly(True)
        self.ca_path_button = QPushButton("选择证书")
        self.ca_path_button.setObjectName("certPicker")
        self.ca_path_button.clicked.connect(self._choose_ca)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 120)
        self.timeout_spin.setSuffix(" 秒")
        base_form.addWidget(QLabel("证书"), 4, 0)
        base_form.addWidget(self._row(self.verify_ssl_check, self.ca_path_edit, self.ca_path_button), 4, 1)
        base_form.addWidget(QLabel("超时"), 4, 2)
        base_form.addWidget(self.timeout_spin, 4, 3)

        self.sign_headers_edit = QLineEdit()
        self.sign_headers_edit.setPlaceholderText("x-ca-key,x-ca-timestamp,x-ca-nonce")
        base_form.addWidget(QLabel("签名头部"), 5, 0)
        base_form.addWidget(self.sign_headers_edit, 5, 1, 1, 3)

        self.headers_edit = QPlainTextEdit()
        self.headers_edit.setPlaceholderText('{"X-Ca-Stage": "RELEASE"}')
        self.headers_edit.setMinimumHeight(80)
        base_form.addWidget(QLabel("额外请求头 JSON"), 6, 0)
        base_form.addWidget(self.headers_edit, 6, 1, 1, 3)

        layout.addWidget(base_group)

        button_row = QHBoxLayout()
        self.send_button = QPushButton("发送请求")
        self.send_button.clicked.connect(self._on_send)
        self.clear_button = QPushButton("清空结果")
        self.clear_button.clicked.connect(self._clear_result)
        button_row.addWidget(self.send_button)
        button_row.addWidget(self.clear_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        params_group = QGroupBox("请求参数")
        params_layout = QVBoxLayout(params_group)
        self.params_edit = QPlainTextEdit()
        self.params_edit.setPlaceholderText('{\n  "pageNo": 1,\n  "pageSize": 100\n}')
        self.params_edit.setMinimumHeight(220)
        params_layout.addWidget(self.params_edit)

        options_row = QHBoxLayout()
        self.convert_time_check = QCheckBox("时间戳转 ISO8601")
        self.use_date_check = QCheckBox("使用 Date 头")
        self.show_signing_check = QCheckBox("显示签名字符串")
        self.body_form_check = QCheckBox("表单提交")
        self.auto_pretty_check = QCheckBox("自动美化参数")
        options_row.addWidget(self.convert_time_check)
        options_row.addWidget(self.use_date_check)
        options_row.addWidget(self.show_signing_check)
        options_row.addWidget(self.body_form_check)
        options_row.addWidget(self.auto_pretty_check)
        options_row.addStretch(1)
        params_layout.addLayout(options_row)

        layout.addWidget(params_group)

        preview_group = QGroupBox("请求预览")
        preview_form = QFormLayout(preview_group)
        self.full_url_edit = QLineEdit()
        self.full_url_edit.setReadOnly(True)
        preview_form.addRow("完整 URL", self.full_url_edit)
        layout.addWidget(preview_group)

        response_group = QGroupBox("返回结果")
        response_layout = QVBoxLayout(response_group)
        response_layout.setContentsMargins(10, 14, 10, 10)
        self.response_tabs = QTabWidget()
        self.response_view = QPlainTextEdit()
        self.response_view.setReadOnly(True)
        self.response_view.setMinimumHeight(320)
        self.debug_view = QPlainTextEdit()
        self.debug_view.setReadOnly(True)
        self.debug_view.setMinimumHeight(320)
        self.response_tabs.addTab(self.response_view, "响应")
        self.response_tabs.addTab(self.debug_view, "调试")
        response_layout.addWidget(self.response_tabs)
        layout.addWidget(response_group)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def _build_extract_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        notice = QLabel("信息提取模块开发中，当前版本暂不开放。")
        notice.setObjectName("devNotice")
        notice.setWordWrap(True)
        layout.addWidget(notice)

        config_group = QGroupBox("提取配置")
        cfg_grid = QGridLayout(config_group)
        cfg_grid.setHorizontalSpacing(10)
        cfg_grid.setVerticalSpacing(8)
        cfg_grid.setColumnStretch(1, 1)
        cfg_grid.setColumnStretch(3, 1)

        self.extract_app_key_edit = QLineEdit()
        self.extract_app_key_edit.setPlaceholderText("AppKey")
        self.extract_app_secret_edit = QLineEdit()
        self.extract_app_secret_edit.setEchoMode(QLineEdit.Password)
        self.extract_app_secret_edit.setPlaceholderText("AppSecret")
        self.extract_show_secret_check = QCheckBox("显示")
        self.extract_show_secret_check.stateChanged.connect(self._toggle_extract_secret)
        cfg_grid.addWidget(QLabel("AppKey"), 0, 0)
        cfg_grid.addWidget(self.extract_app_key_edit, 0, 1)
        cfg_grid.addWidget(QLabel("AppSecret"), 0, 2)
        cfg_grid.addWidget(self._row(self.extract_app_secret_edit, self.extract_show_secret_check), 0, 3)

        self.extract_scheme_combo = QComboBox()
        self.extract_scheme_combo.addItems(["https", "http"])
        self.extract_method_combo = QComboBox()
        self.extract_method_combo.addItems(["AUTO", "POST", "GET", "PUT", "DELETE"])
        self.extract_host_edit = QLineEdit()
        self.extract_host_edit.setPlaceholderText("10.112.1.8:443")
        cfg_grid.addWidget(QLabel("协议/方法"), 1, 0)
        cfg_grid.addWidget(self._row(self.extract_scheme_combo, self.extract_method_combo), 1, 1)
        cfg_grid.addWidget(QLabel("平台地址"), 1, 2)
        cfg_grid.addWidget(self.extract_host_edit, 1, 3)

        sync_row = QHBoxLayout()
        self.extract_sync_test_btn = QPushButton("从接口测试页读取")
        self.extract_sync_test_btn.clicked.connect(self._sync_extract_from_test_tab)
        self.extract_sync_cfg_btn = QPushButton("从配置文件读取")
        self.extract_sync_cfg_btn.clicked.connect(self._sync_extract_from_file_config)
        self.extract_run_all_btn = QPushButton("一键提取")
        self.extract_run_all_btn.setObjectName("extractAll")
        self.extract_run_all_btn.clicked.connect(self._run_extract_all)
        sync_row.addWidget(self.extract_sync_test_btn)
        sync_row.addWidget(self.extract_sync_cfg_btn)
        sync_row.addStretch(1)
        sync_row.addWidget(self.extract_run_all_btn)
        cfg_grid.addLayout(sync_row, 2, 0, 1, 4)
        layout.addWidget(config_group)

        api_group = QGroupBox("接口按钮")
        api_layout = QVBoxLayout(api_group)
        self.extract_buttons_wrap = QWidget()
        self.extract_buttons_layout = QVBoxLayout(self.extract_buttons_wrap)
        self.extract_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.extract_buttons_layout.setSpacing(8)
        api_layout.addWidget(self.extract_buttons_wrap)
        layout.addWidget(api_group)

        progress_group = QGroupBox("提取进度")
        progress_layout = QVBoxLayout(progress_group)
        self.extract_current_label = QLabel("当前接口: -")
        self.extract_current_progress = QProgressBar()
        self.extract_current_progress.setRange(0, 100)
        self.extract_current_progress.setValue(0)
        self.extract_all_progress = QProgressBar()
        self.extract_all_progress.setRange(0, 100)
        self.extract_all_progress.setValue(0)
        self.extract_speed_label = QLabel("速度: - | 预计剩余: -")
        progress_layout.addWidget(self.extract_current_label)
        progress_layout.addWidget(self.extract_current_progress)
        progress_layout.addWidget(QLabel("总进度"))
        progress_layout.addWidget(self.extract_all_progress)
        progress_layout.addWidget(self.extract_speed_label)
        layout.addWidget(progress_group)

        log_group = QGroupBox("实时日志")
        log_layout = QVBoxLayout(log_group)
        self.extract_log_edit = QPlainTextEdit()
        self.extract_log_edit.setReadOnly(True)
        self.extract_log_edit.setMinimumHeight(220)
        log_layout.addWidget(self.extract_log_edit)
        layout.addWidget(log_group, 1)

        self._load_extract_api_buttons()
        self._apply_extract_dev_mode()
        return container

    def _apply_extract_dev_mode(self) -> None:
        self.extract_log_edit.setPlainText(
            "【开发中】信息提取模块已临时禁用。\n"
            "该页当前仅保留界面占位，后续修复稳定后再开放。"
        )
        disabled_widgets: list[QWidget] = [
            self.extract_sync_test_btn,
            self.extract_sync_cfg_btn,
            self.extract_run_all_btn,
            self.extract_show_secret_check,
            self.extract_app_key_edit,
            self.extract_app_secret_edit,
            self.extract_scheme_combo,
            self.extract_method_combo,
            self.extract_host_edit,
            self.extract_buttons_wrap,
            self.extract_current_progress,
            self.extract_all_progress,
            self.extract_log_edit,
        ]
        for widget in disabled_widgets:
            widget.setEnabled(False)
        self.extract_current_label.setText("当前接口: 开发中")
        self.extract_speed_label.setText("速度: 开发中 | 预计剩余: 开发中")

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def _load_extract_api_buttons(self) -> None:
        self._extract_apis = load_extract_apis(self._project_root())
        while self.extract_buttons_layout.count():
            item = self.extract_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        grouped: dict[str, list[ExtractAPI]] = {name: [] for name in CATEGORY_ORDER}
        for api in self._extract_apis:
            grouped.setdefault(api.category, []).append(api)

        for category in CATEGORY_ORDER:
            entries = grouped.get(category, [])
            if not entries:
                continue
            block = QGroupBox(category)
            grid = QGridLayout(block)
            grid.setHorizontalSpacing(8)
            grid.setVerticalSpacing(6)
            col = 0
            row = 0
            for api in entries:
                text = api.title
                button = QPushButton(text)
                if api.disabled:
                    button.setText(f"{text} (跳过)")
                    button.setEnabled(False)
                else:
                    button.clicked.connect(lambda _=False, item=api: self._run_extract_single(item))
                grid.addWidget(button, row, col)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            self.extract_buttons_layout.addWidget(block)
        self.extract_buttons_layout.addStretch(1)

    def _toggle_extract_secret(self) -> None:
        self.extract_app_secret_edit.setEchoMode(
            QLineEdit.Normal if self.extract_show_secret_check.isChecked() else QLineEdit.Password
        )

    def _sync_extract_from_test_tab(self) -> None:
        test_cfg = self._collect_config()
        self.extract_app_key_edit.setText(str(test_cfg.get("app_key", "")))
        self.extract_app_secret_edit.setText(str(test_cfg.get("app_secret", "")))
        self.extract_scheme_combo.setCurrentText(str(test_cfg.get("scheme", "https")))
        self.extract_method_combo.setCurrentText(str(test_cfg.get("method", "POST")).upper())
        self.extract_host_edit.setText(str(test_cfg.get("host", "")))
        self._append_extract_log("已从接口测试页读取基础配置")

    def _sync_extract_from_file_config(self) -> None:
        cfg = load_config()
        self.extract_app_key_edit.setText(str(cfg.get("app_key", "")))
        self.extract_app_secret_edit.setText(str(cfg.get("app_secret", "")))
        self.extract_scheme_combo.setCurrentText(str(cfg.get("scheme", "https")))
        self.extract_method_combo.setCurrentText(str(cfg.get("method", "POST")).upper())
        self.extract_host_edit.setText(str(cfg.get("host", "")))
        self._append_extract_log("已从配置文件读取基础配置")

    def _auto_fill_extract_if_empty(self) -> None:
        if (
            self.extract_app_key_edit.text().strip()
            and self.extract_app_secret_edit.text().strip()
            and self.extract_host_edit.text().strip()
        ):
            return
        cfg = self._collect_config()
        if not cfg.get("app_key") and not cfg.get("app_secret"):
            cfg = load_config()
        self.extract_app_key_edit.setText(str(cfg.get("app_key", "")))
        self.extract_app_secret_edit.setText(str(cfg.get("app_secret", "")))
        self.extract_scheme_combo.setCurrentText(str(cfg.get("scheme", "https")))
        self.extract_method_combo.setCurrentText(str(cfg.get("method", "POST")).upper())
        self.extract_host_edit.setText(str(cfg.get("host", "")))

    def _collect_extract_base_config(self) -> dict[str, Any]:
        test_cfg = self._collect_config()
        return {
            "app_key": self.extract_app_key_edit.text().strip(),
            "app_secret": self.extract_app_secret_edit.text().strip(),
            "scheme": self.extract_scheme_combo.currentText().strip(),
            "method_override": self.extract_method_combo.currentText().strip().upper() or "AUTO",
            "host": self.extract_host_edit.text().strip(),
            "headers_json": test_cfg.get("headers_json", "{}"),
            "sign_headers": test_cfg.get("sign_headers", ""),
            "accept": test_cfg.get("accept", "*/*"),
            "content_type": test_cfg.get("content_type", "application/json"),
            "use_date": test_cfg.get("use_date", False),
            "verify_ssl": test_cfg.get("verify_ssl", True),
            "ca_bundle": test_cfg.get("ca_bundle", ""),
            "timeout_sec": test_cfg.get("timeout_sec", 20),
        }

    def _set_extract_controls_enabled(self, enabled: bool) -> None:
        self.extract_run_all_btn.setEnabled(enabled)
        self.extract_sync_cfg_btn.setEnabled(enabled)
        self.extract_sync_test_btn.setEnabled(enabled)
        self.extract_show_secret_check.setEnabled(enabled)
        self.extract_app_key_edit.setEnabled(enabled)
        self.extract_app_secret_edit.setEnabled(enabled)
        self.extract_scheme_combo.setEnabled(enabled)
        self.extract_method_combo.setEnabled(enabled)
        self.extract_host_edit.setEnabled(enabled)
        self.extract_buttons_wrap.setEnabled(enabled)

    def _run_extract_single(self, api: ExtractAPI) -> None:
        self._start_extraction([api], f"开始 {api.title} 信息提取")

    def _run_extract_all(self) -> None:
        self._start_extraction(self._extract_apis, "开始一键提取")

    def _start_extraction(self, tasks: list[ExtractAPI], start_message: str) -> None:
        if self._extract_under_development:
            QMessageBox.information(self, "开发中", "信息提取模块开发中，当前版本暂不开放。")
            return
        if self._extract_worker is not None and self._extract_worker.isRunning():
            QMessageBox.warning(self, "任务进行中", "已有提取任务正在执行，请稍后。")
            return
        cfg = self._collect_extract_base_config()
        if not cfg["app_key"] or not cfg["app_secret"] or not cfg["host"]:
            QMessageBox.warning(self, "配置不完整", "请先填写 AppKey、AppSecret、平台地址。")
            return

        enabled_tasks = [item for item in tasks if not item.disabled]
        if not enabled_tasks:
            QMessageBox.warning(self, "无可执行接口", "当前任务列表没有可执行接口。")
            return

        output_dir = self._project_root() / "exports"
        self.extract_log_edit.clear()
        self.extract_current_label.setText("当前接口: -")
        self.extract_current_progress.setRange(0, 100)
        self.extract_current_progress.setValue(0)
        self.extract_all_progress.setRange(0, max(1, len(enabled_tasks)))
        self.extract_all_progress.setValue(0)
        self.extract_speed_label.setText("速度: - | 预计剩余: -")
        self._append_extract_log(start_message)

        self._extract_worker = ExtractionWorker(enabled_tasks, cfg, output_dir)
        self._extract_worker.log.connect(self._append_extract_log)
        self._extract_worker.api_progress.connect(self._on_extract_api_progress)
        self._extract_worker.all_progress.connect(self._on_extract_all_progress)
        self._extract_worker.speed_eta.connect(self.extract_speed_label.setText)
        self._extract_worker.api_saved.connect(self._on_extract_api_saved)
        self._extract_worker.done.connect(self._on_extract_done)
        self._set_extract_controls_enabled(False)
        self._extract_worker.start()

    def _append_extract_log(self, text: str) -> None:
        self.extract_log_edit.appendPlainText(text)

    def _on_extract_api_progress(self, current_page: int, total_pages: int, title: str) -> None:
        self.extract_current_label.setText(f"当前接口: {title}")
        if total_pages > 0:
            self.extract_current_progress.setRange(0, total_pages)
            self.extract_current_progress.setValue(min(current_page, total_pages))
        else:
            self.extract_current_progress.setRange(0, 0)
        self.status_bar.showMessage(f"{title}: 正在处理第 {current_page} 页")

    def _on_extract_all_progress(self, finished_count: int, total_count: int, title: str) -> None:
        self.extract_all_progress.setRange(0, max(1, total_count))
        self.extract_all_progress.setValue(finished_count)
        if title:
            self.status_bar.showMessage(f"{title} 完成，整体进度 {finished_count}/{total_count}")

    def _on_extract_api_saved(self, title: str, file_path: str, row_count: int) -> None:
        self._append_extract_log(f"{title}: 导出完成 -> {file_path}，共 {row_count} 条")

    def _on_extract_done(self, ok: bool, message: str) -> None:
        self._set_extract_controls_enabled(True)
        self.extract_current_progress.setRange(0, 100)
        self.extract_current_progress.setValue(100 if ok else 0)
        self.status_bar.showMessage(message, 6000)
        self._append_extract_log(message)
        if not ok:
            QMessageBox.warning(self, "提取失败", message)
        self._extract_worker = None

    def _on_tab_changed(self, index: int) -> None:
        if self.tabs.tabText(index).startswith("信息提取"):
            self._auto_fill_extract_if_empty()

    def _build_reserved_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        info = QLabel(
            "以下功能为预留占位：\n"
            "• Key 泄露扫描与批量测试\n"
            "• API 列表浏览与收藏\n"
            "• 认证/会话管理\n"
            "• 常见利用链模板\n"
            "• 批量资产测试与导出"
        )
        info.setObjectName("reserved")
        info.setWordWrap(True)

        layout.addWidget(info)
        layout.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        return scroll

    def _build_docs_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        search_row = QHBoxLayout()
        search_label = QLabel("搜索")
        self.doc_search_edit = QLineEdit()
        self.doc_search_edit.setPlaceholderText("接口名 / 路径 / 方法 / 文件名")
        self.doc_search_edit.textChanged.connect(self._filter_doc_tree)
        self.doc_apply_button = QPushButton("填充到接口测试")
        self.doc_apply_button.setEnabled(False)
        self.doc_apply_button.clicked.connect(self._apply_doc_to_test_tab)
        search_row.addWidget(search_label)
        search_row.addWidget(self.doc_search_edit, 1)
        search_row.addWidget(self.doc_apply_button)
        layout.addLayout(search_row)

        splitter = QSplitter(Qt.Horizontal)
        self.doc_tree = QTreeWidget()
        self.doc_tree.setHeaderHidden(True)
        self.doc_tree.itemSelectionChanged.connect(self._on_doc_selected)
        self.doc_view = QTextBrowser()
        self.doc_view.setOpenExternalLinks(True)
        splitter.addWidget(self.doc_tree)
        splitter.addWidget(self.doc_view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, 1)

        self._load_docs_index()
        return container

    def _docs_base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent / "doc"

    def _load_docs_index(self) -> None:
        self.doc_tree.clear()
        base_dir = self._docs_base_dir()
        index_path = base_dir / "index.json"
        if not index_path.exists():
            self.doc_view.setPlainText("未找到 API 文档索引文件：doc/index.json")
            return
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.doc_view.setPlainText(f"读取 index.json 失败: {exc}")
            return
        if not isinstance(data, list):
            self.doc_view.setPlainText("index.json 格式不正确。")
            return

        self._doc_entries = data
        node_map: dict[str, QTreeWidgetItem] = {}
        for entry in data:
            rel_path = Path(str(entry.get("doc_path", "")))
            if not rel_path.parts:
                continue
            parent = self.doc_tree.invisibleRootItem()
            current_path = ""
            for part in rel_path.parts[:-1]:
                current_path = f"{current_path}/{part}" if current_path else part
                if current_path not in node_map:
                    item = QTreeWidgetItem([part])
                    parent.addChild(item)
                    node_map[current_path] = item
                parent = node_map[current_path]

            title = str(entry.get("title", ""))
            method = str(entry.get("method", "")).strip()
            api_path = str(entry.get("path", "")).strip()
            label = title
            if method or api_path:
                label = f"{title} [{method}] {api_path}".strip()
            leaf = QTreeWidgetItem([label])
            leaf.setData(0, Qt.UserRole, entry)
            parent.addChild(leaf)

        self.doc_tree.expandToDepth(1)
        self._select_first_doc()

    def _select_first_doc(self) -> None:
        def walk(item: QTreeWidgetItem) -> QTreeWidgetItem | None:
            entry = item.data(0, Qt.UserRole)
            if entry:
                return item
            for i in range(item.childCount()):
                found = walk(item.child(i))
                if found is not None:
                    return found
            return None

        root = self.doc_tree.invisibleRootItem()
        for idx in range(root.childCount()):
            first = walk(root.child(idx))
            if first is not None:
                self.doc_tree.setCurrentItem(first)
                break

    def _on_doc_selected(self) -> None:
        items = self.doc_tree.selectedItems()
        if not items:
            self.doc_apply_button.setEnabled(False)
            return
        entry = items[0].data(0, Qt.UserRole)
        if not entry:
            self.doc_apply_button.setEnabled(False)
            return
        can_apply = (
            str(entry.get("doc_type", "")).lower() == "api"
            and (
                bool(str(entry.get("method", "")).strip())
                or bool(str(entry.get("path", "")).strip())
                or bool(str(entry.get("request_example", "")).strip())
            )
        )
        self.doc_apply_button.setEnabled(can_apply)
        base_dir = self._docs_base_dir()
        doc_path = base_dir / str(entry.get("doc_path", ""))
        if not doc_path.exists():
            self.doc_view.setPlainText("文档文件不存在。")
            return
        try:
            content = doc_path.read_text(encoding="utf-8")
        except Exception as exc:
            self.doc_view.setPlainText(f"读取文档失败: {exc}")
            return
        self._render_doc(entry, content)

    def _extract_body_html(self, html_text: str) -> str:
        lower_text = html_text.lower()
        body_start = lower_text.find("<body")
        if body_start < 0:
            return html_text
        open_end = html_text.find(">", body_start)
        if open_end < 0:
            return html_text
        body_end = lower_text.rfind("</body>")
        if body_end < 0:
            body_end = len(html_text)
        return html_text[open_end + 1 : body_end]

    def _render_doc(self, entry: dict[str, Any], markdown_text: str) -> None:
        markdown_text = self._normalize_doc_markdown(markdown_text)
        title = html.escape(str(entry.get("title", "")))
        method = str(entry.get("method", "")).upper().strip()
        method_text = html.escape(method or "-")
        api_path = html.escape(str(entry.get("path", "")).strip() or "-")
        source_path = html.escape(str(entry.get("source_path", "")).strip() or "-")
        doc_type = html.escape(str(entry.get("doc_type", "")).strip() or "general")

        md_doc = QTextDocument()
        md_doc.setMarkdown(markdown_text)
        body_html = self._extract_body_html(md_doc.toHtml())

        method_badge_class = method.lower() if method in {"GET", "POST", "PUT", "DELETE"} else "any"
        rendered = f"""
<html>
<head>
<meta charset="utf-8" />
<style>
body {{
    margin: 0;
    background: #f8fafc;
    color: #1f2933;
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
}}
.doc-shell {{
    max-width: 1160px;
    margin: 0 auto;
    padding: 14px 16px 22px 16px;
}}
.doc-hero {{
    background: linear-gradient(125deg, #0f4c81 0%, #1f7a8c 100%);
    color: #f4f8fb;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 14px;
    box-shadow: 0 8px 22px rgba(15, 76, 129, 0.25);
}}
.doc-title {{
    font-size: 18px;
    font-weight: 700;
    margin: 0 0 8px 0;
}}
.doc-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    font-size: 12px;
}}
.badge {{
    border-radius: 999px;
    padding: 3px 10px;
    font-weight: 700;
    letter-spacing: 0.2px;
}}
.badge-get {{ background: #d1fae5; color: #065f46; }}
.badge-post {{ background: #dbeafe; color: #1e40af; }}
.badge-put {{ background: #ede9fe; color: #5b21b6; }}
.badge-delete {{ background: #fee2e2; color: #991b1b; }}
.badge-any {{ background: #e4e7eb; color: #334e68; }}
.meta-chip {{
    border-radius: 999px;
    padding: 3px 10px;
    background: rgba(255, 255, 255, 0.15);
    color: #e6f0f6;
}}
.doc-content {{
    background: #ffffff;
    border: 1px solid #d9e2ec;
    border-radius: 10px;
    padding: 14px 16px;
}}
.doc-content h1 {{
    font-size: 24px;
    margin: 4px 0 12px 0;
    color: #102a43;
    border-left: 5px solid #1f7a8c;
    padding-left: 10px;
}}
.doc-content h2 {{
    font-size: 18px;
    margin: 18px 0 8px 0;
    color: #1f2933;
}}
.doc-content h3 {{
    font-size: 15px;
    margin: 14px 0 6px 0;
    color: #334e68;
}}
.doc-content p, .doc-content li {{
    font-size: 13px;
    line-height: 1.65;
}}
.doc-content blockquote {{
    margin: 10px 0;
    padding: 8px 12px;
    border-left: 4px solid #1f7a8c;
    background: #f0f8ff;
    color: #1f2933;
}}
.doc-content table {{
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    margin: 10px 0 14px 0;
    font-size: 12px;
}}
.doc-content th {{
    background: #eef5fb;
    color: #243b53;
    font-weight: 700;
}}
.doc-content th, .doc-content td {{
    border: 1px solid #d9e2ec;
    padding: 7px 8px;
    text-align: left;
    vertical-align: top;
    overflow-wrap: anywhere;
    word-break: break-word;
}}
.doc-content code {{
    background: #eef2f7;
    color: #243b53;
    border-radius: 4px;
    padding: 1px 4px;
    font-size: 12px;
    overflow-wrap: anywhere;
    word-break: break-word;
}}
.doc-content pre {{
    background: #0f172a;
    color: #d6e3f0;
    border-radius: 8px;
    padding: 12px;
    border: 1px solid #29394a;
    overflow-wrap: anywhere;
    word-break: break-word;
    white-space: pre-wrap;
}}
.doc-content pre code {{
    background: transparent;
    color: inherit;
    padding: 0;
}}
.doc-content hr {{
    border: none;
    border-top: 1px solid #d9e2ec;
    margin: 18px 0;
}}
</style>
</head>
<body>
<div class="doc-shell">
    <div class="doc-hero">
        <div class="doc-title">{title}</div>
        <div class="doc-meta">
            <span class="badge badge-{method_badge_class}">{method_text}</span>
            <span class="meta-chip">Path: {api_path}</span>
            <span class="meta-chip">Type: {doc_type}</span>
            <span class="meta-chip">Source: {source_path}</span>
        </div>
    </div>
    <div class="doc-content">{body_html}</div>
</div>
</body>
</html>
"""
        self.doc_view.setHtml(rendered)

    def _normalize_doc_markdown(self, markdown_text: str) -> str:
        lines = markdown_text.splitlines()
        normalized: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped in {"## 注释", "## 备注"}:
                normalized.append("### 说明")
                continue
            normalized.append(line)
        return "\n".join(normalized)

    def _apply_doc_to_test_tab(self) -> None:
        items = self.doc_tree.selectedItems()
        if not items:
            return
        entry = items[0].data(0, Qt.UserRole)
        if not entry:
            return
        if str(entry.get("doc_type", "")).lower() != "api":
            self.status_bar.showMessage("当前文档不是接口条目，无法自动填充。", 4000)
            return

        method = str(entry.get("method", "")).upper().strip()
        api_path = str(entry.get("path", "")).strip()
        request_example = str(entry.get("request_example", "")).strip()

        if method:
            self.method_combo.setCurrentText(method)
        if api_path:
            self.api_path_edit.setText(api_path)
        if request_example:
            self.params_edit.setPlainText(request_example)

        self.tabs.setCurrentIndex(0)
        self.status_bar.showMessage("已将文档接口信息填充到接口测试页", 5000)

    def _filter_doc_tree(self, text: str) -> None:
        keyword = text.strip().lower()

        def match_item(item: QTreeWidgetItem) -> bool:
            entry = item.data(0, Qt.UserRole)
            if entry:
                hay = " ".join(
                    [
                        str(entry.get("title", "")),
                        str(entry.get("path", "")),
                        str(entry.get("method", "")),
                        str(entry.get("source_path", "")),
                    ]
                ).lower()
                visible = not keyword or keyword in hay
                item.setHidden(not visible)
                return visible
            visible_any = False
            for idx in range(item.childCount()):
                if match_item(item.child(idx)):
                    visible_any = True
            item.setHidden(not visible_any and bool(keyword))
            return visible_any

        root = self.doc_tree.invisibleRootItem()
        for idx in range(root.childCount()):
            match_item(root.child(idx))

    def _apply_styles(self) -> None:
        font = QFont("Microsoft YaHei UI", 10)
        self.setFont(font)
        self.setStyleSheet(
            """
            QMainWindow { background-color: #f7f5f2; }
            QLabel#reserved { color: #334e68; font-size: 14px; }
            QGroupBox { border: 1px solid #d9e2ec; border-radius: 8px; margin-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {
                border: 1px solid #cbd2d9; border-radius: 6px; padding: 5px; background: #ffffff;
            }
            QPushButton {
                background: #2f3c4f; color: #ffffff; border-radius: 6px; padding: 8px 16px;
            }
            QPushButton:hover { background: #3f4e63; }
            QPushButton:pressed { background: #253041; }
            QPushButton:disabled {
                background: #e7edf4; color: #95a4b8; border: 1px dashed #c1ccd9;
            }
            QPushButton#extractAll {
                background: #0f766e;
                color: #ffffff;
                font-weight: 600;
            }
            QPushButton#extractAll:hover { background: #0d9488; }
            QPushButton#extractAll:pressed { background: #115e59; }
            QPushButton#certPicker:disabled {
                background: #edf2f7;
                color: #9aa7b8;
                border: 1px solid #cfd8e3;
            }
            QLabel#devNotice {
                color: #7c2d12;
                background: #ffedd5;
                border: 1px solid #fdba74;
                border-radius: 6px;
                padding: 8px 10px;
                font-weight: 600;
            }
            QTabWidget::pane { border: 1px solid #d9e2ec; border-radius: 8px; }
            QTabBar::tab { background: #e3e7ed; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border: 1px solid #d9e2ec; border-bottom: none; }
            QTreeWidget {
                border: 1px solid #d9e2ec; border-radius: 6px; background: #ffffff; padding: 4px;
            }
            QTreeWidget::item { padding: 4px 2px; }
            QTreeWidget::item:selected { background: #dceefb; color: #102a43; }
            QTextBrowser {
                border: 1px solid #d9e2ec; border-radius: 6px; background: #ffffff;
                padding: 12px; selection-background-color: #dceefb;
            }
            """
        )

    def _apply_config(self) -> None:
        cfg = {**DEFAULT_CONFIG, **self._config}
        self.app_key_edit.setText(str(cfg.get("app_key", "")))
        self.app_secret_edit.setText(str(cfg.get("app_secret", "")))
        self.scheme_combo.setCurrentText(str(cfg.get("scheme", "https")))
        self.method_combo.setCurrentText(str(cfg.get("method", "POST")).upper())
        self.host_edit.setText(str(cfg.get("host", "")))
        self.api_path_edit.setText(str(cfg.get("api_path", "")))
        self.auto_artemis_check.setChecked(bool(cfg.get("auto_artemis", True)))
        params_text = str(cfg.get("params_json", "")).strip()
        if not params_text or params_text == "{}":
            params_text = str(DEFAULT_CONFIG.get("params_json", "{}"))
        self.params_edit.setPlainText(params_text)
        self.headers_edit.setPlainText(str(cfg.get("headers_json", "")))
        self.sign_headers_edit.setText(str(cfg.get("sign_headers", "")))
        self.accept_edit.setText(str(cfg.get("accept", "")))
        self.content_type_edit.setText(str(cfg.get("content_type", "")))
        self.use_date_check.setChecked(bool(cfg.get("use_date")))
        self.verify_ssl_check.setChecked(bool(cfg.get("verify_ssl", True)))
        self.ca_path_edit.setText(str(cfg.get("ca_bundle", "")))
        self.timeout_spin.setValue(int(cfg.get("timeout_sec", 20)))
        self.convert_time_check.setChecked(bool(cfg.get("convert_time")))
        self.show_signing_check.setChecked(bool(cfg.get("show_signing")))
        self.body_form_check.setChecked(bool(cfg.get("body_form")))
        self.auto_pretty_check.setChecked(bool(cfg.get("auto_pretty_params", True)))
        self._toggle_ca_widgets()
        self._auto_fill_extract_if_empty()

    def _collect_config(self) -> Dict[str, Any]:
        return {
            "app_key": self.app_key_edit.text().strip(),
            "app_secret": self.app_secret_edit.text().strip(),
            "scheme": self.scheme_combo.currentText(),
            "method": self.method_combo.currentText(),
            "host": self.host_edit.text().strip(),
            "api_path": self.api_path_edit.text().strip(),
            "auto_artemis": self.auto_artemis_check.isChecked(),
            "params_json": self.params_edit.toPlainText().strip(),
            "headers_json": self.headers_edit.toPlainText().strip(),
            "sign_headers": self.sign_headers_edit.text().strip(),
            "accept": self.accept_edit.text().strip(),
            "content_type": self.content_type_edit.text().strip(),
            "use_date": self.use_date_check.isChecked(),
            "verify_ssl": self.verify_ssl_check.isChecked(),
            "ca_bundle": self.ca_path_edit.text().strip(),
            "timeout_sec": self.timeout_spin.value(),
            "convert_time": self.convert_time_check.isChecked(),
            "show_signing": self.show_signing_check.isChecked(),
            "body_form": self.body_form_check.isChecked(),
            "auto_pretty_params": self.auto_pretty_check.isChecked(),
        }

    def _toggle_secret(self) -> None:
        self.app_secret_edit.setEchoMode(
            QLineEdit.Normal if self.show_secret_check.isChecked() else QLineEdit.Password
        )

    def _toggle_ca_widgets(self) -> None:
        enabled = self.verify_ssl_check.isChecked()
        self.ca_path_edit.setEnabled(enabled)
        self.ca_path_button.setEnabled(enabled)
        self.ca_path_button.setProperty("caDisabled", not enabled)
        self.ca_path_button.style().unpolish(self.ca_path_button)
        self.ca_path_button.style().polish(self.ca_path_button)

    def _choose_ca(self) -> None:
        start_dir = str(Path.cwd())
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择证书",
            start_dir,
            "证书文件 (*.crt *.pem *.cer *.der *.p12 *.pfx);;所有文件 (*.*)",
        )
        if file_path:
            self.ca_path_edit.setText(file_path)

    def _clear_result(self) -> None:
        self.response_view.clear()
        self.debug_view.clear()
        self.status_bar.showMessage("已清空结果", 3000)

    def _format_debug(self, data: ResponseData) -> str:
        if not data.debug:
            return ""
        sections = [
            "[URL]",
            data.debug.full_url,
            "",
            "[Canonical Resource]",
            data.debug.canonical_resource,
            "",
            "[String To Sign]",
            data.debug.string_to_sign,
            "",
            "[Request Headers]",
            json.dumps(data.debug.request_headers, ensure_ascii=False, indent=2),
            "",
            "[Request Body]",
            data.debug.request_body,
        ]
        return "\n".join(sections)

    def _pretty_params(self) -> None:
        ok, params_obj, err = parse_json_text(self.params_edit.toPlainText())
        if not ok:
            return
        if params_obj is None:
            self.params_edit.setPlainText("{}")
            return
        try:
            self.params_edit.setPlainText(json.dumps(params_obj, ensure_ascii=False, indent=2))
        except Exception:
            return

    def _format_response(self, data: ResponseData) -> str:
        if data.error and not data.response_text:
            return data.error
        warning = ""
        ctype = data.response_headers.get("Content-Type", "")
        if ctype and "text/html" in ctype.lower():
            warning = "提示：返回 HTML，可能请求地址不正确（如缺少 /artemis 前缀）。"
        elif data.response_text and "<html" in data.response_text.lower():
            warning = "提示：返回 HTML，可能请求地址不正确（如缺少 /artemis 前缀）。"
        summary = []
        if data.status_code is not None:
            summary.append(f"HTTP {data.status_code}")
        if data.elapsed_ms is not None:
            summary.append(f"耗时 {data.elapsed_ms:.1f} ms")
        summary_text = " | ".join(summary)
        parts = []
        if warning:
            parts.append(warning)
        if summary_text:
            parts.append(summary_text)
        if data.response_text:
            parts.append(data.response_text)
        return "\n\n".join(parts)

    def _on_send(self) -> None:
        cfg = self._collect_config()
        if self.auto_pretty_check.isChecked():
            self._pretty_params()
            cfg = self._collect_config()
        save_config(cfg)

        self.status_bar.showMessage("正在发送请求...")
        result = send_request(cfg)
        self.full_url_edit.setText(result.debug.full_url if result.debug else "")

        self.response_view.setPlainText(self._format_response(result))
        if self.show_signing_check.isChecked():
            self.debug_view.setPlainText(self._format_debug(result))
        else:
            self.debug_view.setPlainText("签名调试已隐藏，可勾选“显示签名字符串”查看。")

        if result.ok:
            self.status_bar.showMessage("请求完成", 5000)
        else:
            self.status_bar.showMessage("请求失败", 5000)
            if result.error:
                QMessageBox.warning(self, "请求失败", result.error)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._extract_worker is not None and self._extract_worker.isRunning():
            self._extract_worker.wait(800)
        save_config(self._collect_config())
        super().closeEvent(event)


def main() -> None:
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
