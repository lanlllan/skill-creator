"""Phase 17 测试：深化鲁棒性增强"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skill-creator'))

import pytest
from creator.commands.create import (
    _check_answer_quality,
    _effective_length,
    _FIELD_MIN_LENGTH,
    _clear_spec_group,
)
from creator.spec import validate_spec, classify_errors_by_group, SkillSpec


class TestEffectiveLength:
    def test_chinese_21_chars(self):
        text = "开发者在排查线上故障时需要快速定位错误模式"
        assert _effective_length(text) == 21

    def test_strips_whitespace(self):
        assert _effective_length("  hello  ") == 5

    def test_empty(self):
        assert _effective_length("") == 0

    def test_mixed_cjk_and_ascii(self):
        assert _effective_length("hello世界") == 7


class TestFieldMinLength:
    def test_command_name_short_ok(self):
        result = _check_answer_quality('command_name', 'ls', '描述信息')
        assert result is None

    def test_target_user_short_ok(self):
        result = _check_answer_quality('target_user', '开发者', '描述信息')
        assert result is None

    def test_purpose_problem_too_short(self):
        result = _check_answer_quality('purpose_problem', '问题', '描述信息')
        assert result is not None
        assert '简短' in result

    def test_capability_name_2_chars_ok(self):
        result = _check_answer_quality('capability_name', '扫描功能', '描述')
        assert result is None

    def test_dependencies_runtime_empty_ok(self):
        result = _check_answer_quality('dependencies_runtime', '', '描述')
        assert result is None

    def test_unknown_key_uses_default_10(self):
        result = _check_answer_quality('unknown_field', '短', '描述')
        assert result is not None

    def test_placeholder_still_detected(self):
        result = _check_answer_quality(
            'purpose_problem',
            '这是一个 TODO implement this 的功能描述', '描述')
        assert result is not None


class TestClassifyErrors:
    def test_purpose_errors(self):
        errors = ['purpose.problem 不能为空', 'purpose.target_user 不能为空']
        grouped = classify_errors_by_group(errors)
        assert 'purpose' in grouped
        assert len(grouped['purpose']) == 2

    def test_mixed_groups(self):
        errors = [
            'capabilities 至少需要 1 个能力的 name 非空',
            'commands 至少需要 1 个命令的 name 非空',
        ]
        grouped = classify_errors_by_group(errors)
        assert 'capabilities' in grouped
        assert 'commands' in grouped

    def test_unclassified_goes_to_other(self):
        errors = ['某个未知错误']
        grouped = classify_errors_by_group(errors)
        assert 'other' in grouped


class TestClearSpecGroup:
    def test_clear_capabilities(self):
        variables = {
            'name': 'test',
            'capabilities': [{'name': 'cap1'}],
            'commands': [{'name': 'cmd1'}],
        }
        _clear_spec_group(variables, 'capabilities')
        assert variables['capabilities'] == []
        assert len(variables['commands']) == 1

    def test_clear_purpose_nested_dict(self):
        """purpose 在 spec_to_template_vars 输出中是嵌套字典。"""
        variables = {
            'name': 'test',
            'purpose': {
                'problem': 'some problem',
                'target_user': 'devs',
                'scenarios': ['s1'],
            },
            'capabilities': [{'name': 'cap1'}],
        }
        _clear_spec_group(variables, 'purpose')
        assert variables['purpose']['problem'] == ''
        assert variables['purpose']['target_user'] == ''
        assert variables['purpose']['scenarios'] == []
        assert len(variables['capabilities']) == 1

    def test_clear_purpose_real_spec(self):
        """使用真实 spec_to_template_vars 输出验证 purpose 降级。"""
        from creator.spec import build_spec_from_answers, spec_to_template_vars
        answers = {
            'purpose_problem': '排查线上问题',
            'target_user': '运维人员',
            'scenario': '服务器异常时检测',
            'capability_name': 'detect',
            'capability_desc': '检测系统状态',
            'command_name': 'run',
            'command_desc': '执行检测',
            'error_scenario': '连接失败',
        }
        spec = build_spec_from_answers(answers, 'test', 'desc')
        variables = spec_to_template_vars(spec)
        assert variables['purpose']['problem'] == '排查线上问题'
        _clear_spec_group(variables, 'purpose')
        assert variables['purpose']['problem'] == ''
        assert variables['purpose']['target_user'] == ''
        assert variables['purpose']['scenarios'] == []
        assert len(variables['capabilities']) == 1

    def test_clear_commands(self):
        variables = {
            'name': 'test',
            'commands': [{'name': 'cmd1'}],
            'error_handling': [{'scenario': 'e1'}],
        }
        _clear_spec_group(variables, 'commands')
        assert variables['commands'] == []
        assert len(variables['error_handling']) == 1

    def test_clear_error_handling(self):
        variables = {
            'error_handling': [{'scenario': 'e1'}],
        }
        _clear_spec_group(variables, 'error_handling')
        assert variables['error_handling'] == []
