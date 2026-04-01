"""参考实现库核心模块 — 内置样例的列出、查看和复制。"""

import shutil
from pathlib import Path

import yaml

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

COMPLEXITY_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}


def _load_example_meta(example_dir: Path) -> dict:
    """从样例的 .skill-spec.yaml 加载元信息。"""
    spec_file = example_dir / ".skill-spec.yaml"
    if not spec_file.exists():
        return {}
    data = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
    meta = data.get("meta", {})
    return meta


_COMPLEXITY_LEVELS = {"beginner", "intermediate", "advanced"}


def _infer_complexity(example_dir: Path, tags: list[str] | None = None) -> str:
    """根据显式元信息或样例内容推断复杂度级别。优先从 tags 识别显式标记，推断仅作兜底。"""
    if tags:
        for tag in tags:
            if tag in _COMPLEXITY_LEVELS:
                return tag
    run_py = example_dir / "run.py"
    if not run_py.exists():
        return "beginner"
    content = run_py.read_text(encoding="utf-8")
    subcommand_count = content.count("add_parser(")
    if subcommand_count >= 3:
        return "advanced"
    elif subcommand_count >= 2:
        return "intermediate"
    return "beginner"


def list_examples() -> list[dict]:
    """列出所有内置样例，返回 [{name, description, complexity}]。"""
    if not EXAMPLES_DIR.is_dir():
        return []
    results = []
    for d in sorted(EXAMPLES_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        meta = _load_example_meta(d)
        tags = meta.get("tags", [])
        results.append({
            "name": meta.get("name", d.name),
            "description": meta.get("description", ""),
            "complexity": _infer_complexity(d, tags),
            "tags": tags,
        })
    results.sort(key=lambda x: COMPLEXITY_ORDER.get(x["complexity"], 99))
    return results


def show_example(name: str) -> str:
    """返回样例的 SKILL.md 内容（快速预览）。不存在则返回错误信息。"""
    example_dir = EXAMPLES_DIR / name
    if not example_dir.is_dir():
        available = [d.name for d in EXAMPLES_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
        return f"错误：样例 '{name}' 不存在。可用样例：{', '.join(available)}"
    skill_md = example_dir / "SKILL.md"
    if not skill_md.exists():
        return f"错误：样例 '{name}' 缺少 SKILL.md"
    return skill_md.read_text(encoding="utf-8")


def copy_example(
    name: str,
    output_dir: Path,
    conflict: str = 'error',
) -> tuple[bool, str]:
    """将样例复制到指定目录。返回 (success, message)。

    Args:
        conflict: 冲突策略 — 'error'(默认), 'overwrite', 'rename'
    """
    example_dir = EXAMPLES_DIR / name
    if not example_dir.is_dir():
        available = [d.name for d in EXAMPLES_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
        return False, f"错误：样例 '{name}' 不存在。可用样例：{', '.join(available)}"

    target = output_dir / name
    if target.exists():
        if conflict == 'overwrite':
            shutil.rmtree(target)
        elif conflict == 'rename':
            suffix = 1
            while True:
                renamed = output_dir / f"{name}-{suffix}"
                if not renamed.exists():
                    target = renamed
                    break
                suffix += 1
        else:
            return False, (
                f"错误：目标目录已存在 — {target}\n"
                f"  可选操作：覆盖（overwrite）/ 重命名（rename）/ 取消（cancel）"
            )

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(example_dir, target)
    file_count = sum(1 for _ in target.rglob("*") if _.is_file())
    return True, f"✅ 样例 '{name}' 已复制到 {target}（{file_count} 个文件）"


def _extract_keywords_from_text(text: str) -> set[str]:
    """从文本提取关键词：bigrams（中文特征）+ split（英文单词）双模式。"""
    from creator.text_utils import bigrams
    kw = set()
    kw.update(bigrams(text))
    kw.update(w for w in text.replace("，", " ").replace("、", " ").split() if w)
    return kw


def get_example_keywords(name: str) -> set[str]:
    """提取样例的关键词（基于 capabilities 和 commands 字段），用于相似度匹配。"""
    example_dir = EXAMPLES_DIR / name
    spec_file = example_dir / ".skill-spec.yaml"
    if not spec_file.exists():
        return set()

    data = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
    keywords = set()

    for cap in data.get("capabilities", []):
        if isinstance(cap, dict):
            for key in ("name", "description"):
                val = cap.get(key, "")
                if val:
                    keywords.update(_extract_keywords_from_text(val))

    for cmd in data.get("commands", []):
        if isinstance(cmd, dict):
            name_val = cmd.get("name", "")
            desc_val = cmd.get("description", "")
            if name_val:
                keywords.add(name_val)
                keywords.update(_extract_keywords_from_text(name_val))
            if desc_val:
                keywords.update(_extract_keywords_from_text(desc_val))

    keywords.discard("")
    return keywords


def _get_field(obj, key, default=None):
    """兼容 dict 和 dataclass 的字段访问。"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _get_example_description_keywords(name: str) -> str:
    """提取样例的 description + capabilities 文本，用于 2-gram 匹配。"""
    example_dir = EXAMPLES_DIR / name
    spec_file = example_dir / ".skill-spec.yaml"
    if not spec_file.exists():
        return ""
    data = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
    parts = []
    meta = data.get("meta", {})
    if isinstance(meta, dict) and meta.get("description"):
        parts.append(str(meta["description"]))
    for cap in data.get("capabilities", []):
        if isinstance(cap, dict):
            for key in ("name", "description"):
                val = cap.get(key, "")
                if val:
                    parts.append(str(val))
    return " ".join(parts)


def find_similar_example(
    spec_data: 'dict | object | None' = None,
    description: str | None = None,
    threshold: float | None = None,
) -> tuple[str | None, float]:
    """查找最相似的内置样例。

    两种匹配模式：
    - spec_data 非空：从 capabilities/commands 提取关键词（Jaccard，默认阈值 0.15）
    - description 非空：2-gram 覆盖率与样例 description+capabilities 比较（默认阈值 0.25）
    - 均为空：返回 (None, 0.0)

    Returns:
        (matched_example_name, similarity_score) 或 (None, 0.0)
    """
    from creator.text_utils import bigram_coverage

    if description and not spec_data:
        default_threshold = threshold if threshold is not None else 0.25
        best_name = None
        best_score = 0.0
        examples = list_examples()
        for ex in examples:
            ex_text = _get_example_description_keywords(ex["name"])
            if not ex_text:
                continue
            score = bigram_coverage(description, ex_text)
            if score > best_score:
                best_score = score
                best_name = ex["name"]
        if best_score >= default_threshold:
            return best_name, best_score
        return None, 0.0

    if spec_data is None:
        return None, 0.0

    default_threshold = threshold if threshold is not None else 0.15
    user_keywords = set()
    for cap in _get_field(spec_data, "capabilities", []) or []:
        if isinstance(cap, dict):
            for key in ("name", "description"):
                val = cap.get(key, "")
                if val:
                    user_keywords.update(_extract_keywords_from_text(val))
    for cmd in _get_field(spec_data, "commands", []) or []:
        if isinstance(cmd, dict):
            for key in ("name", "description"):
                val = cmd.get(key, "")
                if val:
                    user_keywords.update(_extract_keywords_from_text(val))
    user_keywords.discard("")

    if not user_keywords:
        return None, 0.0

    best_name = None
    best_score = 0.0
    examples = list_examples()
    for ex in examples:
        ex_keywords = get_example_keywords(ex["name"])
        if not ex_keywords:
            continue
        intersection = user_keywords & ex_keywords
        union = user_keywords | ex_keywords
        jaccard = len(intersection) / len(union) if union else 0
        if jaccard > best_score:
            best_score = jaccard
            best_name = ex["name"]

    if best_score >= default_threshold:
        return best_name, best_score
    return None, 0.0
