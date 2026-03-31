"""
archive 命令 — 将 skill 从 skills-temp 归档到正式目录
"""
import shutil
from pathlib import Path

from creator.paths import get_skills_dir, get_skills_temp_dir
from creator.state_manager import archive_skill


def _check_legacy_archive_path(new_dest: Path):
    """检测旧 fallback 路径下是否残留归档 skill，打印迁移提示。"""
    legacy_dir = new_dest.parent
    try:
        legacy_skills = [
            d for d in legacy_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
            and d.name != "skill-creator"
        ]
    except OSError:
        return
    if legacy_skills:
        names = ", ".join(d.name for d in legacy_skills[:5])
        print(f"⚠️  检测到 {legacy_dir} 下存在归档 skill（{names}），"
              f"建议迁移到 {new_dest}/")


def main_archive(args):
    skill_name = args.name
    using_fallback = not args.dest
    dest_dir = Path(args.dest).expanduser().resolve() if args.dest else get_skills_dir()
    dry_run = args.dry_run

    if using_fallback:
        _check_legacy_archive_path(dest_dir)

    if args.source:
        src = Path(args.source).expanduser().resolve() / skill_name
    else:
        src = get_skills_temp_dir() / skill_name

    if not src.exists():
        print(f"❌ 源目录不存在：{src}")
        return 1

    if not dest_dir.exists():
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
        else:
            print(f"📦 [dry_run] 将创建目录：{dest_dir}")

    dst = dest_dir / skill_name
    if dst.exists():
        print(f"❌ 目标目录已存在，跳过归档：{dst}")
        return 1

    try:
        if not dry_run:
            shutil.move(str(src), str(dst))
            print(f"✅ 已归档：{skill_name} -> {dst}")

            try:
                archive_skill(skill_name, archived_to=str(dst))
                print(f"✅ 已更新状态：{skill_name} -> archived")
            except Exception as e:
                print(f"⚠️  状态更新失败（文件已归档）：{e}")

            return 0
        else:
            print(f"📦 [dry_run] 将移动：{src} -> {dst}")
            return 0
    except Exception as e:
        print(f"❌ 归档失败：{e}")
        return 1
