"""
Phase 12 测试套件：内容质量评分 v2（Content-Aware Scoring）

覆盖范围：
- 权重调整验证（7 用例）
- 占位符检测（5 用例）
- 内容多样性（6 用例，含非目标章节排除 + 子标题结构回归）
- 文本相似度工具（4 用例）
- 函数实质性（6 用例）
- USAGE 完整性（3 用例）
- 规约覆盖率（5 用例）
- 基线对比（3 用例）
- 报告集成（2 用例）
- 端到端（3 用例）

合计：44 用例
"""
import os
import sys
import pytest
from pathlib import Path

from creator.scorer import (
    SkillScorer, PLACEHOLDER_PATTERNS, TARGET_SECTIONS,
)


# ═══════════════════════════════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════════════════════════════

GOOD_FRONT_MATTER = (
    '---\nname: test-skill\ndescription: 测试用 skill\n'
    'version: 1.0.0\nauthor: tester\ntags: [test]\n---\n\n'
)

GOOD_PYTHON_ENTRY = (
    '#!/usr/bin/env python3\n'
    '"""测试用 skill"""\n'
    'import argparse\nimport sys\nimport json\n\n'
    'def check_endpoint(url, timeout=10):\n'
    '    """检查端点。"""\n'
    '    try:\n'
    '        import urllib.request\n'
    '        req = urllib.request.Request(url)\n'
    '        response = urllib.request.urlopen(req, timeout=timeout)\n'
    '        return {"url": url, "status": response.status, "ok": True}\n'
    '    except Exception as e:\n'
    '        return {"url": url, "ok": False, "error": str(e)}\n\n'
    'def generate_report(results):\n'
    '    """生成报告。"""\n'
    '    total = len(results)\n'
    '    healthy = sum(1 for r in results if r["ok"])\n'
    '    return {"total": total, "healthy": healthy}\n\n'
    'def format_output(result):\n'
    '    """格式化输出。"""\n'
    '    if result["ok"]:\n'
    '        print(f"✅ {result[\'url\']} OK")\n'
    '    else:\n'
    '        print(f"❌ {result[\'url\']} FAIL", file=sys.stderr)\n\n'
    'def validate_url(url):\n'
    '    """验证 URL。"""\n'
    '    if not url.startswith(("http://", "https://")):\n'
    '        raise ValueError(f"Invalid: {url}")\n'
    '    return url\n\n'
    'def load_config(path):\n'
    '    """加载配置。"""\n'
    '    try:\n'
    '        with open(path) as f:\n'
    '            return json.load(f)\n'
    '    except FileNotFoundError:\n'
    '        print(f"❌ 不存在: {path}", file=sys.stderr)\n'
    '        return None\n\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="测试工具")\n'
    '    parser.add_argument("--verbose", "-v", action="store_true")\n'
    '    parser.add_argument("--dry-run", action="store_true")\n'
    '    subparsers = parser.add_subparsers(dest="command")\n'
    '    p = subparsers.add_parser("check")\n'
    '    p.add_argument("--url", required=True)\n'
    '    p.add_argument("--timeout", type=int, choices=[5,10,30])\n'
    '    r = subparsers.add_parser("report")\n'
    '    r.add_argument("--config", required=True)\n'
    '    args = parser.parse_args()\n'
    '    if not args.command:\n'
    '        parser.print_help()\n'
    '        return 0\n'
    '    if args.command == "check":\n'
    '        result = check_endpoint(args.url)\n'
    '        format_output(result)\n'
    '        return 0 if result["ok"] else 1\n'
    '    return 0\n\n'
    'if __name__ == "__main__":\n'
    '    sys.exit(main())\n'
)


