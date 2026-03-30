"""
scan 命令 — 安全扫描 skill 目录
"""
from pathlib import Path

from creator.security import scan_directory, format_report


def main_scan(args) -> int:
    """安全扫描子命令入口。

    退出码：
        0 - 无发现或仅 info 级别
        1 - 存在 warning 或 error 级别发现
    """
    skill_path = Path(args.path).resolve()

    if not skill_path.exists():
        print(f"❌ 路径不存在：{skill_path}")
        return 1

    if not skill_path.is_dir():
        print(f"❌ 不是目录：{skill_path}")
        return 1

    json_mode = getattr(args, 'json', False)
    if not json_mode:
        print(f"🔒 安全扫描：{skill_path}")
    findings = scan_directory(skill_path)
    print(format_report(findings, json_output=json_mode))

    has_issues = any(f.severity in ('warning', 'error') for f in findings)
    return 1 if has_issues else 0
