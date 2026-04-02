# stock_car v4.1

新能源车股票分析系统，当前版本基于 `React + TypeScript + Tailwind CSS + FastAPI + PostgreSQL + DeepSeek`。

项目支持股票基础数据查询、技术分析图表、新闻与舆情分析、未来趋势预测、Agent 问答，以及 PDF 研报导出。`v4.1` 在 `v4.0` 的基础上补齐了容器化部署链路，并修复了 Docker 环境下 Plotly 导出 PDF 图表时的中文字体与渲染问题。

## v4.1 更新内容

- 新增 `Docker Compose` 部署方案，统一编排 `frontend / backend / db`
- 引入 `Nginx` 作为前端静态资源与后端 API 的统一入口
- 支持通过 `cpolar` 暴露公网访问链路，便于演示与异地联调
- 后端 Docker 镜像补充 `Google Chrome + Noto CJK` 字体，修复 `kaleido` 在容器中的浏览器依赖问题
- 统一 Plotly PDF 导出字体配置，解决中文标题、图例、坐标轴在 PNG/PDF 中乱码或方块的问题
- 优化环境变量与目录组织，便于本地开发与容器部署保持一致

## v4.0 到 v4.1 的功能迭代

### v4.0

- 完成从 `Streamlit` 向 `React + FastAPI` 架构迁移
- 前后端分离，前端负责交互与展示，后端负责数据、AI 和 PDF 报告生成
- 引入 `PostgreSQL` 管理用户、访问记录和报告索引
- 实现 PDF 报告文件落盘与数据库索引双层缓存
- 集成 Agent 能力，支持围绕当前股票上下文进行问答与报告生成

### v4.1

- 增加容器化交付能力，补齐 `backend/Dockerfile`、`frontend/Dockerfile` 与 `docker-compose.yml`
- 增加 `Nginx` 反向代理，减少前后端联调时的跨域与入口配置成本
- 增加 `cpolar` 公网演示方案，方便在非局域网环境下访问系统
- 加强 Docker 运行时图表导出能力，确保 `Plotly + Kaleido + ReportLab` 在 Linux 容器中稳定工作

## 核心功能

- 用户注册、登录
- 股票名称查询与基础行情查询
- 技术分析图表展示
- 新闻与舆情信息分析
- 未来 7 天趋势预测
- Agent 智能问答
- PDF 研报生成、缓存命中与重复下载
- 用户历史访问记录管理

## 当前架构

- 前端：`frontend/`，基于 `React + TypeScript + Tailwind CSS + Plotly`
- 后端：`backend/`，基于 `FastAPI`
- 数据库：`PostgreSQL`
- 大模型：`DeepSeek`
- 图表导出：`Plotly + Kaleido`
- PDF 生成：`ReportLab`
- 报告缓存：`storage/reports/`

## Docker 部署说明

### 启动

在项目根目录准备 `.env` 后执行：

```powershell
docker compose up --build
```

默认服务职责：

- `db`：PostgreSQL
- `backend`：FastAPI 接口、Agent、PDF 报告生成
- `frontend`：Nginx 托管前端页面并反向代理后端接口

### Docker 图表导出说明

后端容器内已经补充以下能力：

- 安装 `google-chrome-stable`，解决 `Kaleido requires Google Chrome to be installed`
- 安装 `fonts-noto-cjk`，为 Plotly 导出的 PNG 图表提供可用中文字体
- 安装 `fontconfig` 并执行 `fc-cache -f -v`，确保容器内字体缓存可被 Chrome/Kaleido 正确识别
- 设置 `CHROME_BIN` 与 `BROWSER_PATH`，降低 Kaleido 在容器里找不到浏览器的概率

## 环境变量

建议使用项目根目录 `.env`：

```env
DEEPSEEK_API_KEY=your_key
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=stock_car
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/stock_car
VITE_API_BASE_URL=http://127.0.0.1:8000
```

说明：

- 后端优先读取 `DEEPSEEK_API_KEY`
- `docker-compose.yml` 中的 `DATABASE_URL` 指向容器内 `db` 服务
- 前端本地开发可单独改写 `VITE_API_BASE_URL`

## 目录结构

```text
stock_car/
├─ backend/                # FastAPI 后端
├─ frontend/               # React 前端
├─ storage/reports/        # PDF 报告缓存目录
├─ docker-compose.yml      # 多服务编排
├─ README.md
```

## PDF 缓存策略

- 报告文件落盘到 `storage/reports/`
- 文件名格式：`report_{stock_code}_{date_hash}.pdf`
- 数据库索引表：`ai_reports`
- 同一股票、同一区间、同一天内重复请求优先命中缓存
- 应用启动时自动清理超过 7 天的历史 PDF 与失效索引

## 已知说明

- PDF 中正文使用 `ReportLab` 的中文字体，图表文字使用 `Plotly + Chrome + Noto CJK`
- 当前仓库已收敛为 `React + FastAPI + PostgreSQL` 主线结构
- 若 Docker 首次构建较慢，通常是 Chrome 与 Python 依赖安装耗时导致
