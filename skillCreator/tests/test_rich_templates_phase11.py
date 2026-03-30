"""
Phase 11 富内容模板 — 测试套件

覆盖维度（33 用例）：
  1. TestGuidedTemplateDiscovery — guided 模板发现（3）
  2. TestGuidedTemplateRendering — python-guided 4 个模板渲染正确性（4）
  3. TestShellGuidedTemplateRendering — shell-guided 模板渲染 + boolean shift 1 + arg_flag（5）
  4. TestSpecFieldCoverage — 规约字段覆盖（1）
  5. TestResultPattern — run.py 产物 Result 数据类（1）
  6. TestCommandGeneration — argparse 子命令映射（4）
  7. TestTodoComments — TODO 步骤注释（1）
  8. TestSelfBootstrap — 自举测试 python + shell（2）
  9. TestBackwardCompat — 向后兼容（1）
  10. TestBackwardCompatNoGuidedDir — 降级逻辑（1）
  11. TestExpandVariablesTagsList — tags_list 保留（1）
  12. TestSpecToVarsNameSnake — name_snake + dispatch_entries（2）
  13. TestEmptySpec — 空规约渲染（1）
  14. TestCreateFromSpecIntegration — 端到端（1）
  15. TestMultipleCommands — 多命令（1）
  16. TestNoResidualPlaceholders — 无残留占位符（1）
  17. TestQuoteEscaping — 单引号转义（1）
  18. TestArgFlagInUsage — USAGE 参数展示 arg_flag（1）
  19. TestBooleanOptional — boolean 可选标记（1）
"""
import os
import re
import shutil
import sys
import yaml

import pytest
from pathlib import Path
from types import SimpleNamespace

from creator.spec import (
    SkillSpec,
    generate_spec_skeleton,
    save_spec,
    load_spec,
    validate_spec,
    spec_to_template_vars,
    SPEC_VERSION,
    SPEC_FILENAME,
)
from creator.templates import (
    generate_files,
    _expand_variables,
    BUILTIN_TEMPLATE_DIR,
)
from creator.commands.create import create_skill, _create_from_spec


def _make_filled_spec() -> SkillSpec:
    """完整填充的 SkillSpec（2 命令 + 2 能力 + 2 错误场景）。"""
    return SkillSpec(
        spec_version=SPEC_VERSION,
        meta={
            'name': 'log-analyzer',
            'description': '日志分析与异常检测工具',
            'version': '2.0.0',
            'author': 'Phase11 Tester',
            'tags': ['log', 'analysis'],
        },
        purpose={
            'problem': '团队在排查线上故障时需要手动翻阅大量日志，耗时且容易遗漏关键错误信息',
            'target_user': 'SRE 工程师和后端开发',
            'scenarios': [
                'SRE 在收到告警后用此工具快速定位错误日志的时间和来源',
                '开发者在版本发布后用此工具检查是否有新增异常',
            ],
        },
        capabilities=[
            {
                'name': '关键词搜索',
                'description': '在日志文件中按关键词过滤并高亮匹配行',
                'inputs': '日志文件路径和搜索关键词',
                'outputs': '匹配的日志行及上下文',
                'example': '输入 app.log + "ERROR" → 输出所有包含 ERROR 的行',
            },
            {
                'name': '异常统计',
                'description': '统计指定时间范围内各类异常的出现频次',
                'inputs': '日志文件路径和时间范围',
                'outputs': '按异常类型分组的频次报告',
                'example': '输入 app.log + 最近1小时 → 输出 NullPointerException: 5次',
            },
        ],
        commands=[
            {
                'name': 'search',
                'description': '在日志文件中搜索包含指定关键词的行',
                'args': [
                    {'name': 'file', 'description': '日志文件路径', 'type': 'string'},
                    {'name': '--keyword', 'description': '搜索关键词', 'type': 'string'},
                    {'name': '--case-sensitive', 'description': '区分大小写', 'type': 'boolean'},
                ],
                'example': 'python run.py search --file app.log --keyword ERROR',
                'expected_output': '找到 12 条匹配记录',
            },
            {
                'name': 'stats',
                'description': '统计日志中各类异常的出现频次',
                'args': [
                    {'name': '--file', 'description': '日志文件路径', 'type': 'string'},
                    {'name': '--hours', 'description': '最近 N 小时', 'type': 'integer'},
                ],
                'example': 'python run.py stats --file app.log --hours 24',
                'expected_output': 'NullPointerException: 5, TimeoutException: 3',
            },
        ],
        error_handling=[
            {
                'scenario': '日志文件不存在',
                'cause': '指定的文件路径错误或文件已被轮转删除',
                'solution': '检查文件路径是否正确，确认日志轮转策略',
            },
            {
                'scenario': '日志格式无法解析',
                'cause': '日志不符合预期的格式规范',
                'solution': '检查日志格式配置，确认是否为支持的格式',
            },
        ],
        dependencies={
            'runtime': ['click', 'rich'],
            'external': ['grep 命令行工具'],
        },
    )


