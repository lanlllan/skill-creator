"""
Phase 10 规约系统 — 测试套件

覆盖维度（39 用例）：
  1. TestSpecSkeleton — 骨架生成（4）
  2. TestSpecSave — save_spec 输出格式 + 特殊字符转义（4）
  3. TestSpecLoad — 加载正常 / 缺失字段 / 未知字段 / 非字典 / 不存在文件（5）
  4. TestSchemaFreeze — schema 冻结兼容（2）
  5. TestValidateSpecErrors — error 检查（5）
  6. TestValidateSpecWarnings — warning 检查（4）
  7. TestSpecToVars — 类型映射 / required / boolean→store_true / 空 spec（4）
  8. TestCreateGuided — --guided 生成规约（2）
  9. TestCreateFromSpec — --spec 正常 / strict 阻断 / --interactive 忽略（5）
  10. TestBatchSpec — batch 含 spec 字段 / 不含时走传统路径（2）
  11. TestPackagerWhitelist — .skill-spec.yaml 打包白名单（1）
  12. TestCLIIntegration — spec 端到端（1）
"""
import os
import subprocess
import sys
import yaml
import zipfile

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
    PLACEHOLDER_EXAMPLES,
    LENGTH_CONSTRAINTS,
    TYPE_MAPPING,
)

VALID_SKILL_MD = """\
---
name: test-skill
description: A test skill
version: 1.0.0
---

## 概述

测试技能。

## 核心能力

- 功能 A

## 使用方式

运行 run.py。

## 示例

```bash
python run.py example
```
"""

VALID_RUN_PY = """\
#!/usr/bin/env python3
\"\"\"测试技能入口脚本。\"\"\"
import sys

def main():
    try:
        print("ok")
    except Exception as e:
        print(f"error: {e}")
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
"""

VALID_USAGE_MD = """\
# test-skill - 使用指南

## 快速开始

运行 `python run.py example`。
"""


def _make_valid_skill(base: Path, name: str = "test-skill") -> Path:
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD, encoding="utf-8")
    (skill_dir / "run.py").write_text(VALID_RUN_PY, encoding="utf-8")
    (skill_dir / "USAGE.md").write_text(VALID_USAGE_MD, encoding="utf-8")
    (skill_dir / "README.md").write_text("# test-skill\n\n测试。\n", encoding="utf-8")
    try:
        os.chmod(skill_dir / "run.py", 0o755)
    except OSError:
        pass
    return skill_dir


def _make_sample_spec() -> SkillSpec:
    """返回完整填充的 SkillSpec 实例。"""
    return SkillSpec(
        spec_version=SPEC_VERSION,
        meta={
            'name': 'api-monitor',
            'description': 'API 健康监控工具',
            'version': '1.0.0',
            'author': 'Test Author',
            'tags': ['monitoring', 'api'],
        },
        purpose={
            'problem': '运维团队在管理多个微服务时，缺少统一的健康检查机制，需要逐一登录服务器手动验证',
            'target_user': '全栈工程师和 SRE 团队',
            'scenarios': [
                '运维工程师在每日巡检时，批量检查所有服务端点的可用性',
                '开发者在上线新版本后，验证各 API 的响应时间是否正常',
            ],
        },
        capabilities=[{
            'name': 'HTTP 端点检查',
            'description': '对指定 URL 列表发送 GET 请求并汇总状态',
            'inputs': '一组 API URL 列表',
            'outputs': '每个 URL 的状态码和响应时间',
            'example': '输入 https://api.example.com/health → 输出 200 OK, 45ms',
        }],
        commands=[{
            'name': 'healthcheck',
            'description': '批量检查指定 URL 列表的健康状态并生成报告',
            'args': [
                {'name': '--url', 'description': '要检查的 API 端点 URL', 'type': 'string'},
                {'name': '--verbose', 'description': '显示详细输出', 'type': 'boolean'},
            ],
            'example': 'python run.py check --url https://api.example.com/health',
            'expected_output': '✅ https://api.example.com/health — 200 OK (45ms)',
        }],
        error_handling=[{
            'scenario': '目标服务器返回 5xx 错误',
            'cause': '后端服务异常或过载',
            'solution': '检查服务日志，确认服务是否正常运行',
        }],
        dependencies={
            'runtime': ['requests'],
            'external': [],
        },
    )


