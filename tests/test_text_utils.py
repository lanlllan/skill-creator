"""Phase 15 测试：text_utils 公共工具"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skill-creator'))

from creator.text_utils import bigrams, bigram_jaccard


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
