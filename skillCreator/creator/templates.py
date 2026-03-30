"""
Skill 模板定义与文件渲染

模板发现优先级（高→低）：
  1. 用户指定 --template-dir
  2. 内置 templates/<type>/*.j2
  3. DEFAULT_TEMPLATES 硬编码回退（仅 python 类型）
"""
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

SUPPORTED_TYPES = ('python', 'shell')

BUILTIN_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / 'templates'

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
- 需要自动化处理特定任务时
- 作为工作流中的一个环节被调用时

## 🎯 核心能力

### 1. 主要功能
- 接收输入参数并执行核心逻辑
- 返回结构化的执行结果（Result 数据类）

### 2. 错误处理
- 输入参数校验（长度、格式、文件存在性）
- 异常捕获与友好提示

## 📁 Skill 结构

```
{{name}}/
├── SKILL.md          # 技能说明（本文件）
├── run.py            # 主入口（含 Result 数据类和命令分发）
├── USAGE.md          # 使用指南
└── README.md         # 快速入门
```

## 🔧 使用方式

```bash
# 查看帮助
python run.py --help

# 执行示例命令
python run.py example --name test

# 详细输出模式
python run.py --verbose example --name test
```

## 📝 示例

```bash
# 基本调用
python run.py example --name "hello"

# 输出：
# ✅ Hello, hello!
```

## 📊 输出示例

```
✅ Hello, World!
```

失败时输出：
```
❌ 执行失败：名称长度超过 128 字符
```

## 🐛 故障排除

| 问题 | 原因 | 解决 |
|------|------|------|
| `❌ 执行失败：配置文件不存在` | `--config` 指定的路径无效 | 检查文件路径是否正确 |
| `❌ 未预期异常：...` | 代码逻辑异常 | 使用 `--verbose` 查看详细信息 |

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
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Result:
    """标准化命令执行结果。"""
    success: bool = True
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.success = False

    def summary(self) -> str:
        if self.success:
            return f"✅ {self.message}" if self.message else "✅ 执行成功"
        err_text = "; ".join(self.errors)
        return f"❌ 执行失败：{err_text}"


def validate_input(args) -> Result:
    """输入参数校验，返回校验结果。"""
    result = Result()

    if hasattr(args, 'name') and args.name:
        if len(args.name) > 128:
            result.add_error("名称长度超过 128 字符")
        if not args.name.strip():
            result.add_error("名称不能为空白")

    if hasattr(args, 'config') and args.config:
        from pathlib import Path
        config_path = Path(args.config)
        if not config_path.exists():
            result.add_error(f"配置文件不存在：{config_path}")

    return result


