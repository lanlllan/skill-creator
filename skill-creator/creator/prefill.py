"""
描述驱动预填充引擎

基于匹配的内置样例，对新创建的 Skill 进行 SKILL.md 章节预填充
和 run.py TODO 注释升级。
"""
import re
from pathlib import Path

from creator.examples import EXAMPLES_DIR, find_similar_example


_PREFILL_SECTIONS = ['适用场景', '核心能力', '故障排除']

_PREFILL_COMMENT = '<!-- PRE-FILLED: 基于样例 {example} 生成，请根据实际需求修改 -->'


def _extract_skill_md_section(content: str, section_name: str) -> str | None:
    """从 SKILL.md 中提取指定二级标题下的内容（到下一个二级标题为止）。"""
    lines = content.splitlines()
    capturing = False
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## ') and not stripped.startswith('### '):
            heading = stripped.lstrip('#').strip()
            if section_name in heading:
                capturing = True
                continue
            elif capturing:
                break
        if capturing:
            result.append(line)
    text = '\n'.join(result).strip()
    return text if text else None


def _extract_keywords(text: str) -> set[str]:
    """从文本中提取有意义的关键词（2 字中文词 + 英文词）。"""
    _PARTICLES = set('的了和与在中是为以及或者并且其中用于通过使用支持可以需要进行包括提供一个这个')
    segments = re.split(r'[，。、；：\u201c\u201d\u2018\u2019（）\s,.:;()\[\]{}!?！？\-—/]', text)
    keywords = set()
    for seg in segments:
        for eng in re.findall(r'[a-zA-Z]{2,}', seg):
            keywords.add(eng.lower())
        cjk = re.findall(r'[\u4e00-\u9fff]+', seg)
        for chunk in cjk:
            for i in range(len(chunk) - 1):
                bigram = chunk[i:i+2]
                if bigram[0] not in _PARTICLES and bigram[1] not in _PARTICLES:
                    keywords.add(bigram)
    return keywords


def _adapt_content(template_text: str, source_keywords: set[str],
                   target_keywords: set[str]) -> str:
    """将样例文本中的领域关键词替换为目标关键词。

    按出现频率从高到低配对替换，保留句式结构。
    """
    if not source_keywords or not target_keywords:
        return template_text

    source_sorted = sorted(source_keywords, key=lambda w: template_text.count(w), reverse=True)
    target_list = list(target_keywords)

    result = template_text
    replaced = 0
    for i, src_word in enumerate(source_sorted):
        if replaced >= len(target_list):
            break
        if src_word in result:
            result = result.replace(src_word, target_list[replaced], 1)
            replaced += 1

    return result


def _prefill_readme(
    skill_dir: Path,
    matched_example: str,
    source_keywords: set[str],
    target_keywords: set[str],
) -> bool:
    """对 README.md 的概述段进行预填充。"""
    readme_path = skill_dir / 'README.md'
    if not readme_path.exists():
        return False

    example_readme = EXAMPLES_DIR / matched_example / 'README.md'
    if not example_readme.exists():
        return False

    example_text = example_readme.read_text(encoding='utf-8')
    current_text = readme_path.read_text(encoding='utf-8')

    lines = example_text.splitlines()
    desc_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if stripped.startswith('##'):
            break
        if stripped:
            desc_lines.append(stripped)
    if not desc_lines:
        return False

    overview = '\n'.join(desc_lines[:3])
    adapted = _adapt_content(overview, source_keywords, target_keywords)

    current_lines = current_text.splitlines()
    insert_after = -1
    for i, line in enumerate(current_lines):
        if line.strip().startswith('# '):
            insert_after = i
            break

    if insert_after < 0:
        return False

    comment = _PREFILL_COMMENT.format(example=matched_example)
    if comment in current_text:
        return False

    new_lines = current_lines[:insert_after + 1]
    new_lines.append('')
    new_lines.append(comment)
    new_lines.append(adapted)
    new_lines.extend(current_lines[insert_after + 1:])
    readme_path.write_text('\n'.join(new_lines), encoding='utf-8')
    return True


def prefill_skill_content(
    skill_dir: Path,
    description: str,
    skill_type: str,
    threshold: float = 0.25,
    matched_example: str | None = None,
) -> dict[str, bool]:
    """对已创建的 skill 目录执行描述驱动预填充。

    Args:
        matched_example: 上游已匹配的样例名，非 None 时跳过内部二次匹配。

    Returns:
        {'skill_md': True/False, 'readme': True/False} 表示各文件是否被预填充
    """
    matched = matched_example
    if not matched:
        matched, _ = find_similar_example(description=description, threshold=threshold)
    if not matched:
        return {'skill_md': False, 'readme': False}

    example_skill_md = EXAMPLES_DIR / matched / 'SKILL.md'
    if not example_skill_md.exists():
        return {'skill_md': False, 'readme': False}

    example_content = example_skill_md.read_text(encoding='utf-8')
    source_keywords = _extract_keywords(example_content)
    target_keywords = _extract_keywords(description)

    skill_md_path = skill_dir / 'SKILL.md'
    if not skill_md_path.exists():
        return {'skill_md': False, 'readme': False}

    current_content = skill_md_path.read_text(encoding='utf-8')
    md_modified = False

    for section in _PREFILL_SECTIONS:
        example_section = _extract_skill_md_section(example_content, section)
        if not example_section:
            continue

        current_section = _extract_skill_md_section(current_content, section)
        if current_section and len(current_section.strip()) > 20:
            continue

        adapted = _adapt_content(example_section, source_keywords, target_keywords)
        comment = _PREFILL_COMMENT.format(example=matched)
        replacement = f'{comment}\n{adapted}'

        pattern = re.compile(
            rf'(## [^\n]*{re.escape(section)}[^\n]*\n)(.*?)(?=\n## |\Z)',
            re.DOTALL
        )
        match = pattern.search(current_content)
        if match:
            current_content = (
                current_content[:match.start(2)] +
                '\n' + replacement + '\n' +
                current_content[match.end(2):]
            )
            md_modified = True

    if md_modified:
        skill_md_path.write_text(current_content, encoding='utf-8')

    readme_modified = _prefill_readme(
        skill_dir, matched, source_keywords, target_keywords)

    return {'skill_md': md_modified, 'readme': readme_modified}


