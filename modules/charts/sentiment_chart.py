# 文件路径: modules/charts/sentiment_chart.py
import streamlit as st
import plotly.graph_objects as go


# --- [修改] 增加 key 参数 ---
def render_sentiment_gauge(score, key=None):
    """
    绘制情绪仪表盘
    :param score: 分数 (0-100), 如果为 None 则显示灰色空盘
    :param key: Streamlit 组件的唯一标识符 (防止重复ID报错)
    """

    # 颜色逻辑
    bar_color = "lightgray"
    if score is not None:
        if score < 40:
            bar_color = "#ff4d4f"  # 红色/恐慌
        elif score < 60:
            bar_color = "#faad14"  # 橙色/中性
        else:
            bar_color = "#52c41a"  # 绿色/贪婪

    val = score if score is not None else 0

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "市场情绪评分", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': bar_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 77, 79, 0.1)'},
                {'range': [40, 60], 'color': 'rgba(250, 173, 20, 0.1)'},
                {'range': [60, 100], 'color': 'rgba(82, 196, 26, 0.1)'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': val}
        }
    ))

    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))

    # --- [关键修改] 在这里把 key 传给 plotly_chart ---
    st.plotly_chart(fig, use_container_width=True, key=key)