"""
Phase 7 验证能力增强 — 测试套件

覆盖 7 项新增检查维度：
  1. 入口脚本 shebang
  2. 入口脚本 docstring / 文件头注释
  3. 入口脚本异常处理
  4. 入口脚本退出码
  5. 文档完整度（USAGE.md + SKILL.md 章节）
  6. 占位符残留检测（error 级别）
  7. Markdown 本地链接有效性
"""
import os
import pytest
from pathlib import Path

from creator.commands.create import (
    validate_skill,
    _validate_entry_script,
    _validate_doc_completeness,
    _validate_placeholder_residue,
    _validate_markdown_links,
)

GOOD_FRONT_MATTER = """\
---
name: test-skill
description: A test skill
version: 1.0.0
---
"""

GOOD_PYTHON_ENTRY = """\
#!/usr/bin/env python3
\"\"\"Test skill entry.\"\"\"
import sys

def main():
    try:
        print("ok")
    except Exception as e:
        print(f"err: {e}")
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
"""

GOOD_SHELL_ENTRY = """\
#!/usr/bin/env bash
# Shell skill entry — automated task runner
set -euo pipefail
main() { echo "ok"; }
main "$@"
exit 0
"""


@pytest.fixture
def good_skill(tmp_path):
    """创建一个完全合格的 Python skill 目录。"""
    d = tmp_path / "good-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        GOOD_FRONT_MATTER + "\n## 概述\n## 核心能力\n## 使用方式\n## 示例\n",
        encoding='utf-8',
    )
    entry = d / "run.py"
    entry.write_text(GOOD_PYTHON_ENTRY, encoding='utf-8')
    os.chmod(entry, 0o755)
    (d / "USAGE.md").write_text("# usage", encoding='utf-8')
    (d / "README.md").write_text(
        "# readme\n\n[SKILL](SKILL.md) [USAGE](USAGE.md)\n",
        encoding='utf-8',
    )
    return d


@pytest.fixture
def good_shell_skill(tmp_path):
    """创建一个完全合格的 Shell skill 目录。"""
    d = tmp_path / "shell-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        GOOD_FRONT_MATTER + "\n## 概述\n## 核心能力\n## 使用方式\n## 示例\n",
        encoding='utf-8',
    )
    entry = d / "run.sh"
    entry.write_text(GOOD_SHELL_ENTRY, encoding='utf-8')
    os.chmod(entry, 0o755)
    (d / "USAGE.md").write_text("# usage", encoding='utf-8')
    (d / "README.md").write_text("# readme\n", encoding='utf-8')
    return d


class TestBackwardCompatibility:
    def test_good_skill_passes(self, good_skill):
        errors, warnings = validate_skill(good_skill)
        assert errors == []

    def test_good_shell_skill_passes(self, good_shell_skill):
        errors, warnings = validate_skill(good_shell_skill)
        assert errors == []


class TestShebangCheck:
    def test_python_no_shebang(self, good_skill):
        (good_skill / "run.py").write_text('import sys\n', encoding='utf-8')
        _, warnings = validate_skill(good_skill)
        assert any('shebang' in w for w in warnings)

    def test_python_with_shebang(self, good_skill):
        _, warnings = validate_skill(good_skill)
        assert not any('shebang' in w for w in warnings)

    def test_shell_no_shebang(self, good_shell_skill):
        (good_shell_skill / "run.sh").write_text('echo hello\n', encoding='utf-8')
        _, warnings = validate_skill(good_shell_skill)
        assert any('shebang' in w for w in warnings)

    def test_shell_with_shebang(self, good_shell_skill):
        _, warnings = validate_skill(good_shell_skill)
        assert not any('shebang' in w for w in warnings)


