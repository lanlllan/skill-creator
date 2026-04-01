"""
create 命令 — 创建新 skill
"""
import os
import re
import yaml
from datetime import datetime
from pathlib import Path

import shutil

from creator.paths import get_skills_temp_dir
from creator.validators import validate_skill_name, validate_version
from creator.templates import generate_files
from creator.scorer import SkillScorer
from creator.examples import find_similar_example
from creator.prefill import prefill_skill_content, upgrade_todo_comments
from creator.state_manager import add_skill
from creator.spec import (
    generate_spec_skeleton, save_spec, load_spec, validate_spec, classify_errors_by_group,
    spec_to_template_vars, build_spec_from_answers, SPEC_FILENAME,
)

KNOWN_PARAMS = frozenset({'name', 'description', 'version', 'author', 'tags', 'output'})


def create_skill_directory(base_path, skill_name: str) -> Path:
    """创建 skill 目录，目录已存在时抛 FileExistsError。"""
    skill_dir = Path(base_path) / skill_name
    if skill_dir.exists():
        raise FileExistsError(f"目录已存在：{skill_dir}")
    skill_dir.mkdir(parents=True, exist_ok=True)
    return skill_dir


def validate_skill(skill_dir: Path):
    """验证 skill 目录的完整性，返回 (errors, warnings) 两个列表。"""
    errors = []
    warnings = []
    skill_dir = Path(skill_dir)

    skill_md = skill_dir / "SKILL.md"
    run_py = skill_dir / "run.py"

    if not skill_md.exists():
        errors.append("❌ SKILL.md 不存在")
    else:
        content = skill_md.read_text(encoding='utf-8')
        if not content.startswith('---'):
            errors.append("❌ SKILL.md 缺少 YAML front matter")
        else:
            try:
                front_matter_str = content.split('---', 2)[1]
                front_matter = yaml.safe_load(front_matter_str)
                if not front_matter:
                    errors.append("❌ front matter 为空")
                else:
                    if 'name' not in front_matter:
                        errors.append("❌ front matter 缺少 'name' 字段")
                    if 'description' not in front_matter:
                        errors.append("❌ front matter 缺少 'description' 字段")
                    if 'version' not in front_matter:
                        errors.append("❌ front matter 缺少 'version' 字段")
                    if 'name' in front_matter and not validate_skill_name(front_matter['name']):
                        errors.append(f"❌ skill 名称 '{front_matter['name']}' 不符合规范（应小写、短横线分隔）")
                    if 'version' in front_matter and not validate_version(str(front_matter['version'])):
                        warnings.append(f"⚠️  版本号 '{front_matter['version']}' 不符合语义化版本格式（建议 x.y.z）")
            except Exception as e:
                errors.append(f"❌ front matter 解析失败：{e}")

    run_sh = skill_dir / "run.sh"
    if not run_py.exists() and not run_sh.exists():
        errors.append("❌ 入口脚本不存在（需要 run.py 或 run.sh）")
    else:
        entry = run_py if run_py.exists() else run_sh
        if not os.access(entry, os.X_OK):
            warnings.append(f"⚠️  {entry.name} 缺少可执行权限（建议 chmod +x）")
        _validate_entry_script(entry, warnings)

    _validate_doc_completeness(skill_dir, skill_md, warnings)
    _validate_placeholder_residue(skill_dir, errors)
    _validate_markdown_links(skill_dir, warnings)

    return errors, warnings


