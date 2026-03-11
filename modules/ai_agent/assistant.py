from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.services.api_client import (
    generate_pdf_report,
    get_agent_response as api_get_agent_response,
    get_agent_chat_stream as api_get_agent_chat_stream,
    get_deepseek_chat_stream as api_get_deepseek_chat_stream,
)


def get_deepseek_chat_stream(messages, temperature=1.1):
    yield from api_get_deepseek_chat_stream(messages, temperature)


def get_agent_chat_stream(messages, context=None):
    yield from api_get_agent_chat_stream(messages, context)


def get_agent_response(messages, context=None):
    return api_get_agent_response(messages, context)


def _get_agent_status_text(prompt: str) -> str:
    if any(keyword in prompt for keyword in ("pdf", "PDF", "报告", "导出", "下载")):
        return "正在检查当前上下文并准备报告任务..."
    if any(keyword in prompt for keyword in ("新闻", "资讯", "公告", "舆情", "消息")):
        return "正在查询相关新闻并生成分析..."
    if any(keyword in prompt for keyword in ("预测", "趋势", "后市", "未来", "看涨", "看跌")):
        return "正在生成趋势判断并整理分析..."
    return "正在检索数据并生成分析..."


def _is_pdf_request(prompt: str) -> bool:
    return any(keyword in prompt.lower() for keyword in ("pdf", "download", "report")) or any(
        keyword in prompt for keyword in ("报告", "导出", "下载")
    )


def _stream_text_to_placeholder(text: str, placeholder):
    content = ""
    for char in text:
        content += char
        placeholder.markdown(content)
    return content


def _pdf_cache_key(symbol: str, start_date: str, end_date: str) -> str:
    return f"{symbol}|{start_date}|{end_date}"


