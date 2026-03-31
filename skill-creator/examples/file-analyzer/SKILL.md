---
name: file-analyzer
description: 分析文件和目录的统计信息，包括行数统计、类型分布和大小报告
version: 1.0.0
author: OpenClaw Team
tags: [file, analysis, statistics]
date: 2026-03-30
type: python
---

# File Analyzer

> 分析文件和目录的统计信息，包括行数统计、类型分布和大小报告。

---

## 概述

File Analyzer 是一个中等复杂度的 Skill 示例，演示了多命令架构、文件 I/O 操作和数据统计汇总。包含 3 个子命令，展示了标准的 argparse + Result 模式。

## 适用场景

- 技术主管评审时需要快速了解项目代码规模和语言分布
- 重构前分析目录结构，识别大文件和冗余文件
- CI 流水线中自动生成项目统计报告

## 核心能力

### 1. 行数统计

- 递归遍历目录中所有文本文件，逐行统计
- 支持按扩展名过滤（如仅统计 `.py` 文件）
- 自动跳过二进制文件，避免统计错误

### 2. 类型分布

- 按文件扩展名分组，统计文件数量和体积
- 输出各类型的占比百分比，直观了解项目语言构成

### 3. 大小报告

- 输出目录中最大文件的排名列表
- 支持自定义显示数量，默认前 10 名
- 文件大小以可读格式展示（KB / MB）

## 使用方式

```bash
# 统计行数
python run.py count --path ./my-project

# 仅统计 Python 文件行数
python run.py count --path ./my-project --ext .py

# 文件类型分布
python run.py types --path ./my-project

# 最大文件 Top 5
python run.py top --path ./my-project --limit 5
```

## 示例

```bash
$ python run.py count --path ./my-project --ext .py
📊 行数统计 — ./my-project
  .py             3,245 行

  合计             3,245 行

$ python run.py types --path ./my-project
📊 文件类型分布 — ./my-project
  扩展名           数量        大小      占比
  ------------------------------------------
  .py              15     45.2 KB   62.3%
  .md               5     18.1 KB   24.9%

  合计：20 个文件，63.3 KB

$ python run.py top --path ./my-project --limit 3
📊 最大文件 Top 3 — ./my-project
    1.    15.2 KB  src/main.py
    2.    12.8 KB  tests/test_core.py
    3.     9.1 KB  docs/guide.md
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 路径不存在 | 传入的 --path 目录不存在 | 检查路径拼写 |
| 统计结果缺少文件 | 二进制文件被自动跳过 | 正常行为，仅统计文本文件 |
| 隐藏文件未被统计 | 以 `.` 开头的文件被排除 | 正常行为，设计如此 |

## 前置依赖

- Python >= 3.9（标准库即可，无第三方依赖）

## 📁 Skill 结构

```
file-analyzer/
├── SKILL.md              # 技能说明（本文件）
├── run.py                # 主入口（3 个子命令：count / types / top）
├── .skill-spec.yaml      # 规约文件
├── USAGE.md              # 使用指南
└── README.md             # 快速入门
```
