"""examples 子命令 — 列出、查看和复制内置样例。"""

from pathlib import Path
from creator.examples import list_examples, show_example, copy_example


COMPLEXITY_LABELS = {
    "beginner": "入门",
    "intermediate": "中等",
    "advanced": "进阶",
}


def main_examples(args) -> int:
    """examples 命令入口：根据参数分发到列出 / 查看 / 复制。"""
    show = getattr(args, "show", None)
    copy_name = getattr(args, "copy", None)
    output = getattr(args, "output", None)

    if show:
        content = show_example(show)
        print(content)
        return 1 if content.startswith("错误") else 0

    if copy_name:
        output_dir = Path(output) if output else Path(".")
        ok, msg = copy_example(copy_name, output_dir)
        print(msg)
        return 0 if ok else 1

    examples = list_examples()
    if not examples:
        print("⚠️  没有找到内置样例。")
        return 0

    print("📚 内置参考样例\n")
    for ex in examples:
        level = COMPLEXITY_LABELS.get(ex["complexity"], ex["complexity"])
        tags_str = ", ".join(ex["tags"]) if ex["tags"] else ""
        print(f"  📦 {ex['name']}")
        print(f"     {ex['description']}")
        print(f"     复杂度: {level}" + (f"  标签: {tags_str}" if tags_str else ""))
        print()

    print("用法:")
    print("  python run.py examples --show <name>        查看样例详情")
    print("  python run.py examples --copy <name> -o .   复制样例到当前目录")
    return 0
