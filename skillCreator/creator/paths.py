"""
路径解析模块

所有路径函数接受显式 project_root 参数（skillCreator/ 目录），
避免依赖 __file__ 自推断，确保模块化后路径计算不因文件位置变化而出错。

路径公式（project_root = skillCreator/）：
  get_skills_dir(project_root)      -> project_root.parent
  get_skills_temp_dir(project_root) -> project_root.parent.parent / "skills-temp"
  get_readme_path(project_root)     -> get_skills_temp_dir(project_root) / "README.md"
"""
import os
from pathlib import Path

# 默认 project_root：本文件位于 skillCreator/creator/，
# parent = creator/，parent.parent = skillCreator/
_DEFAULT_PROJECT_ROOT = Path(__file__).parent.parent


def get_skills_temp_dir(project_root: Path = None) -> Path:
    """获取 skills-temp 目录路径。

    查找顺序（两级 fallback）：
    1. 环境变量 OPENCLAW_SKILLS_TEMP
    2. 脚本位置推断：project_root 上两级目录 / skills-temp
    """
    if project_root is None:
        project_root = _DEFAULT_PROJECT_ROOT
    env_path = os.getenv('OPENCLAW_SKILLS_TEMP')
    if env_path:
        return Path(env_path).expanduser().resolve()
    return (project_root.parent.parent / "skills-temp").resolve()


def get_skills_dir(project_root: Path = None) -> Path:
    """获取正式技能归档目录（skills/）。

    查找顺序：
    1. 环境变量 OPENCLAW_SKILLS_DIR
    2. project_root.parent（skill-creator/ 的上级目录）
    """
    if project_root is None:
        project_root = _DEFAULT_PROJECT_ROOT
    env_path = os.getenv('OPENCLAW_SKILLS_DIR')
    if env_path:
        p = Path(env_path).expanduser().resolve()
        if p.exists():
            return p
    return project_root.parent.resolve()


def get_readme_path(project_root: Path = None) -> Path:
    """获取 skills-temp/README.md 路径。"""
    return get_skills_temp_dir(project_root) / "README.md"
