#!/usr/bin/env python3
"""Simple Greeter — 根据姓名和语言生成个性化问候语。"""

import argparse
import sys
from dataclasses import dataclass


@dataclass
class Result:
    """命令执行结果。"""
    success: bool
    message: str = ""

    def __bool__(self):
        return self.success


GREETINGS = {
    "zh": "你好，{name}！欢迎使用 OpenClaw。",
    "en": "Hello, {name}! Welcome to OpenClaw.",
    "ja": "こんにちは、{name}さん！OpenClawへようこそ。",
}

SUPPORTED_LANGS = sorted(GREETINGS.keys())


def validate_name(name: str) -> Result:
    """校验姓名参数有效性。"""
    if not name or not name.strip():
        return Result(success=False, message="错误：--name 不能为空")
    if len(name.strip()) > 100:
        return Result(success=False, message="错误：姓名过长（最多 100 字符）")
    return Result(success=True)


def resolve_lang(lang: str, verbose: bool = False) -> str:
    """解析语言代码，不支持的语言回退到英文。"""
    if lang in GREETINGS:
        return lang
    if verbose:
        print(f"⚠️  不支持的语言 '{lang}'，可用语言：{', '.join(SUPPORTED_LANGS)}")
    print(f"⚠️  不支持的语言 '{lang}'，回退到英文 (en)")
    return "en"


def format_greeting(name: str, lang: str) -> str:
    """根据姓名和语言生成问候语。"""
    return GREETINGS[lang].format(name=name.strip())


def cmd_greet(args) -> Result:
    """生成个性化问候语。"""
    check = validate_name(args.name)
    if not check:
        return check

    verbose = getattr(args, "verbose", False)
    lang = resolve_lang(getattr(args, "lang", "zh") or "zh", verbose)
    greeting = format_greeting(args.name, lang)

    if verbose:
        print(f"📋 语言: {lang}, 姓名: {args.name.strip()}")
    return Result(success=True, message=greeting)


def cmd_check(args) -> Result:
    """检查指定语言代码是否受支持。"""
    lang = args.lang
    if lang in GREETINGS:
        return Result(success=True, message=f"✅ 语言 '{lang}' 受支持")
    return Result(success=False, message=f"❌ 语言 '{lang}' 不受支持，可用：{', '.join(SUPPORTED_LANGS)}")


def main():
    """CLI 入口：参数解析与命令分发。"""
    parser = argparse.ArgumentParser(description="Simple Greeter - 多语言问候语生成")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    subparsers = parser.add_subparsers(dest="command")

    greet_parser = subparsers.add_parser("greet", help="生成问候语")
    greet_parser.add_argument("--name", required=True, help="要问候的姓名")
    greet_parser.add_argument("--lang", default="zh",
                              choices=["zh", "en", "ja"],
                              help="语言代码（默认 zh）")

    check_parser = subparsers.add_parser("check", help="检查语言是否受支持")
    check_parser.add_argument("--lang", required=True, help="要检查的语言代码")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    dispatch = {"greet": cmd_greet, "check": cmd_check}
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
