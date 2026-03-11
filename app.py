import os
import sys
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta

import streamlit as st

from frontend.services.api_client import (
    generate_forecast,
    generate_pdf_report,
    get_stock_data,
    get_stock_news,
    log_history,
)
from modules.ai_agent.chat_panel import render_ai_assistant_panel
from modules.ai_agent.assistant import (
    build_forecast_prompt,
    build_sentiment_prompt,
    build_technical_prompt,
    get_deepseek_chat_stream,
    get_price_trend_str,
)
from modules.charts.comparison import render_comparison_chart
from modules.charts.forecast_chart import render_forecast_chart
from modules.charts.kline import calculate_metrics, render_chart as render_kline
from modules.charts.return_chart import render_return_chart
from modules.charts.sentiment_chart import render_sentiment_gauge
from ui.auth import render_login_ui, render_user_header
from ui.dashboard import show_dashboard
from ui.sidebar import show_sidebar

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
st.set_page_config(page_title="新能源车股票分析系统", layout="wide", page_icon="🚗")

PDF_EXECUTOR = ThreadPoolExecutor(max_workers=1)


def _pdf_cache_key(symbol: str, start_date, end_date) -> str:
    start_str = start_date.isoformat() if hasattr(start_date, "isoformat") else str(start_date)
    end_str = end_date.isoformat() if hasattr(end_date, "isoformat") else str(end_date)
    return f"{symbol}|{start_str}|{end_str}"


def _generate_pdf_task(symbol: str, stock_name: str, start_date: str, end_date: str) -> dict:
    pdf_bytes, filename = generate_pdf_report(symbol, start_date, end_date, stock_name)
    return {
        "symbol": symbol,
        "stock_name": stock_name,
        "start_date": start_date,
        "end_date": end_date,
        "bytes": pdf_bytes,
        "filename": filename,
    }


def clear_pdf_runtime_state():
    st.session_state.pdf_cache = {}
    st.session_state.pdf_generation_future = None
    st.session_state.pdf_generation_meta = None
    st.session_state.pdf_generation_pending = None
    st.session_state.pdf_generation_session = st.session_state.get("pdf_generation_session", 0) + 1
    st.session_state.pdf_report_bytes = None
    st.session_state.pdf_report_filename = None
    st.session_state.pdf_report_symbol = None
    st.session_state.sidebar_pdf_bytes = None
    st.session_state.sidebar_pdf_filename = None
    st.session_state.sidebar_pdf_symbol = None


def _submit_pdf_generation(symbol: str, stock_name: str, start_date, end_date):
    start_str = start_date.isoformat() if hasattr(start_date, "isoformat") else str(start_date)
    end_str = end_date.isoformat() if hasattr(end_date, "isoformat") else str(end_date)
    future = PDF_EXECUTOR.submit(_generate_pdf_task, symbol, stock_name, start_str, end_str)
    st.session_state.pdf_generation_future = future
    st.session_state.pdf_generation_meta = {
        "symbol": symbol,
        "stock_name": stock_name,
        "start_date": start_str,
        "end_date": end_str,
        "session_id": st.session_state.pdf_generation_session,
    }


def process_pdf_generation_queue():
    future: Future | None = st.session_state.get("pdf_generation_future")
    meta = st.session_state.get("pdf_generation_meta")
    if future is None or meta is None:
        return False
    if not future.done():
        return False

    st.session_state.pdf_generation_future = None
    st.session_state.pdf_generation_meta = None

    try:
        result = future.result()
        if meta["session_id"] == st.session_state.get("pdf_generation_session"):
            cache_key = _pdf_cache_key(result["symbol"], result["start_date"], result["end_date"])
            st.session_state.pdf_cache[cache_key] = result
            st.session_state.pdf_report_bytes = result["bytes"]
            st.session_state.pdf_report_filename = result["filename"]
            st.session_state.pdf_report_symbol = result["symbol"]
    except Exception:
        pass

    pending = st.session_state.get("pdf_generation_pending")
    st.session_state.pdf_generation_pending = None
    if not pending:
        return True

    cache_key = _pdf_cache_key(pending["symbol"], pending["start_date"], pending["end_date"])
    if cache_key in st.session_state.get("pdf_cache", {}):
        return True

    _submit_pdf_generation(
        pending["symbol"],
        pending["stock_name"],
        pending["start_date"],
        pending["end_date"],
    )
    return True


