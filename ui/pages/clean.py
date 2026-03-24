"""
ui/pages/clean.py
数据清洗主页：布局编排 + 历史记录 + 撤销 + 即时预览
具体操作 UI 见 clean_ops.py
"""

import datetime

import pandas as pd
import streamlit as st

from core.exporter import export_csv, export_excel, export_stata
from ui.components.operation_card import render_log_entry
from ui.components.preview import render_data_preview, render_data_stats
from ui.pages import clean_ops


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def _push_history(df_before: pd.DataFrame) -> None:
    """将当前 df 快照压入历史栈（最多保留 10 步）。"""
    history: list = st.session_state.setdefault("df_history", [])
    history.append(df_before.copy())
    if len(history) > 10:
        history.pop(0)
    st.session_state["df_history"] = history


def _log_operation(op: str, vars_list: list, params: dict) -> None:
    log: list = st.session_state.setdefault("operations_log", [])
    log.append({
        "op": op,
        "vars": vars_list,
        "params": params,
        "timestamp": datetime.datetime.now().isoformat(),
    })


def _undo() -> None:
    history: list = st.session_state.get("df_history", [])
    op_log: list = st.session_state.get("operations_log", [])
    if not history:
        st.warning("没有可撤销的操作。")
        return
    st.session_state["df"] = history.pop()
    st.session_state["df_history"] = history
    if op_log:
        op_log.pop()
    st.session_state["operations_log"] = op_log
    st.success("✅ 已撤销上一步操作。")


# ---------------------------------------------------------------------------
# 导出区
# ---------------------------------------------------------------------------

def _render_export_section(df: pd.DataFrame) -> None:
    st.markdown("---")
    st.markdown("#### 💾 导出数据")
    fname = st.session_state.get("filename", "data")
    base_name = fname.rsplit(".", 1)[0] if "." in fname else fname

    c1, c2, c3 = st.columns(3)
    with c1:
        try:
            st.download_button(
                "⬇️ CSV", export_csv(df), f"{base_name}_clean.csv",
                mime="text/csv", use_container_width=True,
            )
        except Exception as e:
            st.error(f"CSV 导出错误：{e}")
    with c2:
        try:
            st.download_button(
                "⬇️ Excel", export_excel(df), f"{base_name}_clean.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Excel 导出错误：{e}")
    with c3:
        try:
            st.download_button(
                "⬇️ Stata .dta", export_stata(df), f"{base_name}_clean.dta",
                mime="application/octet-stream", use_container_width=True,
            )
        except ImportError as e:
            st.warning(f"Stata 导出：{e}")
        except Exception as e:
            st.error(f"Stata 导出错误：{e}")


# ---------------------------------------------------------------------------
# 操作历史区
# ---------------------------------------------------------------------------

def _render_history_section() -> None:
    op_log: list = st.session_state.get("operations_log", [])
    history: list = st.session_state.get("df_history", [])

    st.markdown("#### 📜 操作历史")
    if not op_log:
        st.caption("暂无操作记录。")
    else:
        for i, entry in enumerate(reversed(op_log)):
            render_log_entry(entry, len(op_log) - 1 - i)

    if history:
        if st.button("↩️ 撤销上一步", use_container_width=True):
            _undo()
            st.rerun()

    if op_log:
        if st.button("📋 生成操作脚本", use_container_width=True):
            st.code(_generate_script(op_log), language="python")


