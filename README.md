# stock_car

新能源汽车股票分析系统，当前版本基于 `Streamlit + FastAPI + LangChain`。

## 项目概览

- `v1.0`：基于 Streamlit 的单体版本，完成股票分析、对比、预测、AI 问答等核心功能。
- `v2.0`：完成前后端分离，引入 FastAPI，前端通过 HTTP API 访问后端服务。
- `v3.1`：引入 LangChain Agent，让系统从普通对话升级为可调用工具的智能助手。
- `v3.2`：增加固定模板 PDF 报告导出能力。
- `v3.3`：让 Agent 读取页面上下文，支持基于当前选中股票生成和下载 PDF，并加入会话级临时缓存与后台预生成。

## 当前架构

- 前端：`Streamlit`
- 后端：`FastAPI`
- AI：`DeepSeek + LangChain Agent`
- 数据库：`SQLite`
- 图表：`Plotly`
- 报告：`ReportLab`

## 环境准备

建议使用 Python `3.10.x`。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 配置密钥

先复制配置模板：

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

然后在 `.streamlit/secrets.toml` 中配置：

- `DEEPSEEK_API_KEY`
- `BACKEND_BASE_URL`

默认后端地址可使用：

```toml
BACKEND_BASE_URL = "http://127.0.0.1:8000"
```

## 启动方式

后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## 当前主要能力

- 多股票对比分析
- K 线与收益率可视化
- Prophet 趋势预测
- 舆情与情绪分析
- LangChain Agent 智能问答
- 基于当前选中股票的 PDF 报告生成与下载

## 说明

- `.venv/`、`.streamlit/`、`__pycache__/`、`*.db` 等文件通常不应提交到 Git。
- `stock_data.db` 会在本地首次运行时自动创建。
- 当前版本仍使用 Streamlit 作为前端原型框架，后续计划升级为更适合产品化的前端技术栈。
