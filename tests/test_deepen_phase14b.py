"""
Phase 14b 测试套件：创建流程融合（意图深化 + 自动 guided）

覆盖范围：
- build_spec_from_answers 纯函数（4 用例）
- _interactive_deepen I/O 函数（4 用例）
- 深化集成（5 用例）

合计：13 用例
"""
import subprocess
import sys
from pathlib import Path

import pytest

from helpers import SKILL_ROOT, RUN_PY
from creator.spec import build_spec_from_answers, validate_spec
from creator.commands.create import _interactive_deepen, DEEPEN_QUESTIONS


# ═══════════════════════════════════════════════════════════════════════
#  TestBuildSpecFromAnswers — 纯函数测试
# ═══════════════════════════════════════════════════════════════════════

class TestBuildSpecFromAnswers:
    def test_full_answers(self):
        answers = {
            'purpose_problem': '开发者缺少统一的日志分析方式',
            'target_user': '后端开发者',
            'scenario': '开发者在排查线上故障时用此工具分析日志',
            'capability_name': '日志解析',
            'capability_desc': '对日志文件进行结构化解析',
            'command_name': 'analyze',
            'command_desc': '分析指定日志文件',
            'error_scenario': '日志文件不存在',
        }
        spec = build_spec_from_answers(answers, 'log-analyzer', '日志分析工具')

        assert spec.meta['name'] == 'log-analyzer'
        assert spec.meta['description'] == '日志分析工具'
        assert spec.purpose['problem'] == '开发者缺少统一的日志分析方式'
        assert spec.purpose['target_user'] == '后端开发者'
        assert '开发者在排查线上故障时用此工具分析日志' in spec.purpose['scenarios']
        assert spec.capabilities[0]['name'] == '日志解析'
        assert spec.commands[0]['name'] == 'analyze'
        assert spec.error_handling[0]['scenario'] == '日志文件不存在'

    def test_partial_answers(self):
        answers = {
            'purpose_problem': '需要监控 API',
            'target_user': '运维',
        }
        spec = build_spec_from_answers(answers, 'api-mon', '监控')

        assert spec.purpose['problem'] == '需要监控 API'
        assert spec.purpose['target_user'] == '运维'
        assert spec.capabilities[0]['name'] == ''
        assert spec.commands[0]['name'] == ''

    def test_empty_answers(self):
        spec = build_spec_from_answers({}, 'empty', '空')

        assert spec.meta['name'] == 'empty'
        assert spec.purpose['problem'] == ''
        assert spec.capabilities[0]['name'] == ''
        assert spec.commands[0]['name'] == ''

    def test_meta_passthrough(self):
        spec = build_spec_from_answers(
            {}, 'my-skill', '描述',
            version='2.0.0', author='Test Author', tags=['tag1', 'tag2'],
        )
        assert spec.meta['version'] == '2.0.0'
        assert spec.meta['author'] == 'Test Author'
        assert spec.meta['tags'] == ['tag1', 'tag2']


# ═══════════════════════════════════════════════════════════════════════
#  TestInteractiveDeepen — I/O 函数测试（通过 reader 注入 mock）
# ═══════════════════════════════════════════════════════════════════════

class TestInteractiveDeepen:
    def test_all_answered(self):
        responses = iter([
            '开发者缺少统一的日志分析方式来排查问题',
            '后端开发者和运维工程师',
            '排查线上故障时用此工具快速分析日志文件',
            '日志解析与错误信息定位',
            '对日志文件进行结构化解析并提取关键信息',
            'analyze-log',
            '',  # retry: keep (analyze-log is 11 chars, but just in case)
            '分析指定日志文件中的错误分布',
            '日志文件路径不存在或格式错误',
            '路径拼写错误或文件已被清理删除',
            '检查日志文件路径是否正确并确认文件存在',
            '',
        ])

        result = _interactive_deepen('', reader=lambda _: next(responses))

        assert result is not None
        assert len(result) == len(DEEPEN_QUESTIONS)
        assert '日志' in result['purpose_problem']
        assert '日志' in result['error_scenario']

    def test_skip_first_question(self):
        result = _interactive_deepen('', reader=lambda _: 's')
        assert result is None

    def test_skip_midway(self):
        answers = [
            '开发者缺少统一的日志分析方式来排查问题',
            '后端开发者和运维工程师',
            '排查线上故障时用此工具快速分析日志文件',
        ]
        call_count = 0
        def mock_reader(_):
            nonlocal call_count
            call_count += 1
            if call_count <= len(answers):
                return answers[call_count - 1]
            return 's'

        result = _interactive_deepen('', reader=mock_reader)

        assert result is not None
        assert len(result) == 3
        assert '日志' in result['purpose_problem']

    def test_empty_enter_skips_field(self):
        responses = iter([''] * len(DEEPEN_QUESTIONS))
        result = _interactive_deepen('', reader=lambda _: next(responses))

        assert result is not None
        assert result.get('purpose_problem', '') == ''


