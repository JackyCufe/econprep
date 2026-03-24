"""
ui/pages/clean_ops.py
清洗操作 UI 辅助函数（由 clean.py 调用）
每个操作的参数配置区 + 执行逻辑
"""

import streamlit as st

from operations import encoder, missing, string_clean, winsorize
from operations import transform as tr


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------

def _numeric_cols(df) -> list:
    return df.select_dtypes(include="number").columns.tolist()


def _string_cols(df) -> list:
    return df.select_dtypes(include=["object", "string"]).columns.tolist()


def _all_cols(df) -> list:
    return df.columns.tolist()


def _panel_defaults(df) -> tuple:
    panel_info = st.session_state.get("panel_info", {}) or {}
    return panel_info.get("id_col"), panel_info.get("time_col")


# ---------------------------------------------------------------------------
# 各操作 UI
# ---------------------------------------------------------------------------

def op_winsorize(df, push_history, log_op) -> None:
    st.markdown("**缩尾（Winsorize）**")
    vars_sel = st.multiselect("选择变量", _numeric_cols(df), key="wz_vars")
    c1, c2 = st.columns(2)
    lower = c1.number_input("下分位数", 0.0, 0.49, 0.01, 0.01, key="wz_lower")
    upper = c2.number_input("上分位数", 0.51, 1.0, 0.99, 0.01, key="wz_upper")
    if st.button("执行缩尾", key="btn_wz") and vars_sel:
        try:
            push_history(df)
            new_df, log = winsorize.winsorize_vars(df, vars_sel, lower, upper)
            st.session_state["df"] = new_df
            log_op("winsorize", vars_sel, {"lower": lower, "upper": upper})
            st.success(f"缩尾完成：{', '.join(vars_sel)}")
            for var, info in log.items():
                st.caption(
                    f"  {var}: [{info['lower_bound']:.4f}, {info['upper_bound']:.4f}],"
                    f" 截断 {info['n_clipped']} 行"
                )
            st.rerun()
        except Exception as e:
            st.session_state["df_history"].pop()
            st.error(f"缩尾失败：{e}")


def op_log_transform(df, push_history, log_op) -> None:
    st.markdown("**对数化**")
    vars_sel = st.multiselect("选择变量", _numeric_cols(df), key="log_vars")
    c1, c2 = st.columns(2)
    method = c1.selectbox("对数方法", ["ln", "log10", "log2"], key="log_method")
    add_one = c2.checkbox("log(1+x)", value=False, key="log_addone")
    if st.button("执行对数化", key="btn_log") and vars_sel:
        try:
            push_history(df)
            new_df, new_cols = tr.log_transform(df, vars_sel, method, add_one)
            st.session_state["df"] = new_df
            log_op("log_transform", vars_sel, {"method": method, "add_one": add_one})
            st.success(f"对数化完成，新增列：{', '.join(new_cols)}")
            st.rerun()
        except Exception as e:
            st.session_state["df_history"].pop()
            st.error(f"对数化失败：{e}")


def op_standardize(df, push_history, log_op) -> None:
    st.markdown("**标准化**")
    vars_sel = st.multiselect("选择变量", _numeric_cols(df), key="std_vars")
    method = st.selectbox("方法", ["zscore", "minmax"], key="std_method")
    if st.button("执行标准化", key="btn_std") and vars_sel:
        try:
            push_history(df)
            new_df, new_cols = tr.standardize(df, vars_sel, method)
            st.session_state["df"] = new_df
            log_op("standardize", vars_sel, {"method": method})
            st.success(f"标准化完成，新增列：{', '.join(new_cols)}")
            st.rerun()
        except Exception as e:
            st.session_state["df_history"].pop()
            st.error(f"标准化失败：{e}")


def op_lag_lead(df, push_history, log_op) -> None:
    st.markdown("**差分 / 滞后 / 超前**")
    id_col, time_col = _panel_defaults(df)
    vars_sel = st.multiselect("选择变量", _numeric_cols(df), key="ll_vars")
    c1, c2, c3 = st.columns(3)
    op_type = c1.selectbox("类型", ["lag", "lead", "first_diff"], key="ll_type")
    periods = c2.number_input("阶数", 1, 20, 1, key="ll_periods")
    id_input = c3.text_input("ID 列", value=id_col or "", key="ll_id")
    time_input = st.text_input("时间列", value=time_col or "", key="ll_time")
    if st.button("执行", key="btn_ll") and vars_sel:
        id_c = id_input.strip() or None
        time_c = time_input.strip() or None
        try:
            push_history(df)
            if op_type == "first_diff":
                new_df, new_cols = tr.first_difference(df, vars_sel, id_c, time_c)
                log_op("first_difference", vars_sel, {"id_col": id_c, "time_col": time_c})
            else:
                new_df, new_cols = tr.lag_lead(df, vars_sel, int(periods), op_type, id_c, time_c)
                log_op(op_type, vars_sel, {"periods": periods, "id_col": id_c, "time_col": time_c})
            st.session_state["df"] = new_df
            st.success(f"完成，新增列：{', '.join(new_cols)}")
            st.rerun()
        except Exception as e:
            st.session_state["df_history"].pop()
            st.error(f"操作失败：{e}")


