# 文件路径: modules/charts/comparison.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render_comparison_chart(data_dict):
    if not data_dict: return

    fig = go.Figure()
    colors = ['#FF6B6B', '#4ECDC4', '#FFE66D']  # 鲜艳对比色

    idx = 0
    for name, df in data_dict.items():
        if df.empty: continue
        df = df.sort_values('日期').reset_index(drop=True)
        base = df['收盘'].iloc[0]
        df['收益'] = (df['收盘'] - base) / base * 100

        fig.add_trace(go.Scatter(
            x=df['日期'], y=df['收益'], mode='lines', name=name,
            line=dict(width=2, color=colors[idx % 3])
        ))
        idx += 1

    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="⚔️ 收益率竞技场 (多股对比)", yaxis_title="累计收益 (%)", height=400,
        template="plotly_white", hovermode="x unified",
        xaxis=dict(tickformat='%Y年%m月%d日'),
        yaxis=dict(ticksuffix='%')
    )
    st.plotly_chart(fig, width='stretch')