def _make_single_cmd_spec() -> SkillSpec:
    """单命令简单规约。"""
    return SkillSpec(
        spec_version=SPEC_VERSION,
        meta={
            'name': 'simple-tool',
            'description': '简单工具',
            'version': '1.0.0',
            'author': 'Tester',
            'tags': ['tool'],
        },
        purpose={
            'problem': '需要一个简单的命令行工具来完成日常操作任务',
            'target_user': '开发工程师',
            'scenarios': ['开发者在日常工作中使用此工具完成常规操作'],
        },
        capabilities=[{
            'name': '基础操作',
            'description': '执行基本的命令行操作',
            'inputs': '命令参数',
            'outputs': '操作结果',
            'example': '输入参数 → 输出结果',
        }],
        commands=[{
            'name': 'run',
            'description': '执行主要操作',
            'args': [
                {'name': 'target', 'description': '操作目标', 'type': 'string'},
            ],
            'example': 'python run.py run --target test',
            'expected_output': '操作完成',
        }],
        error_handling=[{
            'scenario': '目标不存在',
            'cause': '指定的目标路径或名称无效',
            'solution': '确认目标是否正确',
        }],
        dependencies={'runtime': [], 'external': []},
    )


def _render_python_guided(tmp_path: Path, spec: SkillSpec) -> Path:
    """使用 python-guided 模板渲染并返回 skill 目录。"""
    variables = spec_to_template_vars(spec)
    name = variables['name']
    skill_dir = tmp_path / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    generate_files(skill_dir, variables, skill_type='python', guided=True)
    return skill_dir


def _render_shell_guided(tmp_path: Path, spec: SkillSpec) -> Path:
    """使用 shell-guided 模板渲染并返回 skill 目录。"""
    variables = spec_to_template_vars(spec)
    name = variables['name']
    skill_dir = tmp_path / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    generate_files(skill_dir, variables, skill_type='shell', guided=True)
    return skill_dir


# ─── 1. TestGuidedTemplateDiscovery ───