def ensure_pdf_generation_for_selection(symbol: str | None, stock_name: str | None, start_date, end_date):
    if not symbol or not stock_name:
        return

    cache_key = _pdf_cache_key(symbol, start_date, end_date)
    if cache_key in st.session_state.get("pdf_cache", {}):
        cached = st.session_state.pdf_cache[cache_key]
        st.session_state.pdf_report_bytes = cached["bytes"]
        st.session_state.pdf_report_filename = cached["filename"]
        st.session_state.pdf_report_symbol = cached["symbol"]
        return

    generation_meta = st.session_state.get("pdf_generation_meta")
    if generation_meta and generation_meta.get("symbol") == symbol:
        return

    pending = {
        "symbol": symbol,
        "stock_name": stock_name,
        "start_date": start_date,
        "end_date": end_date,
    }

    if st.session_state.get("pdf_generation_future") is not None:
        st.session_state.pdf_generation_pending = pending
        return

    _submit_pdf_generation(symbol, stock_name, start_date, end_date)


def render_pdf_generation_monitor():
    if not hasattr(st, "fragment"):
        return

    @st.fragment(run_every=2)
    def _poller():
        future = st.session_state.get("pdf_generation_future")
        meta = st.session_state.get("pdf_generation_meta")
        if future is None or meta is None:
            return

        changed = process_pdf_generation_queue()
        current_meta = st.session_state.get("pdf_generation_meta")
        if current_meta is not None:
            st.caption(
                f"PDF 后台处理中：{current_meta.get('stock_name', current_meta.get('symbol', '当前股票'))}"
            )
        if changed:
            st.rerun()

    _poller()


def build_agent_context(user_input: dict | None = None) -> dict:
    context = {
        "analysis_ready": False,
        "current_stock_name": None,
        "current_stock_code": None,
        "start_date": None,
        "end_date": None,
        "pdf_ready_for_current_stock": False,
    }

    if not st.session_state.get("analysis_started"):
        return context

    current_name = st.session_state.get("current_ticker")
    current_code = st.session_state.get("current_ticker_code")
    if not current_name or not current_code:
        return context

    start_date = st.session_state.get("analysis_start_date")
    end_date = st.session_state.get("analysis_end_date")
    if user_input:
        start_date = start_date or user_input.get("start_date")
        end_date = end_date or user_input.get("end_date")

    context["analysis_ready"] = True
    context["current_stock_name"] = current_name
    context["current_stock_code"] = current_code
    context["start_date"] = start_date.isoformat() if hasattr(start_date, "isoformat") else str(start_date)
    context["end_date"] = end_date.isoformat() if hasattr(end_date, "isoformat") else str(end_date)
    cache_key = _pdf_cache_key(current_code, context["start_date"], context["end_date"])
    context["pdf_ready_for_current_stock"] = cache_key in st.session_state.get("pdf_cache", {})
    return context


