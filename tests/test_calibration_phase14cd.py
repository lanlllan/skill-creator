"""
Phase 14c&d 测试套件：评分器校准与报告增强

覆盖范围：
- 模板原文保留率（5 用例）
- 内容相关性（4 用例）
- 命令相关性（5 用例，含短横线回归）
- 校准基线（3 用例）
- 报告增强（5 用例）

合计：22 用例
"""
import os
import pytest
from pathlib import Path

from creator.scorer import SkillScorer, _BASELINE_DIR


GOOD_FRONT_MATTER = (
    '---\nname: test-skill\ndescription: 监控 API 端点的健康状态\n'
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

PYTHON_TEMPLATE_SKILL_MD = (
    '---\nname: empty-skill\ndescription: 一个自动化工具\n'
    'version: 1.0.0\nauthor: tester\ntags: [test]\n---\n\n'
    '# Empty Skill - 一个自动化工具\n\n'
    '## 📋 Skill 概述\n\n'
    '**技能名称**：`empty-skill`  \n'
    '**用途**：一个自动化工具  \n'
    '**适用场景**：\n'
    '- 需要自动化处理特定任务时\n'
    '- 作为工作流中的一个环节被调用时\n\n'
    '## 🎯 核心能力\n\n'
    '### 1. 主要功能\n'
    '- 接收输入参数并执行核心逻辑\n'
    '- 返回结构化的执行结果（Result 数据类）\n\n'
    '### 2. 错误处理\n'
    '- 输入参数校验（长度、格式、文件存在性）\n'
    '- 异常捕获与友好提示\n\n'
    '## 📁 Skill 结构\n\n'
    '```\nempty-skill/\n├── SKILL.md\n├── run.py\n├── USAGE.md\n└── README.md\n```\n\n'
    '## 🔧 使用方式\n\n'
    '```bash\npython run.py --help\npython run.py example --name test\npython run.py --verbose example --name test\n```\n\n'
    '## 📝 示例\n\n'
    '```bash\npython run.py example --name "hello"\n# 输出：\n# ✅ Hello, hello!\n```\n\n'
    '## 📊 输出示例\n\n```\n✅ Hello, World!\n```\n\n'
    '失败时输出：\n```\n❌ 执行失败：名称长度超过 128 字符\n```\n\n'
    '## 🐛 故障排除\n\n'
    '| 问题 | 原因 | 解决 |\n|------|------|------|\n'
    '| `❌ 执行失败：配置文件不存在` | `--config` 指定的路径无效 | 检查文件路径是否正确 |\n'
    '| `❌ 未预期异常：...` | 代码逻辑异常 | 使用 `--verbose` 查看详细信息 |\n\n'
    '## 🔗 相关资源\n\n- OpenClaw 文档：https://docs.openclaw.ai\n\n---\n\n'
    '*版本：1.0.0*  \n*更新：*\n'
)

PYTHON_TEMPLATE_RUN_PY = (
    '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n'
    '"""\n一个自动化工具\n"""\n\n'
    'import argparse\nimport sys\n'
    'from dataclasses import dataclass, field\nfrom typing import Any\n\n\n'
    '@dataclass\nclass Result:\n'
    '    """标准化命令执行结果。"""\n'
    '    success: bool = True\n    message: str = ""\n'
    '    data: dict[str, Any] = field(default_factory=dict)\n'
    '    errors: list[str] = field(default_factory=list)\n\n'
    '    def add_error(self, msg: str):\n'
    '        self.errors.append(msg)\n        self.success = False\n\n'
    '    def summary(self) -> str:\n'
    '        if self.success:\n'
    '            return f"✅ {self.message}" if self.message else "✅ 执行成功"\n'
    '        err_text = "; ".join(self.errors)\n'
    '        return f"❌ 执行失败：{err_text}"\n\n\n'
    'def validate_input(args) -> Result:\n'
    '    """输入参数校验，返回校验结果。"""\n'
    '    result = Result()\n'
    '    if hasattr(args, \'name\') and args.name:\n'
    '        if len(args.name) > 128:\n'
    '            result.add_error("名称长度超过 128 字符")\n'
    '        if not args.name.strip():\n'
    '            result.add_error("名称不能为空白")\n'
    '    if hasattr(args, \'config\') and args.config:\n'
    '        from pathlib import Path\n'
    '        config_path = Path(args.config)\n'
    '        if not config_path.exists():\n'
    '            result.add_error(f"配置文件不存在：{config_path}")\n'
    '    return result\n\n\n'
    'def cmd_example(args) -> Result:\n'
    '    """示例命令：演示标准执行流程。"""\n'
    '    result = validate_input(args)\n'
    '    if not result.success:\n        return result\n'
    '    try:\n'
    '        name = getattr(args, \'name\', None) or \'World\'\n'
    '        result.message = f"Hello, {name}!"\n'
    '        result.data[\'greeting\'] = result.message\n'
    '    except Exception as e:\n'
    '        result.add_error(f"执行异常：{e}")\n'
    '    return result\n\n\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description=\'一个自动化工具\',\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '        epilog="""\n示例:\n  python run.py example --name test\n'
    '  python run.py --verbose example\n        """\n    )\n\n'
    '    parser.add_argument(\'--verbose\', \'-v\', action=\'store_true\',\n'
    '                        help=\'详细输出\')\n'
    '    parser.add_argument(\'--config\', \'-c\', help=\'配置文件路径\')\n\n'
    '    subparsers = parser.add_subparsers(dest=\'command\', help=\'可用命令\')\n\n'
    '    example_parser = subparsers.add_parser(\'example\', help=\'示例命令\')\n'
    '    example_parser.add_argument(\'--name\', help=\'名称\')\n\n'
    '    args = parser.parse_args()\n\n'
    '    if args.verbose:\n        print(f"🔍 调试模式：{args}")\n\n'
    '    dispatch = {\n        \'example\': cmd_example,\n    }\n\n'
    '    handler = dispatch.get(args.command)\n'
    '    if not handler:\n        parser.print_help()\n        return 0\n\n'
    '    try:\n        result = handler(args)\n'
    '    except Exception as e:\n'
    '        print(f"❌ 未预期异常：{e}")\n        return 1\n\n'
    '    print(result.summary())\n'
    '    if args.verbose and result.data:\n'
    '        for k, v in result.data.items():\n'
    '            print(f"  {k}: {v}")\n\n'
    '    return 0 if result.success else 1\n\n\n'
    'if __name__ == \'__main__\':\n    sys.exit(main())\n'
)

PYTHON_TEMPLATE_USAGE = (
    '# empty-skill - 使用指南\n\n## 🚀 快速开始\n\n'
    '```bash\ncd empty-skill\npython run.py --help\npython run.py example --name test\n```\n\n'
    '## 📋 命令参考\n\n| 命令 | 说明 | 示例 |\n|------|------|------|\n'
    '| `example` | 示例命令 | `python run.py example --name test` |\n\n'
    '## 📊 输出说明\n\n- 成功：`✅ <消息>`\n- 失败：`❌ 执行失败：<错误详情>`\n\n'
    '## 🐛 常见问题\n\n**Q: 执行报错怎么办？**\nA: 添加 `--verbose` 查看详细输出。\n'
)


@pytest.fixture
def python_empty_shell(tmp_path):
    """Python 空壳 Skill fixture（模拟模板直接渲染）。"""
    d = tmp_path / "empty-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(PYTHON_TEMPLATE_SKILL_MD, encoding='utf-8')
    (d / "run.py").write_text(PYTHON_TEMPLATE_RUN_PY, encoding='utf-8')
    os.chmod(d / "run.py", 0o755)
    (d / "USAGE.md").write_text(PYTHON_TEMPLATE_USAGE, encoding='utf-8')
    (d / "README.md").write_text(
        '# empty-skill\n\n一个自动化工具\n\n## 🚀 安装\n\n'
        '无需安装，直接运行：\n\n```bash\npython run.py --help\n```\n\n'
        '## 📖 文档\n\n详细说明请查看 [USAGE.md](USAGE.md) 或 [SKILL.md](SKILL.md)。\n',
        encoding='utf-8')
    return d


@pytest.fixture
def shell_empty_shell(tmp_path):
    """Shell 空壳 Skill fixture。"""
    d = tmp_path / "shell-empty"
    d.mkdir()
    (d / "SKILL.md").write_text(
        '---\nname: shell-empty\ndescription: Kubernetes 集群备份工具\n'
        'version: 1.0.0\nauthor: tester\ntags: [test]\ntype: shell\n---\n\n'
        '# Shell Empty - Kubernetes 集群备份工具\n\n'
        '## 📋 Skill 概述\n\n'
        '**技能名称**：`shell-empty`  \n**类型**：Shell 脚本  \n'
        '**用途**：Kubernetes 集群备份工具  \n**适用场景**：\n'
        '- 需要在命令行环境中执行自动化任务时\n'
        '- 作为 CI/CD 流水线中的一个步骤时\n\n'
        '## 🎯 核心能力\n\n### 1. 命令分发\n'
        '- 支持多个子命令（通过 `case` 分支）\n- 内置 `help`、`version` 命令\n\n'
        '### 2. 错误处理\n'
        '- `set -euo pipefail` 严格模式\n- 分级日志函数（info / ok / warn / error）\n\n'
        '## 🔧 使用方式\n\n```bash\nbash run.sh help\nbash run.sh example --name test\n```\n\n'
        '## 📝 示例\n\n```bash\nbash run.sh example --name "hello"\n# 输出：✅ Hello, hello!\n```\n\n'
        '## 🐛 故障排除\n\n| 问题 | 原因 | 解决 |\n|------|------|------|\n'
        '| 权限不足 | 缺少执行权限 | `chmod +x run.sh` |\n\n'
        '## 🔗 相关资源\n\n- OpenClaw 文档：https://docs.openclaw.ai\n\n---\n\n'
        '*版本：1.0.0*  \n*更新：*\n',
        encoding='utf-8')
    (d / "run.sh").write_text(
        '#!/usr/bin/env bash\n# -*- coding: utf-8 -*-\n# Kubernetes 集群备份工具\n'
        'set -euo pipefail\n\nSCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'VERSION="1.0.0"\n\n'
        'usage() {\n    cat <<EOF\nShell Empty v${VERSION}\nKubernetes 集群备份工具\n\n'
        '用法:\n    bash run.sh <command> [options]\n\n命令:\n'
        '    example     示例命令\n    version     显示版本信息\n    help        显示帮助\n\n'
        '选项:\n    --verbose   详细输出\n    --help      显示帮助\n\n'
        '示例:\n    bash run.sh example --name test\n    bash run.sh version\nEOF\n}\n\n'
        'log_info()  { echo "ℹ️  $*"; }\nlog_ok()    { echo "✅ $*"; }\n'
        'log_warn()  { echo "⚠️  $*"; }\nlog_error() { echo "❌ $*" >&2; }\n\n'
        'cmd_example() {\n    local name="World"\n    while [[ $# -gt 0 ]]; do\n'
        '        case "$1" in\n            --name) name="$2"; shift 2 ;;\n'
        '            *) log_error "未知参数: $1"; return 1 ;;\n        esac\n    done\n'
        '    log_ok "Hello, ${name}!"\n}\n\n'
        'cmd_version() {\n    echo "shell-empty v${VERSION}"\n}\n\n'
        'main() {\n    if [[ $# -eq 0 ]]; then\n        usage\n        exit 0\n    fi\n\n'
        '    local cmd="$1"; shift\n    case "${cmd}" in\n'
        '        example) cmd_example "$@" ;;\n'
        '        version) cmd_version ;;\n'
        '        help|--help|-h) usage ;;\n'
        '        *) log_error "未知命令: ${cmd}"; usage; exit 1 ;;\n    esac\n}\n\n'
        'main "$@"\n',
        encoding='utf-8')
    os.chmod(d / "run.sh", 0o755)
    (d / "USAGE.md").write_text(
        '# shell-empty - 使用指南\n\n## 🚀 快速开始\n\n'
        '```bash\nbash run.sh help\nbash run.sh example --name test\n```\n\n'
        '## 📋 命令参考\n\n| 命令 | 说明 |\n|------|------|\n'
        '| example | 示例命令 |\n| version | 版本信息 |\n',
        encoding='utf-8')
    (d / "README.md").write_text(
        '# shell-empty\n\n安装说明。详见 [USAGE.md](USAGE.md) 或 [SKILL.md](SKILL.md)。\n',
        encoding='utf-8')
    return d


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
        '# 使用指南\n\n## 命令参考\n| 命令 | 说明 |\n|------|------|\n'
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


