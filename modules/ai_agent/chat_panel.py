from __future__ import annotations

import streamlit as st

from frontend.services.api_client import (
    generate_pdf_report,
    get_agent_chat_stream,
    get_agent_response,
)


def _get_agent_status_text(prompt: str) -> str:
    if any(keyword in prompt for keyword in ("pdf", "PDF", "报告", "导出", "下载")):
        return "正在检查当前上下文并准备报告任务..."
    if any(keyword in prompt for keyword in ("新闻", "资讯", "公告", "舆情", "消息")):
        return "正在查询相关新闻并生成分析..."
    if any(keyword in prompt for keyword in ("预测", "趋势", "后市", "未来", "看涨", "看跌")):
        return "正在生成趋势判断并整理分析..."
    return "正在检索数据并生成分析..."


def _is_pdf_request(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in ("pdf", "download", "report")) or any(
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


def render_ai_assistant_panel(context=None):
    if "sidebar_chat" not in st.session_state:
        st.session_state.sidebar_chat = []
    if "sidebar_pdf_bytes" not in st.session_state:
        st.session_state.sidebar_pdf_bytes = None
    if "sidebar_pdf_filename" not in st.session_state:
        st.session_state.sidebar_pdf_filename = None
    if "sidebar_pdf_symbol" not in st.session_state:
        st.session_state.sidebar_pdf_symbol = None

    st.subheader("AI 选股助手")
    with st.container(border=True):
        if st.session_state.sidebar_chat:
            if st.button("清空对话历史", use_container_width=True, key="clear_agent_chat"):
                st.session_state.sidebar_chat = []
                st.session_state.sidebar_pdf_bytes = None
                st.session_state.sidebar_pdf_filename = None
                st.session_state.sidebar_pdf_symbol = None
                st.rerun()

        history_container = st.container(height=420)
        with history_container:
            for msg in st.session_state.sidebar_chat:
                role = "user" if msg["role"] == "user" else "assistant"
                st.chat_message(role).write(msg["content"])

        if prompt := st.chat_input("问股票 / 问代码 / 问概念...", key="agent_input"):
            st.session_state.sidebar_chat.append({"role": "user", "content": prompt})
            with history_container:
                st.chat_message("user").write(prompt)

            with history_container:
                with st.chat_message("assistant"):
                    system_prompt = (
                        "你是新能源汽车股票系统里的智能助手。"
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
                label="下载当前对话生成的 PDF",
                data=st.session_state.sidebar_pdf_bytes,
                file_name=st.session_state.sidebar_pdf_filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"sidebar_pdf_{st.session_state.sidebar_pdf_symbol}",
            )