def _generate_script(op_log: list) -> str:
    """生成可复现的 Python 操作脚本。"""
    lines = [
        "import pandas as pd",
        "from operations import winsorize, transform as tr, missing, encoder, string_clean",
        "",
        "df = pd.read_csv('your_data.csv')  # 替换为实际路径",
        "",
    ]
    _OP_TEMPLATES = {
        "winsorize": lambda e: (
            f"df, _ = winsorize.winsorize_vars(df, {e['vars']}, "
            f"{e['params'].get('lower', 0.01)}, {e['params'].get('upper', 0.99)})"
        ),
        "log_transform": lambda e: (
            f"df, _ = tr.log_transform(df, {e['vars']}, "
            f"method='{e['params'].get('method','ln')}', add_one={e['params'].get('add_one',False)})"
        ),
        "standardize": lambda e: (
            f"df, _ = tr.standardize(df, {e['vars']}, method='{e['params'].get('method','zscore')}')"
        ),
        "first_difference": lambda e: (
            f"df, _ = tr.first_difference(df, {e['vars']}, "
            f"id_col={repr(e['params'].get('id_col'))}, time_col={repr(e['params'].get('time_col'))})"
        ),
        "impute_missing": lambda e: (
            f"df, _ = missing.impute_missing(df, {e['vars']}, "
            f"method='{e['params'].get('method','fill_mean')}', id_col={repr(e['params'].get('id_col'))})"
        ),
        "interaction": lambda e: (
            f"df, _ = tr.interaction_term(df, '{e['vars'][0]}', '{e['vars'][1]}')"
            if len(e['vars']) >= 2 else "# interaction term"
        ),
        "string_clean": lambda e: (
            f"df, _ = string_clean.clean_strings(df, '{e['vars'][0]}', {e['params'].get('ops',[])})"
        ),
    }
    for entry in op_log:
        op = entry["op"]
        if op in ("lag", "lead"):
            p = entry["params"]
            lines.append(
                f"df, _ = tr.lag_lead(df, {entry['vars']}, periods={p.get('periods',1)}, "
                f"direction='{op}', id_col={repr(p.get('id_col'))}, time_col={repr(p.get('time_col'))})"
            )
        elif op in _OP_TEMPLATES:
            lines.append(_OP_TEMPLATES[op](entry))
        else:
            lines.append(f"# {op}: {entry['vars']}")
    lines.append("\ndf.to_csv('cleaned_data.csv', index=False)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主页渲染
# ---------------------------------------------------------------------------

def render_clean_page() -> None:
    """渲染清洗主页（2/3 左侧 + 1/3 右侧）。"""
    df = st.session_state.get("df")
    if df is None:
        st.warning("请先上传数据文件。")
        if st.button("← 返回上传"):
            st.session_state["page"] = "upload"
            st.rerun()
        return

    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.markdown(f"### 🧹 清洗工作台 — `{st.session_state.get('filename', '')}`")
    with top_r:
        if st.button("← 重新上传"):
            st.session_state["page"] = "upload"
            st.rerun()

    # ── 数据概览（顶部一行）
    render_data_stats(df)
    render_data_preview(df)

    st.divider()

    # ── 操作面板（横向标签页，不再用侧边竖列）
    st.markdown("#### ⚙️ 操作面板")

    tabs = st.tabs([
        "🔴 缺失值", "✂️ 缩尾", "📐 对数化", "📏 标准化",
        "⏱️ 差分/滞后", "🏷️ 虚拟变量", "🔤 字符串", "✖️ 交互项"
    ])

    with tabs[0]:
        clean_ops.op_missing(df, _push_history, _log_operation)
    with tabs[1]:
        clean_ops.op_winsorize(df, _push_history, _log_operation)
    with tabs[2]:
        clean_ops.op_log_transform(df, _push_history, _log_operation)
    with tabs[3]:
        clean_ops.op_standardize(df, _push_history, _log_operation)
    with tabs[4]:
        clean_ops.op_lag_lead(df, _push_history, _log_operation)
    with tabs[5]:
        clean_ops.op_dummies(df, _push_history, _log_operation)
    with tabs[6]:
        clean_ops.op_string_clean(df, _push_history, _log_operation)
    with tabs[7]:
        clean_ops.op_interaction(df, _push_history, _log_operation)

    st.divider()

    # ── 历史 + 导出（底部）
    col_hist, col_export = st.columns([1, 1])
    with col_hist:
        _render_history_section()
    with col_export:
        _render_export_section(df)
