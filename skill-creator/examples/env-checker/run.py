#!/usr/bin/env python3
"""Env Checker — 检查开发环境的依赖配置，验证 Python 版本、必备工具和环境变量是否就绪。"""

import argparse
import json
import os
import platform
import shutil
import sys
from dataclasses import dataclass


@dataclass
class Result:
    """命令执行结果。"""
    success: bool
    message: str = ""

    def __bool__(self):
        return self.success


DEFAULT_TOOLS = ["git", "python3"]
DEFAULT_ENV_VARS = ["PATH", "HOME"]
DEFAULT_PYTHON_MIN = "3.9"


def _parse_version(version_str: str) -> tuple[int, ...]:
    """将版本号字符串解析为整数元组，便于比较。"""
    parts = []
    for p in version_str.strip().split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts) or (0,)


def _check_python_version(min_version: str) -> tuple[bool, str]:
    """检查当前 Python 版本是否满足最低要求。"""
    current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    current_tuple = (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    required = _parse_version(min_version)
    ok = current_tuple >= required
    return ok, current


def _check_tool(tool_name: str) -> tuple[bool, str]:
    """检查命令行工具是否存在于 PATH 中。"""
    path = shutil.which(tool_name)
    if path:
        return True, path
    return False, ""


def _check_env_var(var_name: str) -> tuple[bool, str]:
    """检查环境变量是否已设置。"""
    value = os.environ.get(var_name)
    if value is not None:
        display = value[:60] + "..." if len(value) > 60 else value
        return True, display
    return False, ""


def cmd_check(args) -> Result:
    """检查开发环境是否满足要求。"""
    verbose = getattr(args, "verbose", False)
    dry_run = getattr(args, "dry_run", False)

    tools_str = getattr(args, "tools", None)
    tools = [t.strip() for t in tools_str.split(",") if t.strip()] if tools_str else DEFAULT_TOOLS

    env_vars_str = getattr(args, "env_vars", None)
    env_vars = [v.strip() for v in env_vars_str.split(",") if v.strip()] if env_vars_str else DEFAULT_ENV_VARS

    python_min = getattr(args, "python_min", None) or DEFAULT_PYTHON_MIN

    if dry_run:
        items = [f"Python >= {python_min}"]
        items.extend(f"工具: {t}" for t in tools)
        items.extend(f"变量: {v}" for v in env_vars)
        return Result(True, f"🔍 预览：将检查 {len(items)} 项\n" + "\n".join(f"  - {x}" for x in items))

    lines = ["🔍 环境检查", ""]
    all_ok = True

    py_ok, py_ver = _check_python_version(python_min)
    icon = "✅" if py_ok else "❌"
    lines.append(f"  {icon} Python 版本: {py_ver} (要求 >= {python_min})")
    if not py_ok:
        all_ok = False

    lines.append("")
    lines.append("  📦 命令行工具:")
    for tool in tools:
        ok, path = _check_tool(tool)
        if ok:
            detail = f" → {path}" if verbose else ""
            lines.append(f"    ✅ {tool}{detail}")
        else:
            lines.append(f"    ❌ {tool} — 未找到")
            all_ok = False

    lines.append("")
    lines.append("  🔑 环境变量:")
    for var in env_vars:
        ok, val = _check_env_var(var)
        if ok:
            detail = f" = {val}" if verbose else ""
            lines.append(f"    ✅ {var}{detail}")
        else:
            lines.append(f"    ❌ {var} — 未设置")
            all_ok = False

    lines.append("")
    if all_ok:
        lines.append("  🎉 环境检查全部通过！")
    else:
        lines.append("  ⚠️  部分检查未通过，请修复上述标记 ❌ 的项目")

    return Result(success=all_ok, message="\n".join(lines))


def cmd_report(args) -> Result:
    """生成环境配置快照报告。"""
    fmt = getattr(args, "format", "text") or "text"

    info = {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
        },
        "tools": {},
        "env_vars": {},
    }

    common_tools = ["git", "docker", "node", "npm", "python3", "pip", "curl", "make"]
    for tool in common_tools:
        path = shutil.which(tool)
        info["tools"][tool] = path or "(未安装)"

    important_vars = ["PATH", "HOME", "USER", "SHELL", "LANG", "VIRTUAL_ENV", "PYTHONPATH"]
    for var in important_vars:
        val = os.environ.get(var)
        if val is not None:
            info["env_vars"][var] = val[:100] + "..." if len(val) > 100 else val
        else:
            info["env_vars"][var] = "(未设置)"

    if fmt == "json":
        return Result(True, json.dumps(info, ensure_ascii=False, indent=2))

    lines = ["📋 环境配置报告", "=" * 40, ""]

    lines.append("🖥️  操作系统:")
    lines.append(f"  系统: {info['os']['system']} {info['os']['release']}")
    lines.append(f"  架构: {info['os']['machine']}")

    lines.append("")
    lines.append("🐍 Python:")
    lines.append(f"  版本: {info['python']['version']}")
    lines.append(f"  路径: {info['python']['executable']}")
    lines.append(f"  实现: {info['python']['implementation']}")

    lines.append("")
    lines.append("📦 常用工具:")
    for tool, path in info["tools"].items():
        icon = "✅" if path != "(未安装)" else "⬚ "
        lines.append(f"  {icon} {tool}: {path}")

    lines.append("")
    lines.append("🔑 环境变量:")
    for var, val in info["env_vars"].items():
        icon = "✅" if val != "(未设置)" else "⬚ "
        lines.append(f"  {icon} {var}: {val}")

    return Result(True, "\n".join(lines))


def main():
    """CLI 入口：参数解析与命令分发。"""
    parser = argparse.ArgumentParser(description="Env Checker - 开发环境检查")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="环境检查")
    check_parser.add_argument("--dry-run", action="store_true",
                              help="预览检查项但不实际执行")
    check_parser.add_argument("--tools",
                              help="必须存在的工具（逗号分隔，如 git,docker,node）")
    check_parser.add_argument("--env-vars",
                              help="必须设置的环境变量（逗号分隔，如 HOME,PATH）")
    check_parser.add_argument("--python-min", default=DEFAULT_PYTHON_MIN,
                              help=f"Python 最低版本（默认 {DEFAULT_PYTHON_MIN}）")

    report_parser = subparsers.add_parser("report", help="环境报告")
    report_parser.add_argument("--format", choices=["text", "json"],
                               default="text", help="输出格式（默认 text）")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    dispatch = {"check": cmd_check, "report": cmd_report}
    try:
        result = dispatch[args.command](args)
        print(result.message)
        return 0 if result.success else 1
    except FileNotFoundError as exc:
        print(f"❌ 文件未找到：{exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"❌ 执行失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
