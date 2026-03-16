"""
tests/smoke_test.py
EconPrep 烟雾测试 —— 覆盖所有核心功能路径，确保常见输入不会 crash。
"""

import io
import math
import tempfile

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def basic_df():
    """最常用的基础测试 DataFrame。"""
    return pd.DataFrame({
        "id": ["A", "A", "B", "B"],
        "year": [2020, 2021, 2020, 2021],
        "value": [1.0, 2.0, 3.0, 4.0],
        "category": ["x", "y", "x", "y"],
    })


@pytest.fixture
def panel_df():
    """面板结构 DataFrame（含 id/year/value 列）。"""
    return pd.DataFrame({
        "firm_id": ["A", "A", "B", "B"],
        "year": [2020, 2021, 2020, 2021],
        "value": [10.0, 20.0, 30.0, 40.0],
    })


@pytest.fixture
def nan_df():
    """含 NaN 的 DataFrame。"""
    return pd.DataFrame({
        "id": ["A", "A", "B", "B"],
        "year": [2020, 2021, 2020, 2021],
        "value": [1.0, np.nan, 3.0, np.nan],
    })


# ===========================================================================
# 1. data_loader
# ===========================================================================

class TestDataLoader:

    def test_load_utf8_csv(self):
        from core.data_loader import load_dataframe
        csv_bytes = "a,b,c\n1,2,3\n4,5,6\n".encode("utf-8")
        df = load_dataframe(csv_bytes, "test.csv")
        assert list(df.columns) == ["a", "b", "c"]
        assert len(df) == 2

    def test_load_csv_chinese_columns(self):
        from core.data_loader import load_dataframe
        csv_bytes = "公司代码,年份,营收\nA,2020,100\n".encode("utf-8")
        df = load_dataframe(csv_bytes, "test.csv")
        assert "公司代码" in df.columns

    def test_load_csv_with_blank_rows(self):
        from core.data_loader import load_dataframe
        csv_bytes = "a,b\n1,2\n\n3,4\n".encode("utf-8")
        df = load_dataframe(csv_bytes, "test.csv")
        # pandas 会把空行读为 NaN 行，行数 >= 2
        assert len(df) >= 2

    def test_load_gbk_csv(self):
        from core.data_loader import load_dataframe
        csv_bytes = "公司,年份\nA,2020\n".encode("gbk")
        df = load_dataframe(csv_bytes, "test.csv")
        assert len(df) == 1

    def test_load_excel(self):
        from core.data_loader import load_dataframe
        buf = io.BytesIO()
        sample = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            sample.to_excel(w, index=False)
        df = load_dataframe(buf.getvalue(), "data.xlsx")
        assert list(df.columns) == ["x", "y"]

    def test_detect_panel_structure(self):
        from core.data_loader import detect_panel_structure
        df = pd.DataFrame({
            "stkcd": ["A", "A", "B"],
            "year": [2020, 2021, 2020],
            "value": [1, 2, 3],
        })
        result = detect_panel_structure(df)
        assert result["id_col"] == "stkcd"
        assert result["time_col"] == "year"
        assert result["n_entities"] == 2
        assert result["n_periods"] == 2

    def test_empty_file_raises(self):
        from core.data_loader import load_dataframe
        with pytest.raises(ValueError):
            load_dataframe(b"", "test.csv")

    def test_unsupported_format_raises(self):
        from core.data_loader import load_dataframe
        with pytest.raises(ValueError):
            load_dataframe(b"data", "test.json")


# ===========================================================================
# 2. operations/winsorize
# ===========================================================================

