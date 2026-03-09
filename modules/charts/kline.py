# 文件路径: modules/charts/kline.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def calculate_metrics(df):
    """
    计算量化指标：夏普比率、最大回撤、波动率
    基于传入的 df（即用户选择的时间段）进行计算
    """
    # [新增] 安全检查：如果数据少于 5 行，计算统计指标没有意义，直接返回 None
    # 避免用户只选了 1-2 天导致报错
    if df is None or len(df) < 5:
        return None, None, None

    # 确保数据按日期升序
    df_sorted = df.sort_values('日期').reset_index(drop=True)

    # 计算日收益率
    df_sorted['pct_change'] = df_sorted['收盘'].pct_change()

    # 1. 年化波动率 (Assuming 252 trading days)
    # 即使只选了1个月，也要乘以 sqrt(252) 转化为“年化”标准，才能和其他股票对比
    volatility = df_sorted['pct_change'].std() * np.sqrt(252)

    # 2. 夏普比率 (Sharpe Ratio)
    # 假设无风险利率为 2% (0.02)
    risk_free_rate = 0.02

    # 计算区间内的平均日收益，并年化
    mean_daily_return = df_sorted['pct_change'].mean()
    annualized_return = mean_daily_return * 252

    if volatility == 0 or np.isnan(volatility):
        sharpe_ratio = 0
    else:
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility

    # 3. 最大回撤 (Max Drawdown)
    # 仅计算用户“选中这段时间”内的最大坑
    roll_max = df_sorted['收盘'].cummax()
    daily_drawdown = df_sorted['收盘'] / roll_max - 1.0
    max_drawdown = daily_drawdown.min()

    return volatility, sharpe_ratio, max_drawdown


def render_chart(df):
    if df is None or df.empty:
        st.warning("⚠️ 暂无数据，无法绘制 K 线图")
        return

    # 预处理数据
    df = df.sort_values('日期').reset_index(drop=True)
    df['MA5'] = df['收盘'].rolling(window=5).mean()
    df['MA20'] = df['收盘'].rolling(window=20).mean()

    # --- [修改] 计算并展示量化指标 ---
    vol, sharpe, max_dd = calculate_metrics(df)

    # 只有当指标计算成功（数据够多）时才显示指标卡片
    if vol is not None:
        st.markdown("##### 📊 风险与收益指标 (基于选中时段)")
        k1, k2, k3 = st.columns(3)

        with k1:
            st.metric(
                label="夏普比率 (Sharpe)",
                value=f"{sharpe:.2f}",
                help="> 1 为优秀。衡量每承担一单位风险能获得多少超额收益。"
            )

        with k2:
            st.metric(
                label="最大回撤 (Max Drawdown)",
                value=f"{max_dd * 100:.2f}%",
                help="选定周期内，买入后可能出现的最糟糕跌幅。"
            )

        with k3:
            st.metric(
                label="年化波动率 (Volatility)",
                value=f"{vol * 100:.2f}%",
                help="数值越大，股票走势越上蹿下跳，风险越高。"
            )
    else:
        # 如果天数太少，给用户一个温和的提示
        st.info("💡 提示：当前选定的时间范围太短（少于5个交易日），无法计算有效风险指标。请尝试拉长日期范围。")

    st.divider()  # 分割线
    # ----------------------------------

    # 下面是画图逻辑（保持不变）
    fig = go.Figure()
    # K线
    fig.add_trace(go.Candlestick(
        x=df['日期'], open=df['开盘'], high=df['最高'], low=df['最低'], close=df['收盘'],
        name='K线', increasing_line_color='#ef5350', decreasing_line_color='#26a69a'
    ))
    # 均线
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA5'], mode='lines', name='MA5', line=dict(color='orange', width=1)))
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA20'], mode='lines', name='MA20', line=dict(color='blue', width=1)))

    fig.update_layout(
        title="股价走势 (K线 + 均线)",
        yaxis_title="价格 (元)",
        height=500,  # 稍微调高一点高度
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            tickformat='%Y-%m-%d',
            rangeslider_visible=True
        ),
        legend=dict(orientation="h", y=1.02, x=0.8)
    )
    st.plotly_chart(fig, width='stretch')