def _make_empty_spec() -> SkillSpec:
    """返回空骨架 SkillSpec。"""
    return generate_spec_skeleton({'name': 'test', 'description': 'test desc'})


# ============================================================
# 1. TestSpecSkeleton
# ============================================================
class TestSpecSkeleton:
    def test_basic_params(self):
        spec = generate_spec_skeleton({'name': 'my-skill', 'description': '描述'})
        assert spec.meta['name'] == 'my-skill'
        assert spec.meta['description'] == '描述'
        assert spec.spec_version == SPEC_VERSION

    def test_tags_as_string(self):
        spec = generate_spec_skeleton({'name': 'x', 'description': 'd', 'tags': 'a,b,c'})
        assert spec.meta['tags'] == ['a', 'b', 'c']

    def test_default_values(self):
        spec = generate_spec_skeleton({'name': 'x', 'description': 'd'})
        assert spec.meta['version'] == '1.0.0'
        assert spec.meta['author'] == 'OpenClaw Assistant'
        assert spec.meta['tags'] == []

    def test_empty_shells(self):
        spec = generate_spec_skeleton({'name': 'x', 'description': 'd'})
        assert spec.purpose['problem'] == ''
        assert len(spec.capabilities) == 1
        assert len(spec.commands) == 1
        assert len(spec.error_handling) == 1


# ============================================================
# 2. TestSpecSave
# ============================================================
class TestSpecSave:
    def test_output_contains_comments(self, tmp_path):
        spec = _make_empty_spec()
        path = tmp_path / SPEC_FILENAME
        save_spec(spec, path)
        content = path.read_text(encoding='utf-8')
        assert '[指令]' in content
        assert '[好的示例]' in content
        assert '[差的示例]' in content

    def test_output_is_valid_yaml(self, tmp_path):
        spec = _make_sample_spec()
        path = tmp_path / SPEC_FILENAME
        save_spec(spec, path)
        parsed = yaml.safe_load(path.read_text(encoding='utf-8'))
        assert isinstance(parsed, dict)
        assert parsed['meta']['name'] == 'api-monitor'
        assert parsed['spec_version'] == SPEC_VERSION

    def test_meta_fields_correct(self, tmp_path):
        spec = _make_sample_spec()
        path = tmp_path / SPEC_FILENAME
        save_spec(spec, path)
        parsed = yaml.safe_load(path.read_text(encoding='utf-8'))
        assert parsed['meta']['tags'] == ['monitoring', 'api']
        assert parsed['meta']['author'] == 'Test Author'

    def test_special_chars_roundtrip(self, tmp_path):
        """description 含 "、:、\\ 时 save → load 往返一致。"""
        spec = _make_sample_spec()
        spec.meta['description'] = '监控: API \\"健康\\" 检查\\n服务'
        path = tmp_path / SPEC_FILENAME
        save_spec(spec, path)
        loaded = load_spec(path)
        assert loaded.meta['description'] == spec.meta['description']


# ============================================================
# 3. TestSpecLoad
# ============================================================
class TestSpecLoad:
    def test_load_normal(self, tmp_path):
        spec = _make_sample_spec()
        path = tmp_path / SPEC_FILENAME
        save_spec(spec, path)
        loaded = load_spec(path)
        assert loaded.meta['name'] == 'api-monitor'
        assert loaded.spec_version == SPEC_VERSION

    def test_load_missing_fields(self, tmp_path):
        path = tmp_path / SPEC_FILENAME
        path.write_text('spec_version: "1.0"\nmeta:\n  name: "x"\n', encoding='utf-8')
        loaded = load_spec(path)
        assert loaded.purpose == {}
        assert loaded.capabilities == []

    def test_load_unknown_fields(self, tmp_path):
        path = tmp_path / SPEC_FILENAME
        path.write_text(
            'spec_version: "1.0"\nmeta:\n  name: "x"\nfuture_field: "ignored"\n',
            encoding='utf-8',
        )
        loaded = load_spec(path)
        assert loaded.meta['name'] == 'x'

    def test_load_non_dict(self, tmp_path):
        path = tmp_path / SPEC_FILENAME
        path.write_text('- item1\n- item2\n', encoding='utf-8')
        with pytest.raises(ValueError, match="顶层应为字典"):
            load_spec(path)

    def test_load_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_spec(tmp_path / "nonexistent.yaml")


