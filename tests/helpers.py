"""测试路径常量 - 所有测试文件统一从此模块获取项目路径。"""
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent / "skill-creator"
RUN_PY = str(SKILL_ROOT / "run.py")
