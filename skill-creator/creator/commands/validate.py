"""
validate 命令 — 验证 skill 并评分（支持单路径、多路径、递归、JSON 输出）
"""
import json
from pathlib import Path

from creator.commands.create import validate_skill
from creator.scorer import SkillScorer


def _resolve_paths(args) -> tuple[list[Path], list[Path]]:
    """根据 args.paths 和 --recursive 解析最终要验证的 skill 目录列表。

    Returns:
        (valid_paths, missing_paths)
    """
    raw_paths = getattr(args, 'paths', None) or [getattr(args, 'path', '.')]
    recursive = getattr(args, 'recursive', False)

    result = []
    missing = []
    for p_str in raw_paths:
        p = Path(p_str).resolve()
        if not p.exists():
            missing.append(p)
            continue
        if recursive and p.is_dir():
            for child in sorted(p.iterdir()):
                if child.is_dir() and (child / 'SKILL.md').exists():
                    result.append(child)
        else:
            result.append(p)
    return result, missing


def _validate_one(skill_path: Path, no_security: bool) -> dict:
    """验证单个 skill，返回结构化结果。"""
    record = {
        'name': skill_path.name,
        'path': str(skill_path),
        'errors': [],
        'warnings': [],
        'score': None,
        'scores': {},
        'security': [],
    }

    if not skill_path.exists():
        record['errors'].append(f'路径不存在：{skill_path}')
        return record
    if not skill_path.is_dir():
        record['errors'].append(f'不是目录：{skill_path}')
        return record

    errors, warnings = validate_skill(skill_path)
    record['errors'] = list(errors)
    record['warnings'] = list(warnings)

    if not no_security:
        from creator.security import scan_directory
        findings = scan_directory(skill_path)
        for f in findings:
            loc = f"{f.file}:{f.line}" if f.line is not None else f.file
            record['security'].append({
                'rule_id': f.rule_id, 'location': loc, 'message': f.message,
            })

    if not errors:
        scorer = SkillScorer(skill_path)
        scores = scorer.score()
        record['score'] = scores.get('total', 0)
        record['scores'] = scores

    return record


def _print_single(record: dict):
    """以可读格式输出单个 skill 的验证结果。"""
    print(f"🔍 验证 skill：{record['path']}")
    if record['errors']:
        print("\n❌ 错误：")
        for e in record['errors']:
            print(f"  {e}")
    if record['warnings']:
        print("\n⚠️  警告：")
        for w in record['warnings']:
            print(f"  {w}")
    if record['security']:
        print("\n🔒 安全扫描：")
        for s in record['security']:
            print(f"  ⚠️  [security] [{s['rule_id']}] {s['location']}")
            print(f"     {s['message']}")
    if record['errors']:
        return

    scorer = SkillScorer(Path(record['path']))
    scorer.score()
    print(f"\n📊 正在进行质量评分...")
    print(scorer.generate_report())
    print("✅ Skill 验证通过！")


def _print_batch_summary(records: list[dict]):
    """输出批量验证的汇总表。"""
    print("\n" + "=" * 60)
    print("📊 批量验证汇总")
    print("=" * 60)

    passed = sum(1 for r in records if not r['errors'])
    failed = len(records) - passed

    for r in records:
        status = "✅" if not r['errors'] else "❌"
        score_str = f"{r['score']}分" if r['score'] is not None else "N/A"
        errs = len(r['errors'])
        warns = len(r['warnings'])
        print(f"  {status} {r['name']:<30} {score_str:>8}  错误:{errs}  警告:{warns}")

    print(f"\n合计：{len(records)} 个 skill，{passed} 通过，{failed} 失败")


def main_validate(args):
    paths, missing = _resolve_paths(args)

    no_security = getattr(args, 'no_security', False)
    use_json = getattr(args, 'json', False)

    records = [_validate_one(p, no_security) for p in paths]

    for m in missing:
        records.append({
            'name': m.name,
            'path': str(m),
            'errors': [f'路径不存在：{m}'],
            'warnings': [],
            'score': None,
            'scores': {},
            'security': [],
        })

    if not records:
        print("❌ 没有找到可验证的 skill 目录")
        return 1

    if use_json:
        output = {'skills': []}
        for r in records:
            output['skills'].append({
                'name': r['name'],
                'path': r['path'],
                'score': r['score'],
                'errors': r['errors'],
                'warnings': r['warnings'],
            })
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif len(records) == 1:
        _print_single(records[0])
    else:
        for i, record in enumerate(records):
            if i > 0:
                print("\n" + "-" * 60 + "\n")
            _print_single(record)
        _print_batch_summary(records)

    has_errors = any(r['errors'] for r in records)
    return 1 if has_errors else 0
