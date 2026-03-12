# stock_car v4 API Reference

Base URL default: `http://127.0.0.1:8000`

## Health

`GET /health`

返回后端存活状态。

## Stock

`GET /stocks/name/{symbol}`

返回股票名称。

`POST /stocks/data`

请求：

```json
{
  "symbol": "002594",
  "start_date": "2025-03-01",
  "end_date": "2026-03-10"
}
```

返回：

```json
{
  "records": [
    {
      "日期": "2026-03-10 00:00:00",
      "收盘": 123.45
    }
  ]
}
```

说明：

- 后端优先从数据库读取
- 数据缺失时自动联网补全
- 补全后写回数据库

`POST /stocks/news`

请求：

```json
{
  "symbol": "002594",
  "stock_name": "比亚迪",
  "limit": 10
}
```

返回：

```json
{
  "records": [],
  "is_fallback": false
}
```

## Auth And History

`POST /auth/register`

`POST /auth/login`

请求：

```json
{
  "username": "demo",
  "password": "demo123"
}
```

`GET /users/{username}/history`

返回用户历史访问记录。

`POST /users/history/log`

请求：

```json
{
  "username": "demo",
  "stock_name": "比亚迪",
  "stock_code": "002594"
}
```

`DELETE /users/history/{item_id}`

删除单条历史。

`DELETE /users/{username}/history`

清空当前用户全部历史。

## Forecast

`POST /forecast`

请求：

```json
{
  "records": [
    {
      "日期": "2026-03-10 00:00:00",
      "收盘": 123.45
    }
  ],
  "days": 7
}
```

返回 Prophet 预测结果。

## AI

`POST /ai/chat/stream`

通用聊天流式输出接口。

请求：

```json
{
  "messages": [
    {
      "role": "user",
      "content": "请分析比亚迪"
    }
  ],
  "temperature": 0.6
}
```

返回：`text/plain` 流式文本。

`POST /ai/chat/respond`

非流式聊天接口。

`POST /ai/agent/stream`

通用 Agent 流式接口。

请求：

```json
{
  "messages": [
    {
      "role": "user",
      "content": "帮我看看宁德时代"
    }
  ],
  "context": {
    "analysis_ready": true,
    "current_stock_name": "宁德时代",
    "current_stock_code": "300750",
    "start_date": "2025-03-01",
    "end_date": "2026-03-10",
    "pdf_ready_for_current_stock": true
  }
}
```

`POST /ai/agent/respond`

返回 Agent 最终内容与动作信息。

## PDF

`POST /reports/pdf`

请求：

```json
{
  "symbol": "002594",
  "stock_name": "比亚迪",
  "start_date": "2025-03-01",
  "end_date": "2026-03-10"
}
```

返回：`application/pdf`

行为说明：

- 同参数且当天已生成：直接返回缓存 PDF
- 同参数跨天：覆盖同名文件并更新时间
- 区间变化：生成新文件
- 图表导出失败时仍会生成纯文字降级版 PDF
