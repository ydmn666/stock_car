# stock_car v4

新能源车股票分析系统，当前版本基于 `React + TypeScript + Tailwind + FastAPI + PostgreSQL + DeepSeek`。

## 当前版本概览

- 前端已从 `Streamlit` 迁移到 `Vite + React`
- 后端统一由 `FastAPI` 提供接口
- 用户登录、访问历史、股票历史数据、AI 报告索引统一入库
- 股票行情采用“本地优先 + 增量补全”的缓存策略
- PDF 报告采用“文件系统落盘 + PostgreSQL 索引”的双层缓存
- 通用 Agent 与四个专用功能页分离

## v4 核心能力

- 登录 / 注册
- 选股、历史记录、访问历史删除与清空
- 基础数据展示
- 技术分析与交互图表
- 未来 7 天趋势预测
- 新闻与舆情分析
- 通用 Agent 聊天
- PDF 报告生成、缓存命中、重复下载

## 当前架构

- 前端：`web/`，基于 `React + TypeScript + Tailwind + Plotly`
- 后端：`backend/`，基于 `FastAPI`
- 数据库：`PostgreSQL`
- AI：`DeepSeek`
- 图表：`Plotly + Kaleido`
- PDF：`ReportLab`
- 本地文件缓存：`storage/reports/`

## 目录说明

- `backend/`：FastAPI 后端、数据库模型、服务层、Agent
- `web/`：React 前端
- `storage/reports/`：本地 PDF 报告缓存目录
- `modules/`：旧版图表/分析模块参考代码
- `app.py`：旧版 Streamlit 入口，现主要作为历史版本参考

## 环境变量

建议使用 `.env`：

```env
DEEPSEEK_API_KEY=your_key
DATABASE_URL=postgresql+psycopg://user:password@127.0.0.1:5432/stock_car
VITE_API_BASE_URL=http://127.0.0.1:8000
```

说明：

- 后端优先读取 `DEEPSEEK_API_KEY`
- `.streamlit/secrets.toml` 目前只保留兼容兜底，不再是推荐配置方式

## 启动方式

后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd web
npm install
npm run dev
```

## PDF 缓存策略

- 文件落盘目录：`storage/reports/`
- 文件名格式：`report_{stock_code}_{date_hash}.pdf`
- 数据库索引表：`ai_reports`
- 同一股票 + 同一区间 + 当天已生成：直接命中缓存
- 同一参数跨天：覆盖同名文件并更新索引时间
- 日期区间变化：生成新文件
- 应用启动时自动清理 7 天前的 PDF 文件与失效索引

## 说明

- 真实缓存命中逻辑在后端，不依赖前端内存状态
- PDF 下载前必须先生成当前股票的分析数据
- 图表已拆分为懒加载 chunk，但 Plotly 体积仍然较大
