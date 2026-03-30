#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Creator - 创建符合 OpenClaw 规范的新 Skill

CLI 入口，仅负责参数解析与命令分发。
业务逻辑位于 creator/ 包中。
"""

import argparse
import sys
from pathlib import Path

# 确保 skillCreator/ 目录在 sys.path 中，使 creator 包可被直接引用
sys.path.insert(0, str(Path(__file__).parent))

from creator.commands.create import main_create
from creator.commands.validate import main_validate
from creator.commands.archive import main_archive
from creator.commands.clean import main_clean
from creator.commands.batch import main_batch
from creator.commands.scan import main_scan
from creator.commands.package import main_package


def main():
    parser = argparse.ArgumentParser(
        description='Skill Creator - 创建符合 OpenClaw 规范的新 Skill',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式创建
  python run.py create --interactive
  
  # 快速创建
  python run.py create --name "my-skill" --description "我的技能" --tags tool,utility
  
  # 验证现有 skill
  python run.py validate ~/.openclaw/workspace/skills/test-writer
  
  # 归档 skill
  python run.py archive my-skill --dest ~/.openclaw/workspace/skills
  
  # 清理待确认技能（删除并移除 README 条目）
  python run.py clean my-skill

工作流:
  1. 使用 `create` 创建新 skill（生在 skills-temp/）
  2. 检查和修改生成的文件
  3. 提交用户确认（在 skills-temp/README.md 查看状态）
  4. 使用 `archive` 将确认后的 skill 归档到正式目录
  5. 使用 `clean` 删除旧的临时目录（可选）
  6. 运行 `openclaw skills list` 验证归档结果
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    create_parser = subparsers.add_parser('create', help='创建新 skill')
    create_parser.add_argument('--name', '-n', help='技能名称（小写、短横线）')
    create_parser.add_argument('--description', '-d', help='技能描述')
    create_parser.add_argument('--version', '-v', default='1.0.0', help='版本号（默认 1.0.0，格式 x.y.z）')
    create_parser.add_argument('--author', '-a', help='作者（默认 OpenClaw Assistant）')
    create_parser.add_argument('--tags', '-t', help='标签，逗号分隔（如 tool,utility）')
    create_parser.add_argument('--output', '-o', help='输出目录（默认由程序自动解析 skills-temp 路径）')
    create_parser.add_argument('--interactive', '-i', action='store_true', help='交互式模式')
    create_parser.add_argument('--type', choices=['python', 'shell'],
                               default='python', help='Skill 类型（默认 python）')
    create_parser.add_argument('--template-dir', help='自定义模板目录路径（覆盖内置模板）')

    validate_parser = subparsers.add_parser('validate', help='验证 skill')
    validate_parser.add_argument('path', help='skill 目录路径')
    validate_parser.add_argument('--no-security', action='store_true',
                                 help='跳过安全扫描')

    archive_parser = subparsers.add_parser('archive', help='归档 skill')
    archive_parser.add_argument('name', help='技能名称')
    archive_parser.add_argument('--source', '-s', help='源目录（默认从 skills-temp 查找）')
    archive_parser.add_argument('--dest', help='目标目录（默认为程序自动推导的 skills/ 路径）')
    archive_parser.add_argument('--dry-run', action='store_true', help='演示操作不实际执行')

    clean_parser = subparsers.add_parser('clean', help='清理待确认技能目录')
    clean_parser.add_argument('name', help='技能名称')
    clean_parser.add_argument('--source', '-s', help='源目录（默认从 skills-temp 查找）')
    clean_parser.add_argument('--dry-run', action='store_true', help='演示操作不实际执行')

    batch_parser = subparsers.add_parser('batch', help='批量创建（从 YAML 列表）')
    batch_parser.add_argument('--file', '-f', required=True, help='技能列表文件（YAML 格式）')
    batch_parser.add_argument('--fail-on-security', action='store_true',
                              help='安全扫描有 error 级别发现时计为失败')

    scan_parser = subparsers.add_parser('scan', help='安全扫描 skill 目录')
    scan_parser.add_argument('path', help='skill 目录路径')
    scan_parser.add_argument('--json', action='store_true', help='JSON 格式输出')

    package_parser = subparsers.add_parser('package', help='打包 skill 为 .skill 文件')
    package_parser.add_argument('path', help='skill 目录路径')
    package_parser.add_argument('--output', '-o', help='包输出目录（默认 skill 同级目录）')
    package_parser.add_argument('--force', action='store_true',
                                help='即使 validate/scan 有 error 也强制打包')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    dispatch = {
        'create': main_create,
        'validate': main_validate,
        'archive': main_archive,
        'clean': main_clean,
        'batch': main_batch,
        'scan': main_scan,
        'package': main_package,
    }
    return dispatch[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
