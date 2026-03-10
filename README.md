# stock_car v2

这是一个基于 `Streamlit + FastAPI` 的新能源车股票分析系统。

`v1` 是单体式 Streamlit 架构；`v2` 在不修改原有 UI 排版和核心功能的前提下，完成了前后端解耦。

## 1. 环境准备

建议使用 Python `3.10.x`。

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. 配置密钥

先复制示例配置文件：

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

然后在 `.streamlit/secrets.toml` 中填写你自己的：

- `DEEPSEEK_API_KEY`
- `BACKEND_BASE_URL`（默认可保持 `http://127.0.0.1:8000`）

如果不配置有效的 `DEEPSEEK_API_KEY`，页面可以启动，但 AI 对话功能会失败。

## 3. 启动方式

### 方式一：分别启动前后端

后端：

```powershell
.\.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

### 方式二：使用统一启动脚本

```powershell
.\run_v2.ps1
```

说明：

- `v2` 采用前后端分离架构，因此运行时本质上仍然是两个进程。
- `run_v2.ps1` 只是把“先启动后端，再启动前端”的动作自动化。

## 4. v2 主要变化

- 引入 `FastAPI`，将数据获取、预测、认证和 AI 调用迁移到独立后端。
- 前端通过 `frontend/services/api_client.py` 统一访问后端接口。
- 保持原有 `Streamlit` UI 排版和核心功能不变。
- 增加 `API_REFERENCE.md` 作为接口文档。
- 增加 `run_v2.ps1` 作为统一启动脚本。

## 5. 本地运行时文件

以下文件或目录通常不应提交到 Git：

- `.venv/`
- `__pycache__/`
- `.streamlit/`
- `*.db`

其中 `stock_data.db` 会在首次运行时自动创建。

## 6. 版本说明

- `v1.0`：初始 Streamlit 单体版本
- `v2.0`：完成前后端解耦的版本

