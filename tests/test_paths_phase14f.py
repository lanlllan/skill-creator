"""
Phase 14f 测试：路径环境自适应

覆盖范围：
- _is_dev_mode() 三级判定逻辑
- 开发模式路径不变（向后兼容 Phase 14a）
- 安装模式 get_skills_temp_dir() 指向内部 .skills-temp/
- 安装模式 get_skills_dir() 指向 parent
- 环境变量覆盖两种模式
- SKILL_CREATOR_DEV 强制开发模式

合计：12 用例
"""
import os
import pytest
from pathlib import Path

from creator.paths import _is_dev_mode, get_skills_temp_dir, get_skills_dir, get_readme_path
from helpers import SKILL_ROOT


REPO_ROOT = SKILL_ROOT.parent


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """确保每个测试开始时无路径环境变量干扰。"""
    monkeypatch.delenv('OPENCLAW_SKILLS_TEMP', raising=False)
    monkeypatch.delenv('OPENCLAW_SKILLS_DIR', raising=False)
    monkeypatch.delenv('SKILL_CREATOR_DEV', raising=False)


class TestIsDevMode:
    """三级判定逻辑：env > .git+tests > 安装模式默认。"""

    def test_real_repo_detected_as_dev(self):
        assert _is_dev_mode(SKILL_ROOT) is True

    def test_env_var_forces_dev_mode(self, monkeypatch, tmp_path):
        fake_root = tmp_path / "skill-creator"
        fake_root.mkdir()
        monkeypatch.setenv('SKILL_CREATOR_DEV', '1')
        assert _is_dev_mode(fake_root) is True

    def test_no_git_no_tests_is_install_mode(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        fake_root = skills_dir / "skill-creator"
        fake_root.mkdir()
        assert _is_dev_mode(fake_root) is False

    def test_git_only_no_tests_is_install_mode(self, tmp_path):
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / ".git").mkdir()
        fake_root = fake_repo / "skill-creator"
        fake_root.mkdir()
        assert _is_dev_mode(fake_root) is False

    def test_tests_only_no_git_is_install_mode(self, tmp_path):
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / "tests").mkdir()
        fake_root = fake_repo / "skill-creator"
        fake_root.mkdir()
        assert _is_dev_mode(fake_root) is False

    def test_git_and_tests_is_dev_mode(self, tmp_path):
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / ".git").mkdir()
        (fake_repo / "tests").mkdir()
        fake_root = fake_repo / "skill-creator"
        fake_root.mkdir()
        assert _is_dev_mode(fake_root) is True


class TestInstallModePaths:
    """安装模式下路径不外溢。"""

    def _make_install_env(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        fake_root = skills_dir / "skill-creator"
        fake_root.mkdir()
        return fake_root, skills_dir

    def test_skills_temp_dir_internal(self, tmp_path):
        fake_root, _ = self._make_install_env(tmp_path)
        result = get_skills_temp_dir(project_root=fake_root)
        assert result == (fake_root / ".skills-temp").resolve()

    def test_skills_dir_is_parent(self, tmp_path):
        fake_root, skills_dir = self._make_install_env(tmp_path)
        result = get_skills_dir(project_root=fake_root)
        assert result == skills_dir.resolve()

    def test_readme_path_internal(self, tmp_path):
        fake_root, _ = self._make_install_env(tmp_path)
        result = get_readme_path(project_root=fake_root)
        assert result == (fake_root / ".skills-temp" / "README.md").resolve()


class TestEnvOverridesBothModes:
    """环境变量在开发和安装模式下均为最高优先级。"""

    def test_env_overrides_install_mode_temp(self, monkeypatch, tmp_path):
        custom = tmp_path / "custom-temp"
        custom.mkdir()
        monkeypatch.setenv('OPENCLAW_SKILLS_TEMP', str(custom))
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        fake_root = skills_dir / "skill-creator"
        fake_root.mkdir()
        result = get_skills_temp_dir(project_root=fake_root)
        assert result == custom.resolve()

    def test_env_overrides_install_mode_skills(self, monkeypatch, tmp_path):
        custom = tmp_path / "custom-skills"
        custom.mkdir()
        monkeypatch.setenv('OPENCLAW_SKILLS_DIR', str(custom))
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        fake_root = skills_dir / "skill-creator"
        fake_root.mkdir()
        result = get_skills_dir(project_root=fake_root)
        assert result == custom.resolve()

    def test_env_skills_dir_nonexistent_still_honored(self, monkeypatch, tmp_path):
        """OPENCLAW_SKILLS_DIR 指向不存在目录时仍应返回该路径。"""
        nonexistent = tmp_path / "not-yet-created"
        monkeypatch.setenv('OPENCLAW_SKILLS_DIR', str(nonexistent))
        result = get_skills_dir(project_root=SKILL_ROOT)
        assert result == nonexistent.resolve()
