"""
ui/pages/upload.py
文件上传页：上传 CSV/Excel，展示基础信息，进入清洗流程

CLS 优化策略（不依赖 st.fragment）：
  - format_tips 放在上传框上方 → 上传后内容向下扩展，上方无移位
  - metric 骨架始终渲染（空值"—"），上传后原地更新值 → 高度不变，CLS ≈ 0
  - 上传成功提示、panel_info 在 metric 下方追加 → 不影响已有元素位置
"""

import streamlit as st

from core.data_loader import detect_panel_structure, get_data_summary, load_dataframe


def _init_session_state() -> None:
    defaults = {
        "page": "upload",
        "df": None,
        "df_history": [],
        "operations_log": [],
        "filename": "",
        "panel_info": None,
        "_ep_summary": None,
        "_ep_panel_info": None,
        "_ep_df": None,
        "_ep_filename": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_upload_page() -> None:
    _init_session_state()

    st.markdown("## 🧹 EconPrep — 学术数据清洗工具")
    st.markdown("上传您的数据文件，EconPrep 将帮助您完成缩尾、对数化、缺失值处理等学术数据清洗操作。")
    st.divider()

    # ── ① 格式提示（上传框上方）─────────────────────────────────────────────
    # 关键：放在上方，上传后内容只向下增长，这里不会移位
    _render_format_tips()

    # ── ② 上传框 ─────────────────────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "上传数据文件（CSV / Excel）",
        type=["csv", "xlsx", "xls"],
        help="支持 UTF-8 / GBK 编码的 CSV，以及 .xlsx / .xls 格式",
    )

    # ── ③ metric 骨架（始终渲染）────────────────────────────────────────────
    # 无论是否上传，metric 行都存在，高度固定，上传后只是原地更新数值
    summary = st.session_state.get("_ep_summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("行数",     f"{summary['n_rows']:,}"          if summary else "—")
    c2.metric("列数",     f"{summary['n_cols']}"            if summary else "—")
    c3.metric("数值列",   f"{len(summary['numeric_cols'])}" if summary else "—")
    c4.metric("含缺失列", f"{len(summary['missing_info'])}" if summary else "—")

    # ── ④ 上传后追加的内容（在 metric 下方，不影响上方任何元素）─────────────
    if uploaded_file is not None:
        _process_upload(uploaded_file)
    elif st.session_state.get("_ep_summary"):
        # 已上传过（session 中有数据），显示持久化结果
        _show_persistent_result()


def _process_upload(uploaded_file) -> None:
    """解析新上传的文件，更新 session state，显示结果。"""
    with st.spinner("正在解析文件..."):
        try:
            file_bytes = uploaded_file.read()
            df = load_dataframe(file_bytes, uploaded_file.name)
        except (ValueError, KeyError) as e:
            st.error(f"❌ 文件解析失败：{e}")
            return

    summary = get_data_summary(df)
    panel_info = detect_panel_structure(df)

    # 更新 session（下次 rerun 时 metric 骨架原地更新）
    st.session_state["_ep_summary"] = summary
    st.session_state["_ep_panel_info"] = panel_info
    st.session_state["_ep_df"] = df
    st.session_state["_ep_filename"] = uploaded_file.name

    st.success(f"✅ 成功加载：**{uploaded_file.name}**")
    _render_extra_info(summary, panel_info, df, uploaded_file.name)


def _show_persistent_result() -> None:
    """显示 session 中已有的上传结果（rerun 后保持状态）。"""
    summary = st.session_state["_ep_summary"]
    panel_info = st.session_state["_ep_panel_info"]
    df = st.session_state["_ep_df"]
    filename = st.session_state["_ep_filename"]
    st.success(f"✅ 成功加载：**{filename}**")
    _render_extra_info(summary, panel_info, df, filename)


def _render_extra_info(summary, panel_info, df, filename) -> None:
    """渲染缺失值详情、面板识别、开始清洗按钮。"""
    if summary["missing_info"]:
        with st.expander("📋 缺失值详情"):
            for col, cnt in summary["missing_info"].items():
                pct = cnt / summary["n_rows"] * 100
                st.markdown(f"- **{col}**：{cnt:,} 个缺失（{pct:.1f}%）")

    if panel_info and (panel_info["id_col"] or panel_info["time_col"]):
        with st.expander("🔍 面板结构识别（自动）"):
            cols = st.columns(2)
            cols[0].info(f"主体列（ID）：**{panel_info['id_col'] or '未识别'}**")
            cols[1].info(f"时间列：**{panel_info['time_col'] or '未识别'}**")
            if panel_info["n_entities"] > 0:
                st.caption(f"共 {panel_info['n_entities']} 个主体 × {panel_info['n_periods']} 个时期")

    col_start, _ = st.columns([1, 3])
    with col_start:
        if st.button("🚀 开始清洗", type="primary", use_container_width=True):
            st.session_state["df"] = df
            st.session_state["df_history"] = []
            st.session_state["operations_log"] = []
            st.session_state["filename"] = filename
            st.session_state["panel_info"] = panel_info
            st.session_state["page"] = "clean"
            st.rerun()


def _render_format_tips() -> None:
    with st.expander("💡 支持的格式与编码"):
        st.markdown(
            """
            | 格式 | 扩展名 | 编码支持 |
            |------|--------|---------|
            | CSV | `.csv` | UTF-8 / GBK / GB18030 / Latin-1（自动检测） |
            | Excel | `.xlsx` | — |
            | Excel 97 | `.xls` | — |
            """
        )