def _validate_entry_script(entry: Path, warnings: list):
    """Phase 7：入口脚本质量检查（shebang / docstring / 异常处理 / 退出码）。"""
    try:
        content = entry.read_text(encoding='utf-8')
    except Exception:
        return

    is_python = entry.name.endswith('.py')

    if not content.startswith('#!'):
        shebang_hint = '#!/usr/bin/env python3' if is_python else '#!/usr/bin/env bash'
        warnings.append(f"⚠️  {entry.name} 缺少 shebang（建议 {shebang_hint}）")

    if is_python:
        first_500 = content[:500]
        if '"""' not in first_500 and "'''" not in first_500:
            warnings.append(f"⚠️  {entry.name} 缺少模块级 docstring")
    else:
        lines = content.splitlines()
        has_desc = any(
            l.strip().startswith('#') and len(l.strip()) > 3
            for l in lines[:10] if not l.startswith('#!')
        )
        if not has_desc:
            warnings.append(f"⚠️  {entry.name} 缺少文件头注释说明")

    if is_python:
        if 'try:' not in content and 'except' not in content:
            warnings.append(f"⚠️  {entry.name} 未发现 try/except 异常处理结构")
    else:
        if 'set -e' not in content and 'trap ' not in content:
            warnings.append(f"⚠️  {entry.name} 未发现错误处理（建议 set -e 或 trap）")

    if is_python:
        if 'sys.exit(' not in content and 'return 0' not in content and 'return 1' not in content:
            warnings.append(f"⚠️  {entry.name} main() 未明确返回退出码")
    else:
        if 'exit 0' not in content and 'exit 1' not in content and 'exit $' not in content:
            warnings.append(f"⚠️  {entry.name} 未发现 exit 语句（建议明确退出码）")


def _validate_doc_completeness(skill_dir: Path, skill_md: Path, warnings: list):
    """Phase 7：文档完整度检查。"""
    if not (skill_dir / "USAGE.md").exists():
        warnings.append("⚠️  USAGE.md 不存在（建议提供使用指南）")

    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8')
        expected = ['概述', '核心能力', '使用方式', '示例']
        missing = [s for s in expected if s not in content]
        if missing:
            warnings.append(f"⚠️  SKILL.md 缺少推荐章节：{', '.join(missing)}")


def _validate_placeholder_residue(skill_dir: Path, errors: list):
    """Phase 7：占位符残留检测（error 级别），递归扫描子目录。"""
    check_suffixes = {'.md', '.py', '.sh', '.yaml', '.yml', '.txt'}
    pattern = re.compile(r'\{\{[^}]+\}\}')
    for f in skill_dir.rglob('*'):
        if f.is_file() and f.suffix in check_suffixes and not f.name.endswith('.j2'):
            try:
                content = f.read_text(encoding='utf-8')
            except Exception:
                continue
            found = set(pattern.findall(content))
            if found:
                rel = f.relative_to(skill_dir)
                errors.append(
                    f"❌ {rel} 存在未替换的占位符：{', '.join(sorted(found))}"
                )


def _validate_markdown_links(skill_dir: Path, warnings: list):
    """Phase 7：Markdown 本地链接有效性检查，递归扫描子目录。"""
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    for md_file in skill_dir.rglob('*.md'):
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception:
            continue
        rel_md = md_file.relative_to(skill_dir)
        for label, href in link_pattern.findall(content):
            if href.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            target = (md_file.parent / href).resolve()
            if not target.exists():
                warnings.append(
                    f"⚠️  {rel_md} 中链接 [{label}]({href}) 指向不存在的文件"
                )