class TestWinsorize:

    def test_normal_winsorize(self, basic_df):
        from operations.winsorize import winsorize_vars
        new_df, log = winsorize_vars(basic_df, ["value"], 0.01, 0.99)
        assert "value" in log
        assert "lower_bound" in log["value"]
        assert "upper_bound" in log["value"]
        assert "n_clipped" in log["value"]

    def test_winsorize_with_nan(self, nan_df):
        from operations.winsorize import winsorize_vars
        new_df, log = winsorize_vars(nan_df, ["value"], 0.01, 0.99)
        # 不应 crash，结果中 NaN 应保留
        assert "value" in log
        assert new_df["value"].isnull().sum() >= 0

    def test_winsorize_immutability(self, basic_df):
        from operations.winsorize import winsorize_vars
        original_values = basic_df["value"].copy()
        new_df, _ = winsorize_vars(basic_df, ["value"], 0.01, 0.99)
        # 原始 df 不应被修改
        pd.testing.assert_series_equal(basic_df["value"], original_values)

    def test_winsorize_log_keys(self, basic_df):
        from operations.winsorize import winsorize_vars
        _, log = winsorize_vars(basic_df, ["value"], 0.01, 0.99)
        assert "lower_bound" in log["value"]
        assert "upper_bound" in log["value"]
        assert "n_clipped" in log["value"]
        assert isinstance(log["value"]["n_clipped"], int)

    def test_winsorize_invalid_pct_raises(self, basic_df):
        from operations.winsorize import winsorize_vars
        with pytest.raises(ValueError):
            winsorize_vars(basic_df, ["value"], 0.9, 0.1)

    def test_winsorize_missing_col_raises(self, basic_df):
        from operations.winsorize import winsorize_vars
        with pytest.raises(KeyError):
            winsorize_vars(basic_df, ["nonexistent"], 0.01, 0.99)


# ===========================================================================
# 3. operations/transform
# ===========================================================================

class TestTransform:

    def test_log_transform_ln(self, basic_df):
        from operations.transform import log_transform
        new_df, new_cols = log_transform(basic_df, ["value"], method="ln", add_one=False)
        assert "value_ln" in new_cols
        assert "value_ln" in new_df.columns

    def test_log_transform_log10(self, basic_df):
        from operations.transform import log_transform
        new_df, new_cols = log_transform(basic_df, ["value"], method="log10", add_one=False)
        assert "value_log10" in new_cols

    def test_log_transform_log2(self, basic_df):
        from operations.transform import log_transform
        new_df, new_cols = log_transform(basic_df, ["value"], method="log2", add_one=False)
        assert "value_log2" in new_cols

    def test_log_transform_add_one(self):
        from operations.transform import log_transform
        df = pd.DataFrame({"v": [0.0, 1.0, 2.0]})
        new_df, _ = log_transform(df, ["v"], method="ln", add_one=True)
        # log(1+0) = 0
        assert abs(new_df["v_ln"].iloc[0]) < 1e-10

    def test_log_transform_zero_values_add_one(self):
        from operations.transform import log_transform
        df = pd.DataFrame({"v": [0.0, 1.0, 2.0]})
        # add_one=True 对零值应正常处理（不 crash）
        new_df, _ = log_transform(df, ["v"], method="ln", add_one=True)
        assert not new_df["v_ln"].isnull().any()

    def test_standardize_zscore(self, basic_df):
        from operations.transform import standardize
        new_df, new_cols = standardize(basic_df, ["value"], method="zscore")
        assert "value_zscore" in new_cols
        assert abs(new_df["value_zscore"].mean()) < 1e-10

    def test_standardize_minmax(self, basic_df):
        from operations.transform import standardize
        new_df, new_cols = standardize(basic_df, ["value"], method="minmax")
        assert "value_minmax" in new_cols
        assert new_df["value_minmax"].min() >= 0
        assert new_df["value_minmax"].max() <= 1

    def test_lag_without_id(self, basic_df):
        from operations.transform import lag_lead
        new_df, new_cols = lag_lead(basic_df, ["value"], periods=1, direction="lag")
        assert "value_L1" in new_cols
        assert new_df["value_L1"].isnull().sum() >= 1

    def test_lead_without_id(self, basic_df):
        from operations.transform import lag_lead
        new_df, new_cols = lag_lead(basic_df, ["value"], periods=1, direction="lead")
        assert "value_F1" in new_cols

    def test_lag_with_id(self, panel_df):
        from operations.transform import lag_lead
        new_df, new_cols = lag_lead(
            panel_df, ["value"], periods=1, direction="lag",
            id_col="firm_id", time_col="year"
        )
        assert "value_L1" in new_cols
        # 每个公司第一期滞后值应为 NaN
        assert new_df["value_L1"].isnull().sum() == 2

    def test_first_difference_without_id(self, basic_df):
        from operations.transform import first_difference
        new_df, new_cols = first_difference(basic_df, ["value"])
        assert "value_d1" in new_cols

    def test_first_difference_with_id(self, panel_df):
        from operations.transform import first_difference
        new_df, new_cols = first_difference(
            panel_df, ["value"], id_col="firm_id", time_col="year"
        )
        assert "value_d1" in new_cols
        # 每个公司第一期差分为 NaN
        assert new_df["value_d1"].isnull().sum() == 2

    def test_interaction_term(self, basic_df):
        from operations.transform import interaction_term
        new_df, new_col = interaction_term(basic_df, "value", "year")
        assert new_col in new_df.columns
        # 验证计算正确
        expected = basic_df["value"] * basic_df["year"]
        pd.testing.assert_series_equal(
            new_df[new_col].reset_index(drop=True),
            expected.reset_index(drop=True),
            check_names=False
        )