def render_ai_assistant_sidebar(context=None):
    with st.sidebar.expander("AI 选股助手", expanded=True):
        if "sidebar_chat" not in st.session_state:
            st.session_state.sidebar_chat = []
        if "sidebar_pdf_bytes" not in st.session_state:
            st.session_state.sidebar_pdf_bytes = None
        if "sidebar_pdf_filename" not in st.session_state:
            st.session_state.sidebar_pdf_filename = None
        if "sidebar_pdf_symbol" not in st.session_state:
            st.session_state.sidebar_pdf_symbol = None

        if st.session_state.sidebar_chat:
            if st.button("清空对话历史", use_container_width=True):
                st.session_state.sidebar_chat = []
                st.session_state.sidebar_pdf_bytes = None
                st.session_state.sidebar_pdf_filename = None
                st.session_state.sidebar_pdf_symbol = None
                st.rerun()

        for msg in st.session_state.sidebar_chat:
            role = "user" if msg["role"] == "user" else "assistant"
            st.chat_message(role).write(msg["content"])

        if prompt := st.chat_input("问股票 / 问代码 / 问概念...", key="sidebar_input"):
            st.session_state.sidebar_chat.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                system_prompt = (
                    "你是新能源车股票系统里的智能助手。"
                    "优先回答 A 股股票代码、个股基础分析、新闻摘要和趋势判断。"
                    "如果缺少股票代码且无法可靠判断，请明确提醒用户补充。"
                    "回答尽量简洁。"
                )
                context_messages = st.session_state.sidebar_chat[-10:]
                messages = [{"role": "system", "content": system_prompt}, *context_messages]

                status_placeholder = st.empty()
                status_placeholder.info(_get_agent_status_text(prompt))

                if _is_pdf_request(prompt):
                    result = get_agent_response(messages, context)
                    response_placeholder = st.empty()
                    response = _stream_text_to_placeholder(result.get("content", ""), response_placeholder)

                    actions = result.get("actions", [])
                    for action in actions:
                        if action.get("type") == "use_existing_pdf":
                            cache_key = _pdf_cache_key(
                                action["symbol"],
                                action["start_date"],
                                action["end_date"],
                            )
                            cached = st.session_state.get("pdf_cache", {}).get(cache_key)
                            if cached:
                                st.session_state.sidebar_pdf_bytes = cached["bytes"]
                                st.session_state.sidebar_pdf_filename = cached["filename"]
                            st.session_state.sidebar_pdf_symbol = action["symbol"]
                            continue
                        if action.get("type") == "generate_pdf":
                            with st.spinner("正在生成当前选中股票的 PDF 报告..."):
                                pdf_bytes, filename = generate_pdf_report(
                                    symbol=action["symbol"],
                                    stock_name=action.get("stock_name"),
                                    start_date=action["start_date"],
                                    end_date=action["end_date"],
                                )
                                cache_key = _pdf_cache_key(
                                    action["symbol"],
                                    action["start_date"],
                                    action["end_date"],
                                )
                                st.session_state.setdefault("pdf_cache", {})[cache_key] = {
                                    "symbol": action["symbol"],
                                    "stock_name": action.get("stock_name"),
                                    "start_date": action["start_date"],
                                    "end_date": action["end_date"],
                                    "bytes": pdf_bytes,
                                    "filename": filename,
                                }
                                st.session_state.sidebar_pdf_bytes = pdf_bytes
                                st.session_state.sidebar_pdf_filename = filename
                                st.session_state.sidebar_pdf_symbol = action["symbol"]
                                st.session_state.pdf_report_bytes = pdf_bytes
                                st.session_state.pdf_report_filename = filename
                                st.session_state.pdf_report_symbol = action["symbol"]
                else:
                    response = st.write_stream(get_agent_chat_stream(messages, context))
                status_placeholder.empty()

            st.session_state.sidebar_chat.append({"role": "assistant", "content": response})

        if (
            st.session_state.sidebar_pdf_bytes
            and st.session_state.sidebar_pdf_filename
            and st.session_state.sidebar_pdf_symbol
        ):
            st.download_button(
                label="下载侧边栏生成的 PDF",
                data=st.session_state.sidebar_pdf_bytes,
                file_name=st.session_state.sidebar_pdf_filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"sidebar_pdf_{st.session_state.sidebar_pdf_symbol}",
            )


def build_technical_prompt(ticker_name, df, all_data=None):
    if df is None or df.empty:
        return None

    calc_df = df.copy().sort_values("日期").reset_index(drop=True)
    if len(calc_df) < 2:
        return None

    last_row = calc_df.iloc[-1]
    prev_row = calc_df.iloc[-2]

    ma5 = calc_df["收盘"].rolling(window=5).mean().iloc[-1]
    ma10 = calc_df["收盘"].rolling(window=10).mean().iloc[-1]
    ma20 = calc_df["收盘"].rolling(window=20).mean().iloc[-1]

    prev_volume = prev_row["成交量"] if prev_row["成交量"] else 1
    vol_ratio = last_row["成交量"] / prev_volume

    base_price = calc_df["收盘"].iloc[0]
    curr_price = last_row["收盘"]
    total_return = (curr_price - base_price) / base_price * 100

    competitor_info = []
    if all_data:
        for name, other_df in all_data.items():
            if name == ticker_name or other_df is None or other_df.empty:
                continue
            other_df = other_df.sort_values("日期").reset_index(drop=True)
            s_p = other_df["收盘"].iloc[0]
            e_p = other_df["收盘"].iloc[-1]
            ret = (e_p - s_p) / s_p * 100
            competitor_info.append(f"- {name}: 区间收益率 {ret:.2f}%")

    competitors_str = "\n".join(competitor_info) if competitor_info else "无其他对比数据"

    return f"""
你是一位资深金融分析师，尤其擅长中国新能源车产业链研究。请根据用户给出的客观交易数据，结合行业背景知识，输出一份专业、克制的分析报告。
分析对象: {ticker_name}

技术面客观数据:
- 最新收盘价: {last_row["收盘"]:.2f}
- 当日涨跌幅: {last_row["涨跌幅"]:.2f}%
- 换手率: {last_row["换手率"]:.2f}%
- 量比近似: {vol_ratio:.2f}
- MA5: {ma5:.2f}
- MA10: {ma10:.2f}
- MA20: {ma20:.2f}
- 区间累计收益率: {total_return:.2f}%

行业对比:
{competitors_str}

要求:
1. 不要机械解释指标，要结合行业逻辑。
2. 观点保持客观，明确机会和风险。
3. 输出 Markdown 格式。
"""


