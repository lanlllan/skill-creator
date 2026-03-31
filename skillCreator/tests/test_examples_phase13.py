"""
Phase 13 测试套件：参考实现库（Reference Library）

覆盖范围：
- 样例完整性验证（3 用例）
- 样例评分门禁（3 用例）
- 样例 validate + scan 回归门禁（6 用例）
- 样例复杂度层级断言（1 用例）
- list_examples 接口（4 用例）
- show_example 接口（3 用例）
- copy_example 接口（4 用例）
- get_example_keywords（2 用例）
- find_similar_example（4 用例）
- examples CLI 命令（5 用例）
- create --spec 联动推荐（2 用例）
- create --guided 提示（1 用例）

合计：38 用例
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from creator.examples import (
    EXAMPLES_DIR,
    list_examples,
    show_example,
    copy_example,
    get_example_keywords,
    find_similar_example,
)
from creator.scorer import SkillScorer


EXAMPLE_NAMES = ["simple-greeter", "file-analyzer", "api-health-checker"]

RUN_PY = str(Path(__file__).parent.parent / "run.py")


# ═══════════════════════════════════════════════════════════════════════
#  TestExampleIntegrity — 样例完整性
# ═══════════════════════════════════════════════════════════════════════

class TestExampleIntegrity:
    @pytest.mark.parametrize("name", EXAMPLE_NAMES)
    def test_required_files_exist(self, name):
        """每个样例必须包含 SKILL.md、run.py、USAGE.md、README.md、.skill-spec.yaml。"""
        d = EXAMPLES_DIR / name
        assert d.is_dir(), f"样例目录不存在：{d}"
        for f in ["SKILL.md", "run.py", "USAGE.md", "README.md", ".skill-spec.yaml"]:
            assert (d / f).exists(), f"{name} 缺少 {f}"


# ═══════════════════════════════════════════════════════════════════════
#  TestExampleScoring — 评分门禁（score >= 85）
# ═══════════════════════════════════════════════════════════════════════

class TestExampleScoring:
    @pytest.mark.parametrize("name", EXAMPLE_NAMES)
    def test_score_at_least_85(self, name):
        """每个样例评分必须 >= 85。"""
        s = SkillScorer(EXAMPLES_DIR / name)
        s.score()
        assert s.scores["total"] >= 85, f"{name} 评分 {s.scores['total']} < 85: {s.scores}"


# ═══════════════════════════════════════════════════════════════════════
#  TestExampleValidateScan — validate + scan 回归门禁
# ═══════════════════════════════════════════════════════════════════════

class TestExampleValidateScan:
    @pytest.mark.parametrize("name", EXAMPLE_NAMES)
    def test_validate_passes(self, name):
        """每个样例必须通过 validate 检查（退出码 0）。"""
        example_dir = str(EXAMPLES_DIR / name)
        result = subprocess.run(
            [sys.executable, RUN_PY, "validate", example_dir],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert result.returncode == 0, f"{name} validate 失败:\n{result.stdout}\n{result.stderr}"

    @pytest.mark.parametrize("name", EXAMPLE_NAMES)
    def test_scan_passes(self, name):
        """每个样例必须通过 scan 安全扫描（退出码 0）。"""
        example_dir = str(EXAMPLES_DIR / name)
        result = subprocess.run(
            [sys.executable, RUN_PY, "scan", example_dir],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert result.returncode == 0, f"{name} scan 失败:\n{result.stdout}\n{result.stderr}"


# ═══════════════════════════════════════════════════════════════════════
#  TestExampleComplexity — 复杂度层级断言
# ═══════════════════════════════════════════════════════════════════════

class TestExampleComplexity:
    def test_expected_complexity_levels(self):
        """样例列表至少覆盖 beginner / intermediate / advanced 三个预期层级。"""
        examples = list_examples()
        level_map = {ex["name"]: ex["complexity"] for ex in examples}
        assert level_map["simple-greeter"] == "beginner"
        assert level_map["file-analyzer"] == "intermediate"
        assert level_map["api-health-checker"] == "advanced"


# ═══════════════════════════════════════════════════════════════════════
#  TestListExamples
# ═══════════════════════════════════════════════════════════════════════

class TestListExamples:
    def test_returns_list(self):
        result = list_examples()
        assert isinstance(result, list)

    def test_contains_all_examples(self):
        result = list_examples()
        names = {ex["name"] for ex in result}
        for name in EXAMPLE_NAMES:
            assert name in names

    def test_each_has_required_keys(self):
        result = list_examples()
        for ex in result:
            assert "name" in ex
            assert "description" in ex
            assert "complexity" in ex

    def test_sorted_by_complexity(self):
        result = list_examples()
        order = {"beginner": 0, "intermediate": 1, "advanced": 2}
        levels = [order.get(ex["complexity"], 99) for ex in result]
        assert levels == sorted(levels)


# ═══════════════════════════════════════════════════════════════════════
#  TestShowExample
# ═══════════════════════════════════════════════════════════════════════

class TestShowExample:
    def test_existing_example(self):
        content = show_example("simple-greeter")
        assert "Simple Greeter" in content
        assert "---" in content

    def test_nonexistent_example(self):
        content = show_example("nonexistent-skill")
        assert content.startswith("错误")

    def test_shows_skill_md_content(self):
        content = show_example("file-analyzer")
        assert "File Analyzer" in content


# ═══════════════════════════════════════════════════════════════════════
#  TestCopyExample
# ═══════════════════════════════════════════════════════════════════════

class TestCopyExample:
    def test_copy_success(self, tmp_path):
        ok, msg = copy_example("simple-greeter", tmp_path)
        assert ok
        target = tmp_path / "simple-greeter"
        assert target.is_dir()
        assert (target / "SKILL.md").exists()
        assert (target / "run.py").exists()

    def test_copy_preserves_all_files(self, tmp_path):
        ok, _ = copy_example("file-analyzer", tmp_path)
        assert ok
        target = tmp_path / "file-analyzer"
        for f in ["SKILL.md", "run.py", "USAGE.md", "README.md", ".skill-spec.yaml"]:
            assert (target / f).exists()

    def test_copy_existing_dir_fails(self, tmp_path):
        (tmp_path / "simple-greeter").mkdir()
        ok, msg = copy_example("simple-greeter", tmp_path)
        assert not ok
        assert "已存在" in msg

    def test_copy_nonexistent_fails(self, tmp_path):
        ok, msg = copy_example("nonexistent", tmp_path)
        assert not ok
        assert "不存在" in msg


# ═══════════════════════════════════════════════════════════════════════
#  TestGetExampleKeywords
# ═══════════════════════════════════════════════════════════════════════

class TestGetExampleKeywords:
    def test_returns_set(self):
        kw = get_example_keywords("api-health-checker")
        assert isinstance(kw, set)
        assert len(kw) > 0

    def test_nonexistent_returns_empty(self):
        kw = get_example_keywords("nonexistent")
        assert kw == set()


# ═══════════════════════════════════════════════════════════════════════
#  TestFindSimilarExample
# ═══════════════════════════════════════════════════════════════════════

class TestFindSimilarExample:
    def test_matching_spec(self):
        """含健康检查相关关键词的规约应匹配 api-health-checker。"""
        spec = {
            "capabilities": [
                {"name": "端点健康检查", "description": "发送 HTTP 请求检查 API 端点的可用性"}
            ],
            "commands": [
                {"name": "check", "description": "检查指定端点的健康状态"},
                {"name": "batch", "description": "批量检查端点"},
            ]
        }
        result = find_similar_example(spec)
        assert result == "api-health-checker"

    def test_file_analysis_spec(self):
        """含文件分析相关关键词的规约应匹配 file-analyzer。"""
        spec = {
            "capabilities": [
                {"name": "行数统计", "description": "统计目录中所有文件的行数"}
            ],
            "commands": [
                {"name": "count", "description": "统计行数"},
                {"name": "types", "description": "文件类型分布"},
            ]
        }
        result = find_similar_example(spec)
        assert result == "file-analyzer"

    def test_no_match_returns_none(self):
        """完全不相关的规约不应匹配任何样例。"""
        spec = {
            "capabilities": [
                {"name": "量子加密", "description": "使用量子态进行密钥分发"}
            ],
            "commands": [
                {"name": "encrypt", "description": "加密数据流"},
            ]
        }
        result = find_similar_example(spec)
        assert result is None

    def test_empty_spec_returns_none(self):
        result = find_similar_example({})
        assert result is None


# ═══════════════════════════════════════════════════════════════════════
#  TestExamplesCLI — 命令行集成
# ═══════════════════════════════════════════════════════════════════════

class TestExamplesCLI:
    def test_list_command(self):
        result = subprocess.run(
            [sys.executable, RUN_PY, "examples"],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert result.returncode == 0
        assert "simple-greeter" in result.stdout

    def test_show_command(self):
        result = subprocess.run(
            [sys.executable, RUN_PY, "examples", "--show", "simple-greeter"],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert result.returncode == 0
        assert "Simple Greeter" in result.stdout

    def test_show_nonexistent(self):
        result = subprocess.run(
            [sys.executable, RUN_PY, "examples", "--show", "nonexistent"],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert result.returncode == 1

    def test_copy_command(self, tmp_path):
        result = subprocess.run(
            [sys.executable, RUN_PY, "examples", "--copy", "simple-greeter",
             "-o", str(tmp_path)],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert result.returncode == 0
        assert (tmp_path / "simple-greeter" / "SKILL.md").exists()

    def test_copy_existing_fails(self, tmp_path):
        (tmp_path / "simple-greeter").mkdir()
        result = subprocess.run(
            [sys.executable, RUN_PY, "examples", "--copy", "simple-greeter",
             "-o", str(tmp_path)],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert result.returncode == 1


# ═══════════════════════════════════════════════════════════════════════
#  TestSpecSimilarityIntegration — create --spec 联动
# ═══════════════════════════════════════════════════════════════════════

class TestSpecSimilarityIntegration:
    def test_similar_spec_shows_recommendation(self, tmp_path):
        """--spec 创建时，规约与样例相似应输出推荐提示。"""
        import yaml
        spec = {
            "meta": {"name": "my-checker", "description": "检查 API 端点的健康状态并生成 JSON 报告"},
            "purpose": {
                "problem": "微服务架构中需要批量检查端点的可用性和响应时间",
                "target_users": "运维工程师和SRE团队成员",
                "scenarios": ["运维工程师在每日巡检时批量检查微服务集群中各服务的健康状态"],
            },
            "capabilities": [
                {"name": "单端点检查", "description": "发送 HTTP GET 请求检查指定 URL 的可用性"},
                {"name": "批量探测", "description": "从配置文件读取端点列表 逐一检查并输出汇总报告"},
                {"name": "健康报告", "description": "以 JSON 格式输出所有端点的详细检查结果"},
            ],
            "commands": [
                {"name": "check", "description": "检查单个 API 端点的健康状态",
                 "args": [{"name": "--url", "type": "string", "required": True}]},
                {"name": "batch", "description": "从配置文件批量检查端点",
                 "args": [{"name": "--config", "type": "string", "required": True}]},
                {"name": "report", "description": "生成 JSON 格式的健康报告",
                 "args": [{"name": "--config", "type": "string", "required": True}]},
            ],
            "error_handling": [{"scenario": "网络不可达或DNS解析失败", "action": "标记端点为 unreachable"}],
            "dependencies": ["Python >= 3.9"],
        }
        spec_file = tmp_path / ".skill-spec.yaml"
        spec_file.write_text(yaml.dump(spec, allow_unicode=True), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, RUN_PY, "create", "--spec", str(spec_file),
             "-o", str(tmp_path)],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert "api-health-checker" in result.stdout

    def test_unrelated_spec_no_recommendation(self, tmp_path):
        """不相关的规约不应输出样例推荐。"""
        import yaml
        spec = {
            "meta": {"name": "quantum-tool", "description": "量子计算工具"},
            "purpose": {"problem": "量子态处理", "scenarios": ["量子纠缠"]},
            "capabilities": [
                {"name": "量子加密", "description": "使用量子态进行密钥分发"}
            ],
            "commands": [
                {"name": "encrypt", "description": "加密量子数据",
                 "args": [{"name": "--key", "type": "string", "required": True}]},
            ],
            "error_handling": [],
            "dependencies": [],
        }
        spec_file = tmp_path / ".skill-spec.yaml"
        spec_file.write_text(yaml.dump(spec, allow_unicode=True), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, RUN_PY, "create", "--spec", str(spec_file),
             "-o", str(tmp_path)],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert "建议：你的 Skill 设计与内置样例" not in result.stdout


# ═══════════════════════════════════════════════════════════════════════
#  TestGuidedHint — create --guided 提示
# ═══════════════════════════════════════════════════════════════════════

class TestGuidedHint:
    def test_guided_shows_examples_hint(self, tmp_path):
        """--guided 创建时应提示查看 examples。"""
        result = subprocess.run(
            [sys.executable, RUN_PY, "create", "--guided",
             "-n", "test-guided-hint", "-d", "测试引导提示",
             "-o", str(tmp_path)],
            capture_output=True, text=True, cwd=str(Path(RUN_PY).parent))
        assert result.returncode == 0
        assert "examples" in result.stdout
