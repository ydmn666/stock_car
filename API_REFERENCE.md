# stock_car v2 API Reference

Base URL default: `http://127.0.0.1:8000`

## Health

`GET /health`

Returns backend liveness.

## Stock Data

`GET /stocks/name/{symbol}`

Returns stock display name for a code.

`POST /stocks/data`

Request:

```json
{
  "symbol": "002594",
  "start_date": "2025-03-01",
  "end_date": "2026-03-10"
}
```

Response:

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

`POST /stocks/news`

Request:

```json
{
  "symbol": "002594",
  "stock_name": "比亚迪",
  "limit": 10
}
```

Response returns `records` and `is_fallback`.

## Auth And History

`POST /auth/register`

`POST /auth/login`

Request:

```json
{
  "username": "demo",
  "password": "demo123"
}
```

`GET /users/{username}/history`

Returns recent analysis history.

`POST /users/history/log`

Request:

```json
{
  "username": "demo",
  "stock_name": "比亚迪",
  "stock_code": "002594"
}
```

`DELETE /users/history/{item_id}`

Deletes one history item.

`DELETE /users/{username}/history`

Clears all history for a user.

## Forecast

`POST /forecast`

Request:

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

Response returns Prophet forecast records.

## AI

`POST /ai/chat/stream`

Request:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "..."
    },
    {
      "role": "user",
      "content": "..."
    }
  ],
  "temperature": 0.6
}
```

Response is a plain text stream for incremental chat output.