def build_forecast_prompt(ticker_name, forecast_df):
    if forecast_df is None or forecast_df.empty:
        return None

    future = forecast_df.tail(7)
    start_price = future.iloc[0]["yhat"]
    end_price = future.iloc[-1]["yhat"]
    expected_growth = (end_price - start_price) / start_price * 100
    upper = future.iloc[-1]["yhat_upper"]
    lower = future.iloc[-1]["yhat_lower"]
    uncertainty_range = (upper - lower) / end_price * 100

    direction = "看涨" if expected_growth > 0 else "看跌"

    return f"""
你是一位量化策略顾问。下面是一份由 Prophet 生成的 7 天股价预测结果。
分析对象: {ticker_name}
- 模型方向: {direction}
- 理论涨跌幅: {expected_growth:.2f}%
- 理论目标价: {end_price:.2f}
- 不确定性区间: {uncertainty_range:.1f}%

请完成两件事:
1. 先直接说明模型判断未来一周是涨还是跌。
2. 再结合行业和基本面角度，评价这个预测是否可信。
"""


def build_sentiment_prompt(stock_name, news_df, price_trend_str, metrics=None, is_sector_news=False):
    if news_df is None or news_df.empty:
        return None

    news_list = []
    title_col = "新闻标题" if "新闻标题" in news_df.columns else news_df.columns[-1]
    time_col = "发布时间" if "发布时间" in news_df.columns else None

    for _, row in news_df.head(10).iterrows():
        time_str = "近期"
        if time_col:
            try:
                time_str = pd.to_datetime(row[time_col]).strftime("%Y-%m-%d")
            except Exception:
                pass
        news_list.append(f"- [{time_str}] {row[title_col]}")

    source_type = "行业宏观新闻" if is_sector_news else "个股新闻"
    metrics_str = "暂无量化指标"
    if metrics:
        vol, sharpe, max_dd = metrics
        if vol is not None:
            metrics_str = (
                f"- 年化波动率: {vol * 100:.2f}%\n"
                f"- 夏普比率: {sharpe:.2f}\n"
                f"- 最大回撤: {max_dd * 100:.2f}%"
            )

    return f"""
你是一位交易员。请基于最新市场信息，对 {stock_name} 做舆情与情绪分析。
资讯来源: {source_type}

量化指标:
{metrics_str}

行情摘要:
{price_trend_str}

最新资讯:
{chr(10).join(news_list)}

输出格式必须严格如下:
SCORE: [0-100]
ANALYSIS: [分析内容]
"""


def get_price_trend_str(df):
    if df is None or df.empty:
        return "暂无行情数据"

    df = df.sort_values(by="日期")
    last_close = df.iloc[-1]["收盘"]
    first_close = df.iloc[0]["收盘"]
    max_price = df["最高"].max()
    min_price = df["最低"].min()

    period_change = (last_close - first_close) / first_close * 100
    from_high = (last_close - max_price) / max_price * 100
    from_low = (last_close - min_price) / min_price * 100

    return (
        f"最新收盘价 {last_close:.2f} 元。"
        f"区间累计涨跌幅 {period_change:.2f}%。"
        f"相对区间高点 {max_price:.2f} 元回撤 {from_high:.2f}%。"
        f"相对区间低点 {min_price:.2f} 元反弹 {from_low:.2f}%。"
    )