class TestGuidedTemplateDiscovery:
    """guided 模板发现逻辑测试。"""

    def test_python_guided_dir_used(self, tmp_path):
        """guided=True 时使用 python-guided 目录。"""
        spec = _make_single_cmd_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
        assert '设计规约' in content or '.skill-spec.yaml' in content

    def test_fallback_when_guided_dir_missing(self, tmp_path, monkeypatch):
        """python-guided 目录不存在时降级到 python 模板。"""
        fake_builtin = tmp_path / 'fake_templates'
        fake_builtin.mkdir()
        python_dir = fake_builtin / 'python'
        python_dir.mkdir()
        shutil.copytree(
            BUILTIN_TEMPLATE_DIR / 'python',
            python_dir,
            dirs_exist_ok=True,
        )
        monkeypatch.setattr('creator.templates.BUILTIN_TEMPLATE_DIR', fake_builtin)

        variables = spec_to_template_vars(_make_single_cmd_spec())
        skill_dir = tmp_path / 'fallback-skill'
        skill_dir.mkdir()
        generate_files(skill_dir, variables, skill_type='python', guided=True)
        assert (skill_dir / 'SKILL.md').exists()

    def test_user_template_dir_overrides_guided(self, tmp_path):
        """--template-dir 覆盖 guided 模板。"""
        custom_dir = tmp_path / 'custom_templates'
        custom_dir.mkdir()
        (custom_dir / 'CUSTOM.md.j2').write_text(
            '# Custom {{ name }}', encoding='utf-8'
        )

        variables = spec_to_template_vars(_make_single_cmd_spec())
        skill_dir = tmp_path / 'custom-skill'
        skill_dir.mkdir()
        generate_files(skill_dir, variables, skill_type='python',
                       template_dir=str(custom_dir), guided=True)
        assert (skill_dir / 'CUSTOM.md').exists()
        assert not (skill_dir / 'SKILL.md').exists()


# ─── 2. TestGuidedTemplateRendering ───

