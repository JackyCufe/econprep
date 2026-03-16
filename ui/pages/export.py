"""
ui/pages/export.py
导出页（独立页面，clean.py 已内联导出区，此模块供未来扩展）
"""

import streamlit as st

from core.exporter import export_csv, export_excel, export_stata


def render_export_page() -> None:
    """独立导出页（可从侧边栏直接进入）。"""
    df = st.session_state.get("df")
    if df is None:
        st.warning("尚未加载数据，请先上传文件。")
        return

    st.markdown("## 💾 导出数据")
    fname = st.session_state.get("filename", "data")
    base_name = fname.rsplit(".", 1)[0] if "." in fname else fname

    st.markdown(f"当前数据：**{len(df):,} 行 × {len(df.columns)} 列**")

    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### CSV")
        try:
            csv_bytes = export_csv(df)
            st.download_button(
                "⬇️ 下载 CSV",
                csv_bytes,
                f"{base_name}_clean.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.caption("UTF-8 BOM 编码，Excel 中文兼容")
        except Exception as e:
            st.error(f"CSV 导出失败：{e}")

    with col2:
        st.markdown("#### Excel")
        try:
            xlsx_bytes = export_excel(df)
            st.download_button(
                "⬇️ 下载 Excel",
                xlsx_bytes,
                f"{base_name}_clean.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.caption(".xlsx 格式，使用 openpyxl")
        except Exception as e:
            st.error(f"Excel 导出失败：{e}")

    with col3:
        st.markdown("#### Stata .dta")
        try:
            dta_bytes = export_stata(df)
            st.download_button(
                "⬇️ 下载 Stata",
                dta_bytes,
                f"{base_name}_clean.dta",
                mime="application/octet-stream",
                use_container_width=True,
            )
            st.caption("使用 pyreadstat 导出")
        except ImportError as e:
            st.warning(str(e))
        except Exception as e:
            st.error(f"Stata 导出失败：{e}")
