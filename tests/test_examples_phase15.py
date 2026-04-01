"""Phase 15 测试：新增样例验证 + find_similar_example description 分支"""
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skill-creator'))

import pytest
from helpers import SKILL_ROOT, RUN_PY
from creator.examples import find_similar_example, list_examples, EXAMPLES_DIR
from creator.scorer import SkillScorer


NEW_EXAMPLES = ['data-formatter', 'env-checker']


class TestNewExamples:
    @pytest.mark.parametrize("example_name", NEW_EXAMPLES)
    def test_example_structure_complete(self, example_name):
        """新样例应包含完整的文件结构"""
        example_dir = EXAMPLES_DIR / example_name
        assert example_dir.exists(), f"样例目录不存在: {example_dir}"
        for f in ['SKILL.md', 'run.py', 'README.md', 'USAGE.md', '.skill-spec.yaml']:
            assert (example_dir / f).exists(), f"{example_name} 缺少 {f}"

    @pytest.mark.parametrize("example_name", NEW_EXAMPLES)
    def test_example_listed(self, example_name):
        """新样例应出现在 list_examples 中"""
        examples = list_examples()
        names = [e['name'] for e in examples]
        assert example_name in names

    @pytest.mark.parametrize("example_name", NEW_EXAMPLES)
    def test_example_score(self, example_name):
        """新样例评分应 >= 85，content >= 15, functionality >= 20"""
        example_dir = EXAMPLES_DIR / example_name
        scorer = SkillScorer(example_dir)
        scores = scorer.score()
        assert scores['total'] >= 85, f"{example_name} 总分 {scores['total']} < 85"
        assert scores['content'] >= 15, f"{example_name} content {scores['content']} < 15"
        assert scores['functionality'] >= 20, f"{example_name} functionality {scores['functionality']} < 20"

    @pytest.mark.parametrize("example_name", NEW_EXAMPLES)
    def test_example_has_subcommands(self, example_name):
        """新样例应有 >= 2 个子命令"""
        example_dir = EXAMPLES_DIR / example_name
        run_py = example_dir / 'run.py'
        content = run_py.read_text(encoding='utf-8')
        subcommand_count = content.count("add_parser(")
        assert subcommand_count >= 2, f"{example_name} 子命令数 {subcommand_count} < 2"


class TestFindSimilarByDesc:
    def test_description_matches_data_formatter(self):
        """数据格式转换相关描述应匹配 data-formatter"""
        name, score = find_similar_example(
            description="在 JSON、CSV、YAML 格式之间转换数据，并验证文件结构合法性")
        assert name == 'data-formatter'
        assert score > 0.2

    def test_description_matches_env_checker(self):
        """环境检查相关描述应匹配 env-checker"""
        name, score = find_similar_example(
            description="检查开发环境的依赖配置，验证 Python 版本、必备工具和环境变量是否就绪")
        assert name == 'env-checker'
        assert score > 0.2

    def test_description_no_match(self):
        """完全不相关的描述不应匹配"""
        name, score = find_similar_example(
            description="量子纠缠态模拟与贝尔不等式验证",
            threshold=0.3)
        assert score < 0.3
