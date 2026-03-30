"""
spec 命令 — 规约骨架生成与验证
"""
from pathlib import Path

from creator.spec import (
    generate_spec_skeleton, save_spec, load_spec, validate_spec,
    SPEC_FILENAME,
)


def main_spec(args) -> int:
    """spec 子命令入口。

    模式 A：生成规约骨架
        spec -n my-skill -d "描述" [-o dir]

    模式 B：验证规约文件
        spec --validate path/to/.skill-spec.yaml

    退出码：
        0 - 成功
        1 - 验证失败（有 error 级别问题）
    """
    if args.validate:
        return _validate_mode(args)
    return _generate_mode(args)


def _generate_mode(args) -> int:
    """生成规约骨架。"""
    if not args.name or not args.description:
        print("❌ 生成模式下 --name 和 --description 为必填参数")
        return 1

    params = {
        'name': args.name,
        'description': args.description,
        'version': getattr(args, 'version', '1.0.0') or '1.0.0',
        'author': getattr(args, 'author', None),
        'tags': getattr(args, 'tags', None),
    }

    spec = generate_spec_skeleton(params)

    output_dir = Path(args.output).resolve() if args.output else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    spec_path = output_dir / SPEC_FILENAME

    save_spec(spec, spec_path)

    print(f"📝 规约骨架已生成：{spec_path}")
    print("   请填充 purpose / capabilities / commands / error_handling 各字段")
    print(f"   填充完成后运行：python run.py spec --validate {spec_path}")
    return 0


def _validate_mode(args) -> int:
    """验证规约文件。"""
    spec_path = Path(args.validate)
    try:
        spec = load_spec(spec_path)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1
    except (ValueError, Exception) as e:
        print(f"❌ 规约加载失败：{e}")
        return 1

    errors, warnings = validate_spec(spec)

    for e in errors:
        print(f"  ❌ {e}")
    for w in warnings:
        print(f"  ⚠️  {w}")

    if errors:
        print(f"\n❌ 验证未通过（{len(errors)} 个错误，{len(warnings)} 个警告）")
        return 1

    if warnings:
        print(f"\n⚠️  验证通过，但有 {len(warnings)} 个警告")
    else:
        print("\n✅ 规约验证通过")
    return 0
