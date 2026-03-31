"""
Phase 6 测试：模板系统增强

覆盖范围：
  1. 向后兼容 — 默认 python 类型产物与旧系统一致
  2. 新类型 — shell 类型创建、文件结构、无残留占位符
  3. 自定义模板 — --template-dir 覆盖内置模板
  4. Jinja2 条件渲染 — if/for 逻辑
  5. 模板发现优先级 — 用户目录 > 内置 > 回退
  6. 异常路径 — 无效类型、不存在目录、无 .j2 文件
  7. CLI 集成 — --type 和 --template-dir 参数端到端
"""
import os
import re
import sys
from pathlib import Path

import pytest

from creator.templates import (
    generate_files, DEFAULT_TEMPLATES, SUPPORTED_TYPES,
    BUILTIN_TEMPLATE_DIR, _expand_variables, _discover_template_dir,
)
from creator.commands.create import create_skill, validate_skill

PLACEHOLDER_PATTERN = re.compile(r"\{\{[^}]+\}\}")


def _make_variables(**overrides):
    base = {
        "name": "test-skill",
        "description": "测试描述",
        "version": "1.0.0",
        "author": "Test Author",
        "tags": ["test", "demo"],
        "date": "2026-01-01",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. 向后兼容
# ---------------------------------------------------------------------------
class TestBackwardCompatibility:
    """默认 python 类型产物应与旧 DEFAULT_TEMPLATES 系统输出一致。"""

    @pytest.fixture()
    def skill_dir(self, tmp_path):
        d = tmp_path / "compat-skill"
        d.mkdir()
        return d

    @pytest.fixture()
    def legacy_dir(self, tmp_path):
        d = tmp_path / "legacy-skill"
        d.mkdir()
        return d

    def test_python_default_matches_legacy(self, skill_dir, legacy_dir):
        """Jinja2 渲染的 python 模板与旧字符串替换输出逐字节一致。"""
        variables = _make_variables()

        from creator.templates import _expand_variables, _generate_legacy
        expanded = _expand_variables(variables)
        _generate_legacy(legacy_dir, expanded)

        generate_files(skill_dir, variables, skill_type='python')

        for fname in DEFAULT_TEMPLATES:
            new_content = (skill_dir / fname).read_text(encoding='utf-8')
            old_content = (legacy_dir / fname).read_text(encoding='utf-8')
            assert new_content == old_content, (
                f"{fname} 内容不一致（向后兼容失败）"
            )

    def test_default_type_is_python(self, skill_dir):
        generate_files(skill_dir, _make_variables())
        assert (skill_dir / "run.py").exists()
        assert (skill_dir / "SKILL.md").exists()

    def test_generate_files_no_extra_args(self, skill_dir):
        """不传 skill_type/template_dir 时不报错（签名向后兼容）。"""
        generate_files(skill_dir, _make_variables())
        assert len(list(skill_dir.iterdir())) == len(DEFAULT_TEMPLATES)


# ---------------------------------------------------------------------------
# 2. Shell 类型
# ---------------------------------------------------------------------------
class TestShellType:
    """shell 类型应生成 run.sh 而非 run.py，且无残留占位符。"""

    @pytest.fixture()
    def skill_dir(self, tmp_path):
        d = tmp_path / "shell-skill"
        d.mkdir()
        return d

    def test_shell_creates_run_sh(self, skill_dir):
        generate_files(skill_dir, _make_variables(), skill_type='shell')
        assert (skill_dir / "run.sh").exists()
        assert not (skill_dir / "run.py").exists()

    def test_shell_creates_skill_md(self, skill_dir):
        generate_files(skill_dir, _make_variables(), skill_type='shell')
        content = (skill_dir / "SKILL.md").read_text(encoding='utf-8')
        assert "type: shell" in content

    def test_shell_no_residual_placeholders(self, skill_dir):
        generate_files(skill_dir, _make_variables(), skill_type='shell')
        for f in skill_dir.iterdir():
            content = f.read_text(encoding='utf-8')
            found = PLACEHOLDER_PATTERN.findall(content)
            assert not found, f"{f.name} 中有残留占位符：{found}"

    def test_shell_all_expected_files(self, skill_dir):
        generate_files(skill_dir, _make_variables(), skill_type='shell')
        names = {f.name for f in skill_dir.iterdir()}
        assert "SKILL.md" in names
        assert "run.sh" in names
        assert "USAGE.md" in names
        assert "README.md" in names

    def test_shell_run_sh_content(self, skill_dir):
        generate_files(skill_dir, _make_variables(name="my-tool",
                                                   description="我的工具"),
                       skill_type='shell')
        content = (skill_dir / "run.sh").read_text(encoding='utf-8')
        assert "#!/usr/bin/env bash" in content
        assert "我的工具" in content
        assert "set -euo pipefail" in content

    def test_shell_name_title_rendered(self, skill_dir):
        generate_files(skill_dir, _make_variables(name="hello-world"),
                       skill_type='shell')
        content = (skill_dir / "SKILL.md").read_text(encoding='utf-8')
        assert "Hello World" in content


# ---------------------------------------------------------------------------
# 3. 自定义模板目录
# ---------------------------------------------------------------------------
class TestCustomTemplateDir:

    def _make_custom_templates(self, tpl_dir: Path):
        tpl_dir.mkdir(parents=True, exist_ok=True)
        (tpl_dir / "SKILL.md.j2").write_text(
            "custom: {{ name }} - {{ description }}",
            encoding='utf-8')
        (tpl_dir / "run.py.j2").write_text(
            "# custom entry\nprint('{{ name }}')",
            encoding='utf-8')

    def test_custom_dir_overrides_builtin(self, tmp_path):
        skill_dir = tmp_path / "out"
        skill_dir.mkdir()
        tpl_dir = tmp_path / "my-templates"
        self._make_custom_templates(tpl_dir)

        generate_files(skill_dir, _make_variables(name="custom-skill"),
                       template_dir=str(tpl_dir))

        content = (skill_dir / "SKILL.md").read_text(encoding='utf-8')
        assert content == "custom: custom-skill - 测试描述"

    def test_custom_dir_generates_only_present_templates(self, tmp_path):
        skill_dir = tmp_path / "out"
        skill_dir.mkdir()
        tpl_dir = tmp_path / "sparse-tpl"
        tpl_dir.mkdir()
        (tpl_dir / "SKILL.md.j2").write_text("only-skill: {{ name }}", encoding='utf-8')

        generate_files(skill_dir, _make_variables(), template_dir=str(tpl_dir))

        assert (skill_dir / "SKILL.md").exists()
        assert not (skill_dir / "run.py").exists()
        assert not (skill_dir / "README.md").exists()

    def test_nonexistent_dir_raises(self, tmp_path):
        skill_dir = tmp_path / "out"
        skill_dir.mkdir()
        with pytest.raises(FileNotFoundError, match="模板目录不存在"):
            generate_files(skill_dir, _make_variables(),
                           template_dir=str(tmp_path / "no-such-dir"))

    def test_dir_without_j2_raises(self, tmp_path):
        skill_dir = tmp_path / "out"
        skill_dir.mkdir()
        empty_tpl = tmp_path / "empty-tpl"
        empty_tpl.mkdir()

        with pytest.raises(FileNotFoundError, match="无 .j2 文件"):
            generate_files(skill_dir, _make_variables(),
                           template_dir=str(empty_tpl))


# ---------------------------------------------------------------------------
# 4. Jinja2 条件渲染
# ---------------------------------------------------------------------------
class TestJinja2Conditionals:

    @pytest.fixture()
    def skill_dir(self, tmp_path):
        d = tmp_path / "cond-skill"
        d.mkdir()
        return d

    def test_shell_has_config_true(self, skill_dir):
        """has_config=True 时 shell SKILL.md 包含 config.env 引用。"""
        variables = _make_variables(has_config=True)
        generate_files(skill_dir, variables, skill_type='shell')
        content = (skill_dir / "SKILL.md").read_text(encoding='utf-8')
        assert "config.env" in content

    def test_shell_has_config_false(self, skill_dir):
        """has_config=False 时 shell SKILL.md 不包含 config.env 引用。"""
        variables = _make_variables(has_config=False)
        generate_files(skill_dir, variables, skill_type='shell')
        content = (skill_dir / "SKILL.md").read_text(encoding='utf-8')
        assert "config.env" not in content

    def test_shell_usage_config_section(self, skill_dir):
        variables = _make_variables(has_config=True)
        generate_files(skill_dir, variables, skill_type='shell')
        content = (skill_dir / "USAGE.md").read_text(encoding='utf-8')
        assert "config.env" in content
        assert "source config.env" in content

    def test_shell_usage_no_config(self, skill_dir):
        variables = _make_variables(has_config=False)
        generate_files(skill_dir, variables, skill_type='shell')
        content = (skill_dir / "USAGE.md").read_text(encoding='utf-8')
        assert "暂无外部配置项" in content

    def test_custom_jinja2_if_block(self, tmp_path):
        """自定义模板中的 if 条件渲染。"""
        skill_dir = tmp_path / "out"
        skill_dir.mkdir()
        tpl_dir = tmp_path / "tpl"
        tpl_dir.mkdir()
        (tpl_dir / "output.txt.j2").write_text(
            "{% if enable_logging %}logging: on{% else %}logging: off{% endif %}",
            encoding='utf-8')

        generate_files(skill_dir, _make_variables(enable_logging=True),
                       template_dir=str(tpl_dir))
        assert (skill_dir / "output.txt").read_text(encoding='utf-8') == "logging: on"

    def test_custom_jinja2_for_loop(self, tmp_path):
        """自定义模板中的 for 循环渲染。"""
        skill_dir = tmp_path / "out"
        skill_dir.mkdir()
        tpl_dir = tmp_path / "tpl"
        tpl_dir.mkdir()
        (tpl_dir / "list.txt.j2").write_text(
            "{% for item in items %}{{ item }}\n{% endfor %}",
            encoding='utf-8')

        generate_files(skill_dir, _make_variables(items=["a", "b", "c"]),
                       template_dir=str(tpl_dir))
        content = (skill_dir / "list.txt").read_text(encoding='utf-8')
        assert "a\nb\nc\n" == content


# ---------------------------------------------------------------------------
# 5. 模板发现优先级
# ---------------------------------------------------------------------------
class TestTemplateDiscovery:

    def test_user_dir_takes_priority(self, tmp_path):
        """用户模板目录优先于内置模板。"""
        user_tpl = tmp_path / "user-tpl"
        user_tpl.mkdir()
        (user_tpl / "SKILL.md.j2").write_text("USER: {{ name }}", encoding='utf-8')

        result = _discover_template_dir('python', template_dir=str(user_tpl))
        assert result == user_tpl.resolve()

    def test_builtin_python_dir_exists(self):
        result = _discover_template_dir('python')
        assert result is not None
        assert result.is_dir()

    def test_builtin_shell_dir_exists(self):
        result = _discover_template_dir('shell')
        assert result is not None
        assert result.is_dir()

    def test_nonexistent_builtin_returns_none(self, tmp_path, monkeypatch):
        """内置目录不存在时回退到 None（触发 DEFAULT_TEMPLATES）。"""
        import creator.templates as tpl_mod
        monkeypatch.setattr(tpl_mod, 'BUILTIN_TEMPLATE_DIR', tmp_path / 'nowhere')
        result = _discover_template_dir('python')
        assert result is None


# ---------------------------------------------------------------------------
# 6. 异常路径
# ---------------------------------------------------------------------------
class TestErrorPaths:

    def test_unsupported_type_raises(self, tmp_path):
        skill_dir = tmp_path / "out"
        skill_dir.mkdir()
        with pytest.raises(ValueError, match="不支持的 Skill 类型"):
            generate_files(skill_dir, _make_variables(), skill_type='ruby')

    def test_supported_types_constant(self):
        assert 'python' in SUPPORTED_TYPES
        assert 'shell' in SUPPORTED_TYPES


# ---------------------------------------------------------------------------
# 7. _expand_variables 单元测试
# ---------------------------------------------------------------------------
class TestExpandVariables:

    def test_name_title_derived(self):
        result = _expand_variables({"name": "hello-world", "tags": []})
        assert result['name_title'] == "Hello World"

    def test_tags_list_formatted(self):
        result = _expand_variables({"name": "x", "tags": ["a", "b"]})
        assert result['tags'] == "[a, b]"

    def test_tags_empty_formatted(self):
        result = _expand_variables({"name": "x", "tags": []})
        assert result['tags'] == "[]"

    def test_has_config_default(self):
        result = _expand_variables({"name": "x", "tags": []})
        assert result['has_config'] is False

    def test_has_config_preserved(self):
        result = _expand_variables({"name": "x", "tags": [], "has_config": True})
        assert result['has_config'] is True


# ---------------------------------------------------------------------------
# 8. validate_skill 对 shell 类型的支持
# ---------------------------------------------------------------------------
class TestValidateSkillShellSupport:

    def test_shell_skill_validates_ok(self, tmp_path):
        """shell 类型 skill（有 run.sh 但无 run.py）验证应通过。"""
        skill_dir = tmp_path / "shell-test"
        skill_dir.mkdir()
        generate_files(skill_dir, _make_variables(), skill_type='shell')
        errors, warnings = validate_skill(skill_dir)
        assert not errors, f"验证错误：{errors}"

    def test_no_entry_script_fails(self, tmp_path):
        """既无 run.py 也无 run.sh 时验证应失败。"""
        skill_dir = tmp_path / "no-entry"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: test\nversion: 1.0.0\n---\ncontent",
            encoding='utf-8')
        errors, warnings = validate_skill(skill_dir)
        assert any("入口脚本" in e for e in errors)


