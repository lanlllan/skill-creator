"""Phase 16 测试：创建流程收敛 + validate 批量 + --guided 淡化"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skill-creator'))

import pytest
from creator.commands.validate import _resolve_paths, _validate_one, main_validate


GOOD_FRONT_MATTER = """\
---
name: test-skill
description: A test skill
version: 1.0.0
---
"""


def _make_minimal_skill(d: Path, name: str = 'test-skill') -> Path:
    """创建一个可通过基本验证的最小 skill 目录。"""
    skill_dir = d / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / 'SKILL.md').write_text(
        GOOD_FRONT_MATTER + '\n# Test Skill\n\nA test skill.\n',
        encoding='utf-8'
    )
    (skill_dir / 'run.py').write_text(
        '#!/usr/bin/env python3\n"""Test skill."""\n'
        'import sys\n\ndef main():\n    try:\n        pass\n'
        '    except Exception as e:\n        print(e, file=sys.stderr)\n'
        '        sys.exit(1)\n\nif __name__ == "__main__":\n    main()\n',
        encoding='utf-8'
    )
    (skill_dir / 'README.md').write_text('# Test\n\nUsage info.\n', encoding='utf-8')
    return skill_dir


class TestResolvePaths:
    def test_single_path(self, tmp_path):
        skill = _make_minimal_skill(tmp_path)
        args = MagicMock(paths=[str(skill)], recursive=False)
        valid, missing = _resolve_paths(args)
        assert len(valid) == 1
        assert valid[0] == skill
        assert len(missing) == 0

    def test_multiple_paths(self, tmp_path):
        a = _make_minimal_skill(tmp_path, 'skill-a')
        b = _make_minimal_skill(tmp_path, 'skill-b')
        args = MagicMock(paths=[str(a), str(b)], recursive=False)
        valid, missing = _resolve_paths(args)
        assert len(valid) == 2
        assert len(missing) == 0

    def test_recursive_discovery(self, tmp_path):
        parent = tmp_path / 'skills'
        parent.mkdir()
        _make_minimal_skill(parent, 'alpha')
        _make_minimal_skill(parent, 'beta')
        (parent / 'not-a-skill').mkdir()
        args = MagicMock(paths=[str(parent)], recursive=True)
        valid, missing = _resolve_paths(args)
        assert len(valid) == 2
        names = {p.name for p in valid}
        assert 'alpha' in names and 'beta' in names

    def test_nonexistent_path(self, tmp_path):
        args = MagicMock(paths=[str(tmp_path / 'nonexistent')], recursive=False)
        valid, missing = _resolve_paths(args)
        assert len(valid) == 0
        assert len(missing) == 1

    def test_recursive_skips_dirs_without_skill_md(self, tmp_path):
        parent = tmp_path / 'container'
        parent.mkdir()
        (parent / 'no-skill').mkdir()
        (parent / 'no-skill' / 'README.md').write_text('hello', encoding='utf-8')
        args = MagicMock(paths=[str(parent)], recursive=True)
        valid, missing = _resolve_paths(args)
        assert len(valid) == 0


class TestValidateOne:
    def test_valid_skill(self, tmp_path):
        skill = _make_minimal_skill(tmp_path)
        record = _validate_one(skill, no_security=True)
        assert record['name'] == 'test-skill'
        assert len(record['errors']) == 0

    def test_nonexistent_path(self, tmp_path):
        record = _validate_one(tmp_path / 'gone', no_security=True)
        assert len(record['errors']) > 0

    def test_not_a_directory(self, tmp_path):
        f = tmp_path / 'file.txt'
        f.write_text('hello', encoding='utf-8')
        record = _validate_one(f, no_security=True)
        assert len(record['errors']) > 0


class TestMainValidate:
    def test_single_path_backward_compat(self, tmp_path, capsys):
        skill = _make_minimal_skill(tmp_path)
        args = MagicMock(paths=[str(skill)], recursive=False, json=False, no_security=True)
        code = main_validate(args)
        assert code == 0
        output = capsys.readouterr().out
        assert '验证 skill' in output

    def test_json_output(self, tmp_path, capsys):
        skill = _make_minimal_skill(tmp_path)
        args = MagicMock(paths=[str(skill)], recursive=False, json=True, no_security=True)
        code = main_validate(args)
        assert code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert 'skills' in data
        assert len(data['skills']) == 1
        assert data['skills'][0]['name'] == 'test-skill'

    def test_batch_output_multiple(self, tmp_path, capsys):
        a = _make_minimal_skill(tmp_path, 'skill-a')
        b = _make_minimal_skill(tmp_path, 'skill-b')
        args = MagicMock(
            paths=[str(a), str(b)], recursive=False, json=False, no_security=True)
        code = main_validate(args)
        assert code == 0
        output = capsys.readouterr().out
        assert '批量验证汇总' in output

    def test_exit_code_1_on_error(self, tmp_path):
        bad_dir = tmp_path / 'bad-skill'
        bad_dir.mkdir()
        args = MagicMock(paths=[str(bad_dir)], recursive=False, json=False, no_security=True)
        code = main_validate(args)
        assert code == 1

    def test_recursive_batch(self, tmp_path, capsys):
        parent = tmp_path / 'skills'
        parent.mkdir()
        _make_minimal_skill(parent, 'one')
        _make_minimal_skill(parent, 'two')
        args = MagicMock(
            paths=[str(parent)], recursive=True, json=False, no_security=True)
        code = main_validate(args)
        assert code == 0
        output = capsys.readouterr().out
        assert '批量验证汇总' in output

    def test_json_batch(self, tmp_path, capsys):
        parent = tmp_path / 'skills'
        parent.mkdir()
        _make_minimal_skill(parent, 'x')
        _make_minimal_skill(parent, 'y')
        args = MagicMock(
            paths=[str(parent)], recursive=True, json=True, no_security=True)
        code = main_validate(args)
        output = capsys.readouterr().out
        data = json.loads(output)
        assert len(data['skills']) == 2

    def test_nonexistent_returns_1(self, tmp_path, capsys):
        args = MagicMock(
            paths=[str(tmp_path / 'nodir')], recursive=False, json=False, no_security=True)
        code = main_validate(args)
        assert code == 1

    def test_mixed_valid_and_invalid_returns_1(self, tmp_path, capsys):
        """有效路径 + 不存在路径混合时退出码应为 1"""
        skill = _make_minimal_skill(tmp_path)
        fake = tmp_path / 'not-exist-x'
        args = MagicMock(
            paths=[str(skill), str(fake)], recursive=False, json=False, no_security=True)
        code = main_validate(args)
        assert code == 1
        output = capsys.readouterr().out
        assert '路径不存在' in output

    def test_mixed_valid_and_invalid_json(self, tmp_path, capsys):
        """混合路径 JSON 输出应包含错误条目"""
        skill = _make_minimal_skill(tmp_path)
        fake = tmp_path / 'gone'
        args = MagicMock(
            paths=[str(skill), str(fake)], recursive=False, json=True, no_security=True)
        code = main_validate(args)
        assert code == 1
        data = json.loads(capsys.readouterr().out)
        assert len(data['skills']) == 2
        error_skill = [s for s in data['skills'] if s['errors']]
        assert len(error_skill) == 1


class TestGuidedFading:
    """验证 --guided 帮助文本已淡化为高级模式。"""

    def test_guided_help_text(self):
        import run
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        for action in run.main.__code__.co_consts:
            pass
        from io import StringIO
        import contextlib
        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                sys.argv = ['run.py', 'create', '--help']
                run.main()
            except SystemExit:
                pass
        help_text = buf.getvalue()
        assert '高级模式' in help_text

    def test_interactive_help_text(self):
        from io import StringIO
        import contextlib
        import run
        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                sys.argv = ['run.py', 'create', '--help']
                run.main()
            except SystemExit:
                pass
        help_text = buf.getvalue()
        assert '推荐' in help_text


class TestExamplesHint:
    """验证 examples 命令输出包含 --interactive 提示。"""

    def test_examples_list_has_hint(self, capsys):
        from creator.commands.examples_cmd import main_examples
        args = MagicMock(show=None, copy=None, output=None)
        main_examples(args)
        output = capsys.readouterr().out
        assert '--interactive' in output
