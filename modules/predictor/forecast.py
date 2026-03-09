# 文件路径: modules/predictor/forecast.py
import pandas as pd
from prophet import Prophet
import streamlit as st


def generate_forecast(df, days=7):
    """
    使用 Prophet 模型生成股价预测
    :param df: 包含 '日期' 和 '收盘' 列的 DataFrame
    :param days: 预测未来多少天
    :return: (forecast_df, model)
    """
    if df is None or df.empty or len(df) < 30:
        # 数据太少无法预测
        return None, None

    try:
        # 1. 准备 Prophet 需要的数据格式 (ds, y)
        # Prophet 要求两列：ds (时间), y (值)
        data = df[['日期', '收盘']].rename(columns={'日期': 'ds', '收盘': 'y'})

        # 确保时间格式正确
        data['ds'] = pd.to_datetime(data['ds'])

        # 2. 初始化并训练模型
        # daily_seasonality=True 强制开启日级周期（适合股票）
        # changepoint_prior_scale=0.05 灵活性参数，默认0.05，调大会更敏感
        model = Prophet(daily_seasonality=True, changepoint_prior_scale=0.05)
        model.fit(data)

        # 3. 构建未来日期表
        future = model.make_future_dataframe(periods=days)

        # 4. 预测
        forecast = model.predict(future)

        # 返回预测结果表和模型对象
        return forecast, model

    except Exception as e:
        st.error(f"模型预测出错: {str(e)}")
        return None, None