"""Phase 15 测试：scorer 内容指导 + HTML 排除"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skill-creator'))

import pytest
from creator.scorer import SkillScorer


def _create_skill_dir(tmp_path, skill_md_content, run_py_content=None):
    """辅助函数：创建 skill 目录并写入文件"""
    skill_dir = tmp_path / 'test-skill'
    skill_dir.mkdir()
    (skill_dir / 'SKILL.md').write_text(skill_md_content, encoding='utf-8')
    if run_py_content:
        (skill_dir / 'run.py').write_text(run_py_content, encoding='utf-8')
    return skill_dir


class TestContentGuidance:
    def test_guidance_triggered_when_content_low(self, tmp_path):
        """content <= 5 时应生成内容指导"""
        skill_md = (
            '---\nname: test\ndescription: test\nversion: 1.0.0\n---\n'
            '# Test\n\n'
            '## 适用场景\n\n- 场景1\n- 在以下场景中\n\n'
            '## 核心能力\n\n- 能力1\n- 功能点1\n'
        )
        skill_dir = _create_skill_dir(tmp_path, skill_md)
        scorer = SkillScorer(skill_dir)
        scorer.score()
        report = scorer.generate_report()
        if scorer.scores['content'] <= 5:
            assert '📋 内容填充指导' in report

    def test_guidance_not_triggered_when_content_high(self, tmp_path):
        """content > 5 时不应生成内容指导"""
        skill_md = (
            '---\nname: test-good\ndescription: 分析文件统计\nversion: 1.0.0\n---\n'
            '# Test Good\n\n'
            '## 适用场景\n\n- 开发者需要快速了解项目代码规模分布\n'
            '- 技术主管评审时分析项目结构和语言组成\n\n'
            '## 核心能力\n\n- 递归统计代码行数分布\n'
            '- 按文件类型分组汇总体积占比\n'
        )
        run_py = (
            '#!/usr/bin/env python3\n'
            '"""Test — 分析统计。"""\n\n'
            'import argparse\nimport sys\nimport os\n'
            'from dataclasses import dataclass\nfrom pathlib import Path\n\n'
            '@dataclass\nclass Result:\n'
            '    """命令执行结果。"""\n'
            '    success: bool\n    message: str = ""\n'
            '    def __bool__(self): return self.success\n\n'
            'def cmd_count(args):\n'
            '    """统计行数。"""\n'
            '    root = Path(args.path)\n'
            '    if not root.exists():\n'
            '        return Result(success=False, message=f"错误：{root}")\n'
            '    total = sum(1 for f in root.rglob("*.py") for _ in f.read_text().splitlines())\n'
            '    return Result(success=True, message=f"✅ {total} 行")\n\n'
            'def cmd_types(args):\n'
            '    """类型分布。"""\n'
            '    root = Path(args.path)\n'
            '    if not root.exists():\n'
            '        return Result(success=False, message=f"错误：{root}")\n'
            '    exts = {}\n'
            '    for f in root.rglob("*"):\n'
            '        if f.is_file(): exts[f.suffix] = exts.get(f.suffix, 0) + 1\n'
            '    return Result(success=True, message=str(exts))\n\n'
            'def main():\n'
            '    """CLI 入口。"""\n'
            '    parser = argparse.ArgumentParser()\n'
            '    parser.add_argument("--verbose", action="store_true")\n'
            '    subs = parser.add_subparsers(dest="command")\n'
            '    p1 = subs.add_parser("count")\n'
            '    p1.add_argument("--path", required=True)\n'
            '    p2 = subs.add_parser("types")\n'
            '    p2.add_argument("--path", required=True)\n'
            '    args = parser.parse_args()\n'
            '    if not args.command:\n'
            '        parser.print_help()\n        return 0\n'
            '    dispatch = {"count": cmd_count, "types": cmd_types}\n'
            '    try:\n'
            '        result = dispatch[args.command](args)\n'
            '        print(result.message)\n'
            '        return 0 if result.success else 1\n'
            '    except Exception as exc:\n'
            '        print(f"❌ {exc}", file=sys.stderr)\n'
            '        return 1\n\n'
            'if __name__ == "__main__":\n    sys.exit(main())\n'
        )
        skill_dir = _create_skill_dir(tmp_path, skill_md, run_py)
        scorer = SkillScorer(skill_dir)
        scorer.score()
        report = scorer.generate_report()
        if scorer.scores['content'] > 5:
            assert '📋 内容填充指导' not in report

    def test_guidance_content_correctness(self, tmp_path):
        """指导内容应包含具体的行号或文件名"""
        skill_md = (
            '---\nname: test\ndescription: test\nversion: 1.0.0\n---\n'
            '# Test\n\n## 适用场景\n\n- 场景1\n- 能力1\n\n'
            '## 核心能力\n\n- 功能点1\n'
        )
        skill_dir = _create_skill_dir(tmp_path, skill_md)
        scorer = SkillScorer(skill_dir)
        scorer.score()
        guidance = scorer._generate_content_guidance()
        if guidance:
            combined = '\n'.join(guidance)
            assert 'SKILL.md' in combined

    def test_guidance_empty_for_good_content(self, tmp_path):
        """优质内容不应产生指导"""
        skill_md = (
            '---\nname: good\ndescription: 数据分析工具\nversion: 1.0.0\n---\n'
            '# Good Skill\n\n'
            '## 适用场景\n\n- 数据工程师用此工具快速清洗异常数据\n\n'
            '## 核心能力\n\n- 自动识别空值和异常值并生成清洗报告\n'
        )
        skill_dir = _create_skill_dir(tmp_path, skill_md)
        scorer = SkillScorer(skill_dir)
        scorer.score()
        guidance = scorer._generate_content_guidance()
        placeholder_in_guidance = any('模板默认文本' in g for g in guidance)
        assert not placeholder_in_guidance


class TestScorerHtmlExclusion:
    def test_prefilled_comment_excluded_from_placeholder(self, tmp_path):
        """PRE-FILLED HTML 注释不应被计入占位符检测"""
        skill_md = (
            '---\nname: test\ndescription: test\nversion: 1.0.0\n---\n'
            '# Test\n\n'
            '## 适用场景\n\n'
            '<!-- PRE-FILLED: 基于样例 file-analyzer 生成 -->\n'
            '- 开发者需要快速了解项目规模\n\n'
            '## 核心能力\n\n'
            '<!-- PRE-FILLED: 基于样例 file-analyzer 生成 -->\n'
            '- 统计代码行数和文件类型分布\n'
        )
        skill_dir = _create_skill_dir(tmp_path, skill_md)
        scorer = SkillScorer(skill_dir)
        placeholder_score = scorer._content_placeholder_residue()
        assert placeholder_score >= 4

    def test_prefilled_comment_excluded_from_template_retention(self, tmp_path):
        """PRE-FILLED HTML 注释不应计入模板保留率"""
        skill_md = (
            '---\nname: test\ndescription: test\nversion: 1.0.0\n---\n'
            '# Test\n\n'
            '<!-- PRE-FILLED: 基于样例生成 -->\n'
            '原创内容在此\n'
        )
        skill_dir = _create_skill_dir(tmp_path, skill_md)
        scorer = SkillScorer(skill_dir)
        retention = scorer._content_template_retention()
        assert retention < 1.0
