from __future__ import annotations

import json
from typing import Iterator

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from backend.agents.tools import TOOLS
from backend.services.ai_service import load_deepseek_api_key


SYSTEM_PROMPT = """你是新能源车股票分析系统里的智能投研助手。

你的职责：
1. 优先帮助用户分析 A 股股票、股票代码、新闻和短期趋势。
2. 当用户问题需要客观数据时，优先调用工具，不要凭空编造。
3. 当用户只问概念时，可以直接简洁回答。
4. 如果用户没有提供股票代码，而你又无法可靠判断，请先提醒用户补充代码。
5. 输出尽量简洁、实用，优先给结论，再补充依据。

限制：
- 不提供确定性的投资承诺。
- 不捏造不存在的公司数据、新闻或预测结果。
- 当前系统主要面向中国 A 股新能源车产业链相关问题。
"""


def _is_pdf_request(messages: list[dict]) -> bool:
    if not messages:
        return False
    prompt = messages[-1].get("content", "").lower()
    return any(keyword in prompt for keyword in ("pdf", "report", "download")) or any(
        keyword in messages[-1].get("content", "") for keyword in ("报告", "导出", "下载")
    )


def _build_context_prompt(context: dict | None) -> str:
    if not context:
        return "\n当前页面上下文：暂无可用页面上下文。"

    if not context.get("analysis_ready"):
        return (
            "\n当前页面上下文：用户尚未点击“生成分析报告”，因此当前没有真正选中的股票。"
            "此时你可以回答一般性股票问题，但不能把左侧勾选列表视为当前选中股票。"
        )

    stock_name = context.get("current_stock_name") or "未知"
    stock_code = context.get("current_stock_code") or "未知"
    start_date = context.get("start_date") or "未知"
    end_date = context.get("end_date") or "未知"
    pdf_ready = "是" if context.get("pdf_ready_for_current_stock") else "否"
    return (
        "\n当前页面上下文："
        f"已经生成分析报告；当前真正选中的股票是 {stock_name}({stock_code})；"
        f"当前分析区间为 {start_date} 到 {end_date}；"
        f"当前股票的 PDF 是否已就绪：{pdf_ready}。"
    )


def _build_pdf_tool(context: dict | None):
    @tool
    def request_current_stock_pdf_report() -> str:
        """Request a PDF report for the currently selected stock in the active page context."""

        if not context or not context.get("analysis_ready"):
            return "ERROR::PDF_CONTEXT_MISSING::当前尚未生成分析报告，无法确定当前选中的股票。请先点击生成分析报告并在条目栏选中股票。"

        stock_code = context.get("current_stock_code")
        stock_name = context.get("current_stock_name")
        start_date = context.get("start_date")
        end_date = context.get("end_date")
        if not all([stock_code, stock_name, start_date, end_date]):
            return "ERROR::PDF_CONTEXT_INCOMPLETE::当前页面缺少生成 PDF 所需的股票或日期信息。"

        action = {
            "type": "generate_pdf",
            "symbol": stock_code,
            "stock_name": stock_name,
            "start_date": start_date,
            "end_date": end_date,
        }
        return "ACTION::PDF::" + json.dumps(action, ensure_ascii=False)

    return request_current_stock_pdf_report


def _resolve_pdf_action(context: dict | None) -> dict:
    if not context or not context.get("analysis_ready"):
        return {
            "content": "当前还没有生成分析报告，因此系统里不存在“当前选中股票”。请先点击“生成分析报告”，再在条目栏里选中一支股票后继续生成 PDF。",
            "actions": [],
        }

    stock_code = context.get("current_stock_code")
    stock_name = context.get("current_stock_name")
    start_date = context.get("start_date")
    end_date = context.get("end_date")
    if not all([stock_code, stock_name, start_date, end_date]):
        return {
            "content": "当前页面上下文不完整，暂时无法生成 PDF。请先确认已经生成分析结果，并且页面中存在当前选中的股票与日期范围。",
            "actions": [],
        }

    action_type = "use_existing_pdf" if context.get("pdf_ready_for_current_stock") else "generate_pdf"
    content = (
        f"已定位到当前选中股票 {stock_name}({stock_code})。"
        + (" 当前 PDF 已生成，可直接下载。" if action_type == "use_existing_pdf" else " 我现在为您准备这只股票的 PDF 报告。")
    )
    return {
        "content": content,
        "actions": [
            {
                "type": action_type,
                "symbol": stock_code,
                "stock_name": stock_name,
                "start_date": start_date,
                "end_date": end_date,
            }
        ],
    }


def _build_agent(context: dict | None = None):
    api_key = load_deepseek_api_key()
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY.")

    model = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        temperature=0.3,
        streaming=True,
    )
    tools = [*TOOLS, _build_pdf_tool(context)]
    system_prompt = (
        SYSTEM_PROMPT
        + _build_context_prompt(context)
        + "\n当用户明确要求生成、导出、下载当前股票 PDF 报告时，你必须优先调用 request_current_stock_pdf_report 工具。"
        + "如果工具返回 ACTION::PDF:: 开头的结果，请在最终回答中简洁说明报告已准备好。"
        + "如果工具返回 ERROR:: 开头的结果，请直接向用户解释原因，不要伪造成功。"
    )
    return create_agent(model=model, tools=tools, system_prompt=system_prompt)


def run_agent(messages: list[dict], context: dict | None = None) -> str:
    agent = _build_agent(context)
    result = agent.invoke({"messages": messages})
    output_messages = result.get("messages", [])
    if not output_messages:
        return "未生成可用回复。"

    final_message = output_messages[-1]
    content = getattr(final_message, "content", "")

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        content = "".join(parts)

    return str(content).strip() or "未生成可用回复。"


def run_agent_with_actions(messages: list[dict], context: dict | None = None) -> dict:
    if _is_pdf_request(messages):
        return _resolve_pdf_action(context)

    agent = _build_agent(context)
    result = agent.invoke({"messages": messages})
    output_messages = result.get("messages", [])
    actions: list[dict] = []
    final_content = "未生成可用回复。"

    for message in output_messages:
        content = getattr(message, "content", "")
        if isinstance(content, str) and content.startswith("ACTION::PDF::"):
            try:
                actions.append(json.loads(content.split("ACTION::PDF::", 1)[1]))
            except Exception:
                pass
        elif isinstance(content, str) and content.startswith("ERROR::"):
            parts = content.split("::", 2)
            final_content = parts[-1] if len(parts) >= 3 else content

    if output_messages:
        last_message = output_messages[-1]
        content = getattr(last_message, "content", "")
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            content = "".join(parts)
        if isinstance(content, str) and content and not content.startswith(("ACTION::", "ERROR::")):
            final_content = content.strip()

    return {"content": final_content or "未生成可用回复。", "actions": actions}


def stream_agent(messages: list[dict], context: dict | None = None) -> Iterator[str]:
    agent = _build_agent(context)

    for chunk, _metadata in agent.stream({"messages": messages}, stream_mode="messages"):
        content = getattr(chunk, "content", None)
        if not content:
            continue

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    if text:
                        yield text
            continue

        yield str(content)
