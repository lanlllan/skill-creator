"""
tests/test_scan_command.py — scan 子命令及 validate/batch 安全集成测试

覆盖：scan 基本调用、--json、validate --no-security、validate 退出码不变、
      batch --fail-on-security、batch 默认模式、skip_state 参数行为
"""
import json
import textwrap
import types
import pytest
from pathlib import Path

from creator.commands.scan import main_scan
from creator.commands.validate import main_validate
from creator.commands.batch import main_batch
from creator.commands.create import create_skill


def _make_args(**kwargs):
    """构造一个简单的 args 命名空间对象。"""
    return types.SimpleNamespace(**kwargs)


def _make_valid_skill(base_dir, name='test-skill', with_eval=False, with_env=False):
    """创建一个可通过 validate 的 skill 目录（含 SKILL.md + run.py）。"""
    d = base_dir / name
    d.mkdir(parents=True, exist_ok=True)

    skill_md = f"""---
name: {name}
description: Test skill
version: 1.0.0
author: Test
tags: [test]
---
# {name}
"""
    (d / "SKILL.md").write_text(skill_md, encoding='utf-8')

    run_content = '#!/usr/bin/env python3\nprint("hello")\n'
    if with_eval:
        run_content += 'result = eval(user_input)\n'
    (d / "run.py").write_text(run_content, encoding='utf-8')

    if with_env:
        (d / ".env").write_text("SECRET=value", encoding='utf-8')

    return d


# ═══ scan 子命令测试 ═════════════════════════════════════════

class TestScanCommand:

    def test_clean_skill_returns_0(self, tmp_path):
        d = _make_valid_skill(tmp_path)
        args = _make_args(path=str(d), json=False)
        assert main_scan(args) == 0

    def test_skill_with_eval_returns_1(self, tmp_path):
        d = _make_valid_skill(tmp_path, with_eval=True)
        args = _make_args(path=str(d), json=False)
        assert main_scan(args) == 1

    def test_json_output_parseable(self, tmp_path, capsys):
        d = _make_valid_skill(tmp_path, with_eval=True)
        args = _make_args(path=str(d), json=True)
        main_scan(args)
        output = capsys.readouterr().out
        json_start = output.find('[')
        if json_start >= 0:
            data = json.loads(output[json_start:])
            assert isinstance(data, list)
            assert any(item['rule_id'] == 'DANGEROUS_EVAL' for item in data)

    def test_nonexistent_path_returns_1(self, tmp_path):
        args = _make_args(path=str(tmp_path / "nonexistent"), json=False)
        assert main_scan(args) == 1


# ═══ validate 安全集成测试 ═══════════════════════════════════

class TestValidateSecurity:

    def test_no_security_flag_skips_scan(self, tmp_path, capsys):
        d = _make_valid_skill(tmp_path, with_eval=True)
        args = _make_args(path=str(d), no_security=True)
        main_validate(args)
        output = capsys.readouterr().out
        assert '[security]' not in output

    def test_default_shows_security_warning(self, tmp_path, capsys):
        d = _make_valid_skill(tmp_path, with_eval=True)
        args = _make_args(path=str(d), no_security=False)
        main_validate(args)
        output = capsys.readouterr().out
        assert '[security]' in output

    def test_eval_skill_validate_still_returns_0(self, tmp_path):
        """含 eval() 但无结构错误 → validate 退出码仍为 0（安全扫描不影响退出码）"""
        d = _make_valid_skill(tmp_path, with_eval=True)
        args = _make_args(path=str(d), no_security=False)
        rc = main_validate(args)
        assert rc == 0


# ═══ skip_state 参数测试 ═════════════════════════════════════

class TestSkipState:

    def test_skip_state_true_no_state_written(self, tmp_path, monkeypatch):
        """create_skill(skip_state=True) 后不调用 add_skill。"""
        add_skill_called = []
        import creator.commands.create as create_mod
        original_add = create_mod.add_skill
        monkeypatch.setattr(create_mod, 'add_skill',
                            lambda *a, **kw: add_skill_called.append(1))

        params = {
            'name': 'skip-test',
            'description': 'test skip state',
            'output': str(tmp_path),
        }
        rc = create_skill(params, skip_state=True)
        assert rc == 0
        assert len(add_skill_called) == 0

    def test_skip_state_false_state_written(self, tmp_path, monkeypatch):
        """create_skill(skip_state=False) 后调用 add_skill。"""
        add_skill_called = []
        import creator.commands.create as create_mod
        original_add = create_mod.add_skill
        monkeypatch.setattr(create_mod, 'add_skill',
                            lambda *a, **kw: add_skill_called.append(1))

        params = {
            'name': 'noskip-test',
            'description': 'test no skip state',
            'output': str(tmp_path),
        }
        rc = create_skill(params, skip_state=False)
        assert rc == 0
        assert len(add_skill_called) == 1


