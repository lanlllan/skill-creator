---
name: env-checker
description: 检查开发环境的依赖配置，验证 Python 版本、必备工具和环境变量是否就绪
version: 1.0.0
author: OpenClaw Team
tags: [environment, dependency, check, configuration]
date: 2026-03-30
type: python
---

# Env Checker

> 检查开发环境的依赖配置，验证 Python 版本、必备工具和环境变量是否就绪。

---

## 概述

Env Checker 是一个入门级 Skill 示例，演示了系统探测、依赖检查和结构化报告生成模式。包含 2 个子命令（check / report），展示了 `shutil.which` 工具探测和 `platform` 模块的使用。

## 适用场景

- 新成员入职后运行一键检查脚本，确认开发环境（Python、Git、Docker 等）是否配置完整
- CI 流水线中作为第一步检测运行环境，避免因工具缺失导致后续步骤失败
- 切换到新机器或容器后，快速验证所有必备工具和环境变量是否就绪

## 核心能力

### 1. 环境检查（check）

- 逐项检测 Python 版本是否满足最低要求
- 验证指定的命令行工具（git、docker、node 等）是否存在于 PATH 中
- 检查必需环境变量是否已设置
- 支持自定义检查规则（通过参数指定工具列表和变量列表）

### 2. 环境报告（report）

- 自动检测操作系统类型、版本和架构
- 汇总 Python 版本、路径和实现信息
- 扫描常用命令行工具的安装状态
- 输出重要环境变量的当前值
- 支持 text 和 JSON 两种输出格式

## 使用方式

```bash
# 默认检查（Python 版本 + git + python3 + PATH/HOME）
python run.py check

# 自定义检查工具和环境变量
python run.py check --tools git,docker,node --env-vars HOME,PATH,JAVA_HOME --python-min 3.10

# 生成文本格式环境报告
python run.py report

# 生成 JSON 格式报告（便于管道处理）
python run.py report --format json
```

## 示例

```bash
$ python run.py check
🔍 环境检查

  ✅ Python 版本: 3.11.4 (要求 >= 3.9)

  📦 命令行工具:
    ✅ git
    ✅ python3

  🔑 环境变量:
    ✅ PATH
    ✅ HOME

  🎉 环境检查全部通过！

$ python run.py check --tools git,docker,kubectl
🔍 环境检查

  ✅ Python 版本: 3.11.4 (要求 >= 3.9)

  📦 命令行工具:
    ✅ git
    ✅ docker
    ❌ kubectl — 未找到

  🔑 环境变量:
    ✅ PATH
    ✅ HOME

  ⚠️  部分检查未通过，请修复上述标记 ❌ 的项目
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 工具检查失败（已安装） | 工具未添加到 PATH | 将工具所在目录加入 PATH 环境变量 |
| Python 版本检测不正确 | 运行了错误的 Python 解释器 | 使用 `which python3` 确认当前 Python 路径 |
| 环境变量显示未设置 | 变量仅在其他 shell 中设置 | 在当前 shell 的配置文件中添加 export |

## 前置依赖

- Python >= 3.9（标准库即可，无第三方依赖）

## 📁 Skill 结构

```
env-checker/
├── SKILL.md              # 技能说明（本文件）
├── run.py                # 主入口（2 个子命令：check / report）
├── .skill-spec.yaml      # 规约文件
├── USAGE.md              # 使用指南
└── README.md             # 快速入门
```