def create_skill(params: dict, _out: dict = None, skip_state: bool = False,
                 skill_type: str = 'python',
                 template_dir: str | None = None,
                 spec_path: 'Path | None' = None,
                 spec_variables: dict | None = None) -> int:
    """纯函数：从 params dict 创建 skill，返回退出码（0=成功，非0=失败）。

    params 字段契约（唯一来源，禁止双口径）：
      name        str            必需
      description str            必需
      version     str            可选，默认 "1.0.0"
      author      str            可选，默认 "OpenClaw Assistant"
      tags        list[str]|str  可选，默认 []（支持逗号分隔字符串）
      output      str|None       可选，None 时使用 get_skills_temp_dir()

    可选参数 _out：dict，供调用方获取额外输出（score、skill_name、failure_reason）。
    skill_type：Skill 类型（python / shell），控制使用的模板集。
    template_dir：自定义模板目录路径，覆盖内置模板。
    spec_path：.skill-spec.yaml 路径，创建后复制到产出目录。
    spec_variables：规约驱动的扩展变量（purpose/capabilities/commands 等），非 None 时启用富模板。
    """
    missing = {'name', 'description'} - params.keys()
    if missing:
        raise ValueError(f"缺少必需字段：{', '.join(sorted(missing))}")
    unknown = params.keys() - KNOWN_PARAMS
    if unknown:
        print(f"⚠️  忽略未知字段：{', '.join(sorted(unknown))}")

    skill_name = str(params['name']).lower().replace(' ', '-')
    description = str(params['description'])
    version = str(params.get('version') or '1.0.0')
    author = str(params.get('author') or 'OpenClaw Assistant')

    raw_tags = params.get('tags') or []
    if isinstance(raw_tags, str):
        tags = [t.strip() for t in raw_tags.split(',') if t.strip()]
    else:
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]

    raw_output = params.get('output')
    output_dir = Path(raw_output).expanduser().resolve() if raw_output else get_skills_temp_dir()

    if not skill_name or not description:
        reason = '技能名称和描述不能为空'
        print(f"❌ {reason}")
        if _out is not None:
            _out['failure_reason'] = reason
        return 1

    if not validate_skill_name(skill_name):
        reason = f'名称 "{skill_name}" 不符合规范（应小写字母开头，仅含字母/数字/短横线）'
        print(f"❌ 技能名称 '{skill_name}' 不符合规范")
        print("   规范：小写字母、数字、短横线，必须以字母开头")
        print("   示例：test-runner, log-analyzer")
        if _out is not None:
            _out['failure_reason'] = reason
        return 1

    if not validate_version(version):
        reason = f'版本号 "{version}" 不符合语义化版本格式（应为 x.y.z）'
        print(f"❌ 版本号 '{version}' 不符合语义化版本格式")
        print("   规范：x.y.z（如 1.0.0、2.1.3）")
        if _out is not None:
            _out['failure_reason'] = reason
        return 1

    try:
        skill_dir = create_skill_directory(output_dir, skill_name)
        print(f"📁 创建目录：{skill_dir}")

        variables = {
            'name': skill_name,
            'description': description,
            'author': author,
            'tags': tags,
            'version': version,
            'date': datetime.now().strftime("%Y-%m-%d"),
        }
        if spec_variables:
            variables.update({k: v for k, v in spec_variables.items()
                              if k not in variables or k in (
                                  'purpose', 'capabilities', 'commands',
                                  'error_handling', 'dependencies',
                                  'dispatch_entries')})

        guided = spec_variables is not None
        print("📝 生成文件...")
        generate_files(skill_dir, variables,
                       skill_type=skill_type, template_dir=template_dir,
                       guided=guided)

        if spec_path:
            dest_spec = skill_dir / SPEC_FILENAME
            src_spec = Path(spec_path).resolve()
            if src_spec != dest_spec and src_spec.exists():
                shutil.copy2(src_spec, dest_spec)

        if not guided:
            matched, similarity = find_similar_example(description=variables.get('description', ''))
            if matched and similarity > 0.3:
                prefill_skill_content(skill_dir, variables['description'], skill_type)
                upgrade_todo_comments(skill_dir, matched, skill_type)

        errors, warnings = validate_skill(skill_dir)
        if errors:
            print("\n❌ 发现错误：")
            for e in errors:
                print(f"  {e}")
            return 1
        if warnings:
            print("\n⚠️  警告：")
            for w in warnings:
                print(f"  {w}")

        print("\n📊 正在进行质量评分...")
        scorer = SkillScorer(skill_dir)
        scores = scorer.score()
        print(scorer.generate_report())

        if not skip_state:
            try:
                add_skill(skill_name, score=scores['total'])
            except Exception as e:
                print(f"⚠️  更新状态失败: {e}")

        total = scores['total']
        if total >= 80:
            print("🎯 建议：技能质量良好，可直接归档使用")
        elif total >= 70:
            print("🟡 建议：补充文档后可归档")
        else:
            print("🔴 建议：需进一步完善后再归档")

        print(f"\n✅ Skill '{skill_name}' 创建完成！")
        print(f"   位置：{skill_dir}")
        print(f"   下一步：检查文档并确认后归档到 skills 目录（python run.py archive {skill_name}）")

        if _out is not None:
            _out['score'] = total
            _out['skill_name'] = skill_name

        return 0

    except FileExistsError as e:
        reason = f'目录已存在：{e}'
        print(f"❌ {e}")
        if _out is not None:
            _out['failure_reason'] = reason
        return 1
    except Exception as e:
        reason = f'未知异常：{e}'
        print(f"❌ 创建失败：{e}")
        if _out is not None:
            _out['failure_reason'] = reason
        return 1


