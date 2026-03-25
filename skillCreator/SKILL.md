---
name: skill-creator
description: 创建符合 OpenClaw 规范的新 Skill，自动化生成目录结构、模板文件和文档
version: 3.0.0
author: Zhiheng Yang
tags: [tooling, scaffolding, development]
---

# Skill Creator - Skill 开发脚手架

> 自动化创建、初始化 OpenClaw Skill 的完整工具，包含规范检查、模板生成和验证功能

---

## 📋 Skill 概述

**技能名称**：`skill-creator`  
**用途**：根据 OpenClaw Skill 规范，快速创建、初始化新的 Skill，生成完整的目录结构和模板文件  
**适用场景**：
- 需要开发新的 Skill 功能
- 创建符合规范的 Skill 项目骨架
- 学习 Skill 开发流程
- 批量创建 Skill 原型

---

## 🎯 核心能力

### 1. 项目脚手架
- 生成标准 Skill 目录结构
- 创建必需的 `SKILL.md`（含 front matter）
- 生成 `run.py` 主入口模板
- 生成配置文件、模板等可选文件

### 2. 规范检查
- 验证 SKILL.md front matter 完整性
- 检查必需字段（name, description, version）
- 验证 run.py 基本结构
- 检测常见配置错误

### 3. 模板系统
- 模板定义在 `creator/templates.py` 的 `DEFAULT_TEMPLATES` 字典
- 支持占位符替换（如 `{{name}}`、`{{description}}`、`{{name_title}}`）
- 自动将 `tags` 规范化输出为 YAML 数组格式
- 通过修改 `creator/templates.py` 可扩展模板内容

### 4. 工作流管理
- 创建 → 确认 → 归档 流程
- 结构化状态管理：`.state.json` 原子写入，README.md 自动生成（只读视图）
- 支持 `archive/clean --source` 处理自定义源目录
- `batch --file` 命令：从 YAML 文件批量创建，含批内去重、幂等检查、汇总报告
- 锁机制防止并发写入冲突，自动清理超时残留锁

---

## 📁 Skill 结构

```
skill-creator/
├── run.py                      # CLI 入口（纯 argparse + dispatch）
├── creator/                    # 业务逻辑模块包
│   ├── paths.py / validators.py / templates.py / scorer.py
│   ├── state_manager.py        # .state.json 结构化状态管理
│   ├── readme_manager.py       # 兼容层（转发到 state_manager）
│   └── commands/               # create / validate / archive / clean / batch
├── tests/                      # pytest 测试套件（85 用例）
├── SKILL.md                    # 技能说明
└── USAGE.md                    # 使用指南
```

---

## 🔧 使用方式

### 基本用法

```bash
# 1. 快速创建新 skill（非交互）
python skill-creator/run.py create --name "my-skill" --description "我的新技能"

# 2. 交互式创建（逐项输入）
python skill-creator/run.py create --interactive

# 3. 验证现有 skill
python skill-creator/run.py validate ~/.openclaw/workspace/skills/existing-skill

# 4. 归档 skill（省略 --dest 时自动推导 skills/ 目录）
python skill-creator/run.py archive my-skill

# 5. 归档到指定目录
python skill-creator/run.py archive my-skill --dest ~/.openclaw/workspace/skills

# 6. 清理临时技能目录
python skill-creator/run.py clean my-skill

# 7. 使用自定义源目录进行归档/清理（当 create 使用了 --output 时）
python skill-creator/run.py archive my-skill --source ./custom-dir
python skill-creator/run.py clean my-skill --source ./custom-dir

# 8. 批量创建（从 YAML 文件）
python skill-creator/run.py batch --file skills-to-create.yaml
```

### 交互式创建

```bash
python skill-creator/run.py create --interactive
```

会提示输入：
- Skill 名称（可通过 `--name` 预填）
- 描述（可通过 `--description` 预填）
- 版本号（默认 1.0.0）
- 作者（默认 OpenClaw Assistant）
- 标签（逗号分隔，可留空）
- 输出目录（默认由 `get_skills_temp_dir()` 解析）

---

## 📋 Skill 开发规范（本 skill 的产出）

### 1. 目录结构规范

```
skill-name/
├── SKILL.md                    # 必需：技能说明（含 YAML front matter）
├── run.py                      # 必需：技能主入口（可执行）
├── templates/                  # 可选：模板文件
│   └── *.tmpl
├── utils/                      # 可选：工具函数
│   └── *.py
├── config/                     # 可选：配置文件
│   └── config.yaml
├── requirements.txt            # 可选：Python 依赖
├── USAGE.md                    # 推荐：使用指南
└── README.md                   # 推荐：快速上手
```

### 2. SKILL.md Front Matter 规范

```yaml
---
name: skill-name                # 必需，小写、短横线分隔，如 "test-runner"
description: 简短描述            # 必需，一句话说明用途
version: 1.0.0                  # 必需，语义化版本
author: Your Name              # 可选，作者
tags: [testing, go]            # 可选，标签数组
dependencies: []               # 可选，依赖的其他技能
---

# Skill Name - 详细标题

## 📋 Skill 概述

...

## 🎯 核心能力

...

## 📁 Skill 结构

...

## 🔧 使用方式

...

## 📝 示例

...
```

