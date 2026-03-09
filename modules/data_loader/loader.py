# 文件路径: modules/data_loader/loader.py
import akshare as ak
import pandas as pd
import requests
import streamlit as st
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
DB_FILE = "stock_data.db"


# --- 1. 数据库初始化 (智能修复版) ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 基础表
    c.execute('''
        CREATE TABLE IF NOT EXISTS stock_history (
            日期 TEXT, 开盘 REAL, 收盘 REAL, 最高 REAL, 最低 REAL,
            成交量 INTEGER, 成交额 REAL, 振幅 REAL, 涨跌幅 REAL, 涨跌额 REAL, 换手率 REAL,
            股票代码 TEXT, PRIMARY KEY (日期, 股票代码)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
    ''')

    # 创建历史表
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            stock_name TEXT,
            stock_code TEXT,
            visit_time_str TEXT, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # [自动修复] 检查 user_history 是否有 stock_code 列 (防止旧版数据库报错)
    try:
        c.execute("SELECT stock_code FROM user_history LIMIT 1")
    except sqlite3.OperationalError:
        try:
            c.execute("ALTER TABLE user_history ADD COLUMN stock_code TEXT")
            conn.commit()
        except:
            pass

    conn.commit()
    conn.close()


# --- 2. 用户系统逻辑 ---

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        pwd_hash = hash_password(password)
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pwd_hash))
        conn.commit()
        return True, "✅ 注册成功！请登录。"
    except sqlite3.IntegrityError:
        return False, "⚠️ 该用户名已被占用。"
    finally:
        conn.close()


def login_user(username, password):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    pwd_hash = hash_password(password)
    c.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
    user = c.fetchone()
    conn.close()
    return user is not None


# [修改] 记录历史：包含年份、日期和时间
def log_history(username, stock_name, stock_code):
    if not username or not stock_name: return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 1. 获取最近一条记录的 ID 和 代码
    c.execute("SELECT id, stock_code FROM user_history WHERE username = ? ORDER BY id DESC LIMIT 1", (username,))
    last = c.fetchone()

    # [核心修改] 增加 %Y (年份)
    current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 2. 判断逻辑
    if last and last[1] == stock_code:
        # 情况 A: 如果最近一条就是这只股票 -> 更新它的时间
        last_id = last[0]
        c.execute('''
            UPDATE user_history 
            SET visit_time_str = ?, timestamp = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (current_time_str, last_id))
        print(f"🔄 更新历史记录时间: {stock_name} -> {current_time_str}")
    else:
        # 情况 B: 如果是新股票 -> 插入新的一行
        c.execute('''
            INSERT INTO user_history (username, stock_name, stock_code, visit_time_str) 
            VALUES (?, ?, ?, ?)
        ''', (username, stock_name, stock_code, current_time_str))
        print(f"➕ 插入新历史记录: {stock_name}")

    conn.commit()
    conn.close()


# [修改] 获取历史：返回 ID 以便删除
def get_user_history(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 返回 id, name, code, time
    c.execute(
        "SELECT id, stock_name, stock_code, visit_time_str FROM user_history WHERE username = ? ORDER BY id DESC LIMIT 20",
        (username,))
    data = c.fetchall()
    conn.close()
    return data


# [新增] 删除单条历史
def delete_history_item(item_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM user_history WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# [新增] 一键清空指定用户的所有历史记录
def delete_all_user_history(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM user_history WHERE username = ?", (username,))
    conn.commit()
    conn.close()

# --- 3. 股票数据逻辑 (保持不变) ---
# ... (以下代码与之前完全一致，为节省篇幅略去，请保留原有的 get_stock_data 等函数) ...

def get_db_range(symbol):
    if not os.path.exists(DB_FILE): return None, None
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT MIN(日期), MAX(日期) FROM stock_history WHERE 股票代码 = ?", (symbol,))
        result = c.fetchone()
        conn.close()
        if result and result[0] and result[1]:
            return datetime.strptime(result[0], '%Y-%m-%d').date(), datetime.strptime(result[1], '%Y-%m-%d').date()
    except:
        pass
    return None, None


def save_to_sqlite(df, symbol):
    if df.empty: return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        data_to_insert = []
        for _, row in df.iterrows():
            date_str = row['日期'].strftime('%Y-%m-%d')
            record = (date_str, row['开盘'], row['收盘'], row['最高'], row['最低'],
                      row['成交量'], row['成交额'], row['振幅'], row['涨跌幅'], row['涨跌额'], row['换手率'], symbol)
            data_to_insert.append(record)
        sql = '''INSERT OR IGNORE INTO stock_history 
                 (日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率, 股票代码)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        c.executemany(sql, data_to_insert)
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()


def load_from_sqlite(symbol, start_date, end_date):
    conn = sqlite3.connect(DB_FILE)
    s_date, e_date = start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    query = f"SELECT * FROM stock_history WHERE 股票代码 = '{symbol}' AND 日期 >= '{s_date}' AND 日期 <= '{e_date}' ORDER BY 日期 ASC"
    try:
        df = pd.read_sql(query, conn)
        if not df.empty: df['日期'] = pd.to_datetime(df['日期'])
        return df
    except:
        return None
    finally:
        conn.close()
    return pd.DataFrame()


def get_stock_data(symbol, start_date, end_date):
    init_db()
    db_min, db_max = get_db_range(symbol)
    need_fetch = False
    if db_min is None:
        need_fetch = True
    else:
        if start_date < db_min: need_fetch = True
        if end_date > db_max: need_fetch = True

    if need_fetch:
        st.toast(f"🔄 同步数据: {symbol}...", icon="🔋")
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        try:
            df_new = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_str, end_date=end_str,
                                        adjust="qfq")
            if not df_new.empty:
                df_new['日期'] = pd.to_datetime(df_new['日期'])
                save_to_sqlite(df_new, symbol)
        except Exception as e:
            st.error(f"网络错误: {e}")

    df_final = load_from_sqlite(symbol, start_date, end_date)
    return df_final if df_final is not None else pd.DataFrame()