@pytest.fixture
def good_skill(tmp_path):
    """高质量 Skill fixture。"""
    d = tmp_path / "good-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        GOOD_FRONT_MATTER +
        '## 概述\n监控 API 端点的健康状态。\n\n'
        '## 适用场景\n- 运维工程师在每日巡检时检查微服务端点\n'
        '- 开发者在部署后验证 API 响应\n'
        '- 安全团队定期检测公开 API 的可用性\n\n'
        '## 核心能力\n- 端点健康检查：发送请求验证状态码\n'
        '- 批量监控：从配置读取端点列表\n'
        '- 报告生成：汇总监控结果为报告\n\n'
        '## 使用方式\n运行 check 或 report 子命令。\n\n'
        '## 示例\n```bash\npython run.py check --url https://example.com\n```\n\n'
        '## 故障排除\n| 问题 | 原因 | 解决方案 |\n|------|------|---------|'
        '\n| 连接超时 | 网络问题 | 检查网络 |\n',
        encoding='utf-8')
    (d / "run.py").write_text(GOOD_PYTHON_ENTRY, encoding='utf-8')
    os.chmod(d / "run.py", 0o755)
    (d / "USAGE.md").write_text(
        '# test-skill 使用指南\n\n## 命令参考\n| 命令 | 说明 |\n|------|------|\n'
        '| check | 检查端点 |\n\n## 示例\n```bash\npython run.py check --url URL\n```\n\n'
        '```bash\npython run.py report --config cfg.json\n```\n\n'
        '```\n✅ https://example.com — 200 OK\n```\n',
        encoding='utf-8')
    (d / "README.md").write_text(
        '# test-skill\n快速开始。详见 [USAGE.md](USAGE.md)。\n',
        encoding='utf-8')
    (d / "templates").mkdir()
    (d / "config.yaml").write_text('endpoints: []', encoding='utf-8')
    return d


@pytest.fixture
def placeholder_skill(tmp_path):
    """占位符残留 Skill fixture。"""
    d = tmp_path / "placeholder-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        GOOD_FRONT_MATTER +
        '## 概述\n在以下场景中使用。\n\n'
        '## 核心能力\n- 能力1\n- 能力2\n- 能力3\n\n'
        '## 适用场景\n- 场景1\n- 场景2\n',
        encoding='utf-8')
    (d / "run.py").write_text(
        '#!/usr/bin/env python3\n"""test"""\nimport sys\n\n'
        'def main():\n    print("Hello, World!")\n    return 0\n\n'
        'if __name__ == "__main__":\n    sys.exit(main())\n',
        encoding='utf-8')
    os.chmod(d / "run.py", 0o755)
    (d / "USAGE.md").write_text('# 使用指南\n命令执行后会输出...\n', encoding='utf-8')
    (d / "README.md").write_text('# test\n', encoding='utf-8')
    return d


@pytest.fixture
def mid_skill(tmp_path):
    """中等质量 Skill fixture。"""
    d = tmp_path / "mid-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        GOOD_FRONT_MATTER +
        '## 概述\n检查文件是否存在。\n\n'
        '## 核心能力\n- 检查指定路径的文件是否存在\n'
        '- 输出文件状态信息和大小\n\n'
        '## 使用方式\n运行 check 命令。\n',
        encoding='utf-8')
    (d / "run.py").write_text(
        '#!/usr/bin/env python3\n"""文件检查"""\n'
        'import argparse\nimport sys\nimport os\n\n'
        'def check_file(path):\n'
        '    """检查文件。"""\n'
        '    try:\n'
        '        if os.path.exists(path):\n'
        '            print(f"✅ 存在: {path}")\n'
        '            return True\n'
        '        else:\n'
        '            print(f"❌ 不存在: {path}", file=sys.stderr)\n'
        '            return False\n'
        '    except Exception as e:\n'
        '        print(f"❌ 失败: {e}", file=sys.stderr)\n'
        '        return False\n\n'
        'def main():\n'
        '    parser = argparse.ArgumentParser()\n'
        '    subparsers = parser.add_subparsers(dest="command")\n'
        '    p = subparsers.add_parser("check")\n'
        '    p.add_argument("--path", required=True)\n'
        '    args = parser.parse_args()\n'
        '    if not args.command:\n'
        '        parser.print_help()\n'
        '        return 0\n'
        '    if args.command == "check":\n'
        '        ok = check_file(args.path)\n'
        '        return 0 if ok else 1\n'
        '    return 0\n\n'
        'if __name__ == "__main__":\n'
        '    sys.exit(main())\n',
        encoding='utf-8')
    os.chmod(d / "run.py", 0o755)
    (d / "USAGE.md").write_text(
        '# 使用指南\n\n## 命令参考\ncheck 命令。\n\n'
        '## 示例\n```bash\npython run.py check --path /tmp/x\n```\n',
        encoding='utf-8')
    (d / "README.md").write_text('# mid-skill\n文件检查。\n', encoding='utf-8')
    return d


