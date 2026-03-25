"""
validate 命令 — 验证 skill 并评分
"""
from pathlib import Path

from creator.commands.create import validate_skill
from creator.scorer import SkillScorer


def main_validate(args):
    skill_path = Path(args.path)
    if not skill_path.exists():
        print(f"❌ 路径不存在：{skill_path}")
        return 1

    print(f"🔍 验证 skill：{skill_path}")
    errors, warnings = validate_skill(skill_path)

    if errors:
        print("\n❌ 错误：")
        for e in errors:
            print(f"  {e}")
        return 1

    if warnings:
        print("\n⚠️  警告：")
        for w in warnings:
            print(f"  {w}")

    print("\n📊 正在进行质量评分...")
    scorer = SkillScorer(skill_path)
    scorer.score()
    print(scorer.generate_report())

    print("✅ Skill 验证通过！")
    return 0