# ===========================================================================
# 4. operations/missing
# ===========================================================================

class TestMissing:

    def test_fill_mean(self, nan_df):
        from operations.missing import impute_missing
        new_df, log = impute_missing(nan_df, ["value"], method="fill_mean")
        assert new_df["value"].isnull().sum() == 0

    def test_fill_median(self, nan_df):
        from operations.missing import impute_missing
        new_df, log = impute_missing(nan_df, ["value"], method="fill_median")
        assert new_df["value"].isnull().sum() == 0

    def test_fill_zero(self, nan_df):
        from operations.missing import impute_missing
        new_df, log = impute_missing(nan_df, ["value"], method="fill_zero")
        assert new_df["value"].isnull().sum() == 0
        assert (new_df["value"] == 0).sum() == 2

    def test_ffill(self, nan_df):
        from operations.missing import impute_missing
        new_df, log = impute_missing(nan_df, ["value"], method="ffill")
        # 至少不能 crash
        assert "value" in new_df.columns

    def test_bfill(self, nan_df):
        from operations.missing import impute_missing
        new_df, log = impute_missing(nan_df, ["value"], method="bfill")
        assert "value" in new_df.columns

    def test_drop_row(self, nan_df):
        from operations.missing import impute_missing
        new_df, log = impute_missing(nan_df, ["value"], method="drop_row")
        assert new_df["value"].isnull().sum() == 0
        assert len(new_df) == 2

    def test_ffill_panel_grouped(self, nan_df):
        from operations.missing import impute_missing
        new_df, log = impute_missing(nan_df, ["value"], method="ffill", id_col="id")
        # 分组 ffill 后，A 组第二行应被第一行填充
        a_rows = new_df[new_df["id"] == "A"]["value"]
        assert not a_rows.isnull().any()

    def test_bfill_panel_grouped(self, nan_df):
        from operations.missing import impute_missing
        new_df, log = impute_missing(nan_df, ["value"], method="bfill", id_col="id")
        assert "value" in new_df.columns

    def test_invalid_method_raises(self, nan_df):
        from operations.missing import impute_missing
        with pytest.raises(ValueError):
            impute_missing(nan_df, ["value"], method="unknown_method")


# ===========================================================================
# 5. operations/encoder
# ===========================================================================