# ---------------------------------------------------------------------------
# 9. create_skill 集成 — shell 类型端到端
# ---------------------------------------------------------------------------
class TestCreateSkillShellE2E:

    def test_shell_create_returns_0(self, skill_out):
        params = {
            "name": "shell-e2e",
            "description": "shell 端到端",
            "output": str(skill_out),
        }
        rc = create_skill(params, skill_type='shell')
        assert rc == 0

    def test_shell_create_has_run_sh(self, skill_out):
        params = {
            "name": "shell-files",
            "description": "shell 文件检查",
            "output": str(skill_out),
        }
        create_skill(params, skill_type='shell')
        skill_dir = skill_out / "shell-files"
        assert (skill_dir / "run.sh").exists()
        assert not (skill_dir / "run.py").exists()

    def test_shell_create_no_residual_placeholders(self, skill_out):
        params = {
            "name": "shell-placeholders",
            "description": "占位符检查",
            "output": str(skill_out),
        }
        create_skill(params, skill_type='shell')
        skill_dir = skill_out / "shell-placeholders"
        for f in skill_dir.iterdir():
            content = f.read_text(encoding='utf-8')
            found = PLACEHOLDER_PATTERN.findall(content)
            assert not found, f"{f.name} 残留占位符：{found}"

    def test_custom_template_create(self, skill_out, tmp_path):
        tpl_dir = tmp_path / "custom-tpl"
        tpl_dir.mkdir()
        (tpl_dir / "SKILL.md.j2").write_text(
            "---\nname: {{ name }}\ndescription: {{ description }}\n"
            "version: {{ version }}\n---\ncustom template",
            encoding='utf-8')
        (tpl_dir / "run.py.j2").write_text(
            "#!/usr/bin/env python3\nprint('{{ name }}')",
            encoding='utf-8')

        params = {
            "name": "custom-e2e",
            "description": "自定义模板",
            "output": str(skill_out),
        }
        rc = create_skill(params, template_dir=str(tpl_dir))
        assert rc == 0
        content = (skill_out / "custom-e2e" / "SKILL.md").read_text(encoding='utf-8')
        assert "custom template" in content


