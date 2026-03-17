"""
operations/transform.py
数据变换：对数化、标准化、差分、滞后/超前、交互项
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 对数化
# ---------------------------------------------------------------------------

_LOG_METHODS = {
    "ln": np.log,
    "log10": np.log10,
    "log2": np.log2,
}

_LOG_SUFFIX = {
    "ln": "_ln",
    "log10": "_log10",
    "log2": "_log2",
}


def log_transform(
    df: pd.DataFrame,
    variables: list,
    method: str = "ln",
    add_one: bool = False,
) -> tuple:
    """
    对数化：method 支持 'ln', 'log10', 'log2'。
    add_one=True 时计算 log(1+x)。
    新变量命名：{var}_ln / {var}_log10 / {var}_log2。
    返回 (新 df, 新增变量名列表)。
    """
    if method not in _LOG_METHODS:
        raise ValueError(f"不支持的对数方法：{method}，可选：{list(_LOG_METHODS)}")

    missing = [v for v in variables if v not in df.columns]
    if missing:
        raise KeyError(f"列不存在：{missing}")

    log_fn = _LOG_METHODS[method]
    suffix = _LOG_SUFFIX[method]

    new_df = df.copy()
    new_cols: list = []

    for var in variables:
        series = new_df[var].astype(float)
        values = series + 1 if add_one else series

        # 检测非正值：log 对 <=0 无定义，静默产生 NaN 会误导用户
        n_nonpositive = int((values <= 0).sum())
        if n_nonpositive > 0:
            import warnings as _w
            _w.warn(
                f"变量 '{var}' 含 {n_nonpositive} 个 ≤0 的值（{'add_one=True 后仍有' if add_one else ''}），"
                f"对数化结果将为 NaN。建议使用 add_one=True（计算 log(1+x)）或先过滤非正值。",
                UserWarning,
                stacklevel=2,
            )

        new_col = f"{var}{suffix}"
        new_df[new_col] = log_fn(values)
        new_cols.append(new_col)

    return new_df, new_cols


# ---------------------------------------------------------------------------
# 标准化
# ---------------------------------------------------------------------------

def standardize(
    df: pd.DataFrame,
    variables: list,
    method: str = "zscore",
) -> tuple:
    """
    标准化：method 支持 'zscore' | 'minmax'。
    新变量命名：{var}_zscore / {var}_minmax。
    返回 (新 df, 新增变量名列表)。
    """
    if method not in ("zscore", "minmax"):
        raise ValueError(f"不支持的标准化方法：{method}，可选：zscore, minmax")

    missing = [v for v in variables if v not in df.columns]
    if missing:
        raise KeyError(f"列不存在：{missing}")

    new_df = df.copy()
    new_cols: list = []

    for var in variables:
        series = new_df[var].astype(float)
        new_col = f"{var}_{method}"
        if method == "zscore":
            std = series.std()
            if std == 0:
                raise ValueError(f"变量 {var} 标准差为 0，无法 Z-score 标准化。")
            new_df[new_col] = (series - series.mean()) / std
        else:  # minmax
            vmin, vmax = series.min(), series.max()
            if vmin == vmax:
                raise ValueError(f"变量 {var} 最大值等于最小值，无法 Min-Max 标准化。")
            new_df[new_col] = (series - vmin) / (vmax - vmin)
        new_cols.append(new_col)

    return new_df, new_cols


# ---------------------------------------------------------------------------
# 滞后/超前
# ---------------------------------------------------------------------------

def lag_lead(
    df: pd.DataFrame,
    variables: list,
    periods: int = 1,
    direction: str = "lag",
    id_col: str = None,
    time_col: str = None,
) -> tuple:
    """
    生成滞后/超前变量。direction: 'lag' | 'lead'。
    面板数据时按 id_col 分组（需先按 time_col 排序）。
    新变量命名：{var}_L{periods} / {var}_F{periods}。
    返回 (新 df, 新增变量名列表)。
    """
    if direction not in ("lag", "lead"):
        raise ValueError(f"direction 须为 'lag' 或 'lead'，当前：{direction}")
    if periods < 1:
        raise ValueError(f"periods 须 >= 1，当前：{periods}")

    missing = [v for v in variables if v not in df.columns]
    if missing:
        raise KeyError(f"列不存在：{missing}")

    shift_n = periods if direction == "lag" else -periods
    suffix = f"_L{periods}" if direction == "lag" else f"_F{periods}"

    new_df = df.copy()
    if time_col and time_col in new_df.columns:
        new_df = new_df.sort_values(by=[id_col, time_col] if id_col else [time_col])

    new_cols: list = []
    for var in variables:
        new_col = f"{var}{suffix}"
        if id_col and id_col in new_df.columns:
            new_df[new_col] = new_df.groupby(id_col)[var].shift(shift_n)
        else:
            new_df[new_col] = new_df[var].shift(shift_n)
        new_cols.append(new_col)

    return new_df, new_cols


# ---------------------------------------------------------------------------
# 差分
# ---------------------------------------------------------------------------

def first_difference(
    df: pd.DataFrame,
    variables: list,
    id_col: str = None,
    time_col: str = None,
) -> tuple:
    """
    差分：计算 Δx_t = x_t - x_{t-1}。
    面板数据时按 id_col 分组。
    新变量命名：{var}_d1。
    返回 (新 df, 新增变量名列表)。
    """
    missing = [v for v in variables if v not in df.columns]
    if missing:
        raise KeyError(f"列不存在：{missing}")

    new_df = df.copy()
    if time_col and time_col in new_df.columns:
        new_df = new_df.sort_values(by=[id_col, time_col] if id_col else [time_col])

    new_cols: list = []
    for var in variables:
        new_col = f"{var}_d1"
        if id_col and id_col in new_df.columns:
            new_df[new_col] = new_df.groupby(id_col)[var].diff(1)
        else:
            new_df[new_col] = new_df[var].diff(1)
        new_cols.append(new_col)

    return new_df, new_cols


# ---------------------------------------------------------------------------
# 交互项
# ---------------------------------------------------------------------------

def interaction_term(
    df: pd.DataFrame,
    var1: str,
    var2: str,
) -> tuple:
    """
    生成交互项：{var1}_{var2}_inter = var1 * var2。
    返回 (新 df, 新变量名)。
    """
    for v in (var1, var2):
        if v not in df.columns:
            raise KeyError(f"列不存在：{v}")

    new_df = df.copy()
    new_col = f"{var1}_{var2}_inter"
    new_df[new_col] = new_df[var1] * new_df[var2]
    return new_df, new_col