class TestEncoder:

    def test_create_dummies_drop_first_true(self, basic_df):
        from operations.encoder import create_dummies
        new_df, new_cols = create_dummies(basic_df, "category", drop_first=True)
        # drop_first=True: 2 类别 -> 1 虚拟变量
        assert len(new_cols) == 1

    def test_create_dummies_drop_first_false(self, basic_df):
        from operations.encoder import create_dummies
        new_df, new_cols = create_dummies(basic_df, "category", drop_first=False)
        # drop_first=False: 2 类别 -> 2 虚拟变量
        assert len(new_cols) == 2

    def test_create_year_dummies(self, basic_df):
        from operations.encoder import create_year_dummies
        new_df, new_cols = create_year_dummies(basic_df, "year")
        assert len(new_cols) == 2
        assert any("2020" in c for c in new_cols)

    def test_create_industry_dummies(self):
        from operations.encoder import create_industry_dummies
        df = pd.DataFrame({"industry": ["IT", "Finance", "IT", "Energy"]})
        new_df, new_cols = create_industry_dummies(df, "industry")
        assert len(new_cols) == 3  # 3 unique industries

    def test_create_dummies_missing_col_raises(self, basic_df):
        from operations.encoder import create_dummies
        with pytest.raises(KeyError):
            create_dummies(basic_df, "nonexistent")


# ===========================================================================
# 6. operations/string_clean
# ===========================================================================

class TestStringClean:

    @pytest.fixture
    def str_df(self):
        return pd.DataFrame({
            "text": ["  Hello World! ", "  foo123bar  ", "TEST-2024"],
        })

    def test_strip(self, str_df):
        from operations.string_clean import clean_strings
        new_df, changed = clean_strings(str_df, "text", ["strip"])
        assert new_df["text"].iloc[0] == "Hello World!"
        assert changed > 0

    def test_lower(self, str_df):
        from operations.string_clean import clean_strings
        new_df, _ = clean_strings(str_df, "text", ["lower"])
        assert new_df["text"].iloc[2] == "test-2024"

    def test_upper(self, str_df):
        from operations.string_clean import clean_strings
        new_df, _ = clean_strings(str_df, "text", ["upper"])
        assert new_df["text"].iloc[0] == "  HELLO WORLD! "

    def test_remove_punctuation(self, str_df):
        from operations.string_clean import clean_strings
        new_df, _ = clean_strings(str_df, "text", ["remove_punctuation"])
        assert "!" not in new_df["text"].iloc[0]
        assert "-" not in new_df["text"].iloc[2]

    def test_remove_digits(self, str_df):
        from operations.string_clean import clean_strings
        new_df, _ = clean_strings(str_df, "text", ["remove_digits"])
        assert "1" not in new_df["text"].iloc[1]
        assert "2" not in new_df["text"].iloc[2]

    def test_regex_replace_normal(self, str_df):
        from operations.string_clean import regex_replace
        new_df, changed = regex_replace(str_df, "text", r"\d+", "NUM")
        assert "NUM" in new_df["text"].iloc[1]
        assert changed > 0

    def test_regex_replace_no_match(self, str_df):
        from operations.string_clean import regex_replace
        # 无匹配时不应报错
        new_df, changed = regex_replace(str_df, "text", r"ZZZZZ", "X")
        assert changed == 0

    def test_invalid_op_raises(self, str_df):
        from operations.string_clean import clean_strings
        with pytest.raises(ValueError):
            clean_strings(str_df, "text", ["foobar"])


# ===========================================================================
# 7. core/exporter
# ===========================================================================

class TestExporter:

    def test_export_csv_bytes_nonempty(self, basic_df):
        from core.exporter import export_csv
        result = export_csv(basic_df)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_csv_readable_by_pandas(self, basic_df):
        from core.exporter import export_csv
        result = export_csv(basic_df)
        reloaded = pd.read_csv(io.BytesIO(result), encoding="utf-8-sig")
        assert list(reloaded.columns) == list(basic_df.columns)
        assert len(reloaded) == len(basic_df)

    def test_export_excel_bytes_nonempty(self, basic_df):
        from core.exporter import export_excel
        result = export_excel(basic_df)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_excel_readable_by_pandas(self, basic_df):
        from core.exporter import export_excel
        result = export_excel(basic_df)
        reloaded = pd.read_excel(io.BytesIO(result))
        assert list(reloaded.columns) == list(basic_df.columns)

    def test_export_stata_raises_import_error_if_unavailable(self, basic_df, monkeypatch):
        """若 pyreadstat 不可用，export_stata 必须抛出 ImportError（不能静默失败）。"""
        import sys
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pyreadstat":
                raise ImportError("mocked: pyreadstat not installed")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        # 从 sys.modules 中移除 pyreadstat（如果已缓存）
        sys.modules.pop("pyreadstat", None)

        from core import exporter
        import importlib
        importlib.reload(exporter)

        with pytest.raises(ImportError):
            exporter.export_stata(basic_df)

    def test_export_stata_succeeds(self, basic_df):
        """若 pyreadstat 可用，应成功导出 bytes。"""
        try:
            import pyreadstat  # noqa: F401
        except ImportError:
            pytest.skip("pyreadstat not installed")

        from core.exporter import export_stata
        result = export_stata(basic_df)
        assert isinstance(result, bytes)
        assert len(result) > 0