# ═══════════════════════════════════════════════════════════════════════
#  TestTemplateRetention (14c)
# ═══════════════════════════════════════════════════════════════════════

class TestTemplateRetention:
    def test_load_baseline_python_skill(self):
        s = SkillScorer(Path('.'))
        s._entry_type = 'python'
        lines = s._load_baseline_lines('SKILL')
        assert len(lines) > 30

    def test_load_baseline_shell_run(self):
        s = SkillScorer(Path('.'))
        s._entry_type = 'shell'
        lines = s._load_baseline_lines('run')
        assert len(lines) > 20

    def test_empty_shell_python_high_retention(self, python_empty_shell):
        s = SkillScorer(python_empty_shell)
        retention = s._content_template_retention()
        assert retention > 0.7

    def test_customized_skill_low_retention(self, good_skill):
        s = SkillScorer(good_skill)
        retention = s._content_template_retention()
        assert retention < 0.7

    def test_content_capped_at_5(self, python_empty_shell):
        s = SkillScorer(python_empty_shell)
        s.score()
        assert s.scores['content'] <= 5


# ═══════════════════════════════════════════════════════════════════════
#  TestContentRelevance (14c)
# ═══════════════════════════════════════════════════════════════════════

class TestContentRelevance:
    def test_generic_sections_penalty(self, python_empty_shell):
        s = SkillScorer(python_empty_shell)
        result = s._docs_content_relevance()
        assert result == -5

    def test_relevant_sections_no_penalty(self, good_skill):
        s = SkillScorer(good_skill)
        result = s._docs_content_relevance()
        assert result == 0

    def test_no_description_no_penalty(self, tmp_path):
        d = tmp_path / "no-desc"
        d.mkdir()
        (d / "SKILL.md").write_text(
            '---\nname: test\n---\n## 适用场景\n- 场景1\n',
            encoding='utf-8')
        s = SkillScorer(d)
        assert s._docs_content_relevance() == 0

    def test_no_section_items_no_penalty(self, tmp_path):
        d = tmp_path / "no-items"
        d.mkdir()
        (d / "SKILL.md").write_text(
            GOOD_FRONT_MATTER + '## 概述\n没有列表项的文档。\n',
            encoding='utf-8')
        s = SkillScorer(d)
        assert s._docs_content_relevance() == 0


# ═══════════════════════════════════════════════════════════════════════
#  TestExampleOnlyCommand (14c)
# ═══════════════════════════════════════════════════════════════════════

