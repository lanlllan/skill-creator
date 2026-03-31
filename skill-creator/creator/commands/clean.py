"""
clean 命令 — 清理 skills-temp 中的 skill 目录
"""
import shutil
from pathlib import Path

from creator.paths import get_skills_temp_dir
from creator.state_manager import remove_skill


def main_clean(args):
    skill_name = args.name
    dry_run = args.dry_run

    if args.source:
        src = Path(args.source).expanduser().resolve() / skill_name
    else:
        src = get_skills_temp_dir() / skill_name

    if not src.exists():
        print(f"❌ 源目录不存在：{src}")
        return 1

    try:
        if not dry_run:
            shutil.rmtree(str(src))
            print(f"✅ 已删除：{skill_name}")
        else:
            print(f"🗑️ [dry_run] 将删除：{src}")

        if not dry_run:
            try:
                remove_skill(skill_name)
                print(f"✅ 已移除状态记录：{skill_name}")
            except Exception as e:
                print(f"⚠️  状态更新失败（目录已删除）：{e}")

        return 0
    except Exception as e:
        print(f"❌ 清理失败：{e}")
        return 1
