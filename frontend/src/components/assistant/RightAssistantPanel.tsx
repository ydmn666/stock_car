import { type FormEvent, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { streamAgent } from "../../lib/api";
import type { AgentMessage } from "../../lib/workspace";
import { markdown, pdfIntent } from "../../lib/workspace";

type RightAssistantPanelProps = {
  currentUser: string;
  context: Record<string, unknown>;
  prompts: string[];
  onRequestPdf?: () => Promise<boolean | void>;
};

function Md({ content }: { content: string }) {
  const clean = markdown(content);
  if (!clean) return null;
  return (
    <div className="prose prose-invert max-w-none text-sm prose-p:my-0 prose-p:leading-7 prose-li:leading-7 prose-strong:text-[var(--color-text)]">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{clean}</ReactMarkdown>
    </div>
  );
}

export function RightAssistantPanel({ currentUser, context, prompts, onRequestPdf }: RightAssistantPanelProps) {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  function resizeTextarea(value: string) {
    const node = textareaRef.current;
    if (!node) return;
    node.style.height = "0px";
    const nextHeight = Math.min(Math.max(node.scrollHeight, 52), 160);
    node.style.height = `${nextHeight}px`;
    if (!value.trim()) {
      node.style.height = "52px";
    }
  }

  async function send(prompt: string) {
    const text = prompt.trim();
    if (!text) return;
    const next = [...messages, { role: "user" as const, content: text }];
    setMessages(next);
    setInput("");
    resizeTextarea("");
    setLoading(true);
    try {
      if (onRequestPdf && pdfIntent(text)) {
        const ok = await onRequestPdf();
        setMessages((current) => [
          ...current,
          { role: "assistant", content: ok ? "当前股票报告已开始生成或下载。" : "当前还没有可导出的分析结果，请先完成分析加载。" },
        ]);
        return;
      }
      const assistantIndex = next.length;
      setMessages((current) => [...current, { role: "assistant", content: "" }]);
      let content = "";
      for await (const chunk of streamAgent(next.map((item) => ({ role: item.role, content: item.content })), context)) {
        content += chunk;
        setMessages((current) => current.map((item, index) => (index === assistantIndex ? { ...item, content } : item)));
      }
    } catch (error) {
      setMessages((current) => [
        ...current,
        { role: "assistant", content: error instanceof Error ? error.message : "AI 助手暂时不可用，请稍后重试。" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void send(input);
  }

  return (
    <aside className="assistant-panel flex h-[calc(100vh-121px)] min-h-0 max-h-full flex-col overflow-hidden rounded-[28px] p-4 2xl:h-[calc(100vh-128px)]">
      <div className="shrink-0 border-b border-white/25 pb-2">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-2xl font-semibold text-white">AI 助手</h3>
          </div>
          <span className="rounded-full border border-white/28 bg-white/12 px-3 py-1 text-[11px] text-white">{currentUser || "访客模式"}</span>
        </div>
      </div>

      <div className="mt-3 min-h-0 flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto overscroll-contain pr-1">
          <div className="flex min-h-full flex-col justify-end gap-3">
            {!messages.length ? (
              <div className="rounded-2xl border border-white/25 bg-[rgba(255,255,255,0.12)] px-4 py-4 text-sm leading-7 text-white/88">
                暂无对话，直接从下方输入框开始提问即可。
              </div>
            ) : null}
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`rounded-2xl px-4 py-3 text-sm leading-7 ${message.role === "user" ? "ml-auto max-w-[92%] bg-white/85 text-[var(--color-text-strong)]" : "max-w-[96%] border border-white/25 bg-[rgba(255,255,255,0.12)] text-white"}`}>
                {message.role === "user" ? message.content : <Md content={message.content} />}
              </div>
            ))}
            {loading ? <div className="text-xs text-white/78">AI 正在整理回答...</div> : null}
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-3 shrink-0 space-y-2 border-t border-white/22 pt-3">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(event) => {
            const value = event.target.value;
            setInput(value);
            resizeTextarea(value);
          }}
          rows={1}
          className="min-h-[48px] w-full resize-none overflow-y-auto rounded-[20px] border border-white/28 bg-[rgba(255,255,255,0.22)] px-4 py-3 text-sm leading-7 text-white outline-none transition placeholder:text-white/75 focus:border-white/40"
          placeholder="填写问答，例：询问股票走势"
        />
        <div className="flex justify-end">
          <button type="submit" className="inline-flex min-w-[114px] items-center justify-center rounded-2xl border border-[var(--color-primary)] bg-[var(--color-primary)] px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_28px_rgba(34,193,220,0.24)] transition hover:bg-[var(--color-primary-hover)] disabled:cursor-not-allowed disabled:opacity-50" disabled={loading}>发送</button>
        </div>
      </form>
    </aside>
  );
}
