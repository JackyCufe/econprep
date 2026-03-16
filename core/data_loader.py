"""
core/data_loader.py
数据加载模块：自动检测编码，支持 CSV/xlsx/xls，面板结构识别
"""

import io
from typing import Optional

import chardet
import pandas as pd


# ---------------------------------------------------------------------------
# 编码候选列表（按优先级）
# ---------------------------------------------------------------------------
_ENCODING_CANDIDATES = ["utf-8", "gbk", "gb18030", "latin1"]


def _try_read_csv(file_bytes: bytes) -> pd.DataFrame:
    """按候选编码逐一尝试解析 CSV，全部失败则抛出 ValueError。"""
    # 先用 chardet 猜测
    detected = chardet.detect(file_bytes)
    detected_enc = detected.get("encoding") or ""

    candidates = [detected_enc] + _ENCODING_CANDIDATES if detected_enc else _ENCODING_CANDIDATES
    # 去重保留顺序
    seen: set = set()
    unique_candidates = []
    for enc in candidates:
        key = enc.lower().replace("-", "")
        if key not in seen:
            seen.add(key)
            unique_candidates.append(enc)

    last_err: Optional[Exception] = None
    for enc in unique_candidates:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
            return df
        except (UnicodeDecodeError, Exception) as e:
            last_err = e
            continue

    raise ValueError(f"无法解析 CSV 文件，所有编码均失败。最后错误：{last_err}")


def load_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    自动检测编码，支持 CSV/xlsx/xls。
    失败时抛出 ValueError（含友好提示）。
    """
    if not file_bytes:
        raise ValueError("文件内容为空，请重新上传。")

    fname_lower = filename.lower()

    if fname_lower.endswith(".csv"):
        return _try_read_csv(file_bytes)

    if fname_lower.endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
            return df
        except Exception as e:
            raise ValueError(f"无法解析 Excel 文件：{e}") from e

    raise ValueError(
        f"不支持的文件格式：{filename}。请上传 .csv / .xlsx / .xls 文件。"
    )


# ---------------------------------------------------------------------------
# 面板结构识别
# ---------------------------------------------------------------------------

_TIME_KEYWORDS = ("year", "date", "time", "period", "month", "quarter",
                  "年", "年份", "时间", "日期", "季度")
_ID_KEYWORDS = ("id", "code", "stkcd", "firm", "entity", "company",
                "股票", "公司", "企业", "主体", "代码")


def _score_column(col: str, keywords: tuple) -> int:
    col_lower = col.lower()
    return sum(kw in col_lower for kw in keywords)


def detect_panel_structure(df: pd.DataFrame) -> dict:
    """
    尝试自动识别面板结构。
    返回 {"id_col": str|None, "time_col": str|None,
           "n_entities": int, "n_periods": int}
    """
    id_col: Optional[str] = None
    time_col: Optional[str] = None

    id_scores = {col: _score_column(col, _ID_KEYWORDS) for col in df.columns}
    time_scores = {col: _score_column(col, _TIME_KEYWORDS) for col in df.columns}

    best_id = max(id_scores, key=id_scores.get)  # type: ignore[arg-type]
    best_time = max(time_scores, key=time_scores.get)  # type: ignore[arg-type]

    if id_scores[best_id] > 0:
        id_col = best_id
    if time_scores[best_time] > 0 and best_time != best_id:
        time_col = best_time

    n_entities = int(df[id_col].nunique()) if id_col else 0
    n_periods = int(df[time_col].nunique()) if time_col else 0

    return {
        "id_col": id_col,
        "time_col": time_col,
        "n_entities": n_entities,
        "n_periods": n_periods,
    }


# ---------------------------------------------------------------------------
# 数据概况
# ---------------------------------------------------------------------------

def get_data_summary(df: pd.DataFrame) -> dict:
    """
    返回数据概况：行数、列数、数值列、字符串列、缺失值统计。
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    string_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    missing_counts = df.isnull().sum()
    missing_info = {
        col: int(missing_counts[col])
        for col in df.columns
        if missing_counts[col] > 0
    }

    return {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "numeric_cols": numeric_cols,
        "string_cols": string_cols,
        "missing_info": missing_info,
        "total_missing": int(missing_counts.sum()),
    }