def op_missing(df, push_history, log_op) -> None:
    st.markdown("**缺失值处理**")
    id_col, _ = _panel_defaults(df)
    vars_sel = st.multiselect("选择变量", _all_cols(df), key="miss_vars")
    method = st.selectbox(
        "方法",
        ["drop_row", "fill_mean", "fill_median", "fill_zero", "ffill", "bfill"],
        key="miss_method",
    )
    id_input = st.text_input("ID 列（ffill/bfill）", value=id_col or "", key="miss_id")
    if st.button("执行缺失值处理", key="btn_miss") and vars_sel:
        id_c = id_input.strip() or None
        try:
            push_history(df)
            new_df, log = missing.impute_missing(df, vars_sel, method, id_c)
            st.session_state["df"] = new_df
            log_op("impute_missing", vars_sel, {"method": method, "id_col": id_c})
            st.success("缺失值处理完成")
            for var, info in log.items():
                st.caption(f"  {var}: 影响 {info.get('rows_affected', 0)} 行")
            st.rerun()
        except Exception as e:
            st.session_state["df_history"].pop()
            st.error(f"缺失值处理失败：{e}")


def op_dummies(df, push_history, log_op) -> None:
    st.markdown("**虚拟变量**")
    c1, c2 = st.columns(2)
    dummy_type = c1.selectbox("类型", ["类别虚拟变量", "年份虚拟变量", "行业虚拟变量"], key="dum_type")
    drop_first = c2.checkbox("去掉第一个", True, key="dum_drop")
    var_sel = st.selectbox("选择列", _all_cols(df), key="dum_var")
    if st.button("生成虚拟变量", key="btn_dum"):
        try:
            push_history(df)
            if dummy_type == "类别虚拟变量":
                new_df, new_cols = encoder.create_dummies(df, var_sel, drop_first)
            elif dummy_type == "年份虚拟变量":
                new_df, new_cols = encoder.create_year_dummies(df, var_sel)
            else:
                new_df, new_cols = encoder.create_industry_dummies(df, var_sel)
            st.session_state["df"] = new_df
            log_op("dummies", [var_sel], {"type": dummy_type})
            preview = ', '.join(new_cols[:5]) + ('...' if len(new_cols) > 5 else '')
            st.success(f"生成完成，新增 {len(new_cols)} 列：{preview}")
            st.rerun()
        except Exception as e:
            st.session_state["df_history"].pop()
            st.error(f"生成虚拟变量失败：{e}")


def op_string_clean(df, push_history, log_op) -> None:
    st.markdown("**字符串清洗**")
    str_cols = _string_cols(df)
    if not str_cols:
        st.info("数据中没有字符串列。")
        return
    var_sel = st.selectbox("选择列", str_cols, key="str_var")
    ops_sel = st.multiselect(
        "操作",
        ["strip", "lower", "upper", "remove_punctuation", "remove_digits"],
        default=["strip"],
        key="str_ops",
    )
    c1, c2 = st.columns(2)
    pattern = c1.text_input("正则模式（可选）", key="str_pattern")
    replacement = c2.text_input("替换为", key="str_replace")
    if st.button("执行字符串清洗", key="btn_str"):
        try:
            push_history(df)
            cur_df = df.copy()
            if ops_sel:
                cur_df, changed = string_clean.clean_strings(cur_df, var_sel, ops_sel)
                st.success(f"字符串清洗完成，影响 {changed} 行。")
            if pattern:
                cur_df, r_changed = string_clean.regex_replace(cur_df, var_sel, pattern, replacement)
                st.success(f"正则替换完成，影响 {r_changed} 行。")
            st.session_state["df"] = cur_df
            log_op("string_clean", [var_sel], {"ops": ops_sel, "pattern": pattern})
            st.rerun()
        except Exception as e:
            st.session_state["df_history"].pop()
            st.error(f"字符串清洗失败：{e}")


def op_interaction(df, push_history, log_op) -> None:
    st.markdown("**交互项**")
    num_cols = _numeric_cols(df)
    if len(num_cols) < 2:
        st.info("至少需要 2 个数值列才能生成交互项。")
        return
    c1, c2 = st.columns(2)
    var1 = c1.selectbox("变量 1", num_cols, key="inter_v1")
    var2 = c2.selectbox("变量 2", num_cols, index=1, key="inter_v2")
    if st.button("生成交互项", key="btn_inter"):
        if var1 == var2:
            st.error("请选择不同的两个变量。")
            return
        try:
            push_history(df)
            new_df, new_col = tr.interaction_term(df, var1, var2)
            st.session_state["df"] = new_df
            log_op("interaction", [var1, var2], {})
            st.success(f"交互项已生成：**{new_col}**")
            st.rerun()
        except Exception as e:
            st.session_state["df_history"].pop()
            st.error(f"生成交互项失败：{e}")
