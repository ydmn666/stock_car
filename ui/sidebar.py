# 文件路径: ui/sidebar.py
import streamlit as st
from datetime import datetime, timedelta
from modules.data_loader.loader import get_stock_name
# 引入新的 AI 模块
from modules.ai_agent.assistant import render_ai_assistant_sidebar

# ... (保持 NEV_HOT_STOCKS 定义不变) ...
NEV_HOT_STOCKS = {
    "比亚迪 (整车龙头)": "002594",
    "宁德时代 (动力电池)": "300750",
    "赛力斯 (华为问界)": "601127",
    "长安汽车 (深蓝/阿维塔)": "000625",
    "长城汽车 (坦克/哈弗)": "601633",
    "江淮汽车 (蔚来代工)": "600418",
    "上汽集团 (智己/飞凡)": "600104",
    "赣锋锂业 (上游锂矿)": "002460",
    "拓普集团 (特斯拉产业链)": "601689"
}


def show_sidebar():
    # 1. 渲染真实的 DeepSeek AI 助手
    # 这里的函数现在是全功能的聊天窗口了
    render_ai_assistant_sidebar()

    st.sidebar.divider()
    st.sidebar.header("🔋 新能源数据配置")

    # ... (后续所有代码保持不变，为了节省篇幅我不重复粘贴了，请确保下方代码和之前一致) ...
    # ... (从 if "selected_tickers" ... 开始的代码) ...
    if "selected_tickers" not in st.session_state:
        st.session_state.selected_tickers = [{"code": "002594", "name": "比亚迪"}]

    # --- 股票添加区 ---
    st.sidebar.subheader("➕ 添加对比标的")
    # ... (复制之前的逻辑) ...
    # === 方式A: 热门推荐 (极速优化版) ===
    st.sidebar.markdown("##### 🏛️ 热门企业推荐")
    selected_hot = st.sidebar.selectbox(
        "选择企业:",
        options=["请选择..."] + list(NEV_HOT_STOCKS.keys()),
        label_visibility="collapsed"
    )

    if st.sidebar.button("➕ 添加选中企业", key="btn_add_hot", width='stretch'):
        if selected_hot == "请选择...":
            st.sidebar.warning("⚠️ 请先在下拉框中选择一支股票")
        else:
            code = NEV_HOT_STOCKS[selected_hot]
            if len(st.session_state.selected_tickers) >= 3:
                st.sidebar.error("🚫 最多只能对比 3 支股票")
            elif any(t['code'] == code for t in st.session_state.selected_tickers):
                st.sidebar.warning("⚠️ 该股票已在列表中")
            else:
                try:
                    name = selected_hot.split(' ')[0]
                except:
                    name = selected_hot
                st.session_state.selected_tickers.append({"code": code, "name": name})
                st.rerun()

    # === 方式B: 手动输入 (缓存优化版) ===
    with st.sidebar.expander("🔎 手动查询其他代码"):
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            new_ticker = st.text_input("6位代码", placeholder="如600031", label_visibility="collapsed",
                                       key="manual_input")
        with col_btn:
            if st.button("添加", key="btn_add_manual"):
                if len(st.session_state.selected_tickers) >= 3:
                    st.sidebar.error("已达上限")
                elif len(new_ticker) == 6 and new_ticker.isdigit():
                    if any(t['code'] == new_ticker for t in st.session_state.selected_tickers):
                        st.sidebar.warning("已存在")
                    else:
                        with st.spinner("🌐 正在联网查询名称..."):
                            name = get_stock_name(new_ticker)
                        st.session_state.selected_tickers.append({"code": new_ticker, "name": name})
                        st.rerun()
                else:
                    st.sidebar.error("代码错误")

    st.sidebar.divider()

    st.sidebar.markdown(f"**已选清单 ({len(st.session_state.selected_tickers)}/3):**")
    for i, item in enumerate(st.session_state.selected_tickers):
        col_txt, col_del = st.sidebar.columns([5, 1])
        with col_txt:
            st.info(f"{item['name']}\n`{item['code']}`")
        with col_del:
            st.write("")
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.selected_tickers.pop(i)
                st.rerun()

    if not st.session_state.selected_tickers:
        st.sidebar.warning("⚠️ 请至少添加一支股票")

    st.sidebar.divider()

    st.sidebar.subheader("📅 分析周期 (全局)")
    start_date = st.sidebar.date_input("开始", value=datetime.now() - timedelta(days=365))
    end_date = st.sidebar.date_input("结束", value=datetime.now())

    disable_run = len(st.session_state.selected_tickers) == 0
    run_query = st.sidebar.button(
        "🚀 生成分析报告",
        type="primary",
        width='stretch',
        disabled=disable_run
    )

    return {
        "tickers": st.session_state.selected_tickers,
        "start_date": start_date,
        "end_date": end_date,
        "run_query": run_query
    }