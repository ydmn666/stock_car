# 文件路径: modules/charts/return_chart.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def render_return_chart(df):
    if df is None or df.empty: return

    df = df.sort_values('日期').reset_index(drop=True)
    base = df['收盘'].iloc[0]
    df['收益率'] = (df['收盘'] - base) / base * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['日期'], y=df['收益率'], mode='lines', name='累计收益率',
        line=dict(color='#7B68EE', width=2), fill='tozeroy', fillcolor='rgba(123, 104, 238, 0.1)'
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    fig.update_layout(
        title=f"区间累计收益率 (基准: {base:.2f}元)", yaxis_title="收益率 (%)", height=350,
        template="plotly_white", hovermode="x unified",
        xaxis=dict(tickformat='%Y年%m月%d日', rangeslider_visible=False), # 无滑块
        yaxis=dict(tickformat='.2f', ticksuffix='%')
    )
    st.plotly_chart(fig, width='stretch')