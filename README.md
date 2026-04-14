# stock_car v4.5

新能源汽车股票智能投研毕业设计项目，当前技术栈为 `React + TypeScript + Tailwind CSS + FastAPI + PostgreSQL`。

项目当前已完成股票分析、资讯舆情、趋势预测、AI 辅助问答、PDF 报告导出、用户注册登录、历史记录、个人投资记录与基础账户安全能力。

## 当前版本重点

- 完成前后端分离架构
- 支持 A 股股票基础分析与多页面工作台展示
- 支持 AI 问答与 PDF 报告生成
- 支持用户注册、登录、修改密码
- 支持基于登录态的用户数据隔离
- 支持个人投资交易记录、持仓与收益概览

## 核心功能

- 用户注册与登录
- 登录态鉴权与用户数据隔离
- 用户修改密码
- 股票名称解析与行情数据查询
- 技术分析与图表展示
- 新闻资讯与舆情分析
- 未来趋势预测
- AI 辅助问答
- PDF 研报导出
- 用户历史访问记录
- 个人投资记录、持仓与收益分析

## 项目结构

```text
stock_car/
├─ backend/               # FastAPI 后端
├─ frontend/              # React 前端
├─ alembic/               # 数据库迁移
├─ storage/reports/       # PDF 报告缓存目录
├─ docker-compose.yml
├─ README.md
└─ API_REFERENCE.md
```

## 技术栈

- 前端：`React + TypeScript + Tailwind CSS + Plotly`
- 后端：`FastAPI + SQLAlchemy`
- 数据库：`PostgreSQL`
- 数据分析：`pandas + prophet`
- 图表导出：`Plotly + Kaleido`
- PDF 生成：`ReportLab`
- AI 能力：`OpenAI / DeepSeek 兼容方式接入`

## 认证与账户设计

当前版本已实现基础账户安全能力：

- 用户名长度 4-20 位，不能包含空格
- 密码长度 6-20 位
- 登录成功后由后端签发 token
- 前端后续请求自动携带 token
- 用户历史记录与个人投资数据只允许当前登录用户访问和修改
- 密码使用 `bcrypt` 加密存储
- 支持已登录用户修改密码

## 本地运行

### 1. 后端

在项目根目录配置 `.env` 后启动后端：

```powershell
uvicorn backend.main:app --reload
```

### 2. 前端

```powershell
cd frontend
npm install
npm run dev
```

## 常用环境变量

建议在项目根目录 `.env` 中配置：

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/stock_car
VITE_API_BASE_URL=http://127.0.0.1:8000
AUTH_SECRET=your_own_secret_key
DEEPSEEK_API_KEY=your_key
```

说明：

- `DATABASE_URL`：后端连接 PostgreSQL 使用
- `VITE_API_BASE_URL`：前端请求后端 API 使用
- `AUTH_SECRET`：登录 token 签名密钥
- `DEEPSEEK_API_KEY`：AI 接口密钥

## Docker 部署

项目保留了 Docker 部署能力，可在根目录执行：

```powershell
docker compose up --build
```

服务职责：

- `db`：PostgreSQL
- `backend`：FastAPI、AI、PDF 报告生成
- `frontend`：前端页面与反向代理

## 数据与报告缓存

- PDF 报告保存于 `storage/reports/`
- 同一股票、同一区间的报告支持缓存复用
- 历史记录与个人投资数据存储于 PostgreSQL

## 毕设展示建议

答辩时建议重点展示以下流程：

1. 用户注册与登录
2. 股票选择与分析工作台
3. 历史记录自动保存
4. 个人投资记录录入与收益分析
5. 修改密码
6. PDF 报告导出

## 当前阶段建议

当前项目已经适合进入论文撰写阶段，后续优先建议：

- 补论文初稿
- 整理系统架构图、数据库设计图、功能流程图
- 准备演示截图与答辩说明
