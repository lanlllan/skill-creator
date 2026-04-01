"""Phase 15 测试：深化问答扩展 + 答案质量预检"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skill-creator'))

import pytest
from creator.commands.create import (
    _interactive_deepen, _check_answer_quality, DEEPEN_QUESTIONS,
)
from creator.spec import build_spec_from_answers


class TestDeepenExpansion:
    def test_new_questions_exist(self):
        """DEEPEN_QUESTIONS 应包含 error_cause, error_solution, dependencies_runtime"""
        keys = [k for k, _ in DEEPEN_QUESTIONS]
        assert 'error_cause' in keys
        assert 'error_solution' in keys
        assert 'dependencies_runtime' in keys

    def test_new_questions_mapping(self):
        """新增 3 问应正确映射到 spec 字段"""
        answers = {
            'purpose_problem': '缺少监控工具',
            'target_user': '运维工程师',
            'scenario': '巡检时检查 API',
            'capability_name': '健康检查',
            'capability_desc': '发送 HTTP 请求',
            'command_name': 'check',
            'command_desc': '检查端点',
            'error_scenario': '网络不通',
            'error_cause': 'DNS 解析失败',
            'error_solution': '检查网络配置',
            'dependencies_runtime': 'requests, pyyaml',
        }
        spec = build_spec_from_answers(answers, 'test', '测试')
        assert spec.error_handling[0]['cause'] == 'DNS 解析失败'
        assert spec.error_handling[0]['solution'] == '检查网络配置'
        assert 'requests' in spec.dependencies['runtime']
        assert 'pyyaml' in spec.dependencies['runtime']

    def test_empty_dependencies(self):
        """空依赖应返回空列表"""
        spec = build_spec_from_answers({'dependencies_runtime': ''}, 'test', '测试')
        assert spec.dependencies['runtime'] == []

    def test_question_count(self):
        """应有 11 个问题（原 8 + 新 3）"""
        assert len(DEEPEN_QUESTIONS) == 11


class TestAnswerQuality:
    def test_too_short(self):
        hint = _check_answer_quality('test', '短', '描述')
        assert hint is not None
        assert '简短' in hint

    def test_high_repetition(self):
        desc = '检查开发环境的依赖配置'
        hint = _check_answer_quality('test', desc, desc)
        assert hint is not None
        assert '细节' in hint

    def test_placeholder_detected(self):
        hint = _check_answer_quality('test', '这里 TODO 填写具体的内容', '描述信息')
        assert hint is not None
        assert '具体内容' in hint

    def test_good_answer_passes(self):
        hint = _check_answer_quality(
            'test',
            '后端开发者在部署微服务后需要监控各服务的健康状态',
            '检查 API 健康'
        )
        assert hint is None

    def test_xxx_placeholder(self):
        hint = _check_answer_quality('test', 'xxx 这里需要填写具体内容', '描述')
        assert hint is not None

    def test_boundary_length(self):
        """恰好 10 字应通过"""
        hint = _check_answer_quality('test', '1234567890', '完全不同的描述')
        assert hint is None
