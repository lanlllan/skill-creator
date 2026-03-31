"""
validate 命令 — 验证 skill 并评分
"""
from pathlib import Path

from creator.commands.create import validate_skill
from creator.scorer import SkillScorer


def main_validate(args):
    skill_path = Path(args.path).resolve()
    if not skill_path.exists():
        print(f"❌ 路径不存在：{skill_path}")
        return 1
    if not skill_path.is_dir():
        print(f"❌ 不是目录：{skill_path}")
        return 1

    print(f"🔍 验证 skill：{skill_path}")
    errors, warnings = validate_skill(skill_path)

    if errors:
        print("\n❌ 错误：")
        for e in errors:
            print(f"  {e}")

    if warnings:
        print("\n⚠️  警告：")
        for w in warnings:
            print(f"  {w}")

    no_security = getattr(args, 'no_security', False)
    if not no_security:
        from creator.security import scan_directory
        security_findings = scan_directory(skill_path)
        if security_findings:
            print("\n🔒 安全扫描：")
            for finding in security_findings:
                loc = f"{finding.file}:{finding.line}" if finding.line is not None else finding.file
                print(f"  ⚠️  [security] [{finding.rule_id}] {loc}")
                print(f"     {finding.message}")

    if errors:
        return 1

    print("\n📊 正在进行质量评分...")
    scorer = SkillScorer(skill_path)
    scorer.score()
    print(scorer.generate_report())

    print("✅ Skill 验证通过！")
    return 0
