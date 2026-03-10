import streamlit as st
import time

from frontend.services.api_client import (
    delete_all_user_history,
    delete_history_item,
    get_user_history,
    login_user,
    register_user,
)


@st.dialog("退出确认")
def show_logout_dialog():
    st.write("确定要退出当前账号吗？")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认退出", type="primary", use_container_width=True):
            st.session_state.is_logged_in = False
            st.session_state.enter_system_clicked = False
            st.session_state.current_user = None
            st.rerun()
    with col2:
        if st.button("取消", use_container_width=True):
            st.rerun()


@st.dialog("清空确认")
def show_clear_history_dialog(username):
    st.warning("确定要清空所有历史记录吗？\n\n此操作无法撤销。")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认清空", type="primary", use_container_width=True):
            delete_all_user_history(username)
            st.rerun()
    with col2:
        if st.button("取消", use_container_width=True):
            st.rerun()


def render_user_header():
    c_main, c_user = st.columns([7, 3])
    with c_user:
        with st.container(border=True):
            cols = st.columns([2, 1, 1])

            with cols[0]:
                st.markdown(f"**用户 {st.session_state.get('current_user', 'Guest')}**")

            with cols[1]:
                with st.popover("历史", help="浏览历史"):
                    st.markdown("#### 查阅记录")
                    user = st.session_state.get("current_user")
                    if user:
                        history = get_user_history(user)
                        if history:
                            if st.button("清空全部", type="primary", use_container_width=True):
                                show_clear_history_dialog(user)

                            st.divider()

                            for item in history:
                                rec_id, name, code, t_str = item
                                h_col1, h_col2 = st.columns([5, 1])
                                with h_col1:
                                    st.text(f"[{t_str}] {name}")
                                with h_col2:
                                    if st.button("删", key=f"del_hist_{rec_id}", help="删除此条"):
                                        delete_history_item(rec_id)
                                        st.rerun()
                        else:
                            st.caption("暂无记录")

            with cols[2]:
                if st.button("退出", help="退出登录"):
                    show_logout_dialog()


