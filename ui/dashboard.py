import streamlit as st
import pandas as pd


def show_dashboard(df):
    """
    在主板展示数据概览和表格
    """
    if df is None or df.empty:
        st.warning("⚠️ 暂无数据，请检查股票代码或日期范围。")
        return

    # --- 1. 关键指标卡片 (KPI) ---
    # 获取最后一天的数据
    latest_data = df.iloc[-1]
    last_close = latest_data['收盘']

    # 简单的样式布局
    st.subheader("📈 数据概览")
    col1, col2, col3 = st.columns(3)
    col1.metric("最新收盘价", f"¥{last_close:.2f}")
    col2.metric("最高价 (区间)", f"¥{df['最高'].max():.2f}")
    col3.metric("最低价 (区间)", f"¥{df['最低'].min():.2f}")

    st.divider()

    # --- 2. 数据表格 (带自动翻页/滚动) ---
    st.subheader("📋 历史行情数据")

    # st.dataframe 是交互式的：
    # - width='stretch': 宽度自适应
    # - hide_index=True: 隐藏索引列，看起来更清爽
    # - height: 设置高度，数据多了会自动出现滚动条（类似翻页效果）
    st.dataframe(
        df.sort_values(by='日期', ascending=False),  # 按日期倒序，让最新的在最上面
        width='stretch',
        hide_index=True,
        height=400
    )

    # --- 3. 下载按钮 [cite: 38] ---
    # 方便用户把数据拿走
    csv = df.to_csv(index=False).encode('utf-8-sig')  # utf-8-sig 解决Excel中文乱码 [cite: 39]
    st.download_button(
        label="📥 下载数据 (CSV)",
        data=csv,
        file_name='stock_data.csv',
        mime='text/csv',
    )