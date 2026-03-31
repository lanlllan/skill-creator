"""
package 命令 — 将 skill 打包为 .skill 格式 zip 包
"""
from pathlib import Path

from creator.packager import create_package


def main_package(args) -> int:
    """package 子命令入口。

    退出码：
        0 - 打包成功
        1 - 打包失败（路径无效 / 检查未通过 / 异常）
    """
    skill_dir = Path(args.path).resolve()
    output_dir = Path(args.output).resolve() if args.output else None
    force = args.force

    print(f"📦 打包 skill：{skill_dir.name}")
    print("🔍 前置检查...")

    result = create_package(skill_dir, output_dir=output_dir, force=force)

    if result.warnings:
        for w in result.warnings:
            print(f"  ⚠️  {w}")
    else:
        print("  ✅ 检查通过")

    if not result.success:
        print("\n❌ 打包失败：")
        for e in result.errors:
            print(f"  {e}")
        return 1

    if result.errors:
        print(f"\n⚠️  已忽略 {len(result.errors)} 项错误（--force）")

    size_kb = result.package_size / 1024
    if size_kb >= 1024:
        size_str = f"{size_kb / 1024:.1f} MB"
    else:
        size_str = f"{size_kb:.1f} KB"

    print(f"📁 收集文件：{result.file_count} 个")
    print(f"📦 创建包：{result.package_path} ({size_str})")
    print(f"🔑 SHA256: {result.sha256}")
    print("✅ 打包完成！")
    return 0