# ═══ validate 边界测试 ═══════════════════════════════════════

class TestValidateEdgeCases:

    def test_file_path_returns_1(self, tmp_path):
        """validate 传入文件路径（非目录）应返回 1 而非 traceback"""
        f = tmp_path / "file.txt"
        f.write_text("x")
        args = _make_args(path=str(f), no_security=False)
        rc = main_validate(args)
        assert rc == 1


# ═══ scan --json 纯 JSON 测试 ════════════════════════════════

class TestScanJsonPure:

    def test_json_output_is_pure_json(self, tmp_path, capsys):
        """--json 模式下 stdout 应为纯 JSON，无前缀文本"""
        d = _make_valid_skill(tmp_path, with_eval=True)
        args = _make_args(path=str(d), json=True)
        main_scan(args)
        output = capsys.readouterr().out.strip()
        data = json.loads(output)
        assert isinstance(data, list)


# ═══ batch --fail-on-security 端到端测试 ═════════════════════

def _make_batch_yaml(tmp_path, skills, output_dir=None):
    """生成 batch YAML 文件。使用 yaml.dump 确保正确转义。"""
    import yaml
    data = {'skills': []}
    for s in skills:
        entry = {'name': s['name'], 'description': s['description']}
        if output_dir:
            entry['output'] = output_dir
        data['skills'].append(entry)
    p = tmp_path / "batch.yaml"
    p.write_text(yaml.dump(data, allow_unicode=True), encoding='utf-8')
    return p


class TestBatchFailOnSecurity:

    def test_default_batch_security_no_block(self, tmp_path, monkeypatch):
        """默认 batch 模式：安全发现不阻断，退出码为 0"""
        out = tmp_path / "out"
        out.mkdir()
        yaml_file = _make_batch_yaml(tmp_path, [
            {'name': 'safe-skill', 'description': 'no issues'},
        ], output_dir=str(out))
        args = _make_args(file=str(yaml_file), fail_on_security=False)
        import creator.commands.batch as batch_mod
        monkeypatch.setattr(batch_mod, 'get_skills_temp_dir', lambda: out)
        rc = main_batch(args)
        assert rc == 0

    def test_fail_on_security_with_error_fails(self, tmp_path, capsys, monkeypatch):
        """--fail-on-security + error 级安全发现 → 条目计为失败"""
        out = tmp_path / "out"
        out.mkdir()
        yaml_file = _make_batch_yaml(tmp_path, [
            {'name': 'risky-skill', 'description': 'has secrets'},
        ], output_dir=str(out))
        args = _make_args(file=str(yaml_file), fail_on_security=True)
        import creator.commands.batch as batch_mod
        monkeypatch.setattr(batch_mod, 'get_skills_temp_dir', lambda: out)

        original_create = batch_mod.create_skill

        def patched_create(params, _out=None, skip_state=False, **kwargs):
            rc = original_create(params, _out=_out, skip_state=skip_state, **kwargs)
            if rc == 0 and _out:
                skill_dir = out / _out.get('skill_name', params['name'])
                (skill_dir / ".env").write_text("SECRET=real_value", encoding='utf-8')
            return rc

        monkeypatch.setattr(batch_mod, 'create_skill', patched_create)
        rc = main_batch(args)
        output = capsys.readouterr().out
        assert rc == 1
        assert '安全扫描未通过' in output

    def test_fail_on_security_no_error_succeeds(self, tmp_path, monkeypatch):
        """--fail-on-security + 无 error 级发现 → 条目成功并写状态"""
        out = tmp_path / "out"
        out.mkdir()
        yaml_file = _make_batch_yaml(tmp_path, [
            {'name': 'clean-skill', 'description': 'all clean'},
        ], output_dir=str(out))
        args = _make_args(file=str(yaml_file), fail_on_security=True)
        import creator.commands.batch as batch_mod
        monkeypatch.setattr(batch_mod, 'get_skills_temp_dir', lambda: out)
        add_calls = []
        import creator.state_manager as sm_mod
        monkeypatch.setattr(sm_mod, 'add_skill',
                            lambda *a, **kw: add_calls.append(1))
        import creator.commands.create as create_mod
        monkeypatch.setattr(create_mod, 'add_skill',
                            lambda *a, **kw: None)
        rc = main_batch(args)
        assert rc == 0
