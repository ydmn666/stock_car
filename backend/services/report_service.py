from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta
from html import escape
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import delete, select

from backend.agents.stock_agent import run_agent
from backend.db import ROOT_DIR, SessionLocal
from backend.models import AIReport
from backend.services.forecast_service import generate_forecast
from backend.services.market_service import get_stock_data, get_stock_name, get_stock_news, init_db


pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

REPORTS_DIR = ROOT_DIR / "storage" / "reports"
PDF_RETENTION_DAYS = 7


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CNTitle",
            parent=styles["Title"],
            fontName="STSong-Light",
            fontSize=20,
            leading=28,
            textColor=colors.HexColor("#1F2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="CNHeading",
            parent=styles["Heading2"],
            fontName="STSong-Light",
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CNBody",
            parent=styles["BodyText"],
            fontName="STSong-Light",
            fontSize=10.5,
            leading=16,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="CNSmall",
            parent=styles["BodyText"],
            fontName="STSong-Light",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#6B7280"),
        )
    )
    return styles


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", value)
    return cleaned.replace(" ", "_")


def _paragraphs_from_markdown(text: str, style: ParagraphStyle) -> list[Paragraph]:
    if not text.strip():
        return [Paragraph("暂无内容。", style)]

    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^#+\s*", "", line)
        if line.startswith("- "):
            line = f"• {line[2:]}"
        lines.append(Paragraph(escape(line), style))
    return lines or [Paragraph("暂无内容。", style)]


def _date_range_key(start_date: str, end_date: str) -> str:
    return f"{start_date}:{end_date}"


def _date_hash(symbol: str, date_range: str) -> str:
    return hashlib.sha256(f"{symbol}:{date_range}".encode("utf-8")).hexdigest()[:16]


def _report_basename(symbol: str, date_range: str) -> str:
    return f"report_{symbol}_{_date_hash(symbol, date_range)}.pdf"


def _report_path(symbol: str, date_range: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR / _report_basename(symbol, date_range)


def _build_kline_figure(df: pd.DataFrame) -> go.Figure:
    chart_df = df.sort_values("日期").reset_index(drop=True).copy()
    chart_df["MA5"] = chart_df["收盘"].rolling(window=5).mean()
    chart_df["MA20"] = chart_df["收盘"].rolling(window=20).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=chart_df["日期"],
            open=chart_df["开盘"],
            high=chart_df["最高"],
            low=chart_df["最低"],
            close=chart_df["收盘"],
            name="K线",
            increasing_line_color="#ef5350",
            decreasing_line_color="#26a69a",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=chart_df["日期"],
            y=chart_df["MA5"],
            mode="lines",
            name="MA5",
            line=dict(color="orange", width=1.2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=chart_df["日期"],
            y=chart_df["MA20"],
            mode="lines",
            name="MA20",
            line=dict(color="#2563EB", width=1.2),
        )
    )
    fig.update_layout(
        title="股价走势（K线 + 均线）",
        template="plotly_white",
        height=360,
        margin=dict(l=30, r=30, t=50, b=30),
        legend=dict(orientation="h", y=1.02, x=0.75),
        xaxis=dict(rangeslider_visible=False),
    )
    return fig


def _build_return_figure(df: pd.DataFrame) -> go.Figure:
    chart_df = df.sort_values("日期").reset_index(drop=True).copy()
    base = chart_df["收盘"].iloc[0]
    chart_df["收益率"] = (chart_df["收盘"] - base) / base * 100

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=chart_df["日期"],
            y=chart_df["收益率"],
            mode="lines",
            name="累计收益率",
            line=dict(color="#2563EB", width=2),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.12)",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title=f"区间累计收益率（基准价 {base:.2f}）",
        template="plotly_white",
        height=300,
        margin=dict(l=30, r=30, t=50, b=30),
        xaxis=dict(rangeslider_visible=False),
        yaxis=dict(ticksuffix="%"),
    )
    return fig


def _build_forecast_figure(forecast_df: pd.DataFrame | None, stock_df: pd.DataFrame) -> go.Figure | None:
    if forecast_df is None or forecast_df.empty:
        return None

    original_df = stock_df.sort_values("日期").reset_index(drop=True)
    last_date = original_df["日期"].max()
    past_fit = forecast_df[forecast_df["ds"] <= last_date]
    future_pred = forecast_df[forecast_df["ds"] > last_date]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=original_df["日期"],
            y=original_df["收盘"],
            mode="markers",
            name="历史真实值",
            marker=dict(color="rgba(0,0,0,0.4)", size=4),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=past_fit["ds"],
            y=past_fit["yhat"],
            mode="lines",
            name="模型拟合",
            line=dict(color="rgba(37,99,235,0.6)", width=1.5, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_df["ds"],
            y=forecast_df["yhat_upper"],
            mode="lines",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_df["ds"],
            y=forecast_df["yhat_lower"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(37,99,235,0.15)",
            name="预测区间",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=future_pred["ds"],
            y=future_pred["yhat"],
            mode="lines+markers",
            name="未来预测",
            line=dict(color="#DC2626", width=2.5),
            marker=dict(size=5, color="#DC2626"),
        )
    )
    fig.update_layout(
        title="未来 7 天趋势预测",
        template="plotly_white",
        height=320,
        margin=dict(l=30, r=30, t=50, b=30),
        xaxis=dict(rangeslider_visible=False),
    )
    return fig


