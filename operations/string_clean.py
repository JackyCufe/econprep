"""
operations/string_clean.py
字符串清洗：去空白、大小写转换、去标点/数字、正则替换
"""

import re
import string

import pandas as pd


_SUPPORTED_OPS = ("strip", "lower", "upper", "remove_punctuation", "remove_digits")


def _apply_single_op(series: pd.Series, op: str) -> pd.Series:
    """对 Series 执行单个字符串操作。"""
    if op == "strip":
        return series.str.strip()
    if op == "lower":
        return series.str.lower()
    if op == "upper":
        return series.str.upper()
    if op == "remove_punctuation":
        punct_pattern = f"[{re.escape(string.punctuation)}]"
        return series.str.replace(punct_pattern, "", regex=True)
    if op == "remove_digits":
        return series.str.replace(r"\d", "", regex=True)
    raise ValueError(f"不支持的字符串操作：{op}，可选：{list(_SUPPORTED_OPS)}")


def clean_strings(
    df: pd.DataFrame,
    variable: str,
    operations: list,
) -> tuple:
    """
    对指定字符串列执行一系列清洗操作。
    operations 可包含：strip, lower, upper, remove_punctuation, remove_digits。
    返回 (新 df, 修改的行数)。
    """
    if variable not in df.columns:
        raise KeyError(f"列不存在：{variable}")

    invalid_ops = [op for op in operations if op not in _SUPPORTED_OPS]
    if invalid_ops:
        raise ValueError(f"不支持的操作：{invalid_ops}，可选：{list(_SUPPORTED_OPS)}")

    new_df = df.copy()
    original_series = new_df[variable].astype(str)
    processed = original_series.copy()

    for op in operations:
        processed = _apply_single_op(processed, op)

    new_df[variable] = processed
    changed_rows = int((original_series != processed).sum())
    return new_df, changed_rows


def regex_replace(
    df: pd.DataFrame,
    variable: str,
    pattern: str,
    replacement: str,
) -> tuple:
    """
    对指定列执行正则替换。
    返回 (新 df, 修改的行数)。
    """
    if variable not in df.columns:
        raise KeyError(f"列不存在：{variable}")

    try:
        re.compile(pattern)
    except re.error as e:
        raise ValueError(f"正则表达式无效：{pattern}，错误：{e}") from e

    new_df = df.copy()
    original_series = new_df[variable].astype(str)
    new_series = original_series.str.replace(pattern, replacement, regex=True)
    new_df[variable] = new_series
    changed_rows = int((original_series != new_series).sum())
    return new_df, changed_rows
