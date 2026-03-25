"""
Skill 模板定义与文件渲染
"""
import os
from pathlib import Path

DEFAULT_TEMPLATES = {
    "SKILL.md": '''---
name: {{name}}
description: {{description}}
version: {{version}}
author: {{author}}
tags: {{tags}}
---

# {{name_title}} - {{description}}

## 📋 Skill 概述

**技能名称**：`{{name}}`  
**用途**：{{description}}  
**适用场景**：
- 场景1
- 场景2

## 🎯 核心能力

### 1. 能力1
- 功能点1
- 功能点2

### 2. 能力2
- 功能点1
- 功能点2

## 📁 Skill 结构

```
{{name}}/
├── SKILL.md          # 技能说明（本文件）
├── run.py            # 主入口
└── ...               # 其他文件
```

## 🔧 使用方式

```bash
# 基本用法
python run.py --help
python run.py <子命令> [参数...]
```

## 📝 示例

```bash
# 示例1
python run.py example

# 示例2
python run.py demo --option value
```

## 📊 输出示例

```
✅ 执行成功
结果：...
```

## 🐛 故障排除

| 问题 | 原因 | 解决 |
|------|------|------|
| 错误1 | 原因1 | 方案1 |

## 🔗 相关资源

- OpenClaw 文档：https://docs.openclaw.ai

---

*版本：{{version}}*  
*更新：{{date}}*
''',
    "run.py": '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{{description}}
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='{{description}}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py --help
  python run.py <command> [args...]
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='详细输出')
    parser.add_argument('--config', '-c', help='配置文件路径')
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 示例子命令
    example_parser = subparsers.add_parser('example', help='示例命令')
    example_parser.add_argument('--name', help='名称')
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"🔍 调试模式：{args}")
    
    if args.command == 'example':
        print(f"Hello, {args.name or 'World'}!")
        return 0
    
    parser.print_help()
    return 0

if __name__ == '__main__':
    sys.exit(main())
''',
    "USAGE.md": '''# {{name}} - 使用指南

## 🚀 快速开始

```bash
cd {{name}}
python run.py --help
```

## 📋 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `example` | 示例命令 | `python run.py example --name test` |

## 🛠️ 配置

配置文件（`config.yaml`）示例：

```yaml
option1: value1
option2: value2
```

## 📊 输出说明

命令执行后会输出...

## 🐛 常见问题

**Q: 问题？**  
A: 答案。

---

*最后更新：{{date}}*
''',
    "README.md": '''# {{name}}

{{description}}

## 🚀 安装

无需安装，直接运行：

```bash
python run.py --help
```

## 📖 文档

详细说明请查看 [USAGE.md](USAGE.md) 或 [SKILL.md](SKILL.md)。

---

*版本 {{version}} · 作者 {{author}}*
'''
}


def generate_files(skill_dir: Path, variables: dict):
    """根据模板生成 skill 文件，将所有 {{key}} 占位符替换为变量值。"""
    expanded = dict(variables)
    expanded['name_title'] = variables.get('name', '').replace('-', ' ').title()
    if isinstance(expanded.get('tags'), list):
        tag_list = expanded['tags']
        expanded['tags'] = f"[{', '.join(tag_list)}]" if tag_list else '[]'

    for filename, template_content in DEFAULT_TEMPLATES.items():
        content = template_content
        for key, value in expanded.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        file_path = skill_dir / filename
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ 已创建：{file_path.name}")

        if filename == 'run.py':
            os.chmod(file_path, 0o755)
