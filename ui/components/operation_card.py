"""
ui/components/operation_card.py
操作卡片组件：可展开/折叠的操作面板卡片
"""

import streamlit as st


def render_section_header(title: str, icon: str = "⚙️") -> None:
    """渲染带图标的操作区标题。"""
    st.markdown(
        f"""
        <div class="op-section-header">
            <span class="op-icon">{icon}</span>
            <span class="op-title">{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_op_badge(op_name: str, color: str = "#2C3E50") -> None:
    """渲染操作名称徽章。"""
    st.markdown(
        f'<span style="background:{color};color:#fff;'
        f'padding:2px 8px;border-radius:4px;font-size:0.8em;">'
        f'{op_name}</span>',
        unsafe_allow_html=True,
    )


def render_log_entry(entry: dict, idx: int) -> None:
    """渲染单条操作历史记录。"""
    op = entry.get("op", "unknown")
    ts = entry.get("timestamp", "")
    vars_list = entry.get("vars", [])
    params = entry.get("params", {})

    vars_str = ", ".join(str(v) for v in vars_list) if vars_list else "—"
    params_str = " | ".join(f"{k}={v}" for k, v in params.items()) if params else ""

    st.markdown(
        f"""
        <div class="log-entry">
            <span class="log-idx">#{idx + 1}</span>
            <span class="log-op">{op}</span>
            <span class="log-vars" title="{vars_str}">{vars_str[:30]}{'...' if len(vars_str) > 30 else ''}</span>
            {f'<span class="log-params">{params_str}</span>' if params_str else ''}
            <span class="log-ts">{ts[:19] if ts else ''}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