class TestGuidedTemplateRendering:
    """python-guided 模板渲染正确性。"""

    def test_skill_md_renders(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
        assert 'log-analyzer' in content
        assert '日志分析与异常检测工具' in content
        assert '关键词搜索' in content

    def test_run_py_renders(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert 'def cmd_search(args)' in content
        assert 'def cmd_stats(args)' in content
        assert 'class Result' in content

    def test_usage_md_renders(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'USAGE.md').read_text(encoding='utf-8')
        assert 'search' in content
        assert 'stats' in content
        assert '日志文件路径' in content

    def test_readme_md_renders(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'README.md').read_text(encoding='utf-8')
        assert 'log-analyzer' in content
        assert '日志分析与异常检测工具' in content


# ─── 3. TestShellGuidedTemplateRendering ───

class TestShellGuidedTemplateRendering:
    """shell-guided 模板渲染正确性。"""

    def test_skill_md_renders(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_shell_guided(tmp_path, spec)
        content = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
        assert 'type: shell' in content
        assert 'log-analyzer' in content

    def test_run_sh_renders(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_shell_guided(tmp_path, spec)
        content = (skill_dir / 'run.sh').read_text(encoding='utf-8')
        assert 'cmd_search()' in content
        assert 'cmd_stats()' in content
        assert 'set -euo pipefail' in content

    def test_usage_md_renders(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_shell_guided(tmp_path, spec)
        content = (skill_dir / 'USAGE.md').read_text(encoding='utf-8')
        assert 'bash run.sh' in content
        assert 'search' in content

    def test_readme_md_renders(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_shell_guided(tmp_path, spec)
        content = (skill_dir / 'README.md').read_text(encoding='utf-8')
        assert 'log-analyzer' in content
        assert 'bash run.sh --help' in content

    def test_boolean_shift1_and_arg_flag(self, tmp_path):
        """boolean 参数使用 shift 1 + arg_flag。"""
        spec = _make_filled_spec()
        skill_dir = _render_shell_guided(tmp_path, spec)
        content = (skill_dir / 'run.sh').read_text(encoding='utf-8')
        assert 'case_sensitive=true; shift 1' in content
        assert '--case-sensitive)' in content
        assert '--keyword)' in content
        assert 'shift 2' in content


# ─── 4. TestSpecFieldCoverage ───

class TestSpecFieldCoverage:
    """每个规约字段至少被一个模板消费。"""

    def test_all_fields_consumed(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        all_content = ''
        for f in skill_dir.iterdir():
            if f.is_file():
                all_content += f.read_text(encoding='utf-8')

        checks = [
            ('purpose.problem', '手动翻阅大量日志'),
            ('purpose.target_user', 'SRE 工程师'),
            ('purpose.scenarios', '快速定位错误日志'),
            ('capabilities.name', '关键词搜索'),
            ('capabilities.description', '按关键词过滤'),
            ('commands.name', 'search'),
            ('commands.description', '搜索包含指定关键词'),
            ('commands.args', '--keyword'),
            ('commands.example', 'python run.py search'),
            ('commands.expected_output', '找到 12 条匹配记录'),
            ('error_handling.scenario', '日志文件不存在'),
            ('error_handling.cause', '文件路径错误'),
            ('error_handling.solution', '检查文件路径'),
            ('dependencies.runtime', 'click'),
            ('dependencies.external', 'grep'),
        ]
        for field_name, expected_text in checks:
            assert expected_text in all_content, \
                f"字段 {field_name} 未被消费（期望 '{expected_text}' 出现在产物中）"


# ─── 5. TestResultPattern ───

class TestResultPattern:
    """run.py 包含 Result 数据类 + summary + __bool__。"""

    def test_result_class_present(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert 'class Result' in content
        assert 'def summary(self)' in content
        assert 'def __bool__(self)' in content
        assert 'def add_error(self' in content


# ─── 6. TestCommandGeneration ───

class TestCommandGeneration:
    """规约 commands 映射为 argparse 子命令。"""

    def test_single_command(self, tmp_path):
        spec = _make_single_cmd_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert 'def cmd_run(args)' in content
        assert "'run': cmd_run" in content

    def test_multiple_commands(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert 'def cmd_search(args)' in content
        assert 'def cmd_stats(args)' in content
        assert "'search': cmd_search" in content
        assert "'stats': cmd_stats" in content

    def test_boolean_param_store_true(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert "action='store_true'" in content

    def test_arg_flag_normalization(self, tmp_path):
        """无 -- 前缀的 arg.name 经 arg_flag 规范化后带 --。"""
        spec = _make_single_cmd_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert "'--target'" in content


# ─── 7. TestTodoComments ───

class TestTodoComments:
    """run.py 产物包含 TODO 步骤注释。"""

    def test_todo_steps_present(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert '# TODO 实现步骤' in content
        assert '从 args 获取参数' in content
        assert '对输入做基本校验' in content


# ─── 8. TestSelfBootstrap ───

class TestSelfBootstrap:
    """使用样例规约创建 Skill → validate 通过 + scan 通过。"""

    def test_python_bootstrap(self, tmp_path):
        spec = _make_filled_spec()
        variables = spec_to_template_vars(spec)
        params = {
            'name': variables['name'],
            'description': variables['description'],
            'version': variables['version'],
            'author': variables['author'],
            'tags': variables['tags'],
            'output': str(tmp_path),
        }

        save_spec(spec, tmp_path / SPEC_FILENAME)

        rc = create_skill(params, skill_type='python', skip_state=True,
                          spec_path=tmp_path / SPEC_FILENAME,
                          spec_variables=variables)
        assert rc == 0
        skill_dir = tmp_path / 'log-analyzer'
        assert (skill_dir / 'run.py').exists()
        assert (skill_dir / 'SKILL.md').exists()
        assert (skill_dir / SPEC_FILENAME).exists()

    def test_shell_bootstrap(self, tmp_path):
        spec = _make_filled_spec()
        variables = spec_to_template_vars(spec)
        params = {
            'name': variables['name'],
            'description': variables['description'],
            'version': variables['version'],
            'author': variables['author'],
            'tags': variables['tags'],
            'output': str(tmp_path),
        }

        save_spec(spec, tmp_path / SPEC_FILENAME)

        rc = create_skill(params, skill_type='shell', skip_state=True,
                          spec_path=tmp_path / SPEC_FILENAME,
                          spec_variables=variables)
        assert rc == 0
        skill_dir = tmp_path / 'log-analyzer'
        assert (skill_dir / 'run.sh').exists()
        assert (skill_dir / 'SKILL.md').exists()


# ─── 9. TestBackwardCompat ───

class TestBackwardCompat:
    """不加 --guided/--spec 时产物与 Phase 6 一致。"""

    def test_no_guided_produces_standard_output(self, tmp_path):
        variables = {
            'name': 'compat-test',
            'description': '兼容性测试工具',
            'version': '1.0.0',
            'author': 'Tester',
            'tags': ['test'],
            'date': '2026-03-30',
        }
        skill_dir = tmp_path / 'compat-skill'
        skill_dir.mkdir()
        generate_files(skill_dir, variables, skill_type='python', guided=False)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert 'def cmd_example(args)' in content
        assert 'cmd_search' not in content


# ─── 10. TestBackwardCompatNoGuidedDir ───

class TestBackwardCompatNoGuidedDir:
    """删除 python-guided 目录后 --spec 降级到 python 模板。"""

    def test_fallback_to_standard_template(self, tmp_path, monkeypatch):
        fake_builtin = tmp_path / 'templates_no_guided'
        fake_builtin.mkdir()
        shutil.copytree(
            BUILTIN_TEMPLATE_DIR / 'python',
            fake_builtin / 'python',
        )
        monkeypatch.setattr('creator.templates.BUILTIN_TEMPLATE_DIR', fake_builtin)

        variables = spec_to_template_vars(_make_single_cmd_spec())
        skill_dir = tmp_path / 'fallback-test'
        skill_dir.mkdir()
        generate_files(skill_dir, variables, skill_type='python', guided=True)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert 'def cmd_example(args)' in content


# ─── 11. TestExpandVariablesTagsList ───

class TestExpandVariablesTagsList:
    """_expand_variables 保留 tags_list 原始列表。"""

    def test_tags_list_preserved(self):
        variables = {
            'name': 'test-skill',
            'tags': ['monitoring', 'api', 'health'],
        }
        expanded = _expand_variables(variables)
        assert isinstance(expanded['tags_list'], list)
        assert expanded['tags_list'] == ['monitoring', 'api', 'health']
        assert expanded['tags'] == '[monitoring, api, health]'


# ─── 12. TestSpecToVarsNameSnake ───

class TestSpecToVarsNameSnake:
    """spec_to_template_vars 生成 name_snake + dispatch_entries。"""

    def test_name_snake_generated(self):
        spec = _make_filled_spec()
        variables = spec_to_template_vars(spec)
        cmds = variables['commands']
        assert cmds[0]['name_snake'] == 'search'
        assert cmds[1]['name_snake'] == 'stats'

    def test_dispatch_entries_generated(self):
        spec = _make_filled_spec()
        variables = spec_to_template_vars(spec)
        entries = variables['dispatch_entries']
        assert len(entries) == 2
        assert entries[0] == {'name': 'search', 'name_snake': 'search'}
        assert entries[1] == {'name': 'stats', 'name_snake': 'stats'}


# ─── 13. TestEmptySpec ───

class TestEmptySpec:
    """空规约渲染不报错，产生有效 fallback 内容。"""

    def test_empty_spec_renders(self, tmp_path):
        spec = SkillSpec(
            meta={'name': 'empty-skill', 'description': '空规约测试',
                  'version': '1.0.0', 'author': 'Tester', 'tags': []},
            purpose={},
            capabilities=[],
            commands=[],
            error_handling=[],
            dependencies={},
        )
        variables = spec_to_template_vars(spec)
        skill_dir = tmp_path / 'empty-skill'
        skill_dir.mkdir()
        generate_files(skill_dir, variables, skill_type='python', guided=True)
        assert (skill_dir / 'SKILL.md').exists()
        assert (skill_dir / 'run.py').exists()
        content = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
        assert '需要自动化处理特定任务时' in content


# ─── 14. TestCreateFromSpecIntegration ───

class TestCreateFromSpecIntegration:
    """create --spec 端到端（生成 + 验证 + scan）。"""

    def test_end_to_end(self, tmp_path):
        spec = _make_filled_spec()
        spec_path = tmp_path / SPEC_FILENAME
        save_spec(spec, spec_path)

        args = SimpleNamespace(
            spec=str(spec_path),
            interactive=False,
            strict=False,
            name=None,
            description=None,
            version=None,
            author=None,
            tags=None,
            output=str(tmp_path),
            type='python',
            template_dir=None,
        )

        rc = _create_from_spec(args)
        assert rc == 0

        skill_dir = tmp_path / 'log-analyzer'
        assert skill_dir.is_dir()
        assert (skill_dir / 'run.py').exists()
        assert (skill_dir / 'SKILL.md').exists()
        assert (skill_dir / 'USAGE.md').exists()
        assert (skill_dir / 'README.md').exists()


# ─── 15. TestMultipleCommands ───

class TestMultipleCommands:
    """3 个命令的规约生成 run.py 含 3 个 cmd_ 函数 + dispatch。"""

    def test_three_commands(self, tmp_path):
        spec = _make_filled_spec()
        spec.commands.append({
            'name': 'export',
            'description': '导出分析结果',
            'args': [
                {'name': '--format', 'description': '输出格式', 'type': 'string'},
            ],
            'example': 'python run.py export --format json',
            'expected_output': '导出完成：report.json',
        })

        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        assert 'def cmd_search(args)' in content
        assert 'def cmd_stats(args)' in content
        assert 'def cmd_export(args)' in content
        assert "'search': cmd_search" in content
        assert "'stats': cmd_stats" in content
        assert "'export': cmd_export" in content


# ─── 16. TestNoResidualPlaceholders ───

class TestNoResidualPlaceholders:
    """产物文件中无 {{ }} Jinja2 残留。"""

    def test_no_jinja2_residuals(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        pattern = re.compile(r'\{\{[^}]+\}\}')
        for f in skill_dir.iterdir():
            if f.is_file():
                content = f.read_text(encoding='utf-8')
                found = pattern.findall(content)
                assert not found, \
                    f"{f.name} 包含未替换的 Jinja2 占位符：{found}"


# ─── 17. TestQuoteEscaping (Review Fix 1) ───

class TestQuoteEscaping:
    """含单引号的规约文本不会导致生成代码语法错误。"""

    def test_single_quote_in_description(self, tmp_path):
        spec = _make_single_cmd_spec()
        spec.meta['description'] = "it's a great tool"
        spec.commands[0]['description'] = "it's the main command"
        spec.commands[0]['args'][0]['description'] = "it's the target path"
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'run.py').read_text(encoding='utf-8')
        import py_compile, tempfile
        tmp_py = tmp_path / '_check.py'
        tmp_py.write_text(content, encoding='utf-8')
        py_compile.compile(str(tmp_py), doraise=True)


# ─── 18. TestArgFlagInUsage (Review Fix 2) ───

class TestArgFlagInUsage:
    """USAGE.md 参数表使用 arg_flag 而非原始 arg.name。"""

    def test_arg_flag_shown_in_usage(self, tmp_path):
        spec = _make_single_cmd_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'USAGE.md').read_text(encoding='utf-8')
        assert '`--target`' in content
        assert '`target`（' not in content


# ─── 19. TestBooleanOptional (Review Fix 3) ───

class TestBooleanOptional:
    """boolean 参数在文档中标记为"可选"。"""

    def test_boolean_shown_as_optional(self, tmp_path):
        spec = _make_filled_spec()
        skill_dir = _render_python_guided(tmp_path, spec)
        content = (skill_dir / 'USAGE.md').read_text(encoding='utf-8')
        assert '`--case-sensitive`（可选）' in content