DEEPEN_QUESTIONS = [
    ('purpose_problem',      '这个 skill 要解决什么问题？（1-2 句话描述痛点）'),
    ('target_user',          '目标用户是谁？（5-15 字）'),
    ('scenario',             '列举一个典型使用场景（谁+什么情况+做什么）'),
    ('capability_name',      '主要能力名称（如「端点健康检查」）'),
    ('capability_desc',      '该能力的描述（如「对 URL 发送 HTTP 请求...」）'),
    ('command_name',         '主命令名称（如「check」）'),
    ('command_desc',         '主命令描述（如「检查指定 URL 健康状态」）'),
    ('error_scenario',       '可能遇到的错误场景（如「目标 URL 无法连接」）'),
    ('error_cause',          '针对刚才的错误场景，通常是什么原因导致的？'),
    ('error_solution',       '用户应该如何解决？（给出具体操作步骤）'),
    ('dependencies_runtime', '运行时需要的 Python 包（逗号分隔，如 requests, pyyaml，无则回车跳过）'),
]


_FIELD_MIN_LENGTH: dict[str, int] = {
    'purpose_problem': 10,
    'target_user': 3,
    'scenario': 10,
    'capability_name': 3,
    'capability_desc': 5,
    'command_name': 2,
    'command_desc': 5,
    'error_scenario': 5,
    'error_cause': 5,
    'error_solution': 5,
    'dependencies_runtime': 0,
}


def _effective_length(text: str) -> int:
    """计算有效内容长度（字符数），排除前后空白。"""
    return len(text.strip())


def _check_answer_quality(
    key: str,
    answer: str,
    description: str,
) -> str | None:
    """检测深化答案质量，返回提示信息（None 表示通过）。

    规则（按优先级）：
    1. 过短：按字段差异化阈值
    2. 高重复：bigram_jaccard(answer, description) > 0.8
    3. 占位符：匹配 r'xxx|TODO|填写|示例|placeholder'
    """
    from creator.text_utils import bigram_jaccard

    stripped = answer.strip()
    min_len = _FIELD_MIN_LENGTH.get(key, 10)
    length = _effective_length(stripped)
    if min_len > 0 and length < min_len:
        return f"答案可能过于简短（当前 {length} 字，建议 {min_len} 字以上）"

    if description and bigram_jaccard(stripped, description) > 0.8:
        return "建议补充 description 中未提及的细节"

    if re.search(r'xxx|TODO|填写|示例|placeholder', stripped, re.IGNORECASE):
        return "请提供具体内容"

    return None


def _interactive_deepen(description: str, reader=input) -> dict[str, str] | None:
    """意图深化：通过问答收集 Skill 设计信息。首问 s 全跳过，中途 s 截断。"""
    print('\n🔍 意图深化 — 帮助生成更高质量的 Skill（输入 s 跳过全部）\n')
    answers = {}
    for i, (key, prompt) in enumerate(DEEPEN_QUESTIONS):
        response = reader(f'  [{i+1}/{len(DEEPEN_QUESTIONS)}] {prompt}\n  > ').strip()
        if i == 0 and response.lower() == 's':
            return None
        if response.lower() == 's':
            break
        if response:
            hint = _check_answer_quality(key, response, description)
            if hint:
                print(f"⚠️  {hint}")
                print(f"    重新输入（或按 Enter 保留当前答案）：")
                retry = reader("  > ")
                if retry and retry.strip():
                    response = retry.strip()
        answers[key] = response
    return answers


