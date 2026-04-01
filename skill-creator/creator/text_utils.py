"""
文本分析工具

提供 n-gram 提取和 Jaccard 相似度计算，
供 scorer、prefill、create 等模块共用。
"""


def bigrams(text: str) -> set[str]:
    """提取文本的 2-gram 集合。"""
    t = text.strip()
    return {t[i:i+2] for i in range(len(t) - 1)} if len(t) >= 2 else set()


def bigram_jaccard(text_a: str, text_b: str) -> float:
    """计算两段文本的 2-gram Jaccard 相似度（intersection / union）。"""
    a, b = bigrams(text_a), bigrams(text_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def bigram_coverage(short_text: str, long_text: str) -> float:
    """计算 short_text 的 2-gram 在 long_text 中的覆盖率。

    适用于短描述 vs 长样例文本的相似度计算。
    返回 [0.0, 1.0]，表示短文本有多少比例的 bigram 出现在长文本中。
    """
    short_bg = bigrams(short_text)
    if not short_bg:
        return 0.0
    long_bg = bigrams(long_text)
    return len(short_bg & long_bg) / len(short_bg)