def set_bg_hack_url():
    st.markdown(
        """
         <style>
         .stApp {
             background-color: #000428;
             background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 900'%3E%3Cdefs%3E%3ClinearGradient id='a' x1='0' x2='0' y1='1' y2='0'%3E%3Cstop offset='0' stop-color='%230FF'/%3E%3Cstop offset='1' stop-color='%23CF6'/%3E%3C/linearGradient%3E%3ClinearGradient id='b' x1='0' x2='0' y1='0' y2='1'%3E%3Cstop offset='0' stop-color='%23004e92'/%3E%3Cstop offset='1' stop-color='%23000428'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cg fill='%23FFF' fill-opacity='0' stroke-miterlimit='10'%3E%3Cg stroke='url(%23a)' stroke-width='2'%3E%3Cpath transform='translate(0 0)' d='M1409 581 1450.35 511 1490 581z'%3E%3CanimateTransform attributeName='transform' type='rotate' from='0 1450 550' to='360 1450 550' dur='21s' repeatCount='indefinite'/%3E%3C/path%3E%3Cpath transform='translate(0 0)' d='M1155 536 1196.35 466 1236 536z'%3E%3CanimateTransform attributeName='transform' type='rotate' from='0 1200 500' to='360 1200 500' dur='22s' repeatCount='indefinite'/%3E%3C/path%3E%3Cpath transform='translate(0 0)' d='M1634 624 1675.35 554 1715 624z'%3E%3CanimateTransform attributeName='transform' type='rotate' from='0 1680 600' to='360 1680 600' dur='23s' repeatCount='indefinite'/%3E%3C/path%3E%3C/g%3E%3C/g%3E%3Cpath fill='url(%23b)' d='M0 0h1600v900H0z'/%3E%3Cpath fill='%23004e92' fill-opacity='0.4' d='M0 900h1600V450C1600 450 1200 350 800 450 400 550 0 450 0 450v450z'%3E%3Canimate attributeName='d' dur='10s' repeatCount='indefinite' values='M0 900h1600V450C1600 450 1200 350 800 450 400 550 0 450 0 450v450z;M0 900h1600V450C1600 450 1200 550 800 450 400 350 0 450 0 450v450z;M0 900h1600V450C1600 450 1200 350 800 450 400 550 0 450 0 450v450z'/%3E%3C/path%3E%3Cpath fill='%2300d2ff' fill-opacity='0.2' d='M0 900h1600V500C1600 500 1200 600 800 500 400 400 0 500 0 500v400z'%3E%3Canimate attributeName='d' dur='15s' repeatCount='indefinite' values='M0 900h1600V500C1600 500 1200 600 800 500 400 400 0 500 0 500v400z;M0 900h1600V500C1600 500 1200 400 800 500 400 600 0 500 0 500v400z;M0 900h1600V500C1600 500 1200 600 800 500 400 400 0 500 0 500v400z'/%3E%3C/path%3E%3C/svg%3E");
             background-attachment: fixed;
             background-size: cover;
         }
         .cover-title { font-size: 100px; text-align: center; color: #FFFFFF !important; text-shadow: 0 0 30px #FFD700, 0 0 60px #FFA500; animation: float 3s ease-in-out infinite; }
         @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0px); } }
         .cover-subtitle { font-size: 32px; text-align: center; color: #E0E0E0 !important; font-weight: bold; letter-spacing: 2px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
         div[data-testid="stVerticalBlockBorderWrapper"] { background: rgba(0, 20, 60, 0.7); backdrop-filter: blur(12px); border-radius: 20px; padding: 30px; border: 1px solid rgba(0, 210, 255, 0.3); box-shadow: 0 10px 40px rgba(0,0,0,0.5); }
         .stTextInput input { background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid rgba(255, 255, 255, 0.5); font-weight: bold; }
         .stTextInput input:focus { border-color: #00d2ff !important; box-shadow: 0 0 10px rgba(0, 210, 255, 0.8); }
         .stTextInput label { color: #FFFFFF !important; font-size: 16px; }
         button[kind="primary"] { background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%); border: none; box-shadow: 0 0 15px rgba(0, 210, 255, 0.5); font-weight: bold; font-size: 16px; color: white !important; }
         button { color: white !important; }
         </style>
         """,
        unsafe_allow_html=True,
    )


def render_login_ui():
    set_bg_hack_url()
    if "enter_system_clicked" not in st.session_state:
        st.session_state.enter_system_clicked = False

    if not st.session_state.enter_system_clicked:
        st.write("")
        st.write("")
        st.write("")
        st.markdown("<div class='cover-title'>🚗</div>", unsafe_allow_html=True)
        st.markdown("<div class='cover-subtitle'>新能源车股票分析系统</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            st.write("")
            st.write("")
            st.write("")
            if st.button("点击进入系统", type="primary", use_container_width=True):
                st.session_state.enter_system_clicked = True
                st.rerun()
        return

    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c2:
        st.write("")
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; color: white;'>身份验证</h3>", unsafe_allow_html=True)
            tab_login, tab_reg = st.tabs(["登录账号", "注册新用户"])
            with tab_login:
                st.write("")
                username = st.text_input("账号", key="login_u")
                password = st.text_input("密码", type="password", key="login_p")
                st.write("")
                if st.button("立即登录", use_container_width=True, type="primary"):
                    if login_user(username, password):
                        st.success("欢迎回来，正在跳转...")
                        st.session_state.is_logged_in = True
                        st.session_state.current_user = username
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("账号或密码错误")
            with tab_reg:
                st.write("")
                new_user = st.text_input("设置账号", key="reg_u")
                new_pwd = st.text_input("设置密码", type="password", key="reg_p")
                st.write("")
                if st.button("注册并登录", use_container_width=True, type="primary"):
                    if new_user and new_pwd:
                        success, msg = register_user(new_user, new_pwd)
                        if success:
                            st.success(msg)
                            st.session_state.is_logged_in = True
                            st.session_state.current_user = new_user
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("请填写完整信息")
