"""
ui/components/preview.py
数据预览组件：展示前 N 行，支持列名搜索过滤
"""

import pandas as pd
import streamlit as st


def render_data_preview(df: pd.DataFrame, max_rows: int = 50) -> None:
    """
    渲染数据预览区域。
    支持列名搜索过滤，展示前 max_rows 行。
    """
    if df is None or df.empty:
        st.info("暂无数据，请先上传文件。")
        return

    st.markdown("#### 📊 数据预览")

    col_search, col_info = st.columns([2, 1])
    with col_search:
        search_term = st.text_input(
            "搜索列名",
            placeholder="输入关键词过滤列...",
            key="preview_col_search",
            label_visibility="collapsed",
        )
    with col_info:
        st.caption(f"共 {len(df):,} 行 × {len(df.columns)} 列")

    # 列名过滤
    if search_term:
        filtered_cols = [
            c for c in df.columns if search_term.lower() in c.lower()
        ]
        if not filtered_cols:
            st.warning(f"未找到包含「{search_term}」的列名。")
            return
        display_df = df[filtered_cols].head(max_rows)
    else:
        display_df = df.head(max_rows)

    st.dataframe(
        display_df,
        use_container_width=True,
        height=min(400, 36 + len(display_df) * 35),
    )

    if len(df) > max_rows:
        st.caption(f"⚠️ 仅展示前 {max_rows} 行，完整数据共 {len(df):,} 行。")


def render_data_stats(df: pd.DataFrame) -> None:
    """渲染简单的数据统计卡片。"""
    if df is None or df.empty:
        return

    numeric_cols = df.select_dtypes(include="number").columns
    missing_total = int(df.isnull().sum().sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("行数", f"{len(df):,}")
    c2.metric("列数", f"{len(df.columns)}")
    c3.metric("数值列", f"{len(numeric_cols)}")
    c4.metric("缺失值", f"{missing_total:,}")
