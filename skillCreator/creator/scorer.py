"""
Skill 质量评分器

支持 python（run.py）和 shell（run.sh）两种入口类型。
"""
import os
import re
from pathlib import Path


class SkillScorer:
    """Skill 质量评分器（满分 100 分）。"""

    def __init__(self, skill_dir: Path):
        self.skill_dir = Path(skill_dir).resolve()
        self.scores = {
            'structure': 0,
            'functionality': 0,
            'quality': 0,
            'docs': 0,
            'standard': 0,
            'total': 0,
        }
        self.remarks = []
        self._entry_script, self._entry_type = self._detect_entry_script()

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
        self.scores['total'] = (
            self.scores['structure'] +
            self.scores['functionality'] +
            self.scores['quality'] +
            self.scores['docs'] +
            self.scores['standard']
        )
        return self.scores

    def _score_structure(self):
        """文件结构 (20 分)"""
        score = 0
        base = self.skill_dir

        skill_md = base / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            if content.startswith('---') and 'name:' in content and 'description:' in content:
                score += 5

        if self._entry_script and os.access(self._entry_script, os.X_OK):
            score += 5

        if (base / "USAGE.md").exists():
            score += 3
        if (base / "README.md").exists():
            score += 3
        if (base / "templates").is_dir():
            score += 2
        if (base / "config").is_dir() or any(base.glob("*.yaml")) or any(base.glob("config.*")):
            score += 2

        self.scores['structure'] = score
        self.remarks.append(f"文件结构: {score}/20")

    def _score_functionality(self):
        """功能实现 (30 分)"""
        if not self._entry_script:
            self.scores['functionality'] = 0
            self.remarks.append("功能实现: 0/30 (入口脚本缺失，需要 run.py 或 run.sh)")
            return

        content = self._entry_script.read_text(encoding='utf-8')
        if self._entry_type == 'python':
            score = self._score_functionality_python(content)
        else:
            score = self._score_functionality_shell(content)

        self.scores['functionality'] = score
        self.remarks.append(f"功能实现: {score}/30")

    def _score_functionality_python(self, content: str) -> int:
        score = 0
        has_subparsers = 'add_subparsers' in content
        if has_subparsers:
            score += 6
            subcommands = ['check', 'fix', 'docgen', 'newmodule', 'create',
                           'validate', 'archive', 'clean']
            found = sum(1 for cmd in subcommands
                        if f"'{cmd}'" in content or f'"{cmd}"' in content)
            if found >= 2:
                score += 2

        if 'required=True' in content or '--' in content:
            score += 3
        if 'choices=' in content:
            score += 2
        if 'try:' in content or 'except' in content or 'if rc' in content:
            score += 3
        if 'print(f"❌' in content or 'print("❌' in content:
            score += 2
        if 'sys.exit(' in content and 'return 0' in content:
            score += 3
        if '--dry-run' in content:
            score += 4
        if '--verbose' in content or '-v' in content:
            score += 5
        return score

    def _score_functionality_shell(self, content: str) -> int:
        score = 0
        if 'case' in content and 'esac' in content:
            score += 6
            commands = re.findall(r'^\s*(\w[\w-]*)\)', content, re.MULTILINE)
            if len(commands) >= 2:
                score += 2
        if 'getopts' in content or '--' in content or 'shift' in content:
            score += 3
        if 'set -e' in content or 'set -euo' in content or 'trap ' in content:
            score += 3
        if 'log_error' in content or 'echo "❌' in content or '>&2' in content:
            score += 2
        if 'exit 0' in content or 'exit 1' in content:
            score += 3
        if '--dry-run' in content or 'DRY_RUN' in content:
            score += 4
        if '--verbose' in content or 'VERBOSE' in content:
            score += 5
        if 'usage()' in content or 'help' in content:
            score += 2
        return score

    def _score_quality(self):
        """代码质量 (25 分)"""
        if not self._entry_script:
            self.scores['quality'] = 0
            return

        content = self._entry_script.read_text(encoding='utf-8')
        if self._entry_type == 'python':
            score = self._score_quality_python(content)
        else:
            score = self._score_quality_shell(content)

        self.scores['quality'] = score
        self.remarks.append(f"代码质量: {score}/25")

    def _score_quality_python(self, content: str) -> int:
        score = 0
        func_count = content.count('def ')
        if func_count >= 5:
            score += 5
        elif func_count >= 3:
            score += 3
        else:
            score += 1

        if 'except Exception' in content or 'except OSError' in content:
            score += 5
        elif 'except' in content:
            score += 3

        if 'shutil.which(' in content or 'which ' in content or 'command -v' in content:
            score += 5
        elif 'FileNotFoundError' in content:
            score += 3

        if 'print(' in content and ('✅' in content or '❌' in content or '⚠️' in content):
            score += 3
        if 'os.remove(' in content or 'unlink(' in content or 'shutil.rmtree(' in content:
            score += 3
        if '"""' in content and content.count('"""') >= 4:
            score += 4
        return score

    def _score_quality_shell(self, content: str) -> int:
        score = 0
        func_count = len(re.findall(r'^\w[\w_]*\s*\(\)', content, re.MULTILINE))
        if func_count >= 5:
            score += 5
        elif func_count >= 3:
            score += 3
        else:
            score += 1

        if 'set -euo pipefail' in content:
            score += 5
        elif 'set -e' in content:
            score += 3

        if 'command -v' in content or 'which ' in content or 'type ' in content:
            score += 5
        elif 'test -f' in content or '[ -f' in content:
            score += 3

        if '✅' in content or '❌' in content or '⚠️' in content:
            score += 3
        if 'rm -' in content or 'trap ' in content:
            score += 3
        if content.count('#') >= 5:
            score += 4
        return score

    def _score_docs(self):
        """文档完备性 (15 分)"""
        score = 0
        base = self.skill_dir

        skill_md = base / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            sections = ['概述', '核心能力', '使用方式', '示例', '故障排除']
            hits = sum(1 for s in sections if s in content)
            score += hits
            if '故障排除' in content and ('|' in content or '问题' in content):
                score += 1

        usage = base / "USAGE.md"
        if usage.exists():
            content = usage.read_text(encoding='utf-8')
            if '命令参考' in content or '子命令' in content:
                score += 2
            if any(x in content for x in ['示例', 'example', 'Example']):
                score += 2

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

        self.scores['docs'] = score
        if broken_links > 0:
            self.remarks.append(f"文档完备性: {score}/15 (失效链接 {broken_links} 处)")
        else:
            self.remarks.append(f"文档完备性: {score}/15")

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
        report += "\n\n🏁 建议:\n"

        suggestions = []
        if self.scores['structure'] < 18:
            suggestions.append("补充 USAGE.md 和 README.md 文档")
        if self.scores['functionality'] < 24:
            if self._entry_type == 'shell':
                suggestions.append("增加 --dry-run、--verbose 和更多子命令")
            else:
                suggestions.append("增加 --dry-run 和 --verbose 选项")
        if self.scores['quality'] < 20:
            if self._entry_type == 'shell':
                suggestions.append("增强错误处理，添加 trap 和依赖检查")
            else:
                suggestions.append("增强异常处理，添加命令可用性检查")
        if self.scores['docs'] < 12:
            suggestions.append("完善故障排除表格和输出示例")
        if self.scores['standard'] < 8:
            suggestions.append("调整代码格式与目录结构以符合规范")
        if not suggestions:
            suggestions.append("质量优秀，建议归档到主技能目录")

        report += '\n'.join(f'  {i+1}. {s}' for i, s in enumerate(suggestions))
        report += "\n\n"
        return report
