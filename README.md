# iSecueFucker

iSecueFucker 是一个面向 **海康威视教育综合安防管理平台 iSecure Center** 的 API 测试工具，目标是把 AK/SK 鉴权调试流程做成可视化、可复用、可持续迭代的工程化项目。好用的话给个star吧🙏~ 🥺

## 项目定位

- 聚焦对象：iSecure Center（教育综合安防场景）
- 核心方向：AK/SK 接口测试、签名调试、文档联动
- 使用方式：桌面图形化工具（Python + PySide6）

> 项目说明：截至 2026-03，基于公开代码托管平台与常见技术社区检索，本项目定位为当前少见且垂直聚焦 iSecure Center 的开源测试项目之一。

## 核心优点

- 专用性强：围绕 iSecure Center API 真实调试链路设计，不是通用 HTTP 客户端拼装。
- 调试效率高：签名生成、发包、回包、文档核对在一个界面内完成。
- 定位问题快：支持签名相关调试信息展示，便于快速定位鉴权失败原因。
- 文档联动好：内置 API 文档可视化浏览，并支持一键填充到接口测试页。
- 本地配置自动保存：常用参数可复用，减少重复输入。

## 当前可用功能

- AK/SK 签名请求（支持 `GET/POST/PUT/DELETE`）
- 协议切换（`https/http`）
- 自动补全 `/artemis` 前缀
- 请求参数 JSON 输入与自动美化
- 额外请求头设置
- 证书校验开关与证书文件选择
- 响应结果 / 调试信息分栏展示
- API 文档浏览与一键填充

## 开发中功能

- `信息提取` 模块仍在修复与重构中

## 目录结构

```text
iSecureFucker/
├─ isecure_tool/                   # 主程序
├─ doc/                            # API文档数据
├─ main.py                         # 程序入口
├─ requirements.txt                # 依赖列表
└─ isecure_tool_config.example.ini # 示例配置
```

## 快速开始

```bash
pip install -r requirements.txt
python main.py
```

或：

```bash
python -m isecure_tool
```

## 打包 EXE（可选）

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name iSecueFucker --collect-all PySide6 main.py
```

如果遇到 Qt 插件缺失，建议先用 `--onedir` 定位问题后再切换回 `--onefile`。

## 配置与敏感信息

- 运行时配置文件：`isecure_tool_config.ini`（程序启动后自动生成）
- 仓库仅保留示例：`isecure_tool_config.example.ini`


## 下一步开发计划

1. 重构“信息提取”模块（稳定性、异常恢复、长任务中断重试）。
2. 增加任务队列与并发控制（提升批量接口采集效率）。
3. 增加导出能力（多 Sheet、字段映射、去重与增量更新）。
4. 增加多环境配置管理（多地址/多凭据切换）。
5. 增加预置模板（面向教育安防典型场景）。
6. 增加日志与审计能力（便于团队协作和复盘）。

## 合规声明

本项目仅用于 **授权环境下的接口联调、测试与研究**。严禁用于任何未授权目标。