# ═══════════════════════════════════════════════════════════════════════
#  TestDeepenIntegration — 集成测试
# ═══════════════════════════════════════════════════════════════════════

class TestDeepenIntegration:
    def test_full_deepen_creates_guided_skill(self, tmp_path):
        result = subprocess.run(
            [sys.executable, RUN_PY, 'create',
             '--interactive', '--name', 'deepen-test',
             '--description', '深化测试'],
            input=(
                '\n'  # version
                '\n'  # author
                '\n'  # tags
                f'{tmp_path}\n'  # output
                '开发者缺少统一的日志分析工具来排查问题\n'
                '\n'  # retry: keep (if triggered)
                '后端开发者和运维工程师\n'
                '\n'  # retry: keep
                '排查线上故障时用此工具快速分析日志文件\n'
                '日志解析与错误定位\n'
                '\n'  # retry: keep
                '对日志文件进行结构化解析并提取关键信息\n'
                'analyze\n'
                '\n'  # retry: keep
                '分析指定日志文件中的错误分布\n'
                '日志文件路径不存在或格式错误\n'
                '日志文件路径配置错误或文件已被清理\n'
                '检查日志文件路径是否正确并确认文件存在\n'
                '\n'  # dependencies_runtime (empty)
            ),
            capture_output=True, text=True,
            cwd=str(SKILL_ROOT),
        )
        assert result.returncode == 0
        skill_dir = tmp_path / 'deepen-test'
        assert skill_dir.exists()
        assert (skill_dir / 'SKILL.md').exists()

    def test_skip_deepen_creates_basic_skill(self, tmp_path):
        result = subprocess.run(
            [sys.executable, RUN_PY, 'create',
             '--name', 'basic-test', '--description', '基础测试',
             '--skip-deepen', '--interactive'],
            input=f'\n\n\n{tmp_path}\n',
            capture_output=True, text=True,
            cwd=str(SKILL_ROOT),
        )
        assert result.returncode == 0
        skill_dir = tmp_path / 'basic-test'
        assert skill_dir.exists()
        spec_file = skill_dir / '.skill-spec.yaml'
        assert not spec_file.exists()

    def test_deepen_with_errors_degrades(self, tmp_path):
        result = subprocess.run(
            [sys.executable, RUN_PY, 'create',
             '--interactive', '--name', 'degrade-test',
             '--description', '降级测试'],
            input=(
                '\n'  # version
                '\n'  # author
                '\n'  # tags
                f'{tmp_path}\n'  # output
                '\n'  # purpose_problem (empty → error)
                '\n'  # target_user (empty → error)
                '\n\n\n\n\n\n\n\n\n'
            ),
            capture_output=True, text=True,
            cwd=str(SKILL_ROOT),
        )
        assert result.returncode == 0
        assert '信息不完整' in result.stdout
        skill_dir = tmp_path / 'degrade-test'
        assert skill_dir.exists()

    def test_deepen_warnings_continue(self, tmp_path):
        result = subprocess.run(
            [sys.executable, RUN_PY, 'create',
             '--interactive', '--name', 'warn-test',
             '--description', '警告测试'],
            input=(
                '\n'  # version
                '\n'  # author
                '\n'  # tags
                f'{tmp_path}\n'  # output
                '当需要自动化检测系统运行状态的时候使用此工具\n'
                '运维工程师\n'
                '运维人员在服务器异常时运行检测命令\n'
                '状态检测\n'
                '检测目标系统的运行状态\n'
                'detect\n'
                '执行一次完整的状态检测\n'
                '目标服务器无法连接\n'
                '网络不通或端口被占用\n'
                '重启服务或更换端口\n'
                '\n'  # dependencies_runtime
            ),
            capture_output=True, text=True,
            cwd=str(SKILL_ROOT),
        )
        assert result.returncode == 0
        assert '使用基础模板' not in result.stdout
        skill_dir = tmp_path / 'warn-test'
        assert skill_dir.exists()

    def test_backward_compat_non_interactive(self, tmp_path):
        result = subprocess.run(
            [sys.executable, RUN_PY, 'create',
             '--name', 'compat-test', '--description', '兼容测试',
             '--output', str(tmp_path)],
            capture_output=True, text=True,
            cwd=str(SKILL_ROOT),
        )
        assert result.returncode == 0
        assert '意图深化' not in result.stdout
        skill_dir = tmp_path / 'compat-test'
        assert skill_dir.exists()