def cmd_example(args) -> Result:
    """示例命令：演示标准执行流程。"""
    result = validate_input(args)
    if not result.success:
        return result

    try:
        name = getattr(args, 'name', None) or 'World'
        result.message = f"Hello, {name}!"
        result.data['greeting'] = result.message
    except Exception as e:
        result.add_error(f"执行异常：{e}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description='{{description}}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py example --name test
  python run.py --verbose example
        """
    )

    parser.add_argument('--verbose', '-v', action='store_true',
                        help='详细输出')
    parser.add_argument('--config', '-c', help='配置文件路径')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    example_parser = subparsers.add_parser('example', help='示例命令')
    example_parser.add_argument('--name', help='名称')

    args = parser.parse_args()

    if args.verbose:
        print(f"🔍 调试模式：{args}")

    dispatch = {
        'example': cmd_example,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 0

    try:
        result = handler(args)
    except Exception as e:
        print(f"❌ 未预期异常：{e}")
        return 1

    print(result.summary())
    if args.verbose and result.data:
        for k, v in result.data.items():
            print(f"  {k}: {v}")

    return 0 if result.success else 1


if __name__ == '__main__':
    sys.exit(main())
''',
    "USAGE.md": '''# {{name}} - 使用指南

## 🚀 快速开始

```bash
cd {{name}}
python run.py --help
python run.py example --name test
```

## 📋 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `example` | 示例命令，输出问候语 | `python run.py example --name test` |

### 全局选项

| 选项 | 说明 |
|------|------|
| `--verbose` / `-v` | 详细输出，显示调试信息和返回数据 |
| `--config` / `-c` | 指定配置文件路径 |

## 📊 输出说明

命令执行后返回结构化结果：
- 成功：`✅ <消息>` + 退出码 0
- 失败：`❌ 执行失败：<错误详情>` + 退出码 1

使用 `--verbose` 可查看 `Result.data` 中的详细数据。

## 🐛 常见问题

**Q: 如何自定义配置文件？**  
A: 使用 `--config` 参数指定路径：`python run.py --config config.yaml example`。

**Q: 执行报错 "未预期异常" 怎么办？**  
A: 添加 `--verbose` 参数查看完整调试输出，确认输入参数是否合法。

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


def _expand_variables(variables: dict) -> dict:
    """准备模板变量：派生 name_title、格式化 tags、设置默认值。"""
    expanded = dict(variables)
    expanded['name_title'] = variables.get('name', '').replace('-', ' ').title()
    if isinstance(expanded.get('tags'), list):
        tag_list = expanded['tags']
        expanded['tags'] = f"[{', '.join(tag_list)}]" if tag_list else '[]'
    expanded.setdefault('has_config', False)
    return expanded


def _discover_template_dir(skill_type: str,
                           template_dir: str | None = None) -> Path | None:
    """确定模板目录。返回 None 时使用 DEFAULT_TEMPLATES 回退。"""
    if template_dir is not None:
        p = Path(template_dir).resolve()
        if not p.is_dir():
            raise FileNotFoundError(f"模板目录不存在：{p}")
        if not any(p.glob('*.j2')):
            raise FileNotFoundError(f"模板目录中无 .j2 文件：{p}")
        return p

    builtin = BUILTIN_TEMPLATE_DIR / skill_type
    if builtin.is_dir() and any(builtin.glob('*.j2')):
        return builtin

    return None


def _generate_legacy(skill_dir: Path, expanded: dict):
    """旧路径：DEFAULT_TEMPLATES + 字符串替换。"""
    for filename, template_content in DEFAULT_TEMPLATES.items():
        content = template_content
        for key, value in expanded.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        file_path = skill_dir / filename
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ 已创建：{file_path.name}")

        if filename.endswith('.py'):
            os.chmod(file_path, 0o755)


def _generate_jinja2(skill_dir: Path, tpl_dir: Path, expanded: dict):
    """Jinja2 渲染路径：从 .j2 文件生成产物。"""
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        keep_trailing_newline=True,
    )

    for tpl_file in sorted(tpl_dir.glob('*.j2')):
        output_name = tpl_file.name.removesuffix('.j2')
        template = env.get_template(tpl_file.name)
        content = template.render(**expanded)

        file_path = skill_dir / output_name
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ 已创建：{file_path.name}")

        if output_name.endswith(('.py', '.sh')):
            os.chmod(file_path, 0o755)


def generate_files(skill_dir: Path, variables: dict,
                   skill_type: str = 'python',
                   template_dir: str | None = None):
    """根据模板生成 skill 文件。

    向后兼容：skill_type='python' + template_dir=None 时，
    若内置 .j2 模板存在则用 Jinja2 渲染，否则回退到 DEFAULT_TEMPLATES。

    Args:
        skill_dir: 目标 skill 目录
        variables: 模板变量字典
        skill_type: Skill 类型（python / shell）
        template_dir: 用户自定义模板目录路径
    """
    if skill_type not in SUPPORTED_TYPES:
        raise ValueError(
            f"不支持的 Skill 类型：{skill_type}（支持：{', '.join(SUPPORTED_TYPES)}）"
        )

    expanded = _expand_variables(variables)
    tpl_dir = _discover_template_dir(skill_type, template_dir)

    if tpl_dir is None:
        _generate_legacy(skill_dir, expanded)
    else:
        _generate_jinja2(skill_dir, tpl_dir, expanded)
