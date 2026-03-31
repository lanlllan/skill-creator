"""
Skill 质量评分器

支持 python（run.py）和 shell（run.sh）两种入口类型。
6 维度评分：structure / functionality / quality / docs / standard / content。
"""
import os
import re
from pathlib import Path


PLACEHOLDER_PATTERNS: list[re.Pattern] = [
    re.compile(r'场景\d+'),
    re.compile(r'能力\d+'),
    re.compile(r'功能点\d+'),
    re.compile(r'错误\d+'),
    re.compile(r'原因\d+'),
    re.compile(r'方案\d+'),
    re.compile(r'option\d+:\s*value\d+'),
    re.compile(r'命令执行后会输出\.\.\.'),
    re.compile(r"Hello,\s*\{.*?or\s*'World'\}"),
    re.compile(r'需要自动化处理特定任务'),
    re.compile(r'在以下场景中'),
]

TARGET_SECTIONS = ['适用场景', '核心能力']

_TRIVIAL_PYTHON = [
    re.compile(r'^\s*pass\s*$'),
    re.compile(r'^\s*return\s+(None|0|1|True|False)\s*$'),
    re.compile(r'^\s*raise\s+NotImplementedError'),
    re.compile(r'^\s*\.\.\.\s*$'),
]

_TRIVIAL_SHELL = [
    re.compile(r'^\s*:\s*$'),
    re.compile(r'^\s*return\s+[01]\s*$'),
    re.compile(r'^\s*echo\s+"TODO'),
]

_SKIP_PY_FUNCS = {'main', '__init__', '__bool__', '__repr__', '__str__'}


_BASELINE_DIR = Path(__file__).resolve().parent.parent / 'templates'