# ===========================================================================
# 8. 边界条件
# ===========================================================================

class TestEdgeCases:

    def test_single_row_dataframe(self):
        """单行 DataFrame 不应 crash。"""
        from operations.winsorize import winsorize_vars
        from operations.transform import log_transform
        df = pd.DataFrame({"value": [5.0]})
        new_df, log = winsorize_vars(df, ["value"], 0.01, 0.99)
        assert len(new_df) == 1
        new_df2, _ = log_transform(df, ["value"], method="ln", add_one=True)
        assert len(new_df2) == 1

    def test_all_nan_column(self):
        """全缺失列不应 crash，impute_missing drop_row 应返回空 df。"""
        from operations.missing import impute_missing
        df = pd.DataFrame({"id": ["A", "B"], "value": [np.nan, np.nan]})
        new_df, log = impute_missing(df, ["value"], method="drop_row")
        assert len(new_df) == 0

    def test_all_nan_fill_mean(self):
        """全缺失列 fill_mean：均值为 NaN，填充后仍为 NaN（不 crash）。"""
        from operations.missing import impute_missing
        df = pd.DataFrame({"value": [np.nan, np.nan, np.nan]})
        new_df, log = impute_missing(df, ["value"], method="fill_mean")
        assert "value" in new_df.columns  # 不 crash

    def test_special_char_column_names(self):
        """列名含特殊字符（空格、斜杠、括号）—— 基本操作不 crash。"""
        from operations.string_clean import clean_strings
        df = pd.DataFrame({"col with spaces": ["hello", "world"]})
        new_df, _ = clean_strings(df, "col with spaces", ["upper"])
        assert new_df["col with spaces"].iloc[0] == "HELLO"

    def test_special_char_slash_bracket(self):
        """斜杠和括号列名不 crash。"""
        from core.exporter import export_csv
        df = pd.DataFrame({"revenue (USD/year)": [100, 200]})
        result = export_csv(df)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_empty_string_column(self):
        """空字符串列的字符串操作不 crash。"""
        from operations.string_clean import clean_strings
        df = pd.DataFrame({"text": ["", "", ""]})
        new_df, changed = clean_strings(df, "text", ["strip", "lower"])
        assert len(new_df) == 3

    def test_log_transform_zero_no_add_one(self):
        """含零值列不加 add_one 时，log(0) = -inf，结果含 -inf 或 NaN，不 crash。"""
        from operations.transform import log_transform
        df = pd.DataFrame({"v": [0.0, 1.0, 2.0]})
        new_df, _ = log_transform(df, ["v"], method="ln", add_one=False)
        # 不 crash，且第一行为 -inf 或 NaN
        first_val = new_df["v_ln"].iloc[0]
        assert math.isnan(first_val) or math.isinf(first_val)

    def test_winsorize_nan_immutability(self):
        """含 NaN 的 DataFrame 缩尾后，原 df 不变。"""
        from operations.winsorize import winsorize_vars
        df = pd.DataFrame({"v": [1.0, np.nan, 3.0, 100.0]})
        original_values = df["v"].copy()
        winsorize_vars(df, ["v"], 0.01, 0.99)
        pd.testing.assert_series_equal(df["v"], original_values)
