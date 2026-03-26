[![中文](https://img.shields.io/badge/README-中文-red)](README.zh.md)

---
title: EconPrep 学术数据清洗工具
emoji: 🧹
colorFrom: green
colorTo: teal
sdk: streamlit
sdk_version: "1.32.0"
app_file: app.py
pinned: false
license: MIT
tags:
  - econometrics
  - data-cleaning
  - panel-data
  - streamlit
  - python
---

# 🧹 EconPrep

**Academic Data Cleaning Toolkit for Econometrics & Social Science Research**

Upload CSV/Excel → Select cleaning operations → Download clean data. No more manual Stata do-files.

> Say goodbye to repetitive data cleaning scripts. EconPrep covers everything: missing values, winsorization, log transformation, lagging, dummies, and more.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-red.svg)](https://streamlit.io/)
[![ModelScope](https://img.shields.io/badge/🤖_Demo-ModelScope-624aff)](https://modelscope.cn/studios/JackyCufe/EconPrep)

**🚀 Live Demo (no install):**
- 🤖 [ModelScope Studio](https://modelscope.cn/studios/JackyCufe/EconPrep) — China (Recommended)
- 🤗 [HuggingFace Space](https://huggingface.co/spaces/JackyCufe/EconPrep) — Global

---

## ✨ Features

### Data Loading
- ✅ CSV (UTF-8 / GBK / GB18030 / Latin-1 auto-detected)
- ✅ Excel (`.xlsx` / `.xls`)
- ✅ Auto-detects panel data structure (ID / time columns)
- ✅ Data overview (rows, columns, missing value stats)

### Cleaning Operations

| Operation | Description |
|-----------|-------------|
| **Missing Values** | Drop rows, fill with mean/median/zero, forward/backward fill (grouped by panel ID) |
| **Winsorize** | Clip extreme values by quantile, customizable upper/lower bounds |
| **Log Transform** | ln / log10 / log2, supports log(1+x) |
| **Standardize** | Z-score normalization / Min-Max scaling |
| **Lag / Lead / Diff** | First-difference, any-order lag/lead, grouped by panel ID |
| **Dummy Variables** | Categorical dummies / year FE / industry FE |
| **String Cleaning** | Trim whitespace, case conversion, remove punctuation/digits, regex replace |
| **Interaction Terms** | Multiply two variables to create interaction terms |

### Key UX Features
- 🔄 **Undo**: Up to 10 steps of operation history, one-click revert
- 🛡️ **Non-destructive**: All operations create new columns, original data untouched
- 📋 **Operation Script**: Auto-generates reproducible Python code
- 💾 **Export formats**: CSV / Excel / Stata `.dta`

---

## 🚀 Quick Start

```bash
cd econprep
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501.

---

## 🔗 Works with EconKit

```
Raw Data
   ↓
[EconPrep] Data Cleaning
  · Handle missing values
  · Winsorize
  · Generate controls (log, standardize)
  · Dummies (year / industry FE)
   ↓
Clean Data (CSV / Excel / Stata .dta)
   ↓
[EconKit] Empirical Analysis
  · OLS / Panel FE
  · IV / 2SLS
  · Descriptive statistics
```

---

## 🛠️ Tech Stack

- **Streamlit** ≥ 1.32 — UI
- **pandas** ≥ 2.0 — Data processing
- **scipy** ≥ 1.11 — Scientific computing
- **pyreadstat** ≥ 1.2 — Stata file I/O
- **openpyxl** ≥ 3.1 — Excel export
- **chardet** ≥ 5.2 — Encoding auto-detection