### 3. run.py 入口规范

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Name - 简短描述
"""

import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(
        description='Skill 描述',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py --help
  python run.py <子命令> [参数...]
        """
    )
    
    # 定义参数
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 实现逻辑
    print("Skill 执行中...")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

### 4. 推荐实践

- ✅ **文档完整**：SKILL.md 包含使用示例和完整说明
- ✅ **错误处理**：run.py 正确处理异常，返回非零退出码
- ✅ **参数校验**：验证输入参数，提供清晰错误信息
- ✅ **日志输出**：使用 print 或 logging，便于调试
- ✅ **返回值**：main() 返回整数退出码（0=成功，非0=失败）
- ✅ **可执行权限**：`chmod +x run.py`
- ✅ **README**：提供快速上手指南

---

## 🎯 本 Skill 的设计理念

### 发现问题
- 手动创建 Skill 容易遗漏 front matter
- 目录结构不规范
- 文档不完整
- 验证困难
- 归档与清理流程繁琐

### 解决方案
- **脚手架**：一键生成完整项目结构
- **模板化**：内置标准模板，降低重复劳动
- **验证器**：自动检查常见问题
- **归档工具**：内置 `archive` 命令自动移动并更新 README
- **清理工具**：内置 `clean` 命令清理临时目录并同步 README
- **工作流集成**：覆盖 创建 → 验证 → 归档 → 清理 全流程

---

## 📊 使用示例

### 示例 1：创建测试工具 skill

```bash
python skill-creator/run.py create \
  --name "load-tester" \
  --description "HTTP 负载测试工具" \
  --tags testing,http,performance
```

生成结构：
```
load-tester/
├── SKILL.md (含 front matter)
├── run.py (基本框架)
├── USAGE.md (使用说明模板)
└── utils/ (示例工具函数)
```

### 示例 2：验证现有 skill

```bash
python skill-creator/run.py validate ~/.openclaw/workspace/skills/test-writer
```

输出：
```
🔍 验证 skill：~/.openclaw/workspace/skills/test-writer
📊 正在进行质量评分...
📊 Skill 质量评分报告
...
✅ Skill 验证通过！
```

### 示例 3：批量创建

`skills.yaml`:
```yaml
skills:
  - name: log-analyzer
    description: 日志分析工具
    tags: [logging, analysis]
  - name: config-sync
    description: 配置同步工具
    tags: [config, sync]
```

```bash
python skill-creator/run.py batch --file skills.yaml
```

---

## 🔍 验证检查清单

创建后自动运行检查：

- [ ] SKILL.md 存在且包含 front matter
- [ ] front matter 包含 name、description、version
- [ ] name 符合规范（小写、短横线）
- [ ] version 符合语义化版本格式（x.y.z）
- [ ] run.py 存在且包含 main() 函数
- [ ] run.py 有 shebang 和执行权限
- [ ] 可选文件合理性（templates/, utils/ 等）
- [ ] 文档完整性（SKILL.md 有使用示例）

---

## 🛠️ 技术实现

### 模板引擎
- 模板定义在 `creator/templates.py` 的 `DEFAULT_TEMPLATES` 字典
- 使用内置字符串替换（`str.replace`）
- 支持变量替换：`{{name}}`、`{{description}}`、`{{name_title}}` 等
- `tags` 在生成时输出为 YAML 数组（如 `[tag1, tag2]`）

### 验证器
- 解析 YAML front matter（`yaml.safe_load`）
- 检查必需字段：`name`、`description`、`version`
- 正则检查 name 格式：`^[a-z][a-z0-9-]*$`
- 文件存在性与 `run.py` 可执行权限检查

### 路径管理
- `create` 写入 `--output`（默认由 `get_skills_temp_dir()` 解析，与 `archive/clean` 一致）
- `archive/clean` 默认从 `get_skills_temp_dir()` 查找源目录
- 当输出目录自定义时，建议显式传入 `--source`

---

## 📈 未来增强

- [ ] 支持更多模板类型（Go skill、shell script skill）
- [ ] 集成 clawhub 发布流程
- [ ] 生成 CI/CD 配置文件（GitHub Actions）
- [ ] 自动生成技能文档网站
- [ ] 支持插件系统（自定义模板）
- [ ] 集成测试框架（自动生成测试用例）

---

## 🔗 相关资源

- **OpenClaw Skill 开发指南**：https://docs.openclaw.ai/skills
- **YAML Front Matter 规范**：https://jekyllrb.com/docs/front-matter/
- **Python 模板引擎**：https://docs.python.org/3/library/string.html#template-strings
- **ClawHub CLI**：`npx clawhub` 搜索、安装、同步 skills

---

*Skill 版本：v3.0.0*  
*最后更新：2026-03-25*  
*状态：生效中*
