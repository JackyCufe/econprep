"""
operations/encoder.py
虚拟变量生成：类别虚拟变量、年份虚拟变量、行业虚拟变量
"""

import pandas as pd


def create_dummies(
    df: pd.DataFrame,
    variable: str,
    drop_first: bool = True,
) -> tuple:
    """
    生成虚拟变量，默认去掉第一个（避免多重共线性）。
    新列命名：{variable}_{category}。
    返回 (新 df, 新增列名列表)。
    """
    if variable not in df.columns:
        raise KeyError(f"列不存在：{variable}")

    dummies = pd.get_dummies(
        df[variable],
        prefix=variable,
        drop_first=drop_first,
        dtype=int,
    )
    new_cols = dummies.columns.tolist()

    # 避免列名冲突
    conflict = [c for c in new_cols if c in df.columns]
    if conflict:
        raise ValueError(f"虚拟变量列名与现有列冲突：{conflict}，请先重命名相关列。")

    new_df = pd.concat([df, dummies], axis=1)
    return new_df, new_cols


def create_year_dummies(
    df: pd.DataFrame,
    time_col: str,
) -> tuple:
    """
    生成年份虚拟变量（从 time_col 提取年份）。
    新列命名：year_{yyyy}。
    返回 (新 df, 新增列名列表)。
    """
    if time_col not in df.columns:
        raise KeyError(f"列不存在：{time_col}")

    new_df = df.copy()
    try:
        years = pd.to_datetime(new_df[time_col], errors="coerce").dt.year
    except Exception:
        years = new_df[time_col].astype(str).str[:4]

    temp_col = "__year_temp__"
    new_df[temp_col] = years

    dummies = pd.get_dummies(new_df[temp_col], prefix="year", drop_first=False, dtype=int)
    new_cols = dummies.columns.tolist()
    new_df = pd.concat([new_df.drop(columns=[temp_col]), dummies], axis=1)
    return new_df, new_cols


def create_industry_dummies(
    df: pd.DataFrame,
    industry_col: str,
) -> tuple:
    """
    生成行业虚拟变量。
    新列命名：{industry_col}_{value}。
    返回 (新 df, 新增列名列表)。
    """
    if industry_col not in df.columns:
        raise KeyError(f"列不存在：{industry_col}")

    dummies = pd.get_dummies(
        df[industry_col],
        prefix=industry_col,
        drop_first=False,
        dtype=int,
    )
    new_cols = dummies.columns.tolist()

    conflict = [c for c in new_cols if c in df.columns]
    if conflict:
        raise ValueError(f"行业虚拟变量列名与现有列冲突：{conflict}")

    new_df = pd.concat([df, dummies], axis=1)
    return new_df, new_cols
