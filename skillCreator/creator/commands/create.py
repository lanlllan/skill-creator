"""
create 命令 — 创建新 skill
"""
import os
import yaml
from datetime import datetime
from pathlib import Path

from creator.paths import get_skills_temp_dir
from creator.validators import validate_skill_name, validate_version
from creator.templates import generate_files
from creator.scorer import SkillScorer
from creator.state_manager import add_skill

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

    if not run_py.exists():
        errors.append("❌ run.py 不存在")
    elif not os.access(run_py, os.X_OK):
        warnings.append("⚠️  run.py 缺少可执行权限（建议 chmod +x）")

    return errors, warnings


def create_skill(params: dict, _out: dict = None) -> int:
    """纯函数：从 params dict 创建 skill，返回退出码（0=成功，非0=失败）。

    params 字段契约（唯一来源，禁止双口径）：
      name        str            必需
      description str            必需
      version     str            可选，默认 "1.0.0"
      author      str            可选，默认 "OpenClaw Assistant"
      tags        list[str]|str  可选，默认 []（支持逗号分隔字符串）
      output      str|None       可选，None 时使用 get_skills_temp_dir()

    可选参数 _out：dict，供调用方获取额外输出（score、skill_name、failure_reason）。
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

        print("📝 生成文件...")
        generate_files(skill_dir, variables)

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


def main_create(args):
    """创建新 skill（CLI 适配层，负责交互式输入收集并构造 params dict）。"""
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

    try:
        return create_skill(params)
    except ValueError as e:
        print(f"❌ {e}")
        return 1
