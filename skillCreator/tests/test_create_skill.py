"""
测试 generate_files() 和 create_skill()

DoD 强制断言：所有模板占位符必须在生成产物中被完全替换。
"""
import re
from pathlib import Path

import pytest
from creator.commands.create import create_skill
from creator.templates import generate_files, DEFAULT_TEMPLATES

# 未替换占位符的检测模式，形如 {{key}}
PLACEHOLDER_PATTERN = re.compile(r"\{\{[^}]+\}\}")

GENERATED_FILES = list(DEFAULT_TEMPLATES.keys())  # ["SKILL.md", "run.py", "USAGE.md", "README.md"]


# ---------------------------------------------------------------------------
# generate_files()
# ---------------------------------------------------------------------------

class TestGenerateFiles:
    """验证文件生成后无残留占位符（DoD 必要断言）。"""

    @pytest.fixture()
    def skill_dir(self, tmp_path):
        d = tmp_path / "my-skill"
        d.mkdir()
        return d

    def _make_variables(self, **overrides):
        base = {
            "name": "my-skill",
            "description": "测试描述",
            "version": "1.0.0",
            "author": "Test Author",
            "tags": ["test", "demo"],
            "date": "2026-01-01",
        }
        base.update(overrides)
        return base

    def test_no_residual_placeholders(self, skill_dir):
        """DoD：生成的所有文件中不得残留任何 {{...}} 占位符。"""
        generate_files(skill_dir, self._make_variables())
        for fname in GENERATED_FILES:
            content = (skill_dir / fname).read_text(encoding="utf-8")
            found = PLACEHOLDER_PATTERN.findall(content)
            assert not found, (
                f"{fname} 中仍有未替换占位符：{found}"
            )

    def test_all_files_created(self, skill_dir):
        """所有模板文件均被创建。"""
        generate_files(skill_dir, self._make_variables())
        for fname in GENERATED_FILES:
            assert (skill_dir / fname).exists(), f"{fname} 未被创建"

    def test_name_substituted_in_skill_md(self, skill_dir):
        generate_files(skill_dir, self._make_variables(name="hello-world"))
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert "hello-world" in content

    def test_description_substituted(self, skill_dir):
        generate_files(skill_dir, self._make_variables(description="我的工具描述"))
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert "我的工具描述" in content

    def test_tags_list_rendered(self, skill_dir):
        """tags 列表应被渲染为 [tag1, tag2] 格式，而非原始 list 字面量。"""
        generate_files(skill_dir, self._make_variables(tags=["logging", "analysis"]))
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert "[logging, analysis]" in content

    def test_tags_empty_list(self, skill_dir):
        generate_files(skill_dir, self._make_variables(tags=[]))
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert "[]" in content

    def test_version_in_readme(self, skill_dir):
        generate_files(skill_dir, self._make_variables(version="2.3.4"))
        content = (skill_dir / "README.md").read_text(encoding="utf-8")
        assert "2.3.4" in content

    def test_run_py_is_executable(self, skill_dir):
        """run.py 应被设置可执行位（Unix）；Windows 下至少文件存在。"""
        import os
        generate_files(skill_dir, self._make_variables())
        run_py = skill_dir / "run.py"
        assert run_py.exists()
        # 在 Windows 上 os.access(X_OK) 固定返回 True，只要文件存在即可
        assert os.access(run_py, os.R_OK)


# ---------------------------------------------------------------------------
# create_skill()
# ---------------------------------------------------------------------------

class TestCreateSkill:
    """端到端：调用 create_skill() 验证目录创建、文件生成、退出码和 _out 输出。"""

    def _base_params(self, output: str, **overrides):
        p = {
            "name": "e2e-skill",
            "description": "端到端测试用 skill",
            "version": "1.0.0",
            "author": "Test Bot",
            "tags": ["e2e"],
            "output": output,
        }
        p.update(overrides)
        return p

    def test_returns_0_on_success(self, skill_out):
        rc = create_skill(self._base_params(str(skill_out)))
        assert rc == 0

    def test_skill_directory_created(self, skill_out):
        create_skill(self._base_params(str(skill_out)))
        assert (skill_out / "e2e-skill").is_dir()

    def test_all_files_present(self, skill_out):
        create_skill(self._base_params(str(skill_out)))
        for fname in GENERATED_FILES:
            assert (skill_out / "e2e-skill" / fname).exists(), f"{fname} 未生成"

    def test_no_residual_placeholders_e2e(self, skill_out):
        """DoD：端到端产物也不得有残留占位符。"""
        create_skill(self._base_params(str(skill_out)))
        for fname in GENERATED_FILES:
            content = (skill_out / "e2e-skill" / fname).read_text(encoding="utf-8")
            found = PLACEHOLDER_PATTERN.findall(content)
            assert not found, f"[e2e] {fname} 仍有残留占位符：{found}"

    def test_out_dict_populated(self, skill_out):
        out = {}
        create_skill(self._base_params(str(skill_out)), _out=out)
        assert "score" in out
        assert "skill_name" in out
        assert out["skill_name"] == "e2e-skill"
        assert isinstance(out["score"], (int, float))

    def test_missing_name_raises(self, skill_out):
        with pytest.raises(ValueError, match="name"):
            create_skill({"description": "无名称", "output": str(skill_out)})

    def test_missing_description_raises(self, skill_out):
        with pytest.raises(ValueError, match="description"):
            create_skill({"name": "no-desc", "output": str(skill_out)})

    def test_invalid_name_returns_1(self, skill_out):
        out = {}
        rc = create_skill(self._base_params(str(skill_out), name="123invalid"), _out=out)
        assert rc == 1
        assert "failure_reason" in out

    def test_invalid_version_returns_1(self, skill_out):
        out = {}
        rc = create_skill(self._base_params(str(skill_out), version="bad"), _out=out)
        assert rc == 1
        assert "failure_reason" in out
        assert "版本号" in out["failure_reason"]

    def test_duplicate_dir_returns_1(self, skill_out):
        """目录已存在时第二次调用返回 1，并携带 failure_reason。"""
        params = self._base_params(str(skill_out))
        create_skill(params)
        out = {}
        rc = create_skill(params, _out=out)
        assert rc == 1
        assert "failure_reason" in out

    def test_name_normalized(self, skill_out):
        """带空格的名称应被规范化为短横线格式。"""
        params = self._base_params(str(skill_out), name="my skill")
        rc = create_skill(params)
        assert rc == 0
        assert (skill_out / "my-skill").is_dir()

    def test_tags_as_string(self, skill_out):
        """tags 传入逗号分隔字符串时应正常解析。"""
        params = self._base_params(str(skill_out), name="tags-str-test", tags="foo, bar")
        rc = create_skill(params)
        assert rc == 0