class TestDocstringCheck:
    def test_python_no_docstring(self, good_skill):
        (good_skill / "run.py").write_text(
            '#!/usr/bin/env python3\nimport sys\ntry:\n  pass\nexcept:\n  pass\nreturn 0\n',
            encoding='utf-8',
        )
        _, warnings = validate_skill(good_skill)
        assert any('docstring' in w for w in warnings)

    def test_python_with_docstring(self, good_skill):
        _, warnings = validate_skill(good_skill)
        assert not any('docstring' in w for w in warnings)

    def test_shell_no_header_comment(self, good_shell_skill):
        (good_shell_skill / "run.sh").write_text(
            '#!/usr/bin/env bash\nset -e\nexit 0\n', encoding='utf-8'
        )
        _, warnings = validate_skill(good_shell_skill)
        assert any('注释' in w for w in warnings)

    def test_shell_with_header_comment(self, good_shell_skill):
        _, warnings = validate_skill(good_shell_skill)
        assert not any('注释' in w for w in warnings)


class TestExceptionHandlingCheck:
    def test_python_no_try_except(self, good_skill):
        (good_skill / "run.py").write_text(
            '#!/usr/bin/env python3\n"""doc"""\nimport sys\ndef main():\n  return 0\n',
            encoding='utf-8',
        )
        _, warnings = validate_skill(good_skill)
        assert any('try/except' in w for w in warnings)

    def test_python_with_try_except(self, good_skill):
        _, warnings = validate_skill(good_skill)
        assert not any('try/except' in w for w in warnings)

    def test_shell_no_error_handling(self, good_shell_skill):
        (good_shell_skill / "run.sh").write_text(
            '#!/usr/bin/env bash\n# my tool\necho hello\nexit 0\n',
            encoding='utf-8',
        )
        _, warnings = validate_skill(good_shell_skill)
        assert any('set -e' in w or 'trap' in w for w in warnings)

    def test_shell_with_set_e(self, good_shell_skill):
        _, warnings = validate_skill(good_shell_skill)
        assert not any('set -e' in w or 'trap' in w for w in warnings)


class TestExitCodeCheck:
    def test_python_no_exit_code(self, good_skill):
        (good_skill / "run.py").write_text(
            '#!/usr/bin/env python3\n"""doc"""\ntry:\n  pass\nexcept:\n  pass\n',
            encoding='utf-8',
        )
        _, warnings = validate_skill(good_skill)
        assert any('退出码' in w for w in warnings)

    def test_python_with_return_0(self, good_skill):
        _, warnings = validate_skill(good_skill)
        assert not any('退出码' in w for w in warnings)

    def test_shell_no_exit(self, good_shell_skill):
        (good_shell_skill / "run.sh").write_text(
            '#!/usr/bin/env bash\n# my tool\nset -e\necho hello\n',
            encoding='utf-8',
        )
        _, warnings = validate_skill(good_shell_skill)
        assert any('exit' in w for w in warnings)

    def test_shell_with_exit(self, good_shell_skill):
        _, warnings = validate_skill(good_shell_skill)
        assert not any('exit' in w and '未发现' in w for w in warnings)


class TestDocCompleteness:
    def test_no_usage_md(self, good_skill):
        (good_skill / "USAGE.md").unlink()
        _, warnings = validate_skill(good_skill)
        assert any('USAGE.md' in w for w in warnings)

    def test_skill_md_missing_sections(self, good_skill):
        (good_skill / "SKILL.md").write_text(
            GOOD_FRONT_MATTER + "\n## 概述\n一些内容\n", encoding='utf-8'
        )
        _, warnings = validate_skill(good_skill)
        assert any('缺少推荐章节' in w for w in warnings)

    def test_skill_md_all_sections(self, good_skill):
        _, warnings = validate_skill(good_skill)
        assert not any('缺少推荐章节' in w for w in warnings)


