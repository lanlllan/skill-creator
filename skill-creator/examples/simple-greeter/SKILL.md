---
name: simple-greeter
description: 根据姓名和语言生成个性化问候语
version: 1.0.0
author: OpenClaw Team
tags: [demo, greeting, beginner]
date: 2026-03-30
type: python
---

# Simple Greeter

> 根据姓名和语言生成个性化问候语，支持中文、英文、日文三种语言。

---

## 概述

Simple Greeter 是一个入门级 Skill 示例，演示了单命令 Skill 的标准实现模式。它展示了参数校验、多语言支持、错误回退等基本能力。

## 适用场景

- 新成员入职时，自动发送多语言欢迎消息
- 定时任务中生成每日问候推送内容
- CLI 工具的友好交互提示

## 核心能力

### 1. 多语言问候

- 支持中文、英文、日文三种语言的问候语生成
- 通过 `--lang` 参数选择目标语言，默认中文
- 不支持的语言代码自动回退到英文

### 2. 个性化定制

- 姓名嵌入问候语模板，生成自然的问候表达
- 模板可扩展，便于添加新语言

## 使用方式

```bash
# 中文问候（默认）
python run.py greet --name "张三"

# 英文问候
python run.py greet --name "Alice" --lang en

# 日文问候
python run.py greet --name "田中" --lang ja
```

## 示例

```bash
$ python run.py greet --name "张三"
你好，张三！欢迎使用 OpenClaw。

$ python run.py greet --name "Alice" --lang en
Hello, Alice! Welcome to OpenClaw.

$ python run.py check --lang fr
❌ 语言 'fr' 不受支持，可用：en, ja, zh
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 提示"不支持的语言" | 语言代码不在 zh/en/ja 中 | 使用支持的语言代码，或接受自动回退到英文 |
| 姓名为空 | 未传入 --name 或值为空 | 确保 --name 参数非空 |

## 前置依赖

- Python >= 3.9（标准库即可，无第三方依赖）

## 📁 Skill 结构

```
simple-greeter/
├── SKILL.md              # 技能说明（本文件）
├── run.py                # 主入口
├── .skill-spec.yaml      # 规约文件
├── USAGE.md              # 使用指南
└── README.md             # 快速入门
```
