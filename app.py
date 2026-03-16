"""
app.py
EconPrep - 学术数据清洗工具
Streamlit 入口：页面路由（upload → clean）
"""

import os
import sys

import streamlit as st

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(__file__))

# ---- 页面配置（必须在所有 st 调用之前）----
st.set_page_config(
    page_title="EconPrep - 学术数据清洗工具",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- 加载全局样式 ----
_CSS_PATH = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(_CSS_PATH):
    with open(_CSS_PATH, encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

# ---- 延迟导入页面（避免循环依赖）----
from ui.pages.clean import render_clean_page  # noqa: E402
from ui.pages.upload import render_upload_page  # noqa: E402


def _init_page_state() -> None:
    """初始化页面状态。"""
    if "page" not in st.session_state:
        st.session_state["page"] = "upload"


def main() -> None:
    """主路由函数。"""
    _init_page_state()

    current_page = st.session_state.get("page", "upload")

    if current_page == "upload":
        render_upload_page()
    elif current_page == "clean":
        render_clean_page()
    else:
        st.error(f"未知页面：{current_page}")
        st.session_state["page"] = "upload"
        st.rerun()


if __name__ == "__main__" or True:
    main()
