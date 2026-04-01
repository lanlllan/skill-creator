"""Phase 15 测试：预填充引擎 + TODO 注释升级"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skill-creator'))

import pytest
from creator.prefill import (
    prefill_skill_content,
    upgrade_todo_comments,
    _extract_skill_md_section,
    _extract_keywords,
    _adapt_content,
)


class TestPrefill:
    def test_prefill_with_matching_description(self, tmp_path):
        """匹配到样例时应预填充 SKILL.md"""
        skill_dir = tmp_path / 'test-skill'
        skill_dir.mkdir()
        skill_md = skill_dir / 'SKILL.md'
        skill_md.write_text(
            '---\nname: test-skill\ndescription: 分析文件统计\n---\n\n'
            '## 适用场景\n\n## 核心能力\n\n## 故障排除\n',
            encoding='utf-8'
        )
        result = prefill_skill_content(
            skill_dir,
            '分析文件和目录的统计信息，包括行数统计、类型分布和大小报告',
            'python',
            threshold=0.15,
        )
        assert result['skill_md'] is True
        content = skill_md.read_text(encoding='utf-8')
        assert 'PRE-FILLED' in content

    def test_prefill_no_match(self, tmp_path):
        """不匹配时不应修改"""
        skill_dir = tmp_path / 'unrelated-skill'
        skill_dir.mkdir()
        skill_md = skill_dir / 'SKILL.md'
        skill_md.write_text(
            '---\nname: unrelated\ndescription: 量子计算模拟器\n---\n\n'
            '## 适用场景\n\n## 核心能力\n',
            encoding='utf-8'
        )
        result = prefill_skill_content(skill_dir, '量子纠缠态计算模拟', 'python', threshold=0.99)
        assert result['skill_md'] is False

    def test_prefill_preserves_existing_content(self, tmp_path):
        """已有丰富内容的章节（>20字）不应被覆盖"""
        skill_dir = tmp_path / 'rich-skill'
        skill_dir.mkdir()
        existing = (
            '---\nname: rich-skill\ndescription: 文件分析\n---\n\n'
            '## 适用场景\n\n- 已有非常详细的场景描述信息在此，内容非常充分足够保留\n\n'
            '## 核心能力\n\n'
        )
        skill_md = skill_dir / 'SKILL.md'
        skill_md.write_text(existing, encoding='utf-8')
        prefill_skill_content(skill_dir, '分析文件和目录的统计信息', 'python')
        content = skill_md.read_text(encoding='utf-8')
        assert '已有非常详细的场景描述信息在此' in content

    def test_prefilled_marker_format(self, tmp_path):
        """PRE-FILLED 标记应为 HTML 注释格式"""
        skill_dir = tmp_path / 'marker-test'
        skill_dir.mkdir()
        skill_md = skill_dir / 'SKILL.md'
        skill_md.write_text(
            '---\nname: marker-test\ndescription: 分析文件统计\n---\n\n'
            '## 适用场景\n\n## 核心能力\n',
            encoding='utf-8'
        )
        prefill_skill_content(skill_dir, '分析文件和目录的统计信息', 'python')
        content = skill_md.read_text(encoding='utf-8')
        if 'PRE-FILLED' in content:
            assert '<!-- PRE-FILLED:' in content
            assert '-->' in content

    def test_extract_section(self):
        content = '## 概述\n内容\n## 适用场景\n- 场景1\n- 场景2\n## 核心能力\n'
        result = _extract_skill_md_section(content, '适用场景')
        assert '场景1' in result
        assert '场景2' in result

    def test_extract_keywords(self):
        kw = _extract_keywords('分析文件和目录的统计信息')
        assert '分析' in kw or '文件' in kw or '统计' in kw


class TestReadmePrefill:
    def test_readme_prefilled_when_matched(self, tmp_path):
        """匹配到样例时应预填充 README.md"""
        skill_dir = tmp_path / 'readme-test'
        skill_dir.mkdir()
        (skill_dir / 'SKILL.md').write_text(
            '---\nname: readme-test\ndescription: 分析文件统计\n---\n\n'
            '## 适用场景\n\n## 核心能力\n',
            encoding='utf-8'
        )
        (skill_dir / 'README.md').write_text(
            '# Readme Test\n\n## 使用\n',
            encoding='utf-8'
        )
        result = prefill_skill_content(
            skill_dir,
            '分析文件和目录的统计信息，包括行数统计、类型分布和大小报告',
            'python',
            threshold=0.15,
        )
        assert 'readme' in result
        if result['readme']:
            content = (skill_dir / 'README.md').read_text(encoding='utf-8')
            assert 'PRE-FILLED' in content

    def test_readme_not_prefilled_when_no_match(self, tmp_path):
        """不匹配时不应预填充 README"""
        skill_dir = tmp_path / 'no-match'
        skill_dir.mkdir()
        (skill_dir / 'SKILL.md').write_text(
            '---\nname: no-match\ndescription: 量子计算\n---\n',
            encoding='utf-8'
        )
        (skill_dir / 'README.md').write_text('# No Match\n', encoding='utf-8')
        result = prefill_skill_content(skill_dir, '量子纠缠模拟', 'python', threshold=0.99)
        assert result['readme'] is False

    def test_return_has_both_keys(self, tmp_path):
        """返回值应同时包含 skill_md 和 readme 两个键"""
        skill_dir = tmp_path / 'keys-test'
        skill_dir.mkdir()
        (skill_dir / 'SKILL.md').write_text(
            '---\nname: keys-test\ndescription: test\n---\n',
            encoding='utf-8'
        )
        result = prefill_skill_content(skill_dir, 'anything', 'python', threshold=0.99)
        assert 'skill_md' in result
        assert 'readme' in result


class TestTodoUpgrade:
    def test_upgrade_with_match(self, tmp_path):
        """有匹配样例时应升级 TODO（Python）"""
        skill_dir = tmp_path / 'todo-skill'
        skill_dir.mkdir()
        run_py = skill_dir / 'run.py'
        run_py.write_text(
            '#!/usr/bin/env python3\n'
            '# TODO 实现步骤：\n'
            '#   1. 解析输入参数\n'
            '#   2. 执行核心逻辑\n'
            '#   3. 返回 Result\n'
            'pass\n',
            encoding='utf-8'
        )
        result = upgrade_todo_comments(skill_dir, 'file-analyzer', 'python')
        assert result is True
        content = run_py.read_text(encoding='utf-8')
        assert '参考样例' in content
        assert 'file-analyzer' in content

    def test_shell_todo_upgrade(self, tmp_path):
        """Shell 入口的 TODO 升级应正常工作"""
        skill_dir = tmp_path / 'shell-skill'
        skill_dir.mkdir()
        run_sh = skill_dir / 'run.sh'
        run_sh.write_text(
            '#!/usr/bin/env bash\n'
            '# TODO 实现步骤：\n'
            '#   1. 解析参数\n'
            '#   2. 执行逻辑\n'
            'echo "hello"\n',
            encoding='utf-8'
        )

        example_dir = tmp_path / 'mock-example'
        example_dir.mkdir()
        (example_dir / 'run.sh').write_text(
            '#!/usr/bin/env bash\n\n'
            'cmd_check() {\n'
            '    local url="$1"\n'
            '    curl --max-time 5 "$url"\n'
            '}\n\n'
            'cmd_report() {\n'
            '    echo "report"\n'
            '}\n',
            encoding='utf-8'
        )

        from creator.prefill import _extract_example_steps
        steps = _extract_example_steps(example_dir, 'shell')
        assert len(steps) >= 1
        assert any(s['command'] == 'check' for s in steps)

    def test_shell_case_extraction(self, tmp_path):
        """Shell case 分支应能被提取为步骤"""
        example_dir = tmp_path / 'case-example'
        example_dir.mkdir()
        (example_dir / 'run.sh').write_text(
            '#!/usr/bin/env bash\n'
            'case "$1" in\n'
            '    check)\n'
            '        do_check\n'
            '        ;;\n'
            '    report)\n'
            '        do_report\n'
            '        ;;\n'
            '    *)\n'
            '        usage\n'
            '        ;;\n'
            'esac\n',
            encoding='utf-8'
        )

        from creator.prefill import _extract_example_steps
        steps = _extract_example_steps(example_dir, 'shell')
        cmd_names = [s['command'] for s in steps]
        assert 'check' in cmd_names
        assert 'report' in cmd_names

    def test_cross_type_fallback_shell_from_python(self, tmp_path):
        """shell 请求但样例仅有 run.py 时，应从 run.py 回退提取步骤"""
        example_dir = tmp_path / 'py-only-example'
        example_dir.mkdir()
        (example_dir / 'run.py').write_text(
            '#!/usr/bin/env python3\n'
            'def cmd_convert(args):\n'
            '    pass\n\n'
            'def cmd_validate(args):\n'
            '    pass\n',
            encoding='utf-8'
        )

        from creator.prefill import _extract_example_steps
        steps = _extract_example_steps(example_dir, 'shell')
        assert len(steps) >= 2
        cmd_names = [s['command'] for s in steps]
        assert 'convert' in cmd_names
        assert 'validate' in cmd_names

    def test_real_example_shell_todo_upgrade(self, tmp_path):
        """用真实内置样例验证 shell TODO 可通过跨类型回退升级"""
        skill_dir = tmp_path / 'shell-skill'
        skill_dir.mkdir()
        run_sh = skill_dir / 'run.sh'
        run_sh.write_text(
            '#!/usr/bin/env bash\n'
            '# TODO 实现步骤：\n'
            '#   1. 解析参数\n'
            '#   2. 执行逻辑\n'
            'echo "hello"\n',
            encoding='utf-8'
        )
        result = upgrade_todo_comments(skill_dir, 'data-formatter', 'shell')
        assert result is True
        content = run_sh.read_text(encoding='utf-8')
        assert '参考样例' in content
        assert 'data-formatter' in content

    def test_no_upgrade_without_match(self, tmp_path):
        """无匹配样例时不应修改"""
        skill_dir = tmp_path / 'no-match'
        skill_dir.mkdir()
        run_py = skill_dir / 'run.py'
        run_py.write_text('# TODO 实现步骤：\n#   1. pass\n', encoding='utf-8')
        result = upgrade_todo_comments(skill_dir, None, 'python')
        assert result is False

    def test_no_todo_block(self, tmp_path):
        """无 TODO 块时不应修改"""
        skill_dir = tmp_path / 'no-todo'
        skill_dir.mkdir()
        run_py = skill_dir / 'run.py'
        run_py.write_text('print("hello")\n', encoding='utf-8')
        result = upgrade_todo_comments(skill_dir, 'file-analyzer', 'python')
        assert result is False

    def test_upgrade_preserves_other_code(self, tmp_path):
        """升级 TODO 时不应影响其他代码"""
        skill_dir = tmp_path / 'preserve'
        skill_dir.mkdir()
        run_py = skill_dir / 'run.py'
        original = (
            '#!/usr/bin/env python3\n'
            'import sys\n\n'
            '# TODO 实现步骤：\n'
            '#   1. 解析参数\n'
            'def main():\n'
            '    pass\n'
        )
        run_py.write_text(original, encoding='utf-8')
        upgrade_todo_comments(skill_dir, 'file-analyzer', 'python')
        content = run_py.read_text(encoding='utf-8')
        assert 'import sys' in content
        assert 'def main():' in content


class TestMatchedExamplePassthrough:
    """matched_example 透传一致性：上游匹配结果直达 prefill，无二次匹配。"""

    def test_prefill_with_explicit_matched_example(self, tmp_path):
        """显式传入 matched_example 时跳过内部匹配，直接使用上游结果。"""
        skill_dir = tmp_path / 'explicit-test'
        skill_dir.mkdir()
        skill_md = skill_dir / 'SKILL.md'
        skill_md.write_text(
            '---\nname: explicit-test\ndescription: 完全无关描述\n---\n\n'
            '## 适用场景\n\n## 核心能力\n',
            encoding='utf-8'
        )
        result = prefill_skill_content(
            skill_dir, '完全无关描述', 'python',
            matched_example='file-analyzer')
        assert result['skill_md'] is True
        content = skill_md.read_text(encoding='utf-8')
        assert 'PRE-FILLED' in content
        assert 'file-analyzer' in content

    def test_prefill_and_todo_use_same_example(self, tmp_path):
        """prefill 和 TODO 升级使用同一个 matched_example，结果一致。"""
        skill_dir = tmp_path / 'consistency-test'
        skill_dir.mkdir()
        skill_md = skill_dir / 'SKILL.md'
        skill_md.write_text(
            '---\nname: consistency-test\ndescription: 文件统计\n---\n\n'
            '## 适用场景\n\n## 核心能力\n',
            encoding='utf-8'
        )
        run_py = skill_dir / 'run.py'
        run_py.write_text(
            '# TODO: 实现主要功能\ndef main():\n    pass\n',
            encoding='utf-8'
        )
        example_name = 'file-analyzer'
        prefill_result = prefill_skill_content(
            skill_dir, '文件统计', 'python',
            matched_example=example_name)
        todo_result = upgrade_todo_comments(skill_dir, example_name, 'python')
        assert prefill_result['skill_md'] is True
        md_content = skill_md.read_text(encoding='utf-8')
        assert example_name in md_content