class TestExampleOnlyCommand:
    def test_python_only_example_detected(self, tmp_path):
        d = tmp_path / "py-example"
        d.mkdir()
        (d / "run.py").write_text(
            'import argparse\nparser = argparse.ArgumentParser()\n'
            'subparsers = parser.add_subparsers(dest="command")\n'
            'subparsers.add_parser("example", help="示例")\n',
            encoding='utf-8')
        os.chmod(d / "run.py", 0o755)
        s = SkillScorer(d)
        content = (d / "run.py").read_text(encoding='utf-8')
        assert s._has_only_example_command(content) is True

    def test_python_multiple_commands_ok(self, tmp_path):
        d = tmp_path / "py-multi"
        d.mkdir()
        (d / "run.py").write_text(
            'import argparse\nparser = argparse.ArgumentParser()\n'
            'subparsers = parser.add_subparsers(dest="command")\n'
            'subparsers.add_parser("example")\n'
            'subparsers.add_parser("check")\n',
            encoding='utf-8')
        os.chmod(d / "run.py", 0o755)
        s = SkillScorer(d)
        content = (d / "run.py").read_text(encoding='utf-8')
        assert s._has_only_example_command(content) is False

    def test_python_hyphenated_command_not_only_example(self, tmp_path):
        d = tmp_path / "py-hyphen"
        d.mkdir()
        (d / "run.py").write_text(
            'import argparse\nparser = argparse.ArgumentParser()\n'
            'subparsers = parser.add_subparsers(dest="command")\n'
            'subparsers.add_parser("example")\n'
            'subparsers.add_parser("health-check")\n',
            encoding='utf-8')
        os.chmod(d / "run.py", 0o755)
        s = SkillScorer(d)
        content = (d / "run.py").read_text(encoding='utf-8')
        assert s._has_only_example_command(content) is False

    def test_shell_only_example_detected(self, tmp_path):
        d = tmp_path / "sh-example"
        d.mkdir()
        (d / "run.sh").write_text(
            '#!/bin/bash\ncase "$1" in\n'
            '    example) echo "hello" ;;\n'
            '    help) echo "help" ;;\n'
            '    version) echo "1.0" ;;\n'
            '    *) echo "unknown" ;;\nesac\n',
            encoding='utf-8')
        os.chmod(d / "run.sh", 0o755)
        s = SkillScorer(d)
        content = (d / "run.sh").read_text(encoding='utf-8')
        assert s._has_only_example_command(content) is True

    def test_shell_multiple_commands_ok(self, tmp_path):
        d = tmp_path / "sh-multi"
        d.mkdir()
        (d / "run.sh").write_text(
            '#!/bin/bash\ncase "$1" in\n'
            '    example) echo "hello" ;;\n'
            '    check) echo "checking" ;;\n'
            '    help) echo "help" ;;\nesac\n',
            encoding='utf-8')
        os.chmod(d / "run.sh", 0o755)
        s = SkillScorer(d)
        content = (d / "run.sh").read_text(encoding='utf-8')
        assert s._has_only_example_command(content) is False


# ═══════════════════════════════════════════════════════════════════════
#  TestCalibratedBaseline (14c)
# ═══════════════════════════════════════════════════════════════════════

class TestCalibratedBaseline:
    def test_python_empty_shell_55_pm_5(self, python_empty_shell):
        s = SkillScorer(python_empty_shell)
        s.score()
        assert 50 <= s.scores['total'] <= 60, (
            f"Python 空壳评分 {s.scores['total']} 不在 50-60 区间: {s.scores}")

    def test_shell_empty_shell_55_pm_5(self, shell_empty_shell):
        s = SkillScorer(shell_empty_shell)
        s.score()
        assert 50 <= s.scores['total'] <= 60, (
            f"Shell 空壳评分 {s.scores['total']} 不在 50-60 区间: {s.scores}")

    def test_good_skill_unaffected(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        assert abs(s.scores['total'] - 92) <= 5, (
            f"高质量 Skill 评分偏差过大: {s.scores['total']} vs 基线 92")


# ═══════════════════════════════════════════════════════════════════════
#  TestReportEnhancement (14d)
# ═══════════════════════════════════════════════════════════════════════

class TestReportEnhancement:
    def test_empty_shell_report_has_guided_suggestion(self, python_empty_shell):
        s = SkillScorer(python_empty_shell)
        s.score()
        report = s.generate_report()
        assert '[+20分]' in report
        assert '--interactive' in report

    def test_empty_shell_report_has_example_suggestion(self, python_empty_shell):
        s = SkillScorer(python_empty_shell)
        s.score()
        report = s.generate_report()
        assert '[+5分]' in report
        assert 'cmd_example' in report

    def test_suggestions_sorted_by_delta(self, python_empty_shell):
        s = SkillScorer(python_empty_shell)
        s.score()
        suggestions = s._generate_improvement_suggestions()
        deltas = [s['delta'] for s in suggestions]
        assert deltas == sorted(deltas, reverse=True)

    def test_good_skill_report_archive(self, good_skill):
        s = SkillScorer(good_skill)
        s.score()
        report = s.generate_report()
        assert '归档' in report

    def test_report_format_improvement_path(self, python_empty_shell):
        s = SkillScorer(python_empty_shell)
        s.score()
        report = s.generate_report()
        assert '改进路径（按效果排序）' in report
