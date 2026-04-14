# stock_car API Reference

Base URL 默认值：`http://127.0.0.1:8000`

## Health

`GET /health`

返回后端服务状态：

```json
{
  "status": "ok"
}
```

## Auth

### 注册

`POST /auth/register`

请求体：

```json
{
  "username": "demo_user",
  "password": "123456"
}
```

说明：

- 用户名长度 4-20 位，不能包含空格
- 密码长度 6-20 位

### 登录

`POST /auth/login`

请求体：

```json
{
  "username": "demo_user",
  "password": "123456"
}
```

返回示例：

```json
{
  "success": true,
  "token": "xxxx.yyyy",
  "username": "demo_user"
}
```

### 修改密码

`POST /auth/change-password`

请求头：

```text
Authorization: Bearer <token>
```

请求体：

```json
{
  "old_password": "123456",
  "new_password": "654321"
}
```

## Stock

### 获取股票名称

`GET /stocks/name/{symbol}`

示例：

`GET /stocks/name/002594?market=CN`

### 解析股票标的

`POST /instruments/resolve`

请求体：

```json
{
  "symbol": "002594",
  "market": "CN"
}
```

### 获取价格数据

`POST /stocks/data`

请求体：

```json
{
  "symbol": "002594",
  "market": "CN",
  "start_date": "2025-03-01",
  "end_date": "2026-03-10"
}
```

说明：

- 后端优先从数据库读取缓存
- 数据不足时自动补全并写回数据库

### 获取新闻资讯

`POST /stocks/news`

请求体：

```json
{
  "symbol": "002594",
  "market": "CN",
  "stock_name": "比亚迪",
  "limit": 10
}
```

## Forecast

`POST /forecast`

请求体：

```json
{
  "records": [],
  "days": 7
}
```

## User History

以下接口均需要登录。

### 获取当前用户历史记录

`GET /users/me/history`

请求头：

```text
Authorization: Bearer <token>
```

### 记录访问历史

`POST /users/history/log`

请求体：

```json
{
  "stock_name": "比亚迪",
  "stock_code": "002594"
}
```

### 删除单条历史记录

`DELETE /users/history/{item_id}`

### 清空当前用户历史记录

`DELETE /users/me/history`

## Portfolio

以下接口均需要登录，并且只操作当前登录用户的数据。

### 账户概览

`GET /portfolio/me/summary`

### 当前持仓

`GET /portfolio/me/positions`

### 收益表现

`GET /portfolio/me/performance`

### 交易记录

`GET /portfolio/me/transactions`

### 新增交易

`POST /portfolio/transactions`

请求体：

```json
{
  "symbol": "002594",
  "trade_type": "buy",
  "trade_date": "2026-04-13",
  "price": 100,
  "quantity": 10,
  "fee": 0,
  "note": "首次建仓"
}
```

### 修改交易

`PUT /portfolio/transactions/{transaction_id}`

### 删除交易

`DELETE /portfolio/transactions/{transaction_id}`

## AI

### 流式聊天

`POST /ai/chat/stream`

### 非流式聊天

`POST /ai/chat/respond`

### 流式 Agent

`POST /ai/agent/stream`

### 非流式 Agent

`POST /ai/agent/respond`

## PDF

`POST /reports/pdf`

请求体：

```json
{
  "symbol": "002594",
  "market": "CN",
  "stock_name": "比亚迪",
  "start_date": "2025-03-01",
  "end_date": "2026-03-10"
}
```

返回类型：

`application/pdf`

说明：

- 同一股票、同一区间的报告支持缓存复用
- 报告生成失败时会返回错误信息