@st.cache_data(ttl=86400)
def get_stock_name(symbol):
    try:
        info = ak.stock_individual_info_em(symbol=symbol)
        name_row = info[info['item'] == '股票简称']
        if not name_row.empty:
            return name_row['value'].values[0]
        return symbol
    except:
        return symbol


# [核心修改]：完全使用你验证通过的逻辑，不加任何魔改
def get_stock_news(symbol, stock_name=None, limit=10):
    """
    直接调用 akshare，不进行任何预处理，保持与测试脚本一致
    """
    # 打印日志到终端（后台看）
    print(f"🔄 [Loader] 正在请求: Symbol='{symbol}', Name='{stock_name}'")

    # 1. 核心请求 (和你测试脚本完全一致)
    try:
        # 直接传，不清洗！如果 symbol 是错的，让它直接报错，这样我们才知道问题在哪
        news_df = ak.stock_news_em(symbol=symbol)

        # 2. 判空
        if news_df is None or news_df.empty:
            print(f"⚠️ [Loader] akshare 返回为空: {symbol}")
            # 如果个股没数据，尝试获取行业指数作为兜底 (保留这个是为了用户体验)
            # 但如果你只想调试比亚迪，可以暂时忽略这个 fallback 逻辑
            print(f"⚠️ 尝试获取行业兜底数据...")
            return get_sector_news_fallback(limit)  # 下面定义的辅助函数

        # 3. 排序截取
        if '发布时间' in news_df.columns:
            news_df['发布时间'] = pd.to_datetime(news_df['发布时间'])
            news_df = news_df.sort_values(by='发布时间', ascending=False)

        latest = news_df.head(limit)
        print(f"✅ [Loader] 成功获取 {len(latest)} 条新闻")
        return latest, False  # False 代表这是个股新闻

    except Exception as e:
        print(f"❌ [Loader] 发生异常: {e}")
        # 异常时也尝试兜底，避免页面崩溃
        return get_sector_news_fallback(limit)


def get_sector_news_fallback(limit):
    """辅助函数：获取行业指数新闻"""
    try:
        df = ak.stock_news_em(symbol="399976")
        if df is not None and not df.empty:
            if '发布时间' in df.columns:
                df['发布时间'] = pd.to_datetime(df['发布时间'])
                df = df.sort_values(by='发布时间', ascending=False)
            return df.head(limit), True
    except:
        pass
    return pd.DataFrame(), False