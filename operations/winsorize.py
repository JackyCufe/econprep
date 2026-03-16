"""
operations/winsorize.py
缩尾（Winsorize）处理：对指定变量截断极端值
"""

from typing import Union

import numpy as np
import pandas as pd


def winsorize_vars(
    df: pd.DataFrame,
    variables: list,
    lower_pct: float = 0.01,
    upper_pct: float = 0.99,
) -> tuple:
    """
    对指定变量进行缩尾处理（原地截断极端值到分位数边界）。

    返回 (新 DataFrame, 操作日志 dict)
    操作日志：{"变量名": {"lower_bound": float, "upper_bound": float, "n_clipped": int}}
    注意：永远创建新 DataFrame，不原地修改。
    """
    if not 0 <= lower_pct < upper_pct <= 1:
        raise ValueError(
            f"分位数参数无效：lower_pct={lower_pct}, upper_pct={upper_pct}，"
            "需满足 0 <= lower_pct < upper_pct <= 1"
        )

    missing_vars = [v for v in variables if v not in df.columns]
    if missing_vars:
        raise KeyError(f"列不存在：{missing_vars}")

    non_numeric = [v for v in variables if not pd.api.types.is_numeric_dtype(df[v])]
    if non_numeric:
        raise TypeError(f"以下列非数值类型，无法缩尾：{non_numeric}")

    new_df = df.copy()
    log: dict = {}

    for var in variables:
        series = new_df[var]
        lower_bound = float(series.quantile(lower_pct))
        upper_bound = float(series.quantile(upper_pct))

        original = series.copy()
        new_df[var] = series.clip(lower=lower_bound, upper=upper_bound)
        n_clipped = int(((original < lower_bound) | (original > upper_bound)).sum())

        log[var] = {
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "n_clipped": n_clipped,
        }

    return new_df, log