class SkillScorer:
    """Skill 质量评分器（满分 100 分）。

    维度权重（Phase 12）:
      structure 15 / functionality 25 / quality 20 / docs 10 / standard 10 / content 20
    """

    def __init__(self, skill_dir: Path):
        self.skill_dir = Path(skill_dir).resolve()
        self.scores = {
            'structure': 0,
            'functionality': 0,
            'quality': 0,
            'docs': 0,
            'standard': 0,
            'content': 0,
            'total': 0,
        }
        self.remarks = []
        self._entry_script, self._entry_type = self._detect_entry_script()
        self._template_retention: float = 0.0
        self._example_only: bool = False
        self._relevance_penalty: int = 0

    def _detect_entry_script(self) -> tuple[Path | None, str]:
        """检测入口脚本及其类型。"""
        run_py = self.skill_dir / "run.py"
        run_sh = self.skill_dir / "run.sh"
        if run_py.exists():
            return run_py, 'python'
        if run_sh.exists():
            return run_sh, 'shell'
        return None, 'unknown'

    def score(self):
        """执行全部分项评分，返回 scores 字典。"""
        self._score_structure()
        self._score_functionality()
        self._score_quality()
        self._score_docs()
        self._score_standard()
        self._score_content()
        self.scores['total'] = (
            self.scores['structure'] +
            self.scores['functionality'] +
            self.scores['quality'] +
            self.scores['docs'] +
            self.scores['standard'] +
            self.scores['content']
        )
        return self.scores

    # ------------------------------------------------------------------ #
    #  structure (15)
    # ------------------------------------------------------------------ #

    def _score_structure(self):
        """文件结构 (15 分)"""
        score = 0
        base = self.skill_dir

        skill_md = base / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            if content.startswith('---') and 'name:' in content and 'description:' in content:
                score += 4

        if self._entry_script and os.access(self._entry_script, os.X_OK):
            score += 4

        if (base / "USAGE.md").exists():
            score += 2
        if (base / "README.md").exists():
            score += 2
        if (base / "templates").is_dir():
            score += 2
        if (base / "config").is_dir() or any(base.glob("*.yaml")) or any(base.glob("config.*")):
            score += 1

        self.scores['structure'] = score
        self.remarks.append(f"文件结构: {score}/15")

    # ------------------------------------------------------------------ #
    #  functionality (25)
    # ------------------------------------------------------------------ #

    def _score_functionality(self):
        """功能实现 (25 分)"""
        if not self._entry_script:
            self.scores['functionality'] = 0
            self.remarks.append("功能实现: 0/25 (入口脚本缺失，需要 run.py 或 run.sh)")
            return

        content = self._entry_script.read_text(encoding='utf-8')
        if self._entry_type == 'python':
            score = self._score_functionality_python(content)
        else:
            score = self._score_functionality_shell(content)

        self.scores['functionality'] = score
        self.remarks.append(f"功能实现: {score}/25")

    def _has_only_example_command(self, content: str) -> bool:
        """检测入口脚本是否仅有 example 命令。"""
        if self._entry_type == 'python':
            if 'add_subparsers' not in content:
                return False
            parsers = re.findall(r"add_parser\(['\"]([a-z][a-z0-9-]*)['\"]", content)
            return set(parsers) == {'example'}
        else:
            commands = re.findall(r'^\s*(\w[\w-]*)\)', content, re.MULTILINE)
            real = [c for c in commands if c not in ('help', 'version', '*')]
            return set(real) == {'example'}

    def _score_functionality_python(self, content: str) -> int:
        score = 0
        has_subparsers = 'add_subparsers' in content
        if has_subparsers:
            score += 5
            subcommands = ['check', 'fix', 'docgen', 'newmodule', 'create',
                           'validate', 'archive', 'clean']
            found = sum(1 for cmd in subcommands
                        if f"'{cmd}'" in content or f'"{cmd}"' in content)
            if found >= 2:
                score += 2

        if 'required=True' in content or '--' in content:
            score += 2
        if 'choices=' in content:
            score += 2
        if 'try:' in content or 'except' in content or 'if rc' in content:
            score += 2
        if 'print(f"❌' in content or 'print("❌' in content:
            score += 2
        if 'sys.exit(' in content and 'return 0' in content:
            score += 2
        if '--dry-run' in content:
            score += 4
        if '--verbose' in content or '-v' in content:
            score += 4

        self._example_only = self._has_only_example_command(content)
        if self._example_only:
            score -= 5

        return max(0, score)

    def _score_functionality_shell(self, content: str) -> int:
        score = 0
        if 'case' in content and 'esac' in content:
            score += 5
            commands = re.findall(r'^\s*(\w[\w-]*)\)', content, re.MULTILINE)
            if len(commands) >= 2:
                score += 2
        if 'getopts' in content or '--' in content or 'shift' in content:
            score += 2
        if 'set -e' in content or 'set -euo' in content or 'trap ' in content:
            score += 2
        if 'log_error' in content or 'echo "❌' in content or '>&2' in content:
            score += 2
        if 'exit 0' in content or 'exit 1' in content:
            score += 2
        if '--dry-run' in content or 'DRY_RUN' in content:
            score += 4
        if re.search(r'--verbose[)|]', content) or 'VERBOSE=' in content:
            score += 4
        if 'usage()' in content or 'help' in content:
            score += 2

        self._example_only = self._has_only_example_command(content)
        if self._example_only:
            score -= 5

        return max(0, score)

    # ------------------------------------------------------------------ #
    #  quality (20)
    # ------------------------------------------------------------------ #

    def _score_quality(self):
        """代码质量 (20 分)"""
        if not self._entry_script:
            self.scores['quality'] = 0
            return

        content = self._entry_script.read_text(encoding='utf-8')
        if self._entry_type == 'python':
            score = self._score_quality_python(content)
        else:
            score = self._score_quality_shell(content)

        self.scores['quality'] = min(score, 20)
        self.remarks.append(f"代码质量: {self.scores['quality']}/20")

    def _score_quality_python(self, content: str) -> int:
        score = 0
        func_count = content.count('def ')
        if func_count >= 5:
            score += 4
        elif func_count >= 3:
            score += 2
        else:
            score += 1

        if 'except Exception' in content or 'except OSError' in content:
            score += 4
        elif 'except' in content:
            score += 2

        if 'shutil.which(' in content or 'which ' in content or 'command -v' in content:
            score += 4
        elif 'FileNotFoundError' in content:
            score += 2

        if 'print(' in content and ('✅' in content or '❌' in content or '⚠️' in content):
            score += 2
        if 'os.remove(' in content or 'unlink(' in content or 'shutil.rmtree(' in content:
            score += 2
        if '"""' in content and content.count('"""') >= 4:
            score += 4
        return score

    def _score_quality_shell(self, content: str) -> int:
        score = 0
        func_count = len(re.findall(r'^\w[\w_]*\s*\(\)', content, re.MULTILINE))
        if func_count >= 5:
            score += 4
        elif func_count >= 3:
            score += 2
        else:
            score += 1

        if 'set -euo pipefail' in content:
            score += 4
        elif 'set -e' in content:
            score += 2

        if 'command -v' in content or 'which ' in content or 'type ' in content:
            score += 4
        elif 'test -f' in content or '[ -f' in content:
            score += 2

        if '✅' in content or '❌' in content or '⚠️' in content:
            score += 2
        if 'rm -' in content or 'trap ' in content:
            score += 2
        if content.count('#') >= 5:
            score += 4
        return score

    # ------------------------------------------------------------------ #
    #  docs (10)
    # ------------------------------------------------------------------ #

    def _score_docs(self):
        """文档完备性 (10 分)"""
        score = 0
        base = self.skill_dir

        skill_md = base / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            sections = ['概述', '核心能力', '使用方式', '示例', '故障排除']
            hits = sum(1 for s in sections if s in content)
            score += min(hits, 3)
            if '故障排除' in content and ('|' in content or '问题' in content):
                score += 1

        usage = base / "USAGE.md"
        if usage.exists():
            content = usage.read_text(encoding='utf-8')
            if '命令参考' in content or '子命令' in content:
                score += 1
            if any(x in content for x in ['示例', 'example', 'Example']):
                score += 1

        readme = base / "README.md"
        if readme.exists():
            content = readme.read_text(encoding='utf-8')
            if '快速' in content or '安装' in content or '使用' in content:
                score += 2
            if 'USAGE.md' in content or 'SKILL.md' in content:
                score += 1

        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        broken_links = 0
        for md_file in base.rglob('*.md'):
            try:
                md_content = md_file.read_text(encoding='utf-8')
            except Exception:
                continue
            for _, href in link_pattern.findall(md_content):
                if href.startswith(('http://', 'https://', '#', 'mailto:')):
                    continue
                if not (md_file.parent / href).resolve().exists():
                    broken_links += 1
        if broken_links == 0:
            score += 1

        self._relevance_penalty = self._docs_content_relevance()
        score += self._relevance_penalty

        self.scores['docs'] = max(0, score)
        if self._relevance_penalty < 0:
            self.remarks.append(
                f"文档完备性: {self.scores['docs']}/10 "
                f"(内容与 description 相关性不足，扣 {abs(self._relevance_penalty)} 分)")
        elif broken_links > 0:
            self.remarks.append(f"文档完备性: {self.scores['docs']}/10 (失效链接 {broken_links} 处)")
        else:
            self.remarks.append(f"文档完备性: {score}/10")

    def _docs_content_relevance(self) -> int:
        """检测 SKILL.md 核心章节内容与 description 的 2-gram 覆盖率。

        覆盖率 < 20% 时返回 -5，否则返回 0。
        """
        skill_md = self.skill_dir / 'SKILL.md'
        if not skill_md.exists():
            return 0
        content = skill_md.read_text(encoding='utf-8')

        m = re.search(r'description:\s*(.+)', content)
        if not m:
            return 0
        description = m.group(1).strip()
        if len(description) < 4:
            return 0

        items = self._extract_section_list_items(content)
        if not items:
            return 0

        desc_bigrams = {description[i:i+2] for i in range(len(description) - 1)}
        if not desc_bigrams:
            return 0

        section_text = ' '.join(items)
        covered = sum(1 for bg in desc_bigrams if bg in section_text)
        coverage = covered / len(desc_bigrams)

        if coverage < 0.2:
            return -5
        return 0

    # ------------------------------------------------------------------ #
    #  standard (10)
    # ------------------------------------------------------------------ #

    def _score_standard(self):
        """规范性 (10 分)"""
        score = 0
        base = self.skill_dir

        skill_md = base / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            m = re.search(r'name:\s*([^\s]+)', content)
            if m:
                name = m.group(1)
                if re.fullmatch(r'[a-z][a-z0-9-]*', name):
                    score += 2

        required_entry = ['SKILL.md']
        existing = [f.name for f in base.iterdir() if not f.name.startswith('.')]
        has_entry_script = 'run.py' in existing or 'run.sh' in existing
        if all(r in existing for r in required_entry) and has_entry_script:
            score += 3

        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            if content.startswith('---') and content.count('---') >= 2:
                score += 2

        if self._entry_script:
            content = self._entry_script.read_text(encoding='utf-8')
            if self._entry_type == 'python':
                if '\n\n' in content:
                    score += 1
                lines = content.splitlines()
                if any(line.startswith('    ') for line in lines if line.strip()):
                    score += 1
                if 'def ' in content and '\n\n' in content:
                    score += 1
            else:
                if '#!/' in content:
                    score += 1
                if 'set -' in content:
                    score += 1
                func_count = len(re.findall(r'^\w[\w_]*\s*\(\)', content, re.MULTILINE))
                if func_count >= 2:
                    score += 1

        placeholder_pattern = re.compile(r'\{\{[^}]+\}\}')
        has_placeholder = False
        check_suffixes = {'.md', '.py', '.sh', '.yaml', '.yml', '.txt'}
        for f in base.rglob('*'):
            if f.is_file() and f.suffix in check_suffixes and not f.name.endswith('.j2'):
                try:
                    fc = f.read_text(encoding='utf-8')
                except Exception:
                    continue
                if placeholder_pattern.search(fc):
                    has_placeholder = True
                    break
        if has_placeholder:
            score = max(0, score - 3)

        self.scores['standard'] = score
        if has_placeholder:
            self.remarks.append(f"规范性: {score}/10 (占位符残留扣分)")
        else:
            self.remarks.append(f"规范性: {score}/10")

    # ------------------------------------------------------------------ #
    #  content (20) — Phase 12 新增
    # ------------------------------------------------------------------ #

    def _load_baseline_lines(self, file_key: str) -> set[str]:
        """加载基线文件的非空行集合（file_key: 'SKILL' 或 'run'）。"""
        if self._entry_type not in ('python', 'shell'):
            return set()
        path = _BASELINE_DIR / self._entry_type / f'_baseline_{file_key}.txt'
        if not path.exists():
            return set()
        text = path.read_text(encoding='utf-8')
        return {l.strip() for l in text.splitlines() if l.strip()}

    def _content_template_retention(self) -> float:
        """计算 SKILL.md + 入口脚本的模板原文保留率。"""
        total_actual = 0
        total_matching = 0

        skill_md = self.skill_dir / 'SKILL.md'
        if skill_md.exists():
            baseline = self._load_baseline_lines('SKILL')
            if baseline:
                actual = [l.strip() for l in
                          skill_md.read_text(encoding='utf-8').splitlines()
                          if l.strip()]
                total_actual += len(actual)
                total_matching += sum(1 for l in actual if l in baseline)

        if self._entry_script and self._entry_script.exists():
            baseline = self._load_baseline_lines('run')
            if baseline:
                actual = [l.strip() for l in
                          self._entry_script.read_text(encoding='utf-8').splitlines()
                          if l.strip()]
                total_actual += len(actual)
                total_matching += sum(1 for l in actual if l in baseline)

        if total_actual == 0:
            return 0.0
        return total_matching / total_actual

    def _score_content(self):
        """内容密度 (20 分)"""
        score = 0
        score += self._content_placeholder_residue()
        score += self._content_diversity()
        score += self._content_function_substance()
        score += self._content_usage_completeness()
        score += self._content_spec_coverage()

        self._template_retention = self._content_template_retention()
        if self._template_retention > 0.7:
            score = min(score, 5)
            self.remarks.append(
                f'内容密度: {score}/20 '
                f'(模板原文保留率 {self._template_retention:.0%}，已封顶)')
        else:
            self.remarks.append(f"内容密度: {score}/20")

        self.scores['content'] = score

    def _content_placeholder_residue(self) -> int:
        """SKILL.md 占位符残留率 (0-6 分)"""
        skill_md = self.skill_dir / "SKILL.md"
        if not skill_md.exists():
            return 0
        content = skill_md.read_text(encoding='utf-8')
        lines = [l for l in content.splitlines()
                 if l.strip() and not l.startswith('---')]
        if not lines:
            return 0
        hit_lines = sum(1 for line in lines
                        if any(p.search(line) for p in PLACEHOLDER_PATTERNS))
        rate = hit_lines / len(lines)
        if rate == 0:
            return 6
        elif rate < 0.2:
            return 4
        elif rate < 0.5:
            return 2
        else:
            return 0

    def _content_diversity(self) -> int:
        """SKILL.md 内容多样性 (0-4 分)，仅检测"适用场景"和"核心能力"章节。"""
        skill_md = self.skill_dir / "SKILL.md"
        if not skill_md.exists():
            return 0
        content = skill_md.read_text(encoding='utf-8')
        items = self._extract_section_list_items(content)
        if len(items) < 2:
            return 0
        similar_pairs = 0
        total_pairs = 0
        for i in range(len(items) - 1):
            total_pairs += 1
            if self._text_similarity(items[i], items[i + 1]) > 0.8:
                similar_pairs += 1
        if total_pairs == 0:
            return 0
        diversity_rate = 1 - (similar_pairs / total_pairs)
        if diversity_rate >= 0.9:
            return 4
        elif diversity_rate >= 0.7:
            return 3
        elif diversity_rate >= 0.5:
            return 2
        else:
            return 0

    def _content_function_substance(self) -> int:
        """run.py/run.sh 函数实质性 (0-4 分)"""
        if not self._entry_script:
            return 0
        content = self._entry_script.read_text(encoding='utf-8')
        if self._entry_type == 'python':
            return self._function_substance_python(content)
        else:
            return self._function_substance_shell(content)

    def _function_substance_python(self, content: str) -> int:
        func_pattern = re.compile(r'^def\s+(\w+)\s*\(', re.MULTILINE)
        functions = list(func_pattern.finditer(content))
        substantial = 0
        for i, match in enumerate(functions):
            name = match.group(1)
            if name in _SKIP_PY_FUNCS:
                continue
            start = match.end()
            end = functions[i + 1].start() if i + 1 < len(functions) else len(content)
            body = content[start:end]
            body_lines = [l for l in body.splitlines()
                          if l.strip()
                          and not l.strip().startswith('#')
                          and not l.strip().startswith('"""')
                          and not l.strip().startswith("'''")]
            effective = [l for l in body_lines
                         if not any(p.match(l) for p in _TRIVIAL_PYTHON)]
            if len(effective) >= 3:
                substantial += 1
        if substantial >= 3:
            return 4
        elif substantial >= 2:
            return 3
        elif substantial >= 1:
            return 2
        else:
            return 0

    def _function_substance_shell(self, content: str) -> int:
        func_pattern = re.compile(r'^(\w[\w_]*)\s*\(\)\s*\{', re.MULTILINE)
        functions = list(func_pattern.finditer(content))
        substantial = 0
        for match in functions:
            name = match.group(1)
            if name in ('main', 'usage', 'help'):
                continue
            start = match.end()
            end_brace = content.find('\n}', start)
            if end_brace == -1:
                end_brace = len(content)
            body = content[start:end_brace]
            body_lines = [l for l in body.splitlines()
                          if l.strip() and not l.strip().startswith('#')]
            effective = [l for l in body_lines
                         if not any(p.match(l) for p in _TRIVIAL_SHELL)]
            if len(effective) >= 3:
                substantial += 1
        if substantial >= 3:
            return 4
        elif substantial >= 2:
            return 3
        elif substantial >= 1:
            return 2
        else:
            return 0

    def _content_usage_completeness(self) -> int:
        """USAGE.md 示例完整性 (0-3 分)"""
        usage = self.skill_dir / "USAGE.md"
        if not usage.exists():
            return 0
        content = usage.read_text(encoding='utf-8')
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        non_placeholder_blocks = 0
        for block in code_blocks:
            inner = block.strip('`').strip()
            if inner and not any(p.search(inner) for p in PLACEHOLDER_PATTERNS):
                non_placeholder_blocks += 1
        if non_placeholder_blocks >= 3:
            return 3
        elif non_placeholder_blocks >= 2:
            return 2
        elif non_placeholder_blocks >= 1:
            return 1
        else:
            return 0

    def _content_spec_coverage(self) -> int:
        """规约覆盖率 (0-3 分)，无规约文件时自动满分。"""
        spec_file = self.skill_dir / ".skill-spec.yaml"
        if not spec_file.exists():
            return 3
        try:
            import yaml
            spec_data = yaml.safe_load(spec_file.read_text(encoding='utf-8'))
        except Exception:
            return 0
        if not isinstance(spec_data, dict):
            return 0
        values = self._collect_spec_fields(spec_data)
        total_fields = len(values)
        if total_fields == 0:
            return 0
        filled_fields = sum(1 for v in values if self._is_field_filled(v))
        rate = filled_fields / total_fields
        if rate >= 0.8:
            return 3
        elif rate >= 0.6:
            return 2
        elif rate >= 0.4:
            return 1
        else:
            return 0

    # ------------------------------------------------------------------ #
    #  static utilities
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_section_list_items(content: str) -> list[str]:
        """从 SKILL.md 的"适用场景"和"核心能力"章节中提取列表项。
        章节边界仅以二级标题（``## ``）切换，``###`` 子标题不触发切换，
        确保"核心能力"下含子标题结构的列表项可被正确提取（架构 12.3）。
        """
        items = []
        lines = content.splitlines()
        in_target_section = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('## ') and not stripped.startswith('### '):
                heading_text = stripped.lstrip('#').strip()
                in_target_section = any(t in heading_text for t in TARGET_SECTIONS)
                continue
            if in_target_section and stripped.startswith('- ') and len(stripped) > 4:
                items.append(stripped[2:])
        return items

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        """基于字符 bigram 的 Jaccard 相似度，范围 [0, 1]。"""
        if not a or not b:
            return 0.0
        def bigrams(s):
            s = s.strip()
            return set(s[i:i+2] for i in range(len(s) - 1)) if len(s) >= 2 else {s}
        bg_a, bg_b = bigrams(a), bigrams(b)
        if not bg_a or not bg_b:
            return 0.0
        intersection = bg_a & bg_b
        union = bg_a | bg_b
        return len(intersection) / len(union) if union else 0.0

    @staticmethod
    def _collect_spec_fields(spec_data: dict) -> list:
        """递归收集规约中 purpose/capabilities/commands/error_handling 的叶节点值。"""
        values: list = []
        def _walk(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    _walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    _walk(item)
            else:
                values.append(obj)
        for key in ('purpose', 'capabilities', 'commands', 'error_handling'):
            if key in spec_data:
                _walk(spec_data[key])
        return values

    @staticmethod
    def _is_field_filled(value) -> bool:
        """判断字段值是否已填充（非空、非占位符）。"""
        if value is None:
            return False
        if isinstance(value, str):
            stripped = value.strip()
            return bool(stripped) and stripped not in ('""', "''")
        return isinstance(value, (bool, int, float))

    # ------------------------------------------------------------------ #
    #  report
    # ------------------------------------------------------------------ #

    def get_grade(self):
        total = self.scores['total']
        if total >= 90:
            return '⭐⭐⭐⭐⭐', '优秀'
        elif total >= 80:
            return '⭐⭐⭐⭐', '良好'
        elif total >= 70:
            return '⭐⭐⭐', '可用'
        elif total >= 60:
            return '⭐⭐', '待改进'
        else:
            return '⭐', '不可用'

    def _generate_improvement_suggestions(self) -> list[dict]:
        """生成可操作的改进建议，每项包含 delta（预估提升分值）和 action。"""
        suggestions = []
        skill_name = self.skill_dir.name
        entry_name = self._entry_script.name if self._entry_script else 'run.py'

        if self._template_retention > 0.7:
            suggestions.append({
                'delta': 20,
                'action': f'使用交互式创建重新生成：python run.py create --interactive -n {skill_name}',
                'reason': '交互式创建将引导逐步细化需求，生成包含 TODO 注释的业务骨架',
            })

        if self._example_only:
            suggestions.append({
                'delta': 5,
                'action': f'在 {entry_name} 中将 cmd_example 替换为实际业务命令',
                'reason': '当前仅有示例命令，评分器检测到无实际子命令',
            })

        if self._relevance_penalty < 0:
            suggestions.append({
                'delta': 5,
                'action': '在 SKILL.md 中用具体场景替换占位文本',
                'reason': '当前章节内容与 description 缺乏语义关联',
            })

        if self._entry_script:
            content = self._entry_script.read_text(encoding='utf-8')
            if '--dry-run' not in content and 'DRY_RUN' not in content:
                suggestions.append({
                    'delta': 3,
                    'action': f'在 {entry_name} 中添加 --dry-run 选项',
                    'reason': '支持预览模式提升功能完备性',
                })
            has_dep_check = any(kw in content for kw in
                               ('shutil.which(', 'command -v', 'which '))
            if not has_dep_check and 'FileNotFoundError' not in content:
                suggestions.append({
                    'delta': 2,
                    'action': '添加命令可用性检查（shutil.which / command -v）',
                    'reason': '确保外部依赖缺失时给出明确错误提示',
                })

        if self.scores['structure'] < 13:
            missing = []
            base = self.skill_dir
            if not (base / 'USAGE.md').exists():
                missing.append('USAGE.md')
            if not (base / 'README.md').exists():
                missing.append('README.md')
            if not (base / 'templates').is_dir():
                missing.append('templates/')
            if missing:
                suggestions.append({
                    'delta': 2,
                    'action': f'补充 {", ".join(missing)}',
                    'reason': '完善文件结构',
                })

        return sorted(suggestions, key=lambda s: s['delta'], reverse=True)

    def generate_report(self) -> str:
        """生成文本评分报告。"""
        grade_icons, grade_text = self.get_grade()
        entry_label = self._entry_script.name if self._entry_script else '(无)'
        report = (
            f"\n📊 Skill 质量评分报告\n{'='*40}\n"
            f"Skill: {self.skill_dir.name}\n"
            f"入口脚本: {entry_label}\n"
            f"总评分: {self.scores['total']}/100 {grade_icons} ({grade_text})\n\n"
            "分项:\n"
        )
        report += '\n'.join(self.remarks)
        report += "\n\n🏁 改进路径（按效果排序）：\n"

        suggestions = self._generate_improvement_suggestions()
        if not suggestions:
            report += '  质量优秀，建议归档到主技能目录\n'
        else:
            for i, s in enumerate(suggestions, 1):
                report += f'  {i}. [+{s["delta"]}分] {s["action"]}\n'
                report += f'     → {s["reason"]}\n'

        report += "\n"
        return report