class TestPlaceholderResidue:
    def test_no_placeholders(self, good_skill):
        errors, _ = validate_skill(good_skill)
        assert not any('占位符' in e for e in errors)

    def test_md_with_placeholders(self, good_skill):
        (good_skill / "SKILL.md").write_text(
            GOOD_FRONT_MATTER + "\n{{name}} 未替换\n", encoding='utf-8'
        )
        errors, _ = validate_skill(good_skill)
        assert any('占位符' in e for e in errors)
        assert any('{{name}}' in e for e in errors)

    def test_py_with_placeholders(self, good_skill):
        (good_skill / "run.py").write_text(
            '#!/usr/bin/env python3\n"""{{description}}"""\n', encoding='utf-8'
        )
        errors, _ = validate_skill(good_skill)
        assert any('占位符' in e for e in errors)

    def test_placeholder_is_error_not_warning(self, good_skill):
        (good_skill / "extra.md").write_text("{{version}}", encoding='utf-8')
        errors, warnings = validate_skill(good_skill)
        assert any('占位符' in e for e in errors)
        assert not any('占位符' in w for w in warnings)

    def test_jinja2_templates_skipped(self, good_skill):
        """j2 后缀的模板文件不应触发占位符检测。"""
        (good_skill / "template.md.j2").write_text("{{ name }}", encoding='utf-8')
        errors, _ = validate_skill(good_skill)
        assert not any('占位符' in e for e in errors)

    def test_subdirectory_placeholder_detected(self, good_skill):
        """子目录中的占位符残留也应被检测到。"""
        sub = good_skill / "sub"
        sub.mkdir()
        (sub / "inner.md").write_text("{{name}} 残留", encoding='utf-8')
        errors, _ = validate_skill(good_skill)
        assert any('占位符' in e and 'inner.md' in e for e in errors)


class TestMarkdownLinks:
    def test_valid_local_links(self, good_skill):
        _, warnings = validate_skill(good_skill)
        assert not any('指向不存在的文件' in w for w in warnings)

    def test_broken_local_link(self, good_skill):
        (good_skill / "README.md").write_text(
            "# readme\n\n[missing](NOT_EXIST.md)\n", encoding='utf-8'
        )
        _, warnings = validate_skill(good_skill)
        assert any('NOT_EXIST.md' in w for w in warnings)

    def test_external_links_ignored(self, good_skill):
        (good_skill / "README.md").write_text(
            "# readme\n\n[google](https://google.com)\n", encoding='utf-8'
        )
        _, warnings = validate_skill(good_skill)
        assert not any('指向不存在的文件' in w for w in warnings)

    def test_anchor_links_ignored(self, good_skill):
        (good_skill / "README.md").write_text(
            "# readme\n\n[section](#overview)\n", encoding='utf-8'
        )
        _, warnings = validate_skill(good_skill)
        assert not any('指向不存在的文件' in w for w in warnings)

    def test_subdirectory_broken_link_detected(self, good_skill):
        """子目录中的 Markdown 失效链接也应被检测到。"""
        sub = good_skill / "docs"
        sub.mkdir()
        (sub / "guide.md").write_text("[missing](NOPE.md)\n", encoding='utf-8')
        _, warnings = validate_skill(good_skill)
        assert any('NOPE.md' in w for w in warnings)


class TestUnitValidators:
    def test_validate_entry_script_function(self, tmp_path):
        entry = tmp_path / "run.py"
        entry.write_text('print("no shebang")\n', encoding='utf-8')
        warnings = []
        _validate_entry_script(entry, warnings)
        assert len(warnings) >= 1
        assert any('shebang' in w for w in warnings)

    def test_validate_placeholder_no_false_positive(self, tmp_path):
        d = tmp_path / "clean"
        d.mkdir()
        (d / "README.md").write_text("# hello world\n", encoding='utf-8')
        errors = []
        _validate_placeholder_residue(d, errors)
        assert errors == []

    def test_validate_markdown_links_function(self, tmp_path):
        d = tmp_path / "links"
        d.mkdir()
        (d / "A.md").write_text("[B](B.md)\n", encoding='utf-8')
        warnings = []
        _validate_markdown_links(d, warnings)
        assert any('B.md' in w for w in warnings)

        (d / "B.md").write_text("# B\n", encoding='utf-8')
        warnings.clear()
        _validate_markdown_links(d, warnings)
        assert not any('B.md' in w for w in warnings)
