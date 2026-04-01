#!/usr/bin/env python3
"""Data Formatter — 在 JSON、CSV、YAML 格式之间转换数据，并验证文件结构合法性。"""

import argparse
import csv
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SUPPORTED_FORMATS = {"json", "csv", "yaml"}


@dataclass
class Result:
    """命令执行结果。"""
    success: bool
    message: str = ""

    def __bool__(self):
        return self.success


def _detect_format(path: Path) -> str | None:
    """根据文件扩展名推断数据格式。"""
    ext = path.suffix.lower()
    mapping = {
        ".json": "json",
        ".csv": "csv",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    return mapping.get(ext)


def _read_json(path: Path) -> list[dict]:
    """读取 JSON 文件，返回字典列表。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("JSON 顶层应为对象或数组")


def _read_csv(path: Path) -> list[dict]:
    """读取 CSV 文件，返回字典列表。"""
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for line_no, row in enumerate(reader, start=2):
        if None in row:
            raise ValueError(f"第 {line_no} 行字段数与表头不匹配")
        rows.append(dict(row))
    return rows


def _read_yaml(path: Path) -> list[dict]:
    """读取 YAML 文件，返回字典列表。"""
    if yaml is None:
        raise ImportError("PyYAML 未安装，请运行 pip install pyyaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("YAML 顶层应为映射或序列")


def _write_json(records: list[dict]) -> str:
    """将记录列表序列化为 JSON 字符串。"""
    return json.dumps(records, ensure_ascii=False, indent=2)


def _write_csv(records: list[dict]) -> str:
    """将记录列表序列化为 CSV 字符串。"""
    if not records:
        return ""
    fieldnames = list(records[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in records:
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return buf.getvalue()


def _write_yaml(records: list[dict]) -> str:
    """将记录列表序列化为 YAML 字符串。"""
    if yaml is None:
        raise ImportError("PyYAML 未安装，请运行 pip install pyyaml")
    return yaml.dump(records, allow_unicode=True, default_flow_style=False)


READERS = {"json": _read_json, "csv": _read_csv, "yaml": _read_yaml}
WRITERS = {"json": _write_json, "csv": _write_csv, "yaml": _write_yaml}


def cmd_convert(args) -> Result:
    """将数据文件从一种格式转换为另一种格式。"""
    input_path = Path(args.input)
    if not input_path.exists():
        return Result(False, f"错误：源文件不存在 — {input_path}")

    src_fmt = _detect_format(input_path)
    if not src_fmt:
        return Result(False, f"错误：无法识别源文件格式 — {input_path.suffix}")

    target_fmt = args.to.lower()
    if target_fmt not in SUPPORTED_FORMATS:
        return Result(False, f"错误：不支持的目标格式 '{target_fmt}'（支持 json/csv/yaml）")

    verbose = getattr(args, "verbose", False)
    dry_run = getattr(args, "dry_run", False)
    if verbose:
        print(f"📋 转换: {input_path} ({src_fmt}) → {target_fmt}")

    try:
        records = READERS[src_fmt](input_path)
    except (json.JSONDecodeError, ValueError, ImportError) as e:
        return Result(False, f"错误：读取源文件失败 — {e}")

    if dry_run:
        count = len(records)
        return Result(True, f"🔍 预览：将转换 {count} 条记录（{src_fmt} → {target_fmt}），未实际写入")

    try:
        output_text = WRITERS[target_fmt](records)
    except (ImportError, TypeError) as e:
        return Result(False, f"错误：序列化失败 — {e}")

    output_path = getattr(args, "output", None)
    if output_path:
        Path(output_path).write_text(output_text, encoding="utf-8")
        count = len(records)
        return Result(True, f"✅ 转换完成：{count} 条记录 → {output_path}")

    return Result(True, output_text)


def cmd_validate(args) -> Result:
    """校验数据文件的格式合法性。"""
    input_path = Path(args.input)
    if not input_path.exists():
        return Result(False, f"错误：文件不存在 — {input_path}")

    fmt = _detect_format(input_path)
    if not fmt:
        return Result(False, f"错误：无法识别文件格式 — {input_path.suffix}")

    verbose = getattr(args, "verbose", False)
    if verbose:
        print(f"📋 校验: {input_path} (格式: {fmt})")

    try:
        records = READERS[fmt](input_path)
    except json.JSONDecodeError as e:
        return Result(False, f"❌ JSON 语法错误（第 {e.lineno} 行，第 {e.colno} 列）：{e.msg}")
    except ValueError as e:
        return Result(False, f"❌ 格式校验失败：{e}")
    except ImportError as e:
        return Result(False, f"❌ 依赖缺失：{e}")

    count = len(records)
    if count == 0:
        return Result(True, f"⚠️  {input_path} — 文件为空（格式合法，无数据记录）")

    field_counts = {len(r) for r in records if isinstance(r, dict)}
    if len(field_counts) > 1:
        return Result(False, f"❌ 记录字段数不一致：{sorted(field_counts)}")

    lines = [f"✅ {input_path} — 格式合法"]
    lines.append(f"   格式: {fmt.upper()}")
    lines.append(f"   记录数: {count}")
    if records and isinstance(records[0], dict):
        fields = list(records[0].keys())
        lines.append(f"   字段: {', '.join(fields[:8])}")
        if len(fields) > 8:
            lines.append(f"   （共 {len(fields)} 个字段）")
    return Result(True, "\n".join(lines))


def main():
    """CLI 入口：参数解析与命令分发。"""
    parser = argparse.ArgumentParser(description="Data Formatter - 数据格式转换与校验")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    subparsers = parser.add_subparsers(dest="command")

    convert_parser = subparsers.add_parser("convert", help="格式转换")
    convert_parser.add_argument("--input", required=True, help="源文件路径")
    convert_parser.add_argument("--to", required=True,
                                choices=["json", "csv", "yaml"],
                                help="目标格式")
    convert_parser.add_argument("--output", help="输出文件路径")
    convert_parser.add_argument("--dry-run", action="store_true",
                                help="预览转换结果但不写入文件")

    validate_parser = subparsers.add_parser("validate", help="格式校验")
    validate_parser.add_argument("--input", required=True, help="待校验的文件路径")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    dispatch = {"convert": cmd_convert, "validate": cmd_validate}
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
