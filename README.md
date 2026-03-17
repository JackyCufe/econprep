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

# 🧹 EconPrep — 学术论文数据清洗工具

> 「上传 CSV/Excel → 选择清洗操作 → 下载干净数据」

EconPrep 是专为经济学、管理学等社会科学研究者设计的学术数据预处理工具，与 **EconKit**（实证分析工具）形成完整的数据处理 → 实证分析闭环。

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
# 1. 克隆或进入项目目录
cd econprep

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
streamlit run app.py
```

访问 http://localhost:8501 即可使用。

---

## 🔗 与 EconKit 配合使用

EconPrep + EconKit 构成完整的学术研究数据工作流：

```
原始数据
   ↓
[EconPrep] 数据清洗
  · 缺失值处理
  · 缩尾处理
  · 生成控制变量（对数化、标准化）
  · 虚拟变量（年份 / 行业固定效应）
   ↓
干净数据（CSV / Excel / Stata .dta）
   ↓
[EconKit] 实证分析
  · OLS / 面板固定效应回归
  · 工具变量 / 2SLS
  · 描述性统计
  · 相关性分析
```

**推荐工作流：**
1. 在 EconPrep 完成数据预处理，导出 `.dta` 或 `.csv`
2. 在 EconKit 中加载清洗后数据，进行计量经济学分析
3. 使用 EconPrep 生成的「操作脚本」记录数据处理过程，确保研究可复现

---

## 📁 项目结构

```
econprep/
├── app.py                     # Streamlit 入口
├── requirements.txt
├── README.md
├── core/
│   ├── data_loader.py         # 数据加载 & 面板识别
│   └── exporter.py            # 多格式导出
├── operations/
│   ├── winsorize.py           # 缩尾处理
│   ├── transform.py           # 变换（对数/标准化/差分/滞后）
│   ├── missing.py             # 缺失值处理
│   ├── encoder.py             # 虚拟变量
│   └── string_clean.py        # 字符串清洗
├── ui/
│   ├── components/
│   │   ├── preview.py         # 数据预览组件
│   │   └── operation_card.py  # 操作卡片组件
│   └── pages/
│       ├── upload.py          # 上传页
│       ├── clean.py           # 清洗主页
│       └── export.py          # 导出页
└── assets/
    └── style.css
```

---

## 🛠️ 技术栈

- **[Streamlit](https://streamlit.io/)** ≥ 1.32 — 界面框架
- **[pandas](https://pandas.pydata.org/)** ≥ 2.0 — 数据处理
- **[scipy](https://scipy.org/)** ≥ 1.11 — 科学计算
- **[pyreadstat](https://github.com/Roche/pyreadstat)** ≥ 1.2 — Stata 文件读写
- **[openpyxl](https://openpyxl.readthedocs.io/)** ≥ 3.1 — Excel 导出
- **[chardet](https://github.com/chardet/chardet)** ≥ 5.2 — 编码自动检测

---

## 📌 工程规范

本项目遵循 **deepvcode** 工程规范：
- 单文件 200-400 行，函数 ≤ 50 行
- 防御性编程：快速失败，绝不静默吞噬错误
- 非破坏性操作：永远创建新对象，禁止原地修改
- 语义化 Git commit
