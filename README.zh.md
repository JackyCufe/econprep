[![English](https://img.shields.io/badge/README-English-blue)](README.md)

# 🧹 EconPrep — 学术论文数据清洗工具

**Academic Data Cleaning Toolkit for Econometrics & Social Science Research**

> 「上传 CSV/Excel → 选择清洗操作 → 下载干净数据」，告别 Stata do 文件手动清洗

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-red.svg)](https://streamlit.io/)

**🚀 在线体验（无需安装）：**
- 🤖 [ModelScope Studio](https://modelscope.cn/studios/JackyCufe/EconPrep)（国内推荐）
- 🤗 [HuggingFace Space](https://huggingface.co/spaces/JackyCufe/EconPrep)（国际）

---

## ✨ 功能列表

### 数据加载
- ✅ 支持 CSV（UTF-8 / GBK / GB18030 / Latin-1 自动检测）
- ✅ 支持 Excel（`.xlsx` / `.xls`）
- ✅ 自动识别面板数据结构（ID 列 / 时间列）
- ✅ 数据概况展示（行数、列数、缺失值统计）

### 数据清洗操作

| 操作 | 说明 |
|------|------|
| **缺失值处理** | 删除行、均值/中位数/零填充、前向/后向填充（面板数据支持分组） |
| **缩尾（Winsorize）** | 按分位数截断极端值，可自定义上下分位数 |
| **对数化** | ln / log10 / log2，支持 log(1+x) |
| **标准化** | Z-score 标准化 / Min-Max 归一化 |
| **差分 / 滞后 / 超前** | 一阶差分、任意阶滞后/超前，面板数据支持按 ID 分组 |
| **虚拟变量** | 类别虚拟变量 / 年份固定效应 / 行业固定效应 |
| **字符串清洗** | 去空白、大小写转换、去标点/数字、正则替换 |
| **交互项** | 两变量相乘生成交互项 |

### 核心 UX 特性
- 🔄 **可撤销**：操作历史最多保留 10 步，一键撤销
- 🛡️ **非破坏性**：所有操作生成新列，不修改原始数据
- 📋 **操作脚本**：自动生成可复现的 Python 代码
- 💾 **多格式导出**：CSV / Excel / Stata `.dta`

---

## 🚀 快速开始

```bash
cd econprep
pip install -r requirements.txt
streamlit run app.py
```

访问 http://localhost:8501 即可使用。

---

## 🔗 与 EconKit 配合使用

```
原始数据
   ↓
[EconPrep] 数据清洗
  · 缺失值处理 / 缩尾 / 对数化 / 虚拟变量
   ↓
干净数据（CSV / Excel / Stata .dta）
   ↓
[EconKit] 实证分析
  · OLS / 面板固定效应 / IV / 描述统计
```

---

## 🛠️ 技术栈

- **Streamlit** ≥ 1.32 — 界面框架
- **pandas** ≥ 2.0 — 数据处理
- **scipy** ≥ 1.11 — 科学计算
- **pyreadstat** ≥ 1.2 — Stata 文件读写
- **openpyxl** ≥ 3.1 — Excel 导出
- **chardet** ≥ 5.2 — 编码自动检测