# ═══════════════════════════════════════════════════════════════════════
#  TestWeightAdjustment
# ═══════════════════════════════════════════════════════════════════════

class TestWeightAdjustment:
    def test_total_still_100(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        assert s.scores['total'] <= 100

    def test_structure_max_15(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        assert s.scores['structure'] <= 15

    def test_functionality_max_25(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        assert s.scores['functionality'] <= 25

    def test_quality_max_20(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        assert s.scores['quality'] <= 20

    def test_docs_max_10(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        assert s.scores['docs'] <= 10

    def test_standard_max_10(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        assert s.scores['standard'] <= 10

    def test_content_in_scores(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        assert 'content' in s.scores
        assert s.scores['content'] <= 20


# ═══════════════════════════════════════════════════════════════════════
#  TestPlaceholderDetection
# ═══════════════════════════════════════════════════════════════════════

class TestPlaceholderDetection:
    def test_no_placeholder_full_score(self, good_skill):
        s = SkillScorer(good_skill)
        result = s._content_placeholder_residue()
        assert result == 6

    def test_high_placeholder_zero(self, placeholder_skill):
        s = SkillScorer(placeholder_skill)
        result = s._content_placeholder_residue()
        assert result <= 2

    def test_low_placeholder_partial(self, tmp_path):
        d = tmp_path / "low-ph"
        d.mkdir()
        (d / "SKILL.md").write_text(
            GOOD_FRONT_MATTER +
            '## 概述\n监控 API 端点的健康状态和响应时间。\n\n'
            '## 核心能力\n- 端点健康检查\n- 批量监控\n- 报告生成\n\n'
            '## 适用场景\n- 运维巡检\n- 部署验证\n- 能力1\n',
            encoding='utf-8')
        s = SkillScorer(d)
        result = s._content_placeholder_residue()
        assert result == 4

    def test_placeholder_patterns_match(self):
        test_cases = [
            ('场景1', True), ('能力2', True), ('功能点3', True),
            ('错误1', True), ('原因2', True), ('方案3', True),
            ('option1: value1', True), ('命令执行后会输出...', True),
            ('需要自动化处理特定任务', True), ('在以下场景中', True),
            ('正常的文本内容', False), ('检查 API 健康状态', False),
        ]
        for text, should_match in test_cases:
            matched = any(p.search(text) for p in PLACEHOLDER_PATTERNS)
            assert matched == should_match, f"Pattern match failed for: {text!r}"

    def test_no_skill_md_returns_zero(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        s = SkillScorer(d)
        assert s._content_placeholder_residue() == 0


# ═══════════════════════════════════════════════════════════════════════
#  TestContentDiversity
# ═══════════════════════════════════════════════════════════════════════

class TestContentDiversity:
    def test_diverse_items_full_score(self, tmp_path):
        d = tmp_path / "diverse"
        d.mkdir()
        (d / "SKILL.md").write_text(
            GOOD_FRONT_MATTER +
            '## 适用场景\n'
            '- 运维工程师在每日巡检时检查微服务端点\n'
            '- 开发者在部署后验证 API 响应时间\n'
            '- 安全团队定期检测公开接口可用性\n\n'
            '## 核心能力\n'
            '- 端点健康检查：发送请求验证状态码\n'
            '- 批量监控：从配置读取端点列表\n',
            encoding='utf-8')
        s = SkillScorer(d)
        result = s._content_diversity()
        assert result >= 3

    def test_identical_items_zero(self, tmp_path):
        d = tmp_path / "identical"
        d.mkdir()
        (d / "SKILL.md").write_text(
            GOOD_FRONT_MATTER +
            '## 适用场景\n'
            '- 检查文件是否存在\n'
            '- 检查文件是否存在\n'
            '- 检查文件是否存在\n',
            encoding='utf-8')
        s = SkillScorer(d)
        result = s._content_diversity()
        assert result == 0

    def test_partially_similar(self, tmp_path):
        d = tmp_path / "partial"
        d.mkdir()
        (d / "SKILL.md").write_text(
            GOOD_FRONT_MATTER +
            '## 适用场景\n'
            '- 检查微服务端点的可用性\n'
            '- 检查微服务端点的可用\n'
            '- 安全团队定期评估系统安全性\n',
            encoding='utf-8')
        s = SkillScorer(d)
        result = s._content_diversity()
        assert 0 < result < 4

    def test_single_item_returns_zero(self, tmp_path):
        d = tmp_path / "single"
        d.mkdir()
        (d / "SKILL.md").write_text(
            GOOD_FRONT_MATTER + '## 适用场景\n- 仅一个场景\n',
            encoding='utf-8')
        s = SkillScorer(d)
        assert s._content_diversity() == 0

    def test_non_target_section_excluded(self, tmp_path):
        """非目标章节的列表项不参与多样性评分。"""
        d = tmp_path / "section-filter"
        d.mkdir()
        (d / "SKILL.md").write_text(
            GOOD_FRONT_MATTER +
            '## 故障排除\n- 相同的排查步骤\n- 相同的排查步骤\n- 相同的排查步骤\n\n'
            '## 前置依赖\n- 依赖A\n- 依赖A\n',
            encoding='utf-8')
        s = SkillScorer(d)
        items = s._extract_section_list_items(
            (d / "SKILL.md").read_text(encoding='utf-8'))
        assert len(items) == 0
        assert s._content_diversity() == 0

    def test_capability_with_sub_headings(self, tmp_path):
        """核心能力含 ### 子标题 + 列表项的真实模板结构应被正确提取。"""
        d = tmp_path / "sub-heading"
        d.mkdir()
        (d / "SKILL.md").write_text(
            GOOD_FRONT_MATTER +
            '## 适用场景\n'
            '- 运维工程师在每日巡检时检查微服务\n\n'
            '## 核心能力\n'
            '### 1. 端点健康检查\n'
            '- 发送 HTTP 请求验证状态码\n'
            '- 支持自定义超时和重试策略\n\n'
            '### 2. 批量监控\n'
            '- 从配置文件读取端点列表\n'
            '- 并行探测多个端点并汇总结果\n\n'
            '## 使用方式\n'
            '- 这行不应被提取\n',
            encoding='utf-8')
        s = SkillScorer(d)
        content = (d / "SKILL.md").read_text(encoding='utf-8')
        items = s._extract_section_list_items(content)
        assert len(items) == 5
        assert '发送 HTTP 请求验证状态码' in items
        assert '从配置文件读取端点列表' in items
        assert '这行不应被提取' not in items
        result = s._content_diversity()
        assert result >= 3


# ═══════════════════════════════════════════════════════════════════════
#  TestTextSimilarity
# ═══════════════════════════════════════════════════════════════════════

class TestTextSimilarity:
    def test_identical_strings(self):
        assert SkillScorer._text_similarity("完全相同的字符串", "完全相同的字符串") == 1.0

    def test_completely_different(self):
        sim = SkillScorer._text_similarity("ABCDEF", "xyz123")
        assert sim < 0.1

    def test_empty_string(self):
        assert SkillScorer._text_similarity("", "test") == 0.0
        assert SkillScorer._text_similarity("test", "") == 0.0

    def test_partial_overlap(self):
        sim = SkillScorer._text_similarity(
            "运维工程师在巡检时检查",
            "运维工程师在部署时验证")
        assert 0.0 < sim < 1.0


# ═══════════════════════════════════════════════════════════════════════
#  TestFunctionSubstance
# ═══════════════════════════════════════════════════════════════════════

class TestFunctionSubstance:
    def test_substantial_python_functions(self, good_skill):
        s = SkillScorer(good_skill)
        result = s._content_function_substance()
        assert result >= 3

    def test_trivial_python_functions(self, tmp_path):
        d = tmp_path / "trivial"
        d.mkdir()
        (d / "run.py").write_text(
            '#!/usr/bin/env python3\n'
            'def func_a():\n    pass\n\n'
            'def func_b():\n    return None\n\n'
            'def func_c():\n    raise NotImplementedError\n\n'
            'def main():\n    func_a()\n',
            encoding='utf-8')
        os.chmod(d / "run.py", 0o755)
        s = SkillScorer(d)
        assert s._content_function_substance() == 0

    def test_hello_world_zero(self, tmp_path):
        d = tmp_path / "hw"
        d.mkdir()
        (d / "run.py").write_text(
            '#!/usr/bin/env python3\nimport sys\n\n'
            'def main():\n    print("Hello")\n    return 0\n\n'
            'if __name__ == "__main__":\n    sys.exit(main())\n',
            encoding='utf-8')
        os.chmod(d / "run.py", 0o755)
        s = SkillScorer(d)
        assert s._content_function_substance() == 0

    def test_substantial_shell_functions(self, tmp_path):
        d = tmp_path / "shell-sub"
        d.mkdir()
        (d / "run.sh").write_text(
            '#!/bin/bash\nset -e\n\n'
            'cmd_check() {\n'
            '    local url="$1"\n'
            '    local status\n'
            '    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")\n'
            '    echo "Status: $status"\n'
            '    return 0\n}\n\n'
            'cmd_report() {\n'
            '    local config="$1"\n'
            '    local urls\n'
            '    urls=$(cat "$config")\n'
            '    echo "Processing $urls"\n'
            '    return 0\n}\n\n'
            'cmd_clean() {\n'
            '    local dir="$1"\n'
            '    rm -rf "$dir/tmp"\n'
            '    echo "Cleaned"\n'
            '    return 0\n}\n\n'
            'main() {\n    cmd_check "$1"\n}\n',
            encoding='utf-8')
        os.chmod(d / "run.sh", 0o755)
        s = SkillScorer(d)
        assert s._content_function_substance() == 4

    def test_main_excluded(self, tmp_path):
        d = tmp_path / "main-ex"
        d.mkdir()
        (d / "run.py").write_text(
            '#!/usr/bin/env python3\n'
            'def main():\n'
            '    import argparse\n'
            '    parser = argparse.ArgumentParser()\n'
            '    parser.add_argument("--url")\n'
            '    args = parser.parse_args()\n'
            '    print(args.url)\n'
            '    return 0\n',
            encoding='utf-8')
        os.chmod(d / "run.py", 0o755)
        s = SkillScorer(d)
        assert s._content_function_substance() == 0

    def test_no_entry_script_zero(self, tmp_path):
        d = tmp_path / "no-entry"
        d.mkdir()
        s = SkillScorer(d)
        assert s._content_function_substance() == 0


# ═══════════════════════════════════════════════════════════════════════
#  TestUsageCompleteness
# ═══════════════════════════════════════════════════════════════════════

class TestUsageCompleteness:
    def test_rich_usage_full_score(self, good_skill):
        s = SkillScorer(good_skill)
        assert s._content_usage_completeness() == 3

    def test_placeholder_usage_zero(self, tmp_path):
        d = tmp_path / "ph-usage"
        d.mkdir()
        (d / "USAGE.md").write_text(
            '# 使用指南\n```\n命令执行后会输出...\n```\n\n'
            '```\n场景1 的输出\n```\n',
            encoding='utf-8')
        s = SkillScorer(d)
        assert s._content_usage_completeness() == 0

    def test_no_usage_zero(self, tmp_path):
        d = tmp_path / "no-usage"
        d.mkdir()
        s = SkillScorer(d)
        assert s._content_usage_completeness() == 0


# ═══════════════════════════════════════════════════════════════════════
#  TestSpecCoverage
# ═══════════════════════════════════════════════════════════════════════

class TestSpecCoverage:
    def test_no_spec_auto_full(self, tmp_path):
        d = tmp_path / "no-spec"
        d.mkdir()
        s = SkillScorer(d)
        assert s._content_spec_coverage() == 3

    def test_fully_filled_spec(self, tmp_path):
        d = tmp_path / "full-spec"
        d.mkdir()
        (d / ".skill-spec.yaml").write_text(
            'spec_version: "1.0"\n'
            'purpose:\n'
            '  problem: "需要监控 API 端点"\n'
            '  target_user: "运维工程师"\n'
            '  scenarios:\n'
            '    - "每日巡检检查端点"\n'
            '    - "部署后验证 API"\n'
            'capabilities:\n'
            '  - name: "健康检查"\n'
            '    description: "发送请求验证状态"\n'
            '    inputs: "URL 列表"\n'
            '    outputs: "状态码和耗时"\n'
            'commands:\n'
            '  - name: "check"\n'
            '    description: "检查端点"\n'
            '    args:\n'
            '      - name: "--url"\n'
            '        description: "目标 URL"\n'
            'error_handling:\n'
            '  - scenario: "连接超时"\n'
            '    cause: "网络问题"\n'
            '    solution: "检查网络"\n',
            encoding='utf-8')
        s = SkillScorer(d)
        assert s._content_spec_coverage() == 3

    def test_partially_filled_spec(self, tmp_path):
        d = tmp_path / "partial-spec"
        d.mkdir()
        (d / ".skill-spec.yaml").write_text(
            'spec_version: "1.0"\n'
            'purpose:\n'
            '  problem: "需要监控"\n'
            '  target_user: ""\n'
            '  scenarios:\n'
            '    - ""\n'
            '    - ""\n'
            'capabilities:\n'
            '  - name: "检查"\n'
            '    description: ""\n'
            '    inputs: ""\n'
            '    outputs: ""\n'
            'commands:\n'
            '  - name: "check"\n'
            '    description: ""\n'
            'error_handling:\n'
            '  - scenario: ""\n'
            '    cause: ""\n'
            '    solution: ""\n',
            encoding='utf-8')
        s = SkillScorer(d)
        result = s._content_spec_coverage()
        assert result <= 1

    def test_empty_spec_zero(self, tmp_path):
        d = tmp_path / "empty-spec"
        d.mkdir()
        (d / ".skill-spec.yaml").write_text(
            'spec_version: "1.0"\n'
            'purpose:\n'
            '  problem: ""\n'
            '  target_user: ""\n'
            '  scenarios:\n'
            '    - ""\n',
            encoding='utf-8')
        s = SkillScorer(d)
        assert s._content_spec_coverage() == 0

    def test_invalid_yaml_zero(self, tmp_path):
        d = tmp_path / "bad-yaml"
        d.mkdir()
        (d / ".skill-spec.yaml").write_text(
            '{{invalid yaml content', encoding='utf-8')
        s = SkillScorer(d)
        assert s._content_spec_coverage() == 0


# ═══════════════════════════════════════════════════════════════════════
#  TestBaselineCompatibility
# ═══════════════════════════════════════════════════════════════════════

class TestBaselineCompatibility:
    """确保权重调整后用户可见总分偏差 ≤ 5 分。

    对比口径：新总分（含 content 维度）vs 旧总分（Phase 11 基线）。
    """
    BASELINES = {'high': 92, 'mid': 64, 'low': 34}

    def _build_high(self, base):
        d = base / "bl-high"
        d.mkdir()
        (d / "SKILL.md").write_text(
            '---\nname: api-monitor\ndescription: 监控 API 端点的健康状态和响应时间\n'
            'version: 1.0.0\nauthor: test\ntags: [monitoring]\n---\n\n'
            '## 概述\nAPI Monitor 是一个用于监控多个 API 端点健康状态的工具。\n\n'
            '## 核心能力\n### 端点健康检查\n对指定 URL 发送 HTTP 请求。\n\n'
            '### 批量监控\n支持从配置文件读取端点列表。\n\n'
            '## 使用方式\n通过命令行运行。\n\n## 示例\ncheck 命令。\n\n'
            '## 故障排除\n| 问题 | 原因 | 解决方案 |\n|------|------|---------|'
            '\n| 超时 | 网络 | 检查网络 |\n| 500 | 服务端 | 联系维护 |\n',
            encoding='utf-8')
        (d / "run.py").write_text(GOOD_PYTHON_ENTRY, encoding='utf-8')
        os.chmod(d / "run.py", 0o755)
        (d / "USAGE.md").write_text(
            '# 使用指南\n\n## 命令参考\n| 命令 | 说明 |\n|------|------|\n'
            '| check | 检查 |\n\n## 示例\n```bash\npython run.py check --url URL\n```\n\n'
            '```bash\npython run.py report --config cfg\n```\n\n'
            '```\n✅ OK\n```\n', encoding='utf-8')
        (d / "README.md").write_text(
            '# api-monitor\n快速开始。详见 [USAGE.md](USAGE.md) 和 [SKILL.md](SKILL.md)。\n',
            encoding='utf-8')
        (d / "templates").mkdir()
        (d / "config.yaml").write_text('x: 1', encoding='utf-8')
        return d

    def _build_mid(self, base):
        d = base / "bl-mid"
        d.mkdir()
        (d / "SKILL.md").write_text(
            '---\nname: file-checker\ndescription: 检查文件是否存在\n'
            'version: 1.0.0\nauthor: test\ntags: [utility]\n---\n\n'
            '## 概述\n检查文件是否存在。\n\n## 核心能力\n检查文件。\n\n'
            '## 使用方式\n运行 check。\n', encoding='utf-8')
        (d / "run.py").write_text(
            '#!/usr/bin/env python3\n"""文件检查"""\n'
            'import argparse\nimport sys\nimport os\n\n'
            'def check_file(path):\n    """检查。"""\n'
            '    try:\n        if os.path.exists(path):\n'
            '            print(f"✅ 存在: {path}")\n            return True\n'
            '        else:\n            print(f"❌ 不存在: {path}", file=sys.stderr)\n'
            '            return False\n'
            '    except Exception as e:\n'
            '        print(f"❌ 失败: {e}", file=sys.stderr)\n'
            '        return False\n\n'
            'def main():\n    parser = argparse.ArgumentParser()\n'
            '    subparsers = parser.add_subparsers(dest="command")\n'
            '    p = subparsers.add_parser("check")\n'
            '    p.add_argument("--path", required=True)\n'
            '    args = parser.parse_args()\n'
            '    if not args.command:\n        parser.print_help()\n        return 0\n'
            '    if args.command == "check":\n        ok = check_file(args.path)\n'
            '        return 0 if ok else 1\n    return 0\n\n'
            'if __name__ == "__main__":\n    sys.exit(main())\n',
            encoding='utf-8')
        os.chmod(d / "run.py", 0o755)
        (d / "USAGE.md").write_text(
            '# 使用指南\n\n## 命令参考\ncheck。\n\n## 示例\n```bash\npython run.py check --path x\n```\n',
            encoding='utf-8')
        (d / "README.md").write_text('# file-checker\n文件检查工具。\n', encoding='utf-8')
        return d

    def _build_low(self, base):
        d = base / "bl-low"
        d.mkdir()
        (d / "SKILL.md").write_text(
            '---\nname: my-skill\ndescription: 一个示例 skill\n'
            'version: 1.0.0\nauthor: test\ntags: [example]\n---\n\n'
            '## 概述\n在以下场景中使用：\n- 场景1\n- 场景2\n\n'
            '## 核心能力\n- 能力1\n- 能力2\n', encoding='utf-8')
        (d / "run.py").write_text(
            '#!/usr/bin/env python3\n"""示例"""\nimport sys\n\n'
            'def main():\n    print("Hello, World!")\n    return 0\n\n'
            'if __name__ == "__main__":\n    sys.exit(main())\n',
            encoding='utf-8')
        os.chmod(d / "run.py", 0o755)
        (d / "USAGE.md").write_text('# 使用指南\n命令执行后会输出...\n', encoding='utf-8')
        (d / "README.md").write_text('# my-skill\n', encoding='utf-8')
        return d

    def test_high_quality_deviation(self, tmp_path):
        d = self._build_high(tmp_path)
        s = SkillScorer(d)
        s.score()
        assert abs(s.scores['total'] - self.BASELINES['high']) <= 5

    def test_mid_quality_deviation(self, tmp_path):
        d = self._build_mid(tmp_path)
        s = SkillScorer(d)
        s.score()
        assert abs(s.scores['total'] - self.BASELINES['mid']) <= 5

    def test_low_quality_deviation(self, tmp_path):
        d = self._build_low(tmp_path)
        s = SkillScorer(d)
        s.score()
        assert abs(s.scores['total'] - self.BASELINES['low']) <= 5


# ═══════════════════════════════════════════════════════════════════════
#  TestReportIntegration
# ═══════════════════════════════════════════════════════════════════════

class TestReportIntegration:
    def test_report_includes_content(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        report = s.generate_report()
        assert '内容密度:' in report
        assert '/20' in report

    def test_suggestions_for_low_content(self, placeholder_skill):
        s = SkillScorer(placeholder_skill)
        s.score()
        report = s.generate_report()
        assert '减少占位符残留' in report or '内容' in report


# ═══════════════════════════════════════════════════════════════════════
#  TestEndToEnd
# ═══════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    def test_validate_command_shows_content(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        assert '内容密度' in '\n'.join(s.remarks)

    def test_traditional_skill_no_penalty(self, mid_skill):
        """传统创建的 Skill（无 .skill-spec.yaml）在 content 维度不被惩罚。"""
        s = SkillScorer(mid_skill)
        s.score()
        assert s._content_spec_coverage() == 3

    def test_guided_skill_content_score(self, good_skill):
        """富模板创建的高质量 Skill 在 content 维度得高分。"""
        s = SkillScorer(good_skill)
        s.score()
        assert s.scores['content'] >= 14
