"""
skills-temp/README.md 管理（兼容层）

Phase 4 起，README.md 为 .state.json 的只读视图，由 state_manager.regenerate_readme() 生成。
本模块保留历史 API 供可能的外部引用兼容，内部转发到 state_manager。
"""
from pathlib import Path

from creator.state_manager import add_skill, regenerate_readme


def set_readme_entry(
    skill_name: str,
    status: str,
    date: str,
    comment: str = "",
    target_path: str = "",
) -> bool:
    """兼容接口：直接触发 README 重新生成。

    Phase 4 后所有状态变更已通过 state_manager 完成并自动 regenerate。
    此函数仅作兼容保留，实际只触发一次 regenerate。
    """
    regenerate_readme()
    return True


def update_skills_temp_readme(skill_name: str, skill_dir: Path, score: int = None):
    """兼容接口：转发到 state_manager.add_skill。"""
    try:
        add_skill(skill_name, score=score)
    except Exception as e:
        print(f"⚠️  更新状态失败：{e}")
