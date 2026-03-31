#!/usr/bin/env python3
"""File Analyzer — 分析文件和目录的统计信息。"""

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Result:
    """命令执行结果。"""
    success: bool
    message: str = ""

    def __bool__(self):
        return self.success


BINARY_EXTS = {".exe", ".dll", ".so", ".dylib", ".bin", ".zip", ".gz",
               ".tar", ".png", ".jpg", ".gif", ".ico", ".pdf", ".woff"}


def _is_text_file(path: Path) -> bool:
    """启发式判断文件是否为文本文件。"""
    if path.suffix.lower() in BINARY_EXTS:
        return False
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
        return b"\x00" not in chunk
    except (OSError, PermissionError):
        return False


def _human_size(size_bytes: int) -> str:
    """将字节数转换为可读格式。"""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _collect_files(root: Path) -> list[Path]:
    """递归收集目录中所有文件（排除隐藏目录）。"""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if not name.startswith("."):
                files.append(Path(dirpath) / name)
    return files


def validate_path(path_str: str) -> Result:
    """校验路径参数有效性。"""
    root = Path(path_str)
    if not root.exists():
        return Result(success=False, message=f"错误：路径不存在 — {root}")
    if not root.is_dir():
        return Result(success=False, message=f"错误：路径不是目录 — {root}")
    return Result(success=True)


def cmd_count(args) -> Result:
    """统计目录中所有文件的行数。"""
    check = validate_path(args.path)
    if not check:
        return check

    root = Path(args.path)
    verbose = getattr(args, "verbose", False)
    ext_filter = getattr(args, "ext", None)
    files = _collect_files(root)
    if ext_filter:
        files = [f for f in files if f.suffix == ext_filter]

    total_lines = 0
    ext_stats: dict[str, int] = {}
    skipped = 0
    for f in files:
        if not _is_text_file(f):
            skipped += 1
            continue
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            count = len(lines)
            total_lines += count
            ext = f.suffix or "(无扩展名)"
            ext_stats[ext] = ext_stats.get(ext, 0) + count
            if verbose:
                rel = f.relative_to(root)
                print(f"  📄 {rel}: {count} 行")
        except (OSError, PermissionError):
            skipped += 1
            continue

    if not ext_stats:
        return Result(success=True, message=f"📂 {root} — 无可统计的文本文件")

    lines_report = []
    for ext, count in sorted(ext_stats.items(), key=lambda x: -x[1]):
        lines_report.append(f"  {ext:12s}  {count:>8,} 行")

    msg = f"📊 行数统计 — {root}\n" + "\n".join(lines_report)
    msg += f"\n\n  {'合计':12s}  {total_lines:>8,} 行"
    if verbose and skipped:
        msg += f"\n  （跳过 {skipped} 个二进制/不可读文件）"
    return Result(success=True, message=msg)


def cmd_types(args) -> Result:
    """按文件扩展名统计分布。"""
    check = validate_path(args.path)
    if not check:
        return check

    root = Path(args.path)
    files = _collect_files(root)
    if not files:
        return Result(success=True, message=f"📂 {root} — 目录为空")

    ext_info: dict[str, dict] = {}
    total_size = 0
    for f in files:
        try:
            size = f.stat().st_size
        except OSError:
            continue
        ext = f.suffix or "(无扩展名)"
        info = ext_info.setdefault(ext, {"count": 0, "size": 0})
        info["count"] += 1
        info["size"] += size
        total_size += size

    lines = [f"📊 文件类型分布 — {root}"]
    lines.append(f"  {'扩展名':12s}  {'数量':>6s}  {'大小':>10s}  {'占比':>6s}")
    lines.append("  " + "-" * 42)
    for ext, info in sorted(ext_info.items(), key=lambda x: -x[1]["size"]):
        pct = (info["size"] / total_size * 100) if total_size else 0
        lines.append(f"  {ext:12s}  {info['count']:>6d}  {_human_size(info['size']):>10s}  {pct:>5.1f}%")
    lines.append(f"\n  合计：{sum(i['count'] for i in ext_info.values())} 个文件，{_human_size(total_size)}")
    return Result(success=True, message="\n".join(lines))


def cmd_top(args) -> Result:
    """输出最大文件排名。"""
    check = validate_path(args.path)
    if not check:
        return check

    root = Path(args.path)
    limit = getattr(args, "limit", 10) or 10
    files = _collect_files(root)
    sized = []
    for f in files:
        try:
            sized.append((f, f.stat().st_size))
        except OSError:
            continue

    if not sized:
        return Result(success=True, message=f"📂 {root} — 目录为空")

    sized.sort(key=lambda x: -x[1])
    lines = [f"📊 最大文件 Top {limit} — {root}"]
    for i, (f, size) in enumerate(sized[:limit], 1):
        rel = f.relative_to(root)
        lines.append(f"  {i:>3d}. {_human_size(size):>10s}  {rel}")
    return Result(success=True, message="\n".join(lines))


def main():
    """CLI 入口：参数解析与命令分发。"""
    parser = argparse.ArgumentParser(description="File Analyzer - 文件和目录统计分析")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    subparsers = parser.add_subparsers(dest="command")

    count_parser = subparsers.add_parser("count", help="统计行数")
    count_parser.add_argument("--path", required=True, help="目标目录路径")
    count_parser.add_argument("--ext", help="仅统计指定扩展名（如 .py）")

    types_parser = subparsers.add_parser("types", help="文件类型分布")
    types_parser.add_argument("--path", required=True, help="目标目录路径")

    top_parser = subparsers.add_parser("top", help="最大文件排名")
    top_parser.add_argument("--path", required=True, help="目标目录路径")
    top_parser.add_argument("--limit", type=int, default=10, help="显示前 N 个（默认 10）")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    dispatch = {"count": cmd_count, "types": cmd_types, "top": cmd_top}
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