def _clear_spec_group(variables: dict, group: str):
    """清除降级字段组的模板变量，使其回退到基础模板默认值。

    purpose 组是嵌套字典 variables['purpose']={problem, target_user, scenarios}，
    其余组（capabilities/commands/error_handling）为顶层列表。
    """
    if group == 'purpose':
        purpose = variables.get('purpose')
        if isinstance(purpose, dict):
            purpose['problem'] = ''
            purpose['target_user'] = ''
            purpose['scenarios'] = []
        return
    top_level_keys = {
        'capabilities': ['capabilities'],
        'commands': ['commands'],
        'error_handling': ['error_handling'],
    }
    for key in top_level_keys.get(group, []):
        if key in variables:
            if isinstance(variables[key], list):
                variables[key] = []
            elif isinstance(variables[key], str):
                variables[key] = ''


def main_create(args):
    """创建新 skill（CLI 适配层，负责交互式输入收集并构造 params dict）。"""
    if getattr(args, 'spec', None):
        return _create_from_spec(args)
    if getattr(args, 'guided', False):
        return _create_guided(args)

    if args.interactive:
        skill_name = args.name or input("Skill 名称（小写、短横线分隔）: ").strip()
        description = args.description or input("描述: ").strip()
        version = input(f"版本号 [默认: {args.version or '1.0.0'}]: ").strip() or args.version or "1.0.0"
        author = input(f"作者 [默认: {args.author or 'OpenClaw Assistant'}]: ").strip() or args.author or "OpenClaw Assistant"
        tags_input = args.tags or input("标签（逗号分隔，可留空）: ").strip()
        tags = [t.strip() for t in tags_input.split(',') if t.strip()] if tags_input else []
        default_temp = str(get_skills_temp_dir())
        output = input(f"输出目录 [默认: {default_temp}]: ").strip() or default_temp
    else:
        if not args.name or not args.description:
            print("❌ 非交互模式下 --name 和 --description 为必填参数")
            print("   提示：使用 --interactive 进入交互式模式，或同时提供 -n 和 -d")
            return 1
        skill_name = args.name
        description = args.description
        author = args.author
        tags = args.tags
        version = args.version
        output = args.output

    params = {
        'name': skill_name,
        'description': description,
        'version': version,
        'author': author,
        'tags': tags,
        'output': output,
    }

    skill_type = getattr(args, 'type', 'python')
    template_dir = getattr(args, 'template_dir', None)

    spec_variables = None
    tmp_spec_path = None
    skip_deepen = getattr(args, 'skip_deepen', False)

    if args.interactive and not skip_deepen:
        answers = _interactive_deepen(description)
        if answers is not None:
            spec = build_spec_from_answers(
                answers, skill_name, description,
                version=version, author=author, tags=tags,
            )
            errors, warnings = validate_spec(spec)
            for w in warnings:
                print(f'  ⚠️  {w}')
            if errors:
                grouped = classify_errors_by_group(errors)
                degraded_groups = [g for g in grouped if g != 'other']
                if degraded_groups and not grouped.get('other'):
                    for group, errs in grouped.items():
                        print(f'⚠️  {group} 信息不完整，该章节使用基础模板')
                    import tempfile
                    spec_variables = spec_to_template_vars(spec)
                    for group in degraded_groups:
                        _clear_spec_group(spec_variables, group)
                    tmp = tempfile.NamedTemporaryFile(
                        suffix='.yaml', delete=False, mode='w', encoding='utf-8')
                    save_spec(spec, Path(tmp.name))
                    tmp.close()
                    tmp_spec_path = tmp.name
                else:
                    reasons = '; '.join(errors[:3])
                    print(f'⚠️  深化信息不完整（{reasons}），已使用基础模板创建。')
                    print('   后续可运行 create --interactive 重新创建。')
            else:
                import tempfile
                spec_variables = spec_to_template_vars(spec)
                tmp = tempfile.NamedTemporaryFile(
                    suffix='.yaml', delete=False, mode='w', encoding='utf-8')
                save_spec(spec, Path(tmp.name))
                tmp.close()
                tmp_spec_path = tmp.name

    try:
        return create_skill(params, skill_type=skill_type,
                            template_dir=template_dir,
                            spec_path=tmp_spec_path,
                            spec_variables=spec_variables)
    except ValueError as e:
        print(f"❌ {e}")
        return 1
    finally:
        if tmp_spec_path and Path(tmp_spec_path).exists():
            Path(tmp_spec_path).unlink(missing_ok=True)