# ---------------------------------------------------------------------------
# 10. CLI 集成测试（通过 run.py 入口）
# ---------------------------------------------------------------------------
class TestCLIIntegration:

    def _run_cli(self, args: list[str]) -> int:
        """模拟 CLI 调用。"""
        sys_path_backup = sys.path[:]
        try:
            from helpers import SKILL_ROOT
            sys.path.insert(0, str(SKILL_ROOT))
            import run as cli_module
            import importlib
            importlib.reload(cli_module)
            sys.argv = ['run.py'] + args
            return cli_module.main()
        finally:
            sys.path = sys_path_backup

    def test_create_with_type_shell(self, skill_out):
        rc = self._run_cli([
            'create', '--name', 'cli-shell', '--description', 'CLI shell test',
            '--type', 'shell', '--output', str(skill_out),
        ])
        assert rc == 0
        assert (skill_out / "cli-shell" / "run.sh").exists()

    def test_create_with_type_python(self, skill_out):
        rc = self._run_cli([
            'create', '--name', 'cli-python', '--description', 'CLI python test',
            '--type', 'python', '--output', str(skill_out),
        ])
        assert rc == 0
        assert (skill_out / "cli-python" / "run.py").exists()

    def test_create_default_type(self, skill_out):
        rc = self._run_cli([
            'create', '--name', 'cli-default', '--description', 'default type',
            '--output', str(skill_out),
        ])
        assert rc == 0
        assert (skill_out / "cli-default" / "run.py").exists()

    def test_create_with_template_dir(self, skill_out, tmp_path):
        tpl_dir = tmp_path / "cli-tpl"
        tpl_dir.mkdir()
        (tpl_dir / "SKILL.md.j2").write_text(
            "---\nname: {{ name }}\ndescription: {{ description }}\n"
            "version: {{ version }}\n---\ncli-custom",
            encoding='utf-8')
        (tpl_dir / "run.py.j2").write_text(
            "#!/usr/bin/env python3\nprint('ok')",
            encoding='utf-8')

        rc = self._run_cli([
            'create', '--name', 'cli-custom', '--description', 'custom tpl',
            '--template-dir', str(tpl_dir), '--output', str(skill_out),
        ])
        assert rc == 0
        content = (skill_out / "cli-custom" / "SKILL.md").read_text(encoding='utf-8')
        assert "cli-custom" in content