def _extract_python_steps(content: str) -> list[dict]:
    """从 Python run.py 中提取 cmd_* 函数的步骤信息。"""
    steps = []
    func_pattern = re.compile(r'^def (cmd_\w+)\(.*?\).*?:', re.MULTILINE)
    for match in func_pattern.finditer(content):
        func_name = match.group(1)
        cmd_name = func_name.replace('cmd_', '')
        start = match.end()
        next_func = re.search(r'\ndef \w+\(', content[start:])
        end = start + next_func.start() if next_func else len(content)
        body = content[start:end]

        args = re.findall(r'args\.(\w+)', body)
        steps.append({
            'command': cmd_name,
            'args': list(dict.fromkeys(args)),
            'func_name': func_name,
        })
    return steps


def _extract_shell_steps(content: str) -> list[dict]:
    """从 Shell run.sh 中提取函数定义或 case 分支的步骤信息。"""
    steps = []
    func_pattern = re.compile(r'^(\w[\w_]*)\s*\(\)\s*\{', re.MULTILINE)
    for match in func_pattern.finditer(content):
        func_name = match.group(1)
        if func_name in ('main', 'usage', 'help', 'log_error', 'log_info'):
            continue
        start = match.end()
        end_brace = content.find('\n}', start)
        if end_brace == -1:
            end_brace = len(content)
        body = content[start:end_brace]
        opts = re.findall(r'--(\w[\w-]*)', body)
        steps.append({
            'command': func_name.replace('cmd_', '').replace('_', '-'),
            'args': list(dict.fromkeys(opts))[:3],
            'func_name': func_name,
        })

    if not steps:
        case_cmds = re.findall(r'^\s*(\w[\w-]*)\)', content, re.MULTILINE)
        for cmd in case_cmds:
            if cmd not in ('help', 'version', '*', '--*'):
                steps.append({
                    'command': cmd,
                    'args': [],
                    'func_name': cmd,
                })
    return steps


def _extract_example_steps(example_dir: Path, skill_type: str) -> list[dict]:
    """从样例的入口脚本中提取步骤信息。

    当目标类型入口不存在时，回退到另一类型提取（跨类型回退）。
    """
    primary = example_dir / ('run.py' if skill_type == 'python' else 'run.sh')
    fallback = example_dir / ('run.sh' if skill_type == 'python' else 'run.py')

    if primary.exists():
        content = primary.read_text(encoding='utf-8')
        if skill_type == 'python':
            return _extract_python_steps(content)
        return _extract_shell_steps(content)

    if fallback.exists():
        content = fallback.read_text(encoding='utf-8')
        if skill_type == 'python':
            return _extract_shell_steps(content)
        return _extract_python_steps(content)

    return []


def upgrade_todo_comments(
    skill_dir: Path,
    matched_example: str | None,
    skill_type: str,
) -> bool:
    """升级 TODO 注释，注入匹配样例的步骤参考。"""
    if not matched_example:
        return False

    example_dir = EXAMPLES_DIR / matched_example
    if not example_dir.exists():
        return False

    steps = _extract_example_steps(example_dir, skill_type)
    if not steps:
        return False

    if skill_type == 'python':
        entry = skill_dir / 'run.py'
    else:
        entry = skill_dir / 'run.sh'

    if not entry.exists():
        return False

    content = entry.read_text(encoding='utf-8')
    todo_pattern = re.compile(r'(# TODO 实现步骤：\n(?:#[^\n]*\n)*)')
    match = todo_pattern.search(content)
    if not match:
        return False

    upgrade_lines = [f'# TODO 实现步骤：']
    upgrade_lines.append(f'# 参考样例：{matched_example} 中的实现模式')
    for i, step in enumerate(steps[:3], 1):
        args_desc = f"（{', '.join('--' + a for a in step['args'][:3])}）" if step['args'] else ''
        upgrade_lines.append(f'#   {i}. 实现 {step["command"]} 命令{args_desc}')
    upgrade_lines.append(f'#   提示：运行 `python run.py examples --show {matched_example}` 查看完整实现')
    upgrade_lines.append('')

    replacement = '\n'.join(upgrade_lines)
    content = content[:match.start()] + replacement + content[match.end():]
    entry.write_text(content, encoding='utf-8')
    return True