def _figure_to_image(fig: go.Figure, width: int, height: int) -> BytesIO:
    buffer = BytesIO(pio.to_image(fig, format="png", width=width, height=height, engine="kaleido"))
    buffer.seek(0)
    return buffer


def _append_chart_or_fallback(
    story: list,
    fig: go.Figure | None,
    width: int,
    height: int,
    styles,
    fallback_text: str,
):
    if fig is None:
        story.append(Paragraph(fallback_text, styles["CNBody"]))
        story.append(Spacer(1, 0.35 * cm))
        return

    try:
        story.append(
            Image(
                _figure_to_image(fig, width, height),
                width=17.2 * cm,
                height=(height / width) * 17.2 * cm,
            )
        )
    except Exception:
        story.append(Paragraph(fallback_text, styles["CNBody"]))
    story.append(Spacer(1, 0.35 * cm))


def _build_summary_table(stock_df: pd.DataFrame) -> Table:
    sorted_df = stock_df.sort_values("日期")
    latest = sorted_df.iloc[-1]
    first = sorted_df.iloc[0]

    total_return = (latest["收盘"] - first["收盘"]) / first["收盘"] * 100 if first["收盘"] else 0
    latest_turnover = f'{latest["换手率"]:.2f}%' if pd.notna(latest.get("换手率")) else "暂无"
    latest_volume = f'{latest["成交量"]:.0f}' if pd.notna(latest.get("成交量")) else "暂无"
    high_text = f'{stock_df["最高"].max():.2f}' if "最高" in stock_df.columns else "暂无"
    low_text = f'{stock_df["最低"].min():.2f}' if "最低" in stock_df.columns else "暂无"

    rows = [
        ["最新收盘价", f'{latest["收盘"]:.2f}'],
        ["区间涨跌幅", f"{total_return:.2f}%"],
        ["区间最高价", high_text],
        ["区间最低价", low_text],
        ["最新换手率", latest_turnover],
        ["最新成交量", latest_volume],
    ]
    table = Table(rows, colWidths=[4 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1F2937")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _build_report_pdf(
    symbol: str,
    resolved_name: str,
    start_date: str,
    end_date: str,
    stock_df: pd.DataFrame,
    news_df: pd.DataFrame | None,
    is_fallback: bool,
    forecast_df: pd.DataFrame | None,
    agent_summary: str,
) -> bytes:
    styles = _build_styles()
    story = []

    story.append(Paragraph(f"{resolved_name}({symbol}) 股票分析报告", styles["CNTitle"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            f"报告区间：{start_date} 至 {end_date}　　生成时间：{datetime.now():%Y-%m-%d %H:%M}",
            styles["CNSmall"],
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("一、基础概览", styles["CNHeading"]))
    story.append(_build_summary_table(stock_df))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("二、K 线与均线", styles["CNHeading"]))
    _append_chart_or_fallback(story, _build_kline_figure(stock_df), 1100, 520, styles, "图片暂不可用")

    story.append(Paragraph("三、区间收益率", styles["CNHeading"]))
    _append_chart_or_fallback(story, _build_return_figure(stock_df), 1100, 420, styles, "图片暂不可用")

    story.append(Paragraph("四、趋势预测", styles["CNHeading"]))
    _append_chart_or_fallback(story, _build_forecast_figure(forecast_df, stock_df), 1100, 420, styles, "图片暂不可用")

    story.append(Paragraph("五、新闻摘要", styles["CNHeading"]))
    if news_df is None or news_df.empty:
        story.append(Paragraph("暂无可用新闻数据。", styles["CNBody"]))
    else:
        title_col = "新闻标题" if "新闻标题" in news_df.columns else news_df.columns[-1]
        time_col = "发布时间" if "发布时间" in news_df.columns else None
        source_tip = "当前新闻为行业资讯回退结果。" if is_fallback else "当前新闻为个股资讯。"
        story.append(Paragraph(source_tip, styles["CNSmall"]))
        for _, row in news_df.head(6).iterrows():
            prefix = ""
            if time_col:
                try:
                    prefix = pd.to_datetime(row[time_col]).strftime("%Y-%m-%d") + " "
                except Exception:
                    prefix = ""
            story.append(Paragraph(f"• {escape(prefix + str(row[title_col]))}", styles["CNBody"]))
    story.append(Spacer(1, 0.35 * cm))

    story.append(Paragraph("六、Agent 综合结论", styles["CNHeading"]))
    story.extend(_paragraphs_from_markdown(agent_summary, styles["CNBody"]))
    story.append(Spacer(1, 0.35 * cm))

    story.append(Paragraph("七、风险提示", styles["CNHeading"]))
    story.append(
        Paragraph(
            "本报告基于历史数据、公开新闻和模型预测生成，仅用于学习与展示，不构成投资建议。",
            styles["CNBody"],
        )
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )
    doc.build(story)
    return buffer.getvalue()


def _load_cached_report(symbol: str, date_range: str) -> tuple[AIReport | None, Path]:
    path = _report_path(symbol, date_range)
    with SessionLocal() as session:
        report = session.execute(
            select(AIReport).where(AIReport.stock_code == symbol, AIReport.date_range == date_range)
        ).scalar_one_or_none()
    return report, path


def _is_created_today(created_at: datetime) -> bool:
    return created_at.date() == date.today()


def _write_report_file(path: Path, pdf_bytes: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf_bytes)


def _upsert_report_index(
    symbol: str,
    date_range: str,
    file_path: Path,
    report_json: dict,
) -> None:
    now = datetime.now()
    with SessionLocal() as session:
        report = session.execute(
            select(AIReport).where(AIReport.stock_code == symbol, AIReport.date_range == date_range)
        ).scalar_one_or_none()
        if report is None:
            session.add(
                AIReport(
                    stock_code=symbol,
                    date_range=date_range,
                    file_path=str(file_path),
                    report_json=report_json,
                    created_at=now,
                )
            )
        else:
            report.file_path = str(file_path)
            report.report_json = report_json
            report.created_at = now
        session.commit()


def get_or_create_stock_report(
    symbol: str,
    start_date: str,
    end_date: str,
    stock_name: str | None = None,
) -> tuple[bytes, str]:
    init_db()
    date_range = _date_range_key(start_date, end_date)
    cached_report, report_path = _load_cached_report(symbol, date_range)
    if cached_report and report_path.exists() and _is_created_today(cached_report.created_at):
        return report_path.read_bytes(), report_path.name

    start_value = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_value = datetime.strptime(end_date, "%Y-%m-%d").date()
    resolved_name = stock_name or get_stock_name(symbol)
    stock_df = get_stock_data(symbol, start_value, end_value)
    if stock_df is None or stock_df.empty:
        raise ValueError(f"未获取到 {symbol} 的股票数据，无法生成报告。")

    news_df, is_fallback = get_stock_news(symbol, resolved_name, limit=8)
    forecast_df = generate_forecast(stock_df, days=7)

    summary_prompt = (
        f"请基于 {resolved_name}({symbol}) 的行情、新闻和预测信息，"
        "生成一份适合放入 PDF 报告的简洁总结。要求："
        "1. 先给出核心结论；"
        "2. 再分别说明行情、新闻、预测三个方面；"
        "3. 最后给出风险提示；"
        "4. 输出控制在 6 到 10 行以内。"
    )
    agent_summary = run_agent([{"role": "user", "content": summary_prompt}])
    pdf_bytes = _build_report_pdf(
        symbol=symbol,
        resolved_name=resolved_name,
        start_date=start_date,
        end_date=end_date,
        stock_df=stock_df,
        news_df=news_df,
        is_fallback=is_fallback,
        forecast_df=forecast_df,
        agent_summary=agent_summary,
    )

    _write_report_file(report_path, pdf_bytes)
    _upsert_report_index(
        symbol=symbol,
        date_range=date_range,
        file_path=report_path,
        report_json={
            "summary": agent_summary,
            "stock_name": resolved_name,
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    return pdf_bytes, report_path.name


def cleanup_expired_reports(retention_days: int = PDF_RETENTION_DAYS) -> int:
    init_db()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed_files: list[str] = []

    for path in REPORTS_DIR.glob("*.pdf"):
        try:
            modified_at = datetime.fromtimestamp(path.stat().st_mtime)
            if modified_at < cutoff:
                path.unlink()
                removed_files.append(str(path))
        except FileNotFoundError:
            continue

    with SessionLocal() as session:
        if removed_files:
            session.execute(delete(AIReport).where(AIReport.file_path.in_(removed_files)))

        indexed_reports = session.execute(select(AIReport)).scalars().all()
        for report in indexed_reports:
            if not Path(report.file_path).exists():
                session.delete(report)
        session.commit()

    return len(removed_files)
