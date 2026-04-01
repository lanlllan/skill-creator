"""
路径解析模块

所有路径函数接受显式 project_root 参数（skill-creator/ 目录），
避免依赖 __file__ 自推断，确保模块化后路径计算不因文件位置变化而出错。

双模式路径策略：
  开发模式（SKILL_CREATOR_DEV=1 或 parent 下有 .git + tests）：
    get_skills_dir(project_root)      -> project_root.parent / "skills"
    get_skills_temp_dir(project_root) -> project_root.parent / "skills-temp"

  安装模式（默认，安全侧倒）：
    get_skills_dir(project_root)      -> project_root.parent（parent 即 skills 目录）
    get_skills_temp_dir(project_root) -> project_root / ".skills-temp"（内部隐藏目录）

  get_readme_path 始终继承 get_skills_temp_dir。

环境变量 OPENCLAW_SKILLS_TEMP / OPENCLAW_SKILLS_DIR 为最高优先级覆盖。
"""
import os
from pathlib import Path

_DEFAULT_PROJECT_ROOT = Path(__file__).parent.parent


def _is_dev_mode(project_root: Path) -> bool:
    """检测是否在开发仓库中运行。

    三级判定（高→低优先级）：
    1. SKILL_CREATOR_DEV=1 → 开发模式
    2. parent/.git 且 parent/tests 同时存在 → 开发模式
    3. 以上均不满足 → 安装模式（安全侧倒，路径不外溢）
    """
    if os.getenv('SKILL_CREATOR_DEV', '').strip() == '1':
        return True
    repo_root = project_root.parent
    return (repo_root / '.git').exists() and (repo_root / 'tests').exists()


def get_skills_temp_dir(project_root: Path = None) -> Path:
    """获取 skills-temp 目录路径。

    查找顺序：
    1. 环境变量 OPENCLAW_SKILLS_TEMP
    2. 开发模式 → project_root.parent / "skills-temp"
    3. 安装模式 → project_root / ".skills-temp"（内部隐藏目录，不外溢）
    """
    if project_root is None:
        project_root = _DEFAULT_PROJECT_ROOT
    env_path = os.getenv('OPENCLAW_SKILLS_TEMP')
    if env_path:
        return Path(env_path).expanduser().resolve()
    if _is_dev_mode(project_root):
        return (project_root.parent / "skills-temp").resolve()
    return (project_root / ".skills-temp").resolve()


def get_skills_dir(project_root: Path = None) -> Path:
    """获取正式技能归档目录。

    查找顺序：
    1. 环境变量 OPENCLAW_SKILLS_DIR
    2. 开发模式 → project_root.parent / "skills"
    3. 安装模式 → project_root.parent（parent 本身就是 skills 目录）
    """
    if project_root is None:
        project_root = _DEFAULT_PROJECT_ROOT
    env_path = os.getenv('OPENCLAW_SKILLS_DIR')
    if env_path:
        return Path(env_path).expanduser().resolve()
    if _is_dev_mode(project_root):
        return (project_root.parent / "skills").resolve()
    return project_root.parent.resolve()


def get_readme_path(project_root: Path = None) -> Path:
    """获取 skills-temp/README.md 路径。"""
    return get_skills_temp_dir(project_root) / "README.md"
