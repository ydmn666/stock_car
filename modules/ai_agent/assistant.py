# 文件路径: modules/ai_agent/assistant.py
import streamlit as st
from openai import OpenAI
import pandas as pd

# --- 1. 初始化 DeepSeek 客户端 ---
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except:
    api_key = "sk-placeholder"

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


def get_deepseek_chat_stream(messages, temperature=1.1):
    """
    核心函数：支持多轮对话的流式调用
    新增参数: temperature (控制 AI 的发散程度，越低越稳越快)
    优化: 改为生成器模式，只输出纯文本，提升前端渲染流畅度
    """
    try:
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=True,
            temperature=temperature
        )

        # --- 🌊 流畅度优化核心 ---
        # 不直接返回 stream 对象，而是自己拆解，只把“干货”文字吐给界面
        for chunk in stream:
            # 提取增量内容
            content = chunk.choices[0].delta.content
            if content:
                yield content

    except Exception as e:
        yield f"⚠️ **AI 连接失败**: {str(e)}\n\n请检查 API Key。"


# ==========================================
# 场景 1: 侧边栏助手 (速度优化版)
# ==========================================
def render_ai_assistant_sidebar():
    """侧边栏简易助手 - 10条消息滑动窗口版"""
    with st.expander("🤖 智能选股助手", expanded=True):
        # 初始化
        if "sidebar_chat" not in st.session_state:
            st.session_state.sidebar_chat = []

        # --- 1. 新增：清空记忆按钮 (放在顶部，保持界面整洁) ---
        if st.session_state.sidebar_chat:  # 只有有聊天记录时才显示按钮
            if st.button("🗑️ 清空对话历史", use_container_width=True):
                st.session_state.sidebar_chat = []
                st.rerun()

        # --- 2. 显示历史消息 ---
        for msg in st.session_state.sidebar_chat:
            role = "user" if msg["role"] == "user" else "assistant"
            st.chat_message(role).write(msg["content"])

        # --- 3. 输入框逻辑 ---
        if prompt := st.chat_input("问代码 / 问百科...", key="sidebar_input"):
            # 用户话语存入
            st.session_state.sidebar_chat.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                system_prompt = """
                你是一个新能源行业的侧边栏助手。
                1. 你的首要任务是【查代码】：用户问公司名，你秒回 A 股代码。
                2. 你的次要任务是【简单科普】：用户问概念，你用一句话概括。
                3. 【速度第一】：回答尽量简短，不要长篇大论,除非用户要求。
                4.你也可以适当说些话引起用户兴趣，但是也不用太强调。
                """

                # --- 4. 核心逻辑：强制滑动窗口 (只取最近10条) ---
                # 无论用户聊多久，我们只取最新的 10 条消息发给 AI
                # 这样既不会报错，也能保持基本的上下文连贯
                context_messages = st.session_state.sidebar_chat[-10:]

                # 组装发送给 API 的消息体
                messages = [{"role": "system", "content": system_prompt}]
                for msg in context_messages:
                    messages.append({"role": msg["role"], "content": msg["content"]})

                # 调用 AI
                stream = get_deepseek_chat_stream(messages, temperature=0.6)
                response = st.write_stream(stream)

            # AI 回复存入
            st.session_state.sidebar_chat.append({"role": "assistant", "content": response})

