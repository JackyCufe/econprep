"""
ui/pages/upload.py
文件上传页：上传 CSV/Excel，展示基础信息，进入清洗流程
"""

import streamlit as st

from core.data_loader import detect_panel_structure, get_data_summary, load_dataframe


def _init_session_state() -> None:
    """初始化 session state 默认值。"""
    defaults = {
        "page": "upload",
        "df": None,
        "df_history": [],
        "operations_log": [],
        "filename": "",
        "panel_info": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_upload_page() -> None:
    """渲染文件上传页。"""
    _init_session_state()

    # 注入 CSS：结果区预留最小高度，防止上传后内容从 0 高度硬跳出（减少 CLS）
    st.markdown(
        """
        <style>
        .ep-result-area { min-height: 200px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## 🧹 EconPrep — 学术数据清洗工具")
    st.markdown(
        "上传您的数据文件，EconPrep 将帮助您完成缩尾、对数化、缺失值处理等学术数据清洗操作。"
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "上传数据文件（CSV / Excel）",
        type=["csv", "xlsx", "xls"],
        help="支持 UTF-8 / GBK 编码的 CSV，以及 .xlsx / .xls 格式",
    )

    # 固定高度区域：空状态显示虚线占位框，防止上传后内容从 0 高度跳出（减少 CLS）
    with st.container():
        if uploaded_file is not None:
            _handle_upload(uploaded_file)
        else:
            st.markdown(
                """
                <div style="min-height:340px; display:flex; align-items:center;
                            justify-content:center; color:#ced4da;
                            border:2px dashed #dee2e6; border-radius:8px;
                            margin:1rem 0; flex-direction:column; gap:8px;">
                    <div style="font-size:2rem">📂</div>
                    <div style="font-size:0.9rem">上传文件后，此处显示数据概况</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    _render_format_tips()


def _handle_upload(uploaded_file) -> None:
    """处理上传文件：解析、展示概况、进入清洗页。"""
    with st.spinner("正在解析文件..."):
        try:
            file_bytes = uploaded_file.read()
            df = load_dataframe(file_bytes, uploaded_file.name)
        except (ValueError, KeyError) as e:
            st.error(f"❌ 文件解析失败：{e}")
            return

    summary = get_data_summary(df)
    panel_info = detect_panel_structure(df)

    st.success(f"✅ 成功加载：**{uploaded_file.name}**")

    _render_summary_cards(summary)
    _render_panel_info(panel_info)

    col_start, _ = st.columns([1, 3])
    with col_start:
        if st.button("🚀 开始清洗", type="primary", use_container_width=True):
            st.session_state["df"] = df
            st.session_state["df_history"] = []
            st.session_state["operations_log"] = []
            st.session_state["filename"] = uploaded_file.name
            st.session_state["panel_info"] = panel_info
            st.session_state["page"] = "clean"
            st.rerun()


def _render_summary_cards(summary: dict) -> None:
    """渲染数据概况指标卡片。"""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("行数", f"{summary['n_rows']:,}")
    c2.metric("列数", f"{summary['n_cols']}")
    c3.metric("数值列", f"{len(summary['numeric_cols'])}")
    c4.metric("含缺失列", f"{len(summary['missing_info'])}")

    if summary["missing_info"]:
        with st.expander("📋 缺失值详情"):
            for col, cnt in summary["missing_info"].items():
                pct = cnt / summary["n_rows"] * 100
                st.markdown(f"- **{col}**：{cnt:,} 个缺失（{pct:.1f}%）")


def _render_panel_info(panel_info: dict) -> None:
    """渲染面板结构识别结果。"""
    if panel_info["id_col"] or panel_info["time_col"]:
        with st.expander("🔍 面板结构识别（自动）"):
            cols = st.columns(2)
            cols[0].info(f"主体列（ID）：**{panel_info['id_col'] or '未识别'}**")
            cols[1].info(f"时间列：**{panel_info['time_col'] or '未识别'}**")
            if panel_info["n_entities"] > 0:
                st.caption(
                    f"共 {panel_info['n_entities']} 个主体 × "
                    f"{panel_info['n_periods']} 个时期"
                )


def _render_format_tips() -> None:
    """渲染格式提示。"""
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
