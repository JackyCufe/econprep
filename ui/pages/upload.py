"""
ui/pages/upload.py
文件上传页：上传 CSV/Excel，展示基础信息，进入清洗流程

CLS 优化策略：
  - format_tips 移到 file_uploader 上方，上传后结果只向下扩展，无已有元素移位
  - summary_cards 始终预渲染（空值状态），上传后原地更新，高度不变 → CLS ≈ 0
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
        # 用于稳定 metric 卡片的状态
        "_summary": None,
        "_panel_info": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_upload_page() -> None:
    _init_session_state()

    st.markdown("## 🧹 EconPrep — 学术数据清洗工具")
    st.markdown("上传您的数据文件，EconPrep 将帮助您完成缩尾、对数化、缺失值处理等学术数据清洗操作。")
    st.divider()

    # ── 格式提示放在上传框上方 ────────────────────────────────────────────────
    # 原因：上传后结果区向下增长，上方元素不移位 → CLS 从 0.12 → ~0
    _render_format_tips()

    st.markdown("#### 📤 上传数据文件")

    # ── metric 骨架：始终预渲染，上传后原地更新值，高度完全不变 ───────────────
    summary = st.session_state.get("_summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("行数",    f"{summary['n_rows']:,}"              if summary else "—")
    c2.metric("列数",    f"{summary['n_cols']}"                if summary else "—")
    c3.metric("数值列",  f"{len(summary['numeric_cols'])}"     if summary else "—")
    c4.metric("含缺失列",f"{len(summary['missing_info'])}"     if summary else "—")

    # ── 上传组件（fragment 局部刷新）─────────────────────────────────────────
    @st.fragment
    def _upload_fragment():
        uploaded_file = st.file_uploader(
            "支持 CSV / Excel（拖拽或点击）",
            type=["csv", "xlsx", "xls"],
            help="支持 UTF-8 / GBK / GB18030 编码的 CSV，以及 .xlsx / .xls",
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            _handle_upload(uploaded_file)

    _upload_fragment()


def _handle_upload(uploaded_file) -> None:
    with st.spinner("正在解析文件..."):
        try:
            file_bytes = uploaded_file.read()
            df = load_dataframe(file_bytes, uploaded_file.name)
        except (ValueError, KeyError) as e:
            st.error(f"❌ 文件解析失败：{e}")
            return

    summary = get_data_summary(df)
    panel_info = detect_panel_structure(df)

    # 写入 session，触发全页刷新时 metric 骨架会原地更新
    st.session_state["_summary"] = summary
    st.session_state["_panel_info"] = panel_info

    st.success(f"✅ 成功加载：**{uploaded_file.name}**")

    # 缺失值详情（数量少时展示）
    if summary["missing_info"]:
        with st.expander("📋 缺失值详情"):
            for col, cnt in summary["missing_info"].items():
                pct = cnt / summary["n_rows"] * 100
                st.markdown(f"- **{col}**：{cnt:,} 个缺失（{pct:.1f}%）")

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
            st.rerun(scope="app")


def _render_panel_info(panel_info: dict) -> None:
    if panel_info["id_col"] or panel_info["time_col"]:
        with st.expander("🔍 面板结构识别（自动）"):
            cols = st.columns(2)
            cols[0].info(f"主体列（ID）：**{panel_info['id_col'] or '未识别'}**")
            cols[1].info(f"时间列：**{panel_info['time_col'] or '未识别'}**")
            if panel_info["n_entities"] > 0:
                st.caption(f"共 {panel_info['n_entities']} 个主体 × {panel_info['n_periods']} 个时期")


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
