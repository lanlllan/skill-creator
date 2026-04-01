---
name: data-formatter
description: 在 JSON、CSV、YAML 格式之间转换数据，并验证文件结构合法性
version: 1.0.0
author: OpenClaw Team
tags: [data, format, conversion, csv, json, yaml]
date: 2026-03-30
type: python
---

# Data Formatter

> 在 JSON、CSV、YAML 格式之间转换数据，并验证文件结构合法性。

---

## 概述

Data Formatter 是一个中等复杂度的数据处理 Skill 示例，演示了多格式 I/O、数据校验和格式转换模式。包含 2 个子命令（convert / validate），展示了标准的 argparse + Result 架构。

## 适用场景

- 数据工程师从第三方 API 获取 JSON 数据后，需快速转为 CSV 格式导入 Excel 或数据库
- 测试工程师将 CSV 格式的测试用例转为 YAML 配置，供自动化测试框架使用
- 开发者在发布前批量校验项目中的配置文件（JSON/YAML），确保结构合法无语法错误

## 核心能力

### 1. 格式转换（convert）

- 支持 JSON ↔ CSV ↔ YAML 任意两种格式之间的双向转换
- 自动识别源文件格式（按扩展名推断）
- 支持输出到文件或标准输出（便于管道组合）
- 处理 BOM 编码（UTF-8-sig），兼容 Excel 导出的 CSV

### 2. 结构校验（validate）

- 验证文件格式语法合法性（如 JSON 括号匹配、YAML 缩进正确）
- 检测记录字段数一致性（CSV 每行列数应与表头匹配）
- 输出详细错误位置（行号、列号），便于快速定位问题
- 空文件给出警告而非报错，区分"合法但空"和"格式错误"

## 使用方式

```bash
# JSON → CSV
python run.py convert --input data.json --to csv --output data.csv

# CSV → YAML
python run.py convert --input users.csv --to yaml

# 校验 JSON 文件
python run.py validate --input config.json
```

## 示例

```bash
$ python run.py convert --input users.json --to csv --output users.csv
✅ 转换完成：50 条记录 → users.csv

$ python run.py validate --input config.yaml
✅ config.yaml — 格式合法
   格式: YAML
   记录数: 3
   字段: name, host, port, debug

$ python run.py validate --input broken.json
❌ JSON 语法错误（第 5 行，第 12 列）：Expecting ',' delimiter
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 源文件格式无法识别 | 文件扩展名不在支持范围内 | 将文件重命名为 .json / .csv / .yaml / .yml |
| CSV 转换后中文乱码 | 源文件编码非 UTF-8 | 先将文件转为 UTF-8 编码再转换 |
| YAML 相关命令报错 | PyYAML 未安装 | 运行 `pip install pyyaml` |
| 字段数不一致 | CSV 某行缺少或多出逗号 | 用 validate 命令定位异常行 |

## 前置依赖

- Python >= 3.9（JSON/CSV 使用标准库）
- PyYAML（仅 YAML 格式转换时需要，可选）

## 📁 Skill 结构

```
data-formatter/
├── SKILL.md              # 技能说明（本文件）
├── run.py                # 主入口（2 个子命令：convert / validate）
├── .skill-spec.yaml      # 规约文件
├── USAGE.md              # 使用指南
└── README.md             # 快速入门
```
