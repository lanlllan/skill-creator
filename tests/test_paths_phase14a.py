"""
Phase 14a 测试：paths.py fallback 行为验证

覆盖范围：
- get_skills_temp_dir() fallback 返回 <repo>/skills-temp/
- get_skills_dir() fallback 返回 <repo>/skills/
- 环境变量优先级不变
- get_readme_path() 继承 get_skills_temp_dir()

合计：5 用例
"""
import os
import pytest
from pathlib import Path

from helpers import SKILL_ROOT
from creator.paths import get_skills_temp_dir, get_skills_dir, get_readme_path


REPO_ROOT = SKILL_ROOT.parent


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """确保每个测试开始时无路径环境变量干扰。"""
    monkeypatch.delenv('OPENCLAW_SKILLS_TEMP', raising=False)
    monkeypatch.delenv('OPENCLAW_SKILLS_DIR', raising=False)


class TestSkillsTempDirFallback:
    def test_fallback_within_repo(self):
        result = get_skills_temp_dir(project_root=SKILL_ROOT)
        assert result == (REPO_ROOT / "skills-temp").resolve()

    def test_env_override(self, monkeypatch, tmp_path):
        custom = tmp_path / "custom-temp"
        custom.mkdir()
        monkeypatch.setenv('OPENCLAW_SKILLS_TEMP', str(custom))
        result = get_skills_temp_dir(project_root=SKILL_ROOT)
        assert result == custom.resolve()


class TestSkillsDirFallback:
    def test_fallback_within_repo(self):
        result = get_skills_dir(project_root=SKILL_ROOT)
        assert result == (REPO_ROOT / "skills").resolve()

    def test_env_override(self, monkeypatch, tmp_path):
        custom = tmp_path / "custom-skills"
        custom.mkdir()
        monkeypatch.setenv('OPENCLAW_SKILLS_DIR', str(custom))
        result = get_skills_dir(project_root=SKILL_ROOT)
        assert result == custom.resolve()


class TestReadmePath:
    def test_inherits_temp_dir(self):
        result = get_readme_path(project_root=SKILL_ROOT)
        expected = (REPO_ROOT / "skills-temp" / "README.md").resolve()
        assert result == expected
