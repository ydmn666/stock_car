# 文件路径: modules/charts/forecast_chart.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import timedelta


def render_forecast_chart(forecast_df, original_df):
    """
    绘制 Prophet 预测结果图 (交互式 + 自动聚焦)
    """
    if forecast_df is None or original_df is None:
        st.warning("⚠️ 数据量不足，无法进行准确预测")
        return

    # --- 1. 数据切割 ---
    # 找到历史数据的最后一天
    last_date = original_df['日期'].max()

    # 拆分预测表：过去(拟合) vs 未来(预测)
    # 过去的：日期 <= last_date
    past_fit = forecast_df[forecast_df['ds'] <= last_date]
    # 未来的：日期 > last_date
    future_pred = forecast_df[forecast_df['ds'] > last_date]

    fig = go.Figure()

    # --- 2. 绘制图层 (注意顺序，越后画的在越上层) ---

    # A. 历史真实值 (黑色散点) - 稍微调小透明度，做背景参考
    fig.add_trace(go.Scatter(
        x=original_df['日期'],
        y=original_df['收盘'],
        mode='markers',
        name='历史真实价',
        marker=dict(color='rgba(0,0,0,0.4)', size=4)
    ))

    # B. 历史拟合趋势 (蓝色虚线) - 告诉用户模型是怎么“理解”过去的
    fig.add_trace(go.Scatter(
        x=past_fit['ds'],
        y=past_fit['yhat'],
        mode='lines',
        name='模型拟合线',
        line=dict(color='rgba(41, 128, 185, 0.6)', width=1.5, dash='dash')
    ))

    # C. 置信区间 (阴影) - 只画未来的，或者全部画但未来的深一点
    # 这里我们画全部的置信区间，但颜色淡一点
    fig.add_trace(go.Scatter(
        x=forecast_df['ds'],
        y=forecast_df['yhat_upper'],
        mode='lines',
        line=dict(width=0),
        hoverinfo='skip',
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df['ds'],
        y=forecast_df['yhat_lower'],
        mode='lines',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(41, 128, 185, 0.15)',  # 淡淡的蓝
        name='预测置信区间'
    ))

    # D. 未来预测线 (红色实线，主角！) - 也就是你要的那 7 天
    fig.add_trace(go.Scatter(
        x=future_pred['ds'],
        y=future_pred['yhat'],
        mode='lines+markers',  # 线+点，强调每一天
        name='未来预测 (AI)',
        line=dict(color='#e74c3c', width=3),  # 鲜艳的红
        marker=dict(size=6, color='#e74c3c')
    ))

    # --- 3. 关键：分割线与默认视角 ---

    # 添加一条竖线，标记“今天”
    fig.add_vline(x=last_date, line_width=1, line_dash="dash", line_color="green")
    fig.add_annotation(
        x=last_date, y=original_df['收盘'].iloc[-1],
        text="最新收盘", showarrow=True, arrowhead=1
    )

    # 计算默认显示的日期范围：最近 60 天 + 未来 7 天
    # 这样用户一进来看到的是放大的局部，而不是整年
    zoom_start = last_date - timedelta(days=60)
    zoom_end = future_pred['ds'].max() + timedelta(days=2)

    fig.update_layout(
        title=f"股价趋势预测 (红色为未来 {len(future_pred)} 天走势)",
        yaxis_title="价格 (元)",
        height=500,
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            tickformat='%Y-%m-%d',
            range=[zoom_start, zoom_end],  # <--- 核心修改：强制缩放视角
            rangeslider_visible=True
        ),
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
    )

    st.plotly_chart(fig, width='stretch')