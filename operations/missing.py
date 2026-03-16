"""
operations/missing.py
缺失值处理：多种填充/删除策略，支持面板数据分组操作
"""

import pandas as pd


_VALID_METHODS = (
    "drop_row",
    "fill_mean",
    "fill_median",
    "fill_zero",
    "ffill",
    "bfill",
)


def impute_missing(
    df: pd.DataFrame,
    variables: list,
    method: str,
    id_col: str = None,
) -> tuple:
    """
    缺失值处理。

    method:
        "drop_row"   - 删除含缺失值的行（作用于整个 df，只看选中变量）
        "fill_mean"  - 填充均值
        "fill_median"- 填充中位数
        "fill_zero"  - 填充 0
        "ffill"      - 向前填充（面板数据按 id_col 分组）
        "bfill"      - 向后填充（面板数据按 id_col 分组）

    面板数据时 ffill/bfill 按 id_col 分组。
    返回 (新 df, 操作日志 dict)。
    """
    if method not in _VALID_METHODS:
        raise ValueError(
            f"不支持的缺失值处理方法：{method}，可选：{list(_VALID_METHODS)}"
        )

    missing_vars = [v for v in variables if v not in df.columns]
    if missing_vars:
        raise KeyError(f"列不存在：{missing_vars}")

    new_df = df.copy()
    log: dict = {}

    for var in variables:
        before_missing = int(new_df[var].isnull().sum())
        log[var] = {"before_missing": before_missing}

        if before_missing == 0:
            log[var]["action"] = "无缺失值，跳过"
            continue

        if method == "drop_row":
            new_df = new_df.dropna(subset=[var])
        elif method == "fill_mean":
            fill_val = new_df[var].mean()
            new_df[var] = new_df[var].fillna(fill_val)
            log[var]["fill_value"] = float(fill_val)
        elif method == "fill_median":
            fill_val = new_df[var].median()
            new_df[var] = new_df[var].fillna(fill_val)
            log[var]["fill_value"] = float(fill_val)
        elif method == "fill_zero":
            new_df[var] = new_df[var].fillna(0)
            log[var]["fill_value"] = 0
        elif method in ("ffill", "bfill"):
            new_df = _apply_fill(new_df, var, method, id_col)

        after_missing = int(new_df[var].isnull().sum())
        log[var]["after_missing"] = after_missing
        log[var]["rows_affected"] = before_missing - after_missing

    return new_df, log


def _apply_fill(
    df: pd.DataFrame,
    var: str,
    method: str,
    id_col: str = None,
) -> pd.DataFrame:
    """执行 ffill / bfill，面板数据时按 id_col 分组。"""
    if id_col and id_col in df.columns:
        df[var] = (
            df.groupby(id_col)[var]
            .transform(lambda s: s.ffill() if method == "ffill" else s.bfill())
        )
    else:
        df[var] = df[var].ffill() if method == "ffill" else df[var].bfill()
    return df