# ============================================================
# 4. TestSchemaFreeze
# ============================================================
class TestSchemaFreeze:
    def test_old_code_new_spec(self, tmp_path):
        """新版 spec 含未知字段 → 旧代码不报错。"""
        path = tmp_path / SPEC_FILENAME
        content = (
            'spec_version: "2.0"\n'
            'meta:\n  name: "x"\n'
            'new_section:\n  data: 123\n'
        )
        path.write_text(content, encoding='utf-8')
        loaded = load_spec(path)
        assert loaded.meta['name'] == 'x'
        assert loaded.spec_version == '2.0'

    def test_new_code_old_spec(self, tmp_path):
        """旧版 spec 缺少字段 → 使用默认值。"""
        path = tmp_path / SPEC_FILENAME
        path.write_text('meta:\n  name: "old-skill"\n', encoding='utf-8')
        loaded = load_spec(path)
        assert loaded.spec_version == SPEC_VERSION
        assert loaded.dependencies == {}
        assert loaded.error_handling == []


# ============================================================
# 5. TestValidateSpecErrors
# ============================================================
class TestValidateSpecErrors:
    def test_empty_fields(self):
        spec = _make_empty_spec()
        errors, _ = validate_spec(spec)
        assert len(errors) >= 5

    def test_placeholder_copy(self):
        spec = _make_sample_spec()
        spec.purpose['problem'] = PLACEHOLDER_EXAMPLES['purpose.problem']
        errors, _ = validate_spec(spec)
        assert any('purpose.problem' in e and '示例原文' in e for e in errors)

    def test_placeholder_scenario(self):
        spec = _make_sample_spec()
        spec.purpose['scenarios'] = list(PLACEHOLDER_EXAMPLES['purpose.scenarios'])
        errors, _ = validate_spec(spec)
        assert any('scenarios' in e for e in errors)

    def test_valid_spec_no_errors(self):
        spec = _make_sample_spec()
        errors, _ = validate_spec(spec)
        assert errors == []

    def test_partial_fill(self):
        """只填了部分字段时应报 error。"""
        spec = _make_empty_spec()
        spec.purpose['problem'] = '这是一个有意义的问题描述'
        errors, _ = validate_spec(spec)
        assert len(errors) >= 4


# ============================================================
# 6. TestValidateSpecWarnings
# ============================================================
class TestValidateSpecWarnings:
    def test_too_short(self):
        spec = _make_sample_spec()
        spec.purpose['problem'] = '短'
        _, warnings = validate_spec(spec)
        assert any('purpose.problem' in w and '低于' in w for w in warnings)

    def test_too_long(self):
        spec = _make_sample_spec()
        spec.purpose['problem'] = 'x' * 300
        _, warnings = validate_spec(spec)
        assert any('purpose.problem' in w and '超过' in w for w in warnings)

    def test_description_copy(self):
        spec = _make_sample_spec()
        spec.purpose['problem'] = spec.meta['description']
        _, warnings = validate_spec(spec)
        assert any('purpose.problem' in w and 'description' in w for w in warnings)

    def test_valid_spec_no_warnings(self):
        spec = _make_sample_spec()
        _, warnings = validate_spec(spec)
        assert warnings == []


# ============================================================
# 7. TestSpecToVars
# ============================================================
class TestSpecToVars:
    def test_type_mapping(self):
        spec = _make_sample_spec()
        variables = spec_to_template_vars(spec)
        args = variables['commands'][0]['args']
        url_arg = next(a for a in args if a['name'] == '--url')
        assert url_arg['type_python'] == 'str'

    def test_required_default(self):
        spec = _make_sample_spec()
        variables = spec_to_template_vars(spec)
        args = variables['commands'][0]['args']
        for arg in args:
            assert 'required' in arg

    def test_boolean_store_true(self):
        spec = _make_sample_spec()
        variables = spec_to_template_vars(spec)
        args = variables['commands'][0]['args']
        verbose_arg = next(a for a in args if a['name'] == '--verbose')
        assert verbose_arg['type_python'] == 'bool'
        assert verbose_arg['argparse_action'] == 'store_true'
        url_arg = next(a for a in args if a['name'] == '--url')
        assert url_arg['argparse_action'] is None

    def test_empty_spec(self):
        spec = SkillSpec()
        variables = spec_to_template_vars(spec)
        assert variables['name'] == ''
        assert variables['commands'] == []