# ==========================================
# 场景 2: 技术面分析 (分析师模式)
# ==========================================
def build_technical_prompt(ticker_name, df, all_data=None):
    """
    [技术面 - 开放式分析]
    """
    if df is None or df.empty:
        return None

    # --- 1. 准备客观数据 ---
    calc_df = df.copy()
    calc_df = calc_df.sort_values('日期').reset_index(drop=True)

    last_row = calc_df.iloc[-1]
    prev_row = calc_df.iloc[-2]

    ma5 = calc_df['收盘'].rolling(window=5).mean().iloc[-1]
    ma10 = calc_df['收盘'].rolling(window=10).mean().iloc[-1]
    ma20 = calc_df['收盘'].rolling(window=20).mean().iloc[-1]

    vol_ratio = last_row['成交量'] / prev_row['成交量']

    base_price = calc_df['收盘'].iloc[0]
    curr_price = last_row['收盘']
    total_return = (curr_price - base_price) / base_price * 100

    # --- 2. 准备行业对比 ---
    competitor_info = []
    if all_data:
        for name, other_df in all_data.items():
            if not other_df.empty and name != ticker_name:
                s_p = other_df['收盘'].iloc[0]
                e_p = other_df['收盘'].iloc[-1]
                ret = (e_p - s_p) / s_p * 100
                competitor_info.append(f"- {name}: 收益率 {ret:.2f}%")

    competitors_str = "\n".join(competitor_info) if competitor_info else "无其他对比数据"

    # --- 3. 构建 Prompt ---
    system_content = f"""
    你是一位拥有全球视野的资深金融分析师，尤其擅长中国新能源汽车产业链的研究。
    你需要根据用户提供的【客观交易数据】，结合你所知道的【行业背景知识】（如价格战、原材料成本、政策变化、公司基本面等），输出一份深度的分析报告。

    【分析对象】
    股票名称: {ticker_name}
    所属板块: 新能源汽车 / 锂电池 / 智能驾驶

    【技术面客观数据 (截至今日)】
    1. 价格表现:
       - 最新收盘价: {last_row['收盘']:.2f}
       - 今日涨跌幅: {last_row['涨跌幅']:.2f}%
       - 换手率: {last_row['换手率']:.2f}% (量比: {vol_ratio:.2f}倍)

    2. 均线系统:
       - MA5: {ma5:.2f}
       - MA10: {ma10:.2f}
       - MA20: {ma20:.2f}

    3. 阶段表现:
       - 区间累计收益率: {total_return:.2f}%
       - 相比起始价 ({base_price:.2f}) 的盈亏情况。

    【同行业竞品表现参考】
    {competitors_str}

    【分析要求】
    1. **不要**机械地解释指标，**要**结合行业逻辑。
    2. **要**客观犀利。如果收益率很差，直接指出风险；如果走势强劲，提示机会。
    3. 结合 K 线形态进行推演。

    请开始你的表演，输出Markdown格式，风格干练，像专业的投研报告。
    """

    return system_content


# ==========================================
# 场景 3: 趋势预测解读 (顾问模式)
# ==========================================
def build_forecast_prompt(ticker_name, forecast_df):
    """
    [预测面 - 辩证式分析]
    """
    if forecast_df is None:
        return None

    # 1. 提取数学模型数据
    future = forecast_df.tail(7)
    start_price = future.iloc[0]['yhat']
    end_price = future.iloc[-1]['yhat']
    expected_growth = (end_price - start_price) / start_price * 100

    upper = future.iloc[-1]['yhat_upper']
    lower = future.iloc[-1]['yhat_lower']
    uncertainty_range = (upper - lower) / end_price * 100

    # 2. 构建 Prompt
    system_content = f"""
    你是一位量化策略顾问。你的面前有一份由数学模型 (Prophet Time Series) 生成的股价预测报告。
    你的任务是：**向客户汇报模型结果，但同时用你的行业智慧对结果进行“现实性修正”。**

    【分析对象】: {ticker_name} (新能源板块)

    【数学模型预测数据 (未来7天)】
    - 模型预测方向: {"看涨 📈" if expected_growth > 0 else "看跌 📉"}
    - 预期理论涨幅: {expected_growth:.2f}%
    - 理论目标价位: {end_price:.2f}
    - 模型不确定性: {uncertainty_range:.1f}% 

    【你的任务】
    1. **汇报数据**: 开门见山地告诉用户，模型算出来未来一周是涨是跌。
    2. **批判性解读**: 结合基本面（如价格战、销量榜）评价预测是否靠谱。

    请输出一份“人机结合”的策略建议。
    """

    return system_content


# 文件路径: modules/ai_agent/assistant.py (替换 build_sentiment_prompt)
def build_sentiment_prompt(stock_name, news_df, price_trend_str="暂无走势数据", is_sector_news=False):
    """
    构建舆情分析 Prompt (个股 vs 宏观指数版)
    """
    if news_df.empty:
        return None

    # 1. 拼接新闻
    news_list_str = ""
    for idx, row in news_df.iterrows():
        try:
            time_str = pd.to_datetime(row['发布时间']).strftime('%Y-%m-%d')
        except:
            time_str = "近期"
        news_list_str += f"{idx + 1}. [{time_str}] {row['新闻标题']}\n"

    # 2. 角色设定
    if is_sector_news:
        # --- 场景 A: 宏观/政策新闻 (指数兜底) ---
        role_desc = f"""
        你当前正在分析股票：【{stock_name}】。
        由于该股近期缺乏直接新闻，系统为你提供了**【新能源产业指数】**的宏观资讯。
        这些资讯包含：国家政策（双碳/补贴）、原材料价格（锂电/上游）、行业整体销量数据等。

        你的任务是：**宏观传导分析**。
        请忽略新闻中可能提到的其他无关个股，重点提取**“大环境”**信息。
        思考逻辑：
        1. 政策面：是否有新的支持或退坡政策？(对全行业利好/利空)
        2. 成本面：原材料（如碳酸锂）价格波动对车企成本的影响。
        3. 结论：这些大趋势对【{stock_name}】构成的是顺风还是逆风？
        """
    else:
        # --- 场景 B: 个股专属新闻 ---
        role_desc = f"""
        你是一个敏锐的金融交易员。请根据【{stock_name}】的最新个股新闻，结合市场情绪进行分析。
        """

    # 3. 组装 Prompt
    system_content = f"""
    {role_desc}

    【关键参考：该股近期真实走势】
    👉 **{price_trend_str}**
    (注意：如果行业利好频出，但该股股价下跌，可能说明公司基本面弱于行业，评分需打折。)

    【待分析资讯】
    {news_list_str}

    【输出要求】
    1. **评分 (0-100)**: 
       - <40: 政策收紧/原材料暴涨/行业下行
       - 40-60: 平稳/无明显方向
       - >60: 政策支持/成本下降/需求旺盛
    2. **分析**: 
       - 必须明确指出**“政策”**或**“行业趋势”**对该股的具体影响逻辑。

    【输出格式】
    SCORE: [分数]
    ANALYSIS: [分析内容]
    """
    return system_content