def _create_guided(args) -> int:
    """--guided 路径：生成规约骨架，提示填充后再用 --spec 渲染。"""
    if args.interactive:
        skill_name = args.name or input("Skill 名称（小写、短横线分隔）: ").strip()
        description = args.description or input("描述: ").strip()
    else:
        if not args.name or not args.description:
            print("❌ --guided 非交互模式下需同时提供 --name 和 --description")
            return 1
        skill_name = args.name
        description = args.description

    params = {
        'name': skill_name,
        'description': description,
        'version': getattr(args, 'version', '1.0.0') or '1.0.0',
        'author': getattr(args, 'author', None),
        'tags': getattr(args, 'tags', None),
        'output': getattr(args, 'output', None),
    }

    raw_output = params.get('output')
    output_dir = Path(raw_output).expanduser().resolve() if raw_output else get_skills_temp_dir()

    normalized_name = str(skill_name).lower().replace(' ', '-')
    skill_dir = output_dir / normalized_name
    spec_path = skill_dir / SPEC_FILENAME

    if spec_path.exists():
        print(f"❌ 规约文件已存在：{spec_path}")
        print("   如需重新生成，请先删除已有文件或使用其他输出目录")
        return 1

    skill_dir.mkdir(parents=True, exist_ok=True)

    spec = generate_spec_skeleton(params)
    save_spec(spec, spec_path)

    print(f"📝 规约文件已生成：{spec_path}")
    print("   请填充 purpose / capabilities / commands / error_handling 各字段")
    print(f"   填充完成后运行：python run.py create --spec {spec_path}")
    print()
    print("💡 提示：可运行 `python run.py examples` 查看内置参考样例。")
    return 0


def _create_from_spec(args) -> int:
    """--spec 路径：从已有规约文件创建 Skill。"""
    spec_path = Path(args.spec).resolve()

    if getattr(args, 'interactive', False):
        print("⚠️  --spec 模式下 --interactive 无效（参数已从规约文件加载）")

    try:
        spec = load_spec(spec_path)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1
    except (ValueError, Exception) as e:
        print(f"❌ 规约加载失败：{e}")
        return 1

    errors, warnings = validate_spec(spec)

    for e in errors:
        print(f"  ❌ {e}")
    for w in warnings:
        print(f"  ⚠️  {w}")

    strict = getattr(args, 'strict', False)
    if strict and (errors or warnings):
        print("规约验证未通过（--strict 模式）")
        return 1

    similar, _ = find_similar_example(spec_data=spec)
    if similar:
        print(f"💡 建议：你的 Skill 设计与内置样例 \"{similar}\" 相似。")
        print(f"   运行 `python run.py examples --show {similar}` 查看参考实现。")

    variables = spec_to_template_vars(spec)
    params = {
        'name': variables.get('name', ''),
        'description': variables.get('description', ''),
        'version': variables.get('version', '1.0.0'),
        'author': variables.get('author', 'OpenClaw Assistant'),
        'tags': variables.get('tags', []),
        'output': getattr(args, 'output', None),
    }

    skill_type = getattr(args, 'type', 'python')
    template_dir = getattr(args, 'template_dir', None)

    try:
        return create_skill(params, skill_type=skill_type,
                            template_dir=template_dir,
                            spec_path=spec_path,
                            spec_variables=variables)
    except ValueError as e:
        print(f"❌ {e}")
        return 1