# ============================================================
# 8. TestCreateGuided
# ============================================================
class TestCreateGuided:
    def test_guided_generates_spec(self, tmp_path):
        from creator.commands.create import main_create
        args = SimpleNamespace(
            name='test-skill', description='A test', version='1.0.0',
            author=None, tags=None, output=str(tmp_path),
            interactive=False, type='python', template_dir=None,
            guided=True, spec=None, strict=False,
        )
        rc = main_create(args)
        assert rc == 0
        spec_file = tmp_path / 'test-skill' / SPEC_FILENAME
        assert spec_file.exists()

    def test_guided_no_template_render(self, tmp_path):
        from creator.commands.create import main_create
        args = SimpleNamespace(
            name='test-skill', description='A test', version='1.0.0',
            author=None, tags=None, output=str(tmp_path),
            interactive=False, type='python', template_dir=None,
            guided=True, spec=None, strict=False,
        )
        main_create(args)
        skill_dir = tmp_path / 'test-skill'
        assert not (skill_dir / 'run.py').exists()
        assert not (skill_dir / 'SKILL.md').exists()


# ============================================================
# 9. TestCreateFromSpec
# ============================================================
class TestCreateFromSpec:
    def _write_spec(self, tmp_path) -> Path:
        spec = _make_sample_spec()
        spec.meta['name'] = 'test-skill'
        spec_path = tmp_path / 'input' / SPEC_FILENAME
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        save_spec(spec, spec_path)
        return spec_path

    def test_spec_normal_render(self, tmp_path):
        from creator.commands.create import main_create
        spec_path = self._write_spec(tmp_path)
        out_dir = tmp_path / 'out'
        args = SimpleNamespace(
            name=None, description=None, version='1.0.0',
            author=None, tags=None, output=str(out_dir),
            interactive=False, type='python', template_dir=None,
            guided=False, spec=str(spec_path), strict=False,
        )
        rc = main_create(args)
        assert rc == 0
        assert (out_dir / 'test-skill' / 'SKILL.md').exists()
        assert (out_dir / 'test-skill' / SPEC_FILENAME).exists()

    def test_errors_non_strict_no_block(self, tmp_path):
        """有 errors + 非 strict → 打印但不阻断。"""
        from creator.commands.create import main_create
        spec = _make_empty_spec()
        spec.meta['name'] = 'test-skill'
        spec.meta['description'] = 'A test skill'
        spec_path = tmp_path / 'input' / SPEC_FILENAME
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        save_spec(spec, spec_path)
        out_dir = tmp_path / 'out'
        args = SimpleNamespace(
            name=None, description=None, version='1.0.0',
            author=None, tags=None, output=str(out_dir),
            interactive=False, type='python', template_dir=None,
            guided=False, spec=str(spec_path), strict=False,
        )
        rc = main_create(args)
        assert rc == 0

    def test_warnings_strict_blocks(self, tmp_path):
        """有 warnings + --strict → 阻断。"""
        from creator.commands.create import main_create
        spec = _make_sample_spec()
        spec.meta['name'] = 'test-skill'
        spec.purpose['problem'] = spec.meta['description']
        spec_path = tmp_path / 'input' / SPEC_FILENAME
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        save_spec(spec, spec_path)
        args = SimpleNamespace(
            name=None, description=None, version='1.0.0',
            author=None, tags=None, output=str(tmp_path / 'out'),
            interactive=False, type='python', template_dir=None,
            guided=False, spec=str(spec_path), strict=True,
        )
        rc = main_create(args)
        assert rc == 1

    def test_errors_strict_blocks(self, tmp_path):
        """有 errors + --strict → 阻断。"""
        from creator.commands.create import main_create
        spec = _make_empty_spec()
        spec.meta['name'] = 'test-skill'
        spec.meta['description'] = 'test'
        spec_path = tmp_path / 'input' / SPEC_FILENAME
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        save_spec(spec, spec_path)
        args = SimpleNamespace(
            name=None, description=None, version='1.0.0',
            author=None, tags=None, output=str(tmp_path / 'out'),
            interactive=False, type='python', template_dir=None,
            guided=False, spec=str(spec_path), strict=True,
        )
        rc = main_create(args)
        assert rc == 1

    def test_spec_ignores_interactive(self, tmp_path, capsys):
        """--spec 模式下 --interactive 无效，输出提示。"""
        from creator.commands.create import main_create
        spec_path = self._write_spec(tmp_path)
        out_dir = tmp_path / 'out'
        args = SimpleNamespace(
            name=None, description=None, version='1.0.0',
            author=None, tags=None, output=str(out_dir),
            interactive=True, type='python', template_dir=None,
            guided=False, spec=str(spec_path), strict=False,
        )
        main_create(args)
        captured = capsys.readouterr()
        assert '--interactive 无效' in captured.out