def main_system():
    render_user_header()
    st.title("新能源车股票分析系统")

    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False
    if "chat_history_tech" not in st.session_state:
        st.session_state.chat_history_tech = []
    if "chat_history_pred" not in st.session_state:
        st.session_state.chat_history_pred = []
    if "current_ticker" not in st.session_state:
        st.session_state.current_ticker = None
    if "pdf_report_bytes" not in st.session_state:
        st.session_state.pdf_report_bytes = None
    if "pdf_report_filename" not in st.session_state:
        st.session_state.pdf_report_filename = None
    if "pdf_report_symbol" not in st.session_state:
        st.session_state.pdf_report_symbol = None
    if "pdf_cache" not in st.session_state:
        st.session_state.pdf_cache = {}
    if "pdf_generation_future" not in st.session_state:
        st.session_state.pdf_generation_future = None
    if "pdf_generation_meta" not in st.session_state:
        st.session_state.pdf_generation_meta = None
    if "pdf_generation_pending" not in st.session_state:
        st.session_state.pdf_generation_pending = None
    if "pdf_generation_session" not in st.session_state:
        st.session_state.pdf_generation_session = 0

    process_pdf_generation_queue()
    render_pdf_generation_monitor()

    user_input = show_sidebar()
    tickers = user_input["tickers"]

    if user_input["run_query"]:
        clear_pdf_runtime_state()
        st.session_state.analysis_started = True
        st.session_state.analysis_start_date = user_input["start_date"]
        st.session_state.analysis_end_date = user_input["end_date"]
        if st.session_state.get("is_logged_in") and st.session_state.get("current_user"):
            for ticker in tickers:
                log_history(st.session_state.current_user, ticker["name"], ticker["code"])

    if not (st.session_state.analysis_started and tickers):
        render_ai_assistant_panel(build_agent_context(user_input))
        return

    all_data = {}
    for ticker in tickers:
        df = get_stock_data(ticker["code"], user_input["start_date"], user_input["end_date"])
        if df is not None and not df.empty:
            all_data[ticker["name"]] = df

    if not all_data:
        st.error("未获取到数据。")
        render_ai_assistant_panel(build_agent_context(user_input))
        return

    st.subheader("行业对标 (收益率 PK)")
    render_comparison_chart(all_data)
    st.divider()

    st.subheader("深度透视")
    options = list(all_data.keys())
    selector_col, action_col = st.columns([5, 2])
    with selector_col:
        target_name = st.selectbox("选择要分析的企业:", options, key="stock_selector")
    target_code = next((item["code"] for item in tickers if item["name"] == target_name), None)
    with action_col:
        st.caption("导出当前选中企业的 PDF 报告")
        generation_meta = st.session_state.get("pdf_generation_meta")
        if generation_meta:
            if generation_meta.get("symbol") == target_code:
                st.caption("后台正在预生成当前股票 PDF...")
            else:
                st.caption("后台正在生成其他股票 PDF，完成后会继续处理当前选择。")
        if st.button("生成 PDF 报告", key="generate_pdf_report_btn", use_container_width=True):
            if not target_code:
                st.error("错误: 未能获取当前股票代码。")
            else:
                cache_key = _pdf_cache_key(target_code, user_input["start_date"], user_input["end_date"])
                cached = st.session_state.get("pdf_cache", {}).get(cache_key)
                if cached:
                    st.session_state.pdf_report_bytes = cached["bytes"]
                    st.session_state.pdf_report_filename = cached["filename"]
                    st.session_state.pdf_report_symbol = cached["symbol"]
                else:
                    with st.spinner(f"正在为 {target_name} 生成 PDF 报告..."):
                        pdf_bytes, filename = generate_pdf_report(
                            symbol=target_code,
                            stock_name=target_name,
                            start_date=user_input["start_date"],
                            end_date=user_input["end_date"],
                        )
                        st.session_state.pdf_cache[cache_key] = {
                            "symbol": target_code,
                            "stock_name": target_name,
                            "start_date": user_input["start_date"].isoformat(),
                            "end_date": user_input["end_date"].isoformat(),
                            "bytes": pdf_bytes,
                            "filename": filename,
                        }
                        st.session_state.pdf_report_bytes = pdf_bytes
                        st.session_state.pdf_report_filename = filename
                        st.session_state.pdf_report_symbol = target_code

        if (
            st.session_state.pdf_report_bytes
            and st.session_state.pdf_report_symbol == target_code
            and st.session_state.pdf_report_filename
        ):
            st.download_button(
                label="下载当前 PDF",
                data=st.session_state.pdf_report_bytes,
                file_name=st.session_state.pdf_report_filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"download_pdf_{target_code}",
            )

    if st.session_state.current_ticker != target_name:
        st.session_state.current_ticker = target_name
        st.session_state.current_ticker_code = target_code
        st.session_state.chat_history_tech = []
        st.session_state.chat_history_pred = []
        st.session_state.sentiment_score = None
        st.session_state.sentiment_text = ""
    else:
        st.session_state.current_ticker_code = target_code

    ensure_pdf_generation_for_selection(
        target_code,
        target_name,
        user_input["start_date"],
        user_input["end_date"],
    )

    render_ai_assistant_panel(build_agent_context(user_input))

    with st.spinner(f"正在加载 {target_name} 的数据..."):
        target_df = all_data[target_name]
        t1, t2, t3, t4 = st.tabs(["基础数据", "技术 & AI", "趋势预测", "舆情 & 情绪"])

        with t1:
            show_dashboard(target_df)

        with t2:
            col_chart, col_ai = st.columns([7, 3])
            with col_chart:
                render_kline(target_df)
                st.markdown("---")
                render_return_chart(target_df)

            with col_ai:
                st.markdown("### DeepSeek 技术分析师")
                chat_container = st.container(height=500, border=True)

                if not st.session_state.chat_history_tech:
                    chat_container.info("点击下方按钮，开始 AI 技术分析。")
                    if chat_container.button("生成技术分析报告", key="btn_init_tech", width="stretch"):
                        sys_prompt = build_technical_prompt(target_name, target_df, all_data)
                        if sys_prompt:
                            st.session_state.chat_history_tech = [
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": "请综合分析当前 K 线形态、收益率表现及行业对比情况。"},
                            ]
                            st.rerun()
                else:
                    with chat_container:
                        for msg in st.session_state.chat_history_tech:
                            if msg["role"] != "system":
                                st.chat_message(msg["role"]).write(msg["content"])

                    if st.session_state.chat_history_tech[-1]["role"] == "user":
                        with chat_container:
                            with st.chat_message("assistant"):
                                response = st.write_stream(
                                    get_deepseek_chat_stream(st.session_state.chat_history_tech)
                                )
                                if response:
                                    st.session_state.chat_history_tech.append(
                                        {"role": "assistant", "content": response}
                                    )
                                    st.rerun()

                    if prompt := st.chat_input("追问技术形态...", key="input_tech"):
                        st.session_state.chat_history_tech.append({"role": "user", "content": prompt})
                        st.rerun()

                    if chat_container.button("重新分析", key="reset_tech"):
                        st.session_state.chat_history_tech = []
                        st.rerun()

        with t3:
            col_pred_chart, col_pred_ai = st.columns([7, 3])
            with col_pred_chart:
                forecast_df, _model = generate_forecast(target_df, days=7)
                render_forecast_chart(forecast_df, target_df)

            with col_pred_ai:
                st.markdown("### DeepSeek 趋势顾问")
                pred_container = st.container(height=500, border=True)

                if not st.session_state.chat_history_pred:
                    pred_container.info("Prophet 模型已运行完成。")
                    if pred_container.button("解读未来趋势", key="btn_init_pred", width="stretch"):
                        sys_prompt = build_forecast_prompt(target_name, forecast_df)
                        if sys_prompt:
                            st.session_state.chat_history_pred = [
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": "请解读这份预测结果。"},
                            ]
                            st.rerun()
                else:
                    with pred_container:
                        for msg in st.session_state.chat_history_pred:
                            if msg["role"] != "system":
                                st.chat_message(msg["role"]).write(msg["content"])

                    if st.session_state.chat_history_pred[-1]["role"] == "user":
                        with pred_container:
                            with st.chat_message("assistant"):
                                response = st.write_stream(
                                    get_deepseek_chat_stream(st.session_state.chat_history_pred)
                                )
                                if response:
                                    st.session_state.chat_history_pred.append(
                                        {"role": "assistant", "content": response}
                                    )
                                    st.rerun()

                    if prompt := st.chat_input("追问趋势风险...", key="input_pred"):
                        st.session_state.chat_history_pred.append({"role": "user", "content": prompt})
                        st.rerun()

                    if pred_container.button("重新解读", key="reset_pred"):
                        st.session_state.chat_history_pred = []
                        st.rerun()

        with t4:
            col_news_ai, col_news_raw = st.columns([4, 6])
            if not target_code:
                st.error("错误: 未能获取股票代码。")
                st.stop()

            with st.spinner(f"正在抓取 {target_name} ({target_code}) 的新闻..."):
                news_df, is_fallback = get_stock_news(symbol=target_code, stock_name=target_name, limit=10)

            with col_news_raw:
                if is_fallback:
                    st.warning(f"未找到 {target_name} 的个股新闻，以下为行业资讯：")
                else:
                    st.success(f"获取成功：{target_name} 个股资讯")

                if news_df is not None and not news_df.empty:
                    display_df = news_df.copy()
                    if "发布时间" in display_df.columns:
                        display_df["发布时间"] = display_df["发布时间"].dt.strftime("%m-%d %H:%M")

                    columns = [col for col in ["发布时间", "新闻标题"] if col in display_df.columns]
                    st.dataframe(
                        display_df[columns],
                        use_container_width=True,
                        hide_index=True,
                        height=400,
                    )
                else:
                    st.error("数据为空：接口虽然运行了，但没有返回内容。")

            with col_news_ai:
                st.subheader("AI 舆情分析")

                if "sentiment_score" not in st.session_state:
                    st.session_state.sentiment_score = None
                if "sentiment_text" not in st.session_state:
                    st.session_state.sentiment_text = ""

                if news_df is not None and not news_df.empty:
                    render_sentiment_gauge(st.session_state.sentiment_score, key="gauge_static")

                    if st.button("开始 AI 分析", type="primary", use_container_width=True):
                        real_trend_desc = "暂无行情数据"
                        year_metrics = None

                        try:
                            end_d = datetime.now().date()
                            start_d = end_d - timedelta(days=365)
                            with st.spinner("正在校准 AI 基准数据..."):
                                real_time_df = get_stock_data(target_code, start_d, end_d)

                            if real_time_df is not None and not real_time_df.empty:
                                year_metrics = calculate_metrics(real_time_df)
                                real_trend_desc = get_price_trend_str(real_time_df)
                        except Exception as exc:
                            print(f"数据准备报错: {exc}")

                        prompt = build_sentiment_prompt(
                            stock_name=target_name,
                            news_df=news_df,
                            price_trend_str=real_trend_desc,
                            metrics=year_metrics,
                            is_sector_news=is_fallback,
                        )

                        if prompt:
                            messages = [{"role": "system", "content": prompt}]
                            st.session_state.sentiment_text = ""
                            placeholder = st.empty()
                            full_resp = ""
                            stream = get_deepseek_chat_stream(messages, temperature=0.6)

                            import re

                            found_score = False
                            for chunk in stream:
                                full_resp += chunk
                                if not found_score:
                                    match = re.search(r"SCORE:\s*(\d+)", full_resp)
                                    if match:
                                        score = int(match.group(1))
                                        st.session_state.sentiment_score = score
                                        found_score = True
                                        render_sentiment_gauge(score, key="gauge_dynamic")

                                clean_text = re.sub(r"SCORE:\s*\d+", "", full_resp).strip()
                                placeholder.markdown(clean_text)
                                st.session_state.sentiment_text = clean_text

                            st.rerun()

                    if st.session_state.sentiment_text:
                        st.markdown("---")
                        st.markdown("### 分析报告")
                        st.markdown(st.session_state.sentiment_text)
                else:
                    st.info("等待新闻数据加载...")


def main():
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False

    if not st.session_state.is_logged_in:
        render_login_ui()
    else:
        main_system()


if __name__ == "__main__":
    main()
