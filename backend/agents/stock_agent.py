from __future__ import annotations

from typing import Iterator

from langchain.agents import create_agent
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


def _build_agent():
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
    return create_agent(model=model, tools=TOOLS, system_prompt=SYSTEM_PROMPT)


def run_agent(messages: list[dict]) -> str:
    agent = _build_agent()
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


def stream_agent(messages: list[dict]) -> Iterator[str]:
    agent = _build_agent()

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