# ============================================================
# 10. TestBatchSpec
# ============================================================
class TestBatchSpec:
    def test_batch_with_spec(self, tmp_path):
        from creator.commands.batch import main_batch
        spec = _make_sample_spec()
        spec.meta['name'] = 'batch-skill'
        spec.meta['description'] = 'Batch test'
        spec_file = tmp_path / 'specs' / SPEC_FILENAME
        spec_file.parent.mkdir()
        save_spec(spec, spec_file)

        batch_yaml = tmp_path / 'batch.yaml'
        batch_yaml.write_text(
            f"skills:\n"
            f"  - name: batch-skill\n"
            f"    description: Batch test\n"
            f"    output: {tmp_path / 'out'}\n"
            f"    spec: specs/{SPEC_FILENAME}\n",
            encoding='utf-8',
        )
        args = SimpleNamespace(file=str(batch_yaml), fail_on_security=False)
        rc = main_batch(args)
        assert rc == 0
        assert (tmp_path / 'out' / 'batch-skill' / SPEC_FILENAME).exists()

    def test_batch_without_spec(self, tmp_path):
        from creator.commands.batch import main_batch
        batch_yaml = tmp_path / 'batch.yaml'
        batch_yaml.write_text(
            f"skills:\n"
            f"  - name: normal-skill\n"
            f"    description: Normal test\n"
            f"    output: {tmp_path / 'out'}\n",
            encoding='utf-8',
        )
        args = SimpleNamespace(file=str(batch_yaml), fail_on_security=False)
        rc = main_batch(args)
        assert rc == 0
        assert (tmp_path / 'out' / 'normal-skill' / 'SKILL.md').exists()


# ============================================================
# 11. TestPackagerWhitelist
# ============================================================
class TestPackagerWhitelist:
    def test_spec_yaml_in_package(self, tmp_path):
        from creator.packager import collect_files
        skill = _make_valid_skill(tmp_path)
        (skill / SPEC_FILENAME).write_text('spec_version: "1.0"\n', encoding='utf-8')
        files = collect_files(skill, [])
        names = {f.name for f in files}
        assert SPEC_FILENAME in names


# ============================================================
# 12. TestCLIIntegration
# ============================================================
class TestCLIIntegration:
    def test_spec_generate_and_validate(self, tmp_path):
        run_py = Path(__file__).parent.parent / 'run.py'
        result = subprocess.run(
            [sys.executable, str(run_py), 'spec',
             '-n', 'cli-test', '-d', 'CLI test skill',
             '-o', str(tmp_path)],
            capture_output=True, text=True, cwd=str(run_py.parent),
        )
        assert result.returncode == 0
        spec_path = tmp_path / SPEC_FILENAME
        assert spec_path.exists()

        result2 = subprocess.run(
            [sys.executable, str(run_py), 'spec',
             '--validate', str(spec_path)],
            capture_output=True, text=True, cwd=str(run_py.parent),
        )
        assert result2.returncode == 1
        assert '不能为空' in result2.stdout or '❌' in result2.stdout
