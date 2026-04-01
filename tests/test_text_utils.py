"""Phase 15 测试：text_utils 公共工具"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skill-creator'))

from creator.text_utils import bigrams, bigram_jaccard, bigram_coverage


class TestBigrams:
    def test_normal_text(self):
        result = bigrams("hello")
        assert result == {"he", "el", "ll", "lo"}

    def test_short_text(self):
        assert bigrams("a") == set()
        assert bigrams("") == set()

    def test_chinese(self):
        result = bigrams("检查环境")
        assert "检查" in result
        assert "查环" in result
        assert "环境" in result


class TestBigramJaccard:
    def test_identical(self):
        assert bigram_jaccard("hello world", "hello world") == 1.0

    def test_completely_different(self):
        assert bigram_jaccard("abc", "xyz") == 0.0

    def test_partial_overlap(self):
        score = bigram_jaccard("hello", "help")
        assert 0.0 < score < 1.0

    def test_empty_input(self):
        assert bigram_jaccard("", "hello") == 0.0
        assert bigram_jaccard("hello", "") == 0.0
        assert bigram_jaccard("", "") == 0.0


class TestBigramCoverage:
    def test_short_fully_in_long(self):
        assert bigram_coverage("分析工具", "这是一个分析工具可以统计") == 1.0

    def test_short_partial_in_long(self):
        score = bigram_coverage("日志分析统计工具", "分析文件和目录的统计信息")
        assert 0.0 < score < 1.0

    def test_no_overlap(self):
        assert bigram_coverage("天气查询", "邮件发送") == 0.0

    def test_empty_short(self):
        assert bigram_coverage("", "some long text") == 0.0

    def test_empty_long(self):
        assert bigram_coverage("short", "") == 0.0

    def test_real_description_vs_example(self):
        score = bigram_coverage("开发环境依赖检查工具", "检查开发环境是否满足要求 逐项检测 必备命令行工具和环境变量是否满足要求")
        assert score >= 0.25
