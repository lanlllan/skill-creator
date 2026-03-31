"""
pytest 公共 fixtures

- skill_dir: 在 tmp_path 下创建一个 skill 目录，供 generate_files / create_skill 测试使用
- batch_yaml: 生成临时 YAML 文件的工厂 fixture
"""
import sys
import textwrap
from pathlib import Path

import pytest

# 将 tests/ 自身加入 sys.path，确保 helpers 模块可被各测试文件导入
sys.path.insert(0, str(Path(__file__).parent))
# 将 skill-creator/ 加入 sys.path，使 creator 包和 run.py 可被直接引用
sys.path.insert(0, str(Path(__file__).parent.parent / "skill-creator"))


@pytest.fixture()
def skill_out(tmp_path: Path) -> Path:
    """返回一个临时输出根目录（空），用于接收 create_skill 的产物。"""
    out = tmp_path / "out"
    out.mkdir()
    return out


@pytest.fixture()
def batch_yaml_factory(tmp_path: Path):
    """返回一个工厂函数，接收 YAML 字符串，写入临时文件并返回 Path。"""
    def _make(content: str) -> Path:
        p = tmp_path / "batch.yaml"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p
    return _make
