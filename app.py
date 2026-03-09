# 文件路径: app.py
import streamlit as st
import sys
import os
import pandas as pd
# 在 app.py 顶部添加导入
from modules.data_loader.loader import get_stock_news # <--- 新增
from modules.charts.sentiment_chart import render_sentiment_gauge # <--- 新增
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ui.auth import render_login_ui, render_user_header
from ui.sidebar import show_sidebar
from ui.dashboard import show_dashboard
from modules.data_loader.loader import get_stock_data, log_history
from modules.charts.kline import render_chart as render_kline, calculate_metrics
from modules.charts.return_chart import render_return_chart
from modules.charts.comparison import render_comparison_chart
from modules.predictor.forecast import generate_forecast
from modules.charts.forecast_chart import render_forecast_chart
from modules.ai_agent.assistant import get_deepseek_chat_stream, build_technical_prompt, build_forecast_prompt,get_price_trend_str,build_sentiment_prompt
st.set_page_config(page_title="新能源车企股票分析系统", layout="wide", page_icon="⚡")


def main_system():
    # 1. 顶部用户栏
    render_user_header()

    st.title("⚡ 新能源汽车股票分析系统")

    # 初始化 Session State
    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False
    if "chat_history_tech" not in st.session_state:
        st.session_state.chat_history_tech = []
    if "chat_history_pred" not in st.session_state:
        st.session_state.chat_history_pred = []
    if "current_ticker" not in st.session_state:
        st.session_state.current_ticker = None

    # 2. 侧边栏
    user_input = show_sidebar()
    tickers = user_input["tickers"]

    # === 关键修改：点击“生成分析报告”时，批量记录历史 ===
    if user_input["run_query"]:
        st.session_state.analysis_started = True

        # 如果已登录，记录所有选中的股票
        if st.session_state.get("is_logged_in") and st.session_state.get("current_user"):
            for t in tickers:
                # 记录：用户名, 股票名, 股票代码
                log_history(st.session_state.current_user, t['name'], t['code'])

    if st.session_state.analysis_started and tickers:
        all_data = {}
        for t in tickers:
            df = get_stock_data(t['code'], user_input['start_date'], user_input['end_date'])
            if df is not None and not df.empty:
                all_data[t['name']] = df

        if not all_data:
            st.error("❌ 未获取到数据。")
            return

        # --- 模块1：行业对标 ---
        st.subheader("🏁 行业对标 (收益率 PK)")
        render_comparison_chart(all_data)
        st.divider()

        # --- 模块2：单股深度分析 ---
        st.subheader("🔍 深度透视")

        options = list(all_data.keys())
        target_name = st.selectbox("选择要分析的企业:", options, key="stock_selector")

        # 切换股票时仅清空 AI 聊天历史 (不再记录历史，因为上面已经批量记过了)
        if st.session_state.current_ticker != target_name:
            st.session_state.current_ticker = target_name
            st.session_state.chat_history_tech = []
            st.session_state.chat_history_pred = []

            # [新增] 切换股票时，清空舆情分析结果
            st.session_state.sentiment_score = None
            st.session_state.sentiment_text = ""

        with st.spinner(f"⚡ 正在加载 {target_name} 的数据..."):
            target_df = all_data[target_name]

            # [修改] 扩展为 4 个 Tab
            t1, t2, t3, t4 = st.tabs(["📊 基础数据", "📈 技术 & AI", "🔮 趋势预测", "📰 舆情 & 情绪"])

            # ==========================================
            # Tab 1: 基础数据
            # ==========================================
            with t1:
                show_dashboard(target_df)

            # ==========================================
            # Tab 2: 技术 & AI
            # ==========================================
            with t2:
                col_chart, col_ai = st.columns([7, 3])
                with col_chart:
                    render_kline(target_df)
                    st.markdown("---")
                    render_return_chart(target_df)

                with col_ai:
                    st.markdown("### 🤖 DeepSeek 技术分析师")
                    chat_container = st.container(height=500, border=True)

                    if not st.session_state.chat_history_tech:
                        chat_container.info("👋 点击下方按钮，开始 AI 全面分析。")
                        if chat_container.button("🧠 生成技术分析报告", key="btn_init_tech", width='stretch'):
                            sys_prompt = build_technical_prompt(target_name, target_df, all_data)
                            if sys_prompt:
                                st.session_state.chat_history_tech = [
                                    {"role": "system", "content": sys_prompt},
                                    {"role": "user", "content": "请综合分析当前的K线形态、收益率表现及行业对比情况。"}
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
                                    stream = get_deepseek_chat_stream(st.session_state.chat_history_tech)
                                    response = st.write_stream(stream)
                                    if response:
                                        st.session_state.chat_history_tech.append(
                                            {"role": "assistant", "content": response})
                                        st.rerun()

                        if prompt := st.chat_input("追问技术形态...", key="input_tech"):
                            st.session_state.chat_history_tech.append({"role": "user", "content": prompt})
                            st.rerun()

                        if chat_container.button("🔄 重新分析", key="reset_tech"):
                            st.session_state.chat_history_tech = []
                            st.rerun()

            # ==========================================
            # Tab 3: 趋势预测
            # ==========================================
            with t3:
                col_pred_chart, col_pred_ai = st.columns([7, 3])
                with col_pred_chart:
                    forecast_df, model = generate_forecast(target_df, days=7)
                    render_forecast_chart(forecast_df, target_df)

                with col_pred_ai:
                    st.markdown("### 🔮 DeepSeek 趋势顾问")
                    pred_container = st.container(height=500, border=True)

                    if not st.session_state.chat_history_pred:
                        pred_container.info("👋 Prophet 模型已运行完毕。")
                        if pred_container.button("🧠 解读未来趋势", key="btn_init_pred", width='stretch'):
                            sys_prompt = build_forecast_prompt(target_name, forecast_df)
                            if sys_prompt:
                                st.session_state.chat_history_pred = [
                                    {"role": "system", "content": sys_prompt},
                                    {"role": "user", "content": "请解读这份预测结果。"}
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
                                    stream = get_deepseek_chat_stream(st.session_state.chat_history_pred)
                                    response = st.write_stream(stream)
                                    if response:
                                        st.session_state.chat_history_pred.append(
                                            {"role": "assistant", "content": response})
                                        st.rerun()

                        if prompt := st.chat_input("追问趋势风险...", key="input_pred"):
                            st.session_state.chat_history_pred.append({"role": "user", "content": prompt})
                            st.rerun()

                        if pred_container.button("🔄 重新解读", key="reset_pred"):
                            st.session_state.chat_history_pred = []
                            st.rerun()

            # ==========================================
            # Tab 4: 舆情 & 情绪 (完整修复版)
            # ==========================================
            with t4:
                col_news_ai, col_news_raw = st.columns([4, 6])

                # 1. 获取目标代码 (防止报错)
                target_code = next((item['code'] for item in tickers if item['name'] == target_name), None)
                if not target_code:
                    st.error("❌ 错误: 未能获取到股票代码")
                    st.stop()

                # 2. 获取新闻数据
                with st.spinner(f"正在全网抓取 {target_name} ({target_code}) 的新闻..."):
                    news_df, is_fallback = get_stock_news(symbol=target_code, stock_name=target_name, limit=10)

                # --- 右侧：新闻列表 (保持不变) ---
                with col_news_raw:
                    if is_fallback:
                        st.warning(f"⚠️ 未找到 {target_name} 的个股新闻，以下是行业资讯：")
                    else:
                        st.success(f"📰 获取成功：{target_name} 个股资讯")

                    if news_df is not None and not news_df.empty:
                        # 格式化时间
                        display_df = news_df.copy()
                        if '发布时间' in display_df.columns:
                            display_df['发布时间'] = display_df['发布时间'].dt.strftime('%m-%d %H:%M')

                        st.dataframe(
                            display_df[['发布时间', '新闻标题']],
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    else:
                        st.error("❌ 数据为空：接口虽然运行了，但没返回内容。")

                # --- 左侧：AI 分析 (核心修复部分) ---
                with col_news_ai:
                    st.subheader("🤖 AI 舆情分析")

                    # A. 初始化状态
                    if "sentiment_score" not in st.session_state: st.session_state.sentiment_score = None
                    if "sentiment_text" not in st.session_state: st.session_state.sentiment_text = ""

                    # 只有当有新闻时才显示
                    if not news_df.empty:

                        # B. 静态仪表盘 (防止重复ID报错，加上 key="gauge_static")
                        render_sentiment_gauge(st.session_state.sentiment_score, key="gauge_static")

                        # C. 分析按钮
                        if st.button("▶️ 开始 AI 分析", type="primary", use_container_width=True):

                            # --- 1. 强制获取“最近一年”的真实数据 ---
                            real_trend_desc = "暂无行情数据"
                            year_metrics = None

                            try:
                                from modules.ai_agent.assistant import get_price_trend_str
                                from datetime import datetime, timedelta

                                # 锁定时间窗口：今天往前推 365 天
                                end_d = datetime.now().date()
                                start_d = end_d - timedelta(days=365)

                                with st.spinner("🔄 正在校准 AI 基准数据..."):
                                    real_time_df = get_stock_data(target_code, start_d, end_d)

                                if real_time_df is not None and not real_time_df.empty:
                                    # 计算“现实”的量化指标
                                    year_metrics = calculate_metrics(real_time_df)
                                    # 生成“现实”的行情描述
                                    real_trend_desc = get_price_trend_str(real_time_df)
                            except Exception as e:
                                print(f"数据准备报错: {e}")

                            # --- 2. 构建 Prompt ---
                            from modules.ai_agent.assistant import build_sentiment_prompt

                            prompt = build_sentiment_prompt(
                                stock_name=target_name,
                                news_df=news_df,
                                price_trend_str=real_trend_desc,
                                metrics=year_metrics,
                                is_sector_news=is_fallback
                            )

                            if prompt:
                                messages = [{"role": "system", "content": prompt}]
                                st.session_state.sentiment_text = ""  # 清空旧内容
                                placeholder = st.empty()
                                full_resp = ""
                                stream = get_deepseek_chat_stream(messages, temperature=0.6)

                                import re
                                found_score = False

                                for chunk in stream:
                                    full_resp += chunk

                                    # 实时抓取分数并刷新仪表盘 (Key=dynamic)
                                    if not found_score:
                                        match = re.search(r"SCORE:\s*(\d+)", full_resp)
                                        if match:
                                            score = int(match.group(1))
                                            st.session_state.sentiment_score = score
                                            found_score = True
                                            render_sentiment_gauge(score, key="gauge_dynamic")

                                    clean_text = re.sub(r"SCORE:\s*\d+", "", full_resp).strip()
                                    placeholder.markdown(clean_text)
                                    st.session_state.sentiment_text = clean_text  # 保存到 Session State

                                st.rerun()  # <--- 刷新页面

                        # D. [关键修复] 结果展示区
                        # 这个 if 必须在 button 的外面！
                        # 这样刷新页面后，button 变成了 False，但这里依然会执行，文字就不会消失了。
                        if st.session_state.sentiment_text:
                            st.markdown("---")
                            st.markdown("### 📋 分析报告")
                            st.markdown(st.session_state.sentiment_text)

                    else:
                        st.info("📡 等待新闻数据加载...")



def main():
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False

    if not st.session_state.is_logged_in:
        render_login_ui()
    else:
        main_system()


if __name__ == "__main__":
    main()