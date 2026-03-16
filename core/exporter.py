"""
core/exporter.py
数据导出模块：CSV / Excel / Stata .dta
"""

import io

import pandas as pd


def export_csv(df: pd.DataFrame) -> bytes:
    """导出为 UTF-8 BOM 编码的 CSV（Excel 中文兼容）。"""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    return buffer.getvalue().encode("utf-8-sig")


def export_excel(df: pd.DataFrame) -> bytes:
    """导出为 Excel .xlsx 格式。"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
    return buffer.getvalue()


def export_stata(df: pd.DataFrame) -> bytes:
    """
    使用 pyreadstat 导出 Stata .dta 格式。
    若 pyreadstat 未安装或失败，抛出 ImportError 并给用户友好提示。
    """
    try:
        import pyreadstat  # noqa: PLC0415
    except ImportError as e:
        raise ImportError(
            "导出 Stata .dta 需要安装 pyreadstat：pip install pyreadstat"
        ) from e

    # pyreadstat 不支持 object 列含混合类型，先转为字符串
    df_clean = df.copy()
    for col in df_clean.select_dtypes(include="object").columns:
        df_clean[col] = df_clean[col].astype(str)

    # pyreadstat 不支持列名含特殊字符，替换为下划线
    df_clean.columns = [
        col.replace(" ", "_").replace("-", "_").replace(".", "_")
        for col in df_clean.columns
    ]

    buffer = io.BytesIO()
    try:
        pyreadstat.write_dta(df_clean, buffer)
    except Exception as e:
        raise RuntimeError(f"导出 Stata 文件失败：{e}") from e

    return buffer.getvalue()