#新闻舆情交谈
# --- 新增：生成行情摘要 ---
def get_price_trend_str(df):
    """
    将股价历史转换为一段文字摘要，供 AI 参考。
    """
    if df is None or df.empty:
        return "暂无行情数据"

    # 按时间排序
    df = df.sort_values(by='日期')
    last_close = df.iloc[-1]['收盘']
    first_close = df.iloc[0]['收盘']
    max_price = df['最高'].max()
    min_price = df['最低'].min()

    # 计算涨跌幅
    period_change = (last_close - first_close) / first_close * 100
    from_high = (last_close - max_price) / max_price * 100

    trend_str = (
        f"该股最新收盘价为 {last_close:.2f} 元。"
        f"在选定区间内，累计涨跌幅为 {period_change:.2f}%。"
        f"当前价格距离区间最高点 ({max_price:.2f} 元) 回撤了 {from_high:.2f}%，"
        f"距离区间最低点 ({min_price:.2f} 元) 反弹了 {(last_close - min_price) / min_price * 100:.2f}%。"
    )
    return trend_str


# 文件路径: modules/ai_agent/assistant.py

def build_sentiment_prompt(stock_name, news_df, price_trend_str, metrics=None, is_sector_news=False):
    """
    构建包含【新闻 + 现实行情 + 量化指标】的 Prompt
    强制 AI 基于“当下现实”进行分析
    """
    if news_df.empty:
        return None

    # 1. 拼接新闻 (只取前 10 条)
    news_list_str = ""
    for idx, row in news_df.head(10).iterrows():
        try:
            time_str = pd.to_datetime(row['发布时间']).strftime('%Y-%m-%d')
        except:
            time_str = "近期"
        news_list_str += f"- [{time_str}] {row['新闻标题']}\n"

    # 2. 动态角色设定
    source_type = "行业宏观指数（因为个股新闻不足）" if is_sector_news else "个股具体新闻"

    # 3. 构建量化指标描述 (核心修改：接收硬核指标)
    metrics_str = "暂无量化数据"
    if metrics:
        vol, sharpe, max_dd = metrics
        if vol is not None:
            metrics_str = f"""
            - 年化波动率: {vol * 100:.2f}% (数值越高越不稳定)
            - 夏普比率: {sharpe:.2f} (衡量性价比，>1为优秀)
            - 近一年最大回撤: {max_dd * 100:.2f}% (过去一年最惨跌了多少)
            """

    system_content = f"""
    你是一个华尔街资深交易员。你的任务是忽略用户可能的历史查看行为，**完全基于“当前最新”的市场数据**，对【{stock_name}】进行投资价值评估。

    【资讯来源】: {source_type}

    【硬核量化指标 (基于今日往前推一年的真实数据)】
    {metrics_str}
    (关键判断逻辑：如果最大回撤很小(<15%)，说明近期抗跌；如果波动率极大，说明风险高。)

    【当前行情快照 (最新)】
    {price_trend_str}

    【最新舆情 (News)】
    {news_list_str}

    【任务要求】
    1. **打分 (0-100)**: 
       - 0-40: 极度悲观/利空/处于高位下跌趋势。
       - 40-60: 中性/观望/多空博弈。
       - 60-100: 乐观/利好/低位反弹或强势突破。

    2. **给出“现实建议”**:
       - 必须明确指出：**“基于当前的量化指标和舆情...”**
       - 结合夏普比率和新闻判断现在是“机会”还是“陷阱”。
       - **不要**被用户可能查看的历史图表干扰，只说现在的结论。

    【输出格式】
    SCORE: [分数]
    ANALYSIS: [分析内容]
    """
    return system_content