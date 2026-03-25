"""
batch 命令 — 批量创建 skill（从 YAML 文件）
"""
import yaml
from pathlib import Path

from creator.paths import get_skills_temp_dir
from creator.validators import validate_skill_name, validate_version
from creator.commands.create import create_skill


def main_batch(args):
    """批量创建 skill（从 YAML 文件）"""
    yaml_path = Path(args.file)

    if not yaml_path.exists():
        print(f"❌ 文件不存在：{yaml_path}")
        return 2

    try:
        with open(yaml_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ YAML 解析错误（请检查语法）：{e}")
        return 2

    if not isinstance(data, dict) or 'skills' not in data:
        print("❌ YAML 格式错误：顶层必须包含 'skills' 字段")
        return 2

    skills_list = data['skills']
    if not isinstance(skills_list, list) or len(skills_list) == 0:
        print("❌ 'skills' 字段必须为非空数组")
        return 2

    results = {'success': [], 'failure': [], 'skip': []}
    seen_keys: set = set()  # (str(target_root), normalized_name)，允许同名不同目录

    for item in skills_list:
        if not isinstance(item, dict):
            results['failure'].append({'name': str(item), 'reason': '条目格式错误，非字典类型'})
            continue

        raw_output = item.get('output')
        target_root = Path(raw_output).expanduser().resolve() if raw_output else get_skills_temp_dir()

        name_raw = item.get('name')
        if name_raw is None:
            results['failure'].append({'name': '(null)', 'reason': 'name 字段为 null，必须为非空字符串'})
            continue
        raw_name = str(name_raw).strip()

        desc_raw = item.get('description')
        if desc_raw is None:
            results['failure'].append({'name': raw_name or '(无名称)', 'reason': 'description 字段为 null，必须为非空字符串'})
            continue

        normalized = raw_name.lower().replace(' ', '-')

        dedup_key = (str(target_root), normalized)
        if dedup_key in seen_keys:
            results['skip'].append({'name': raw_name or normalized, 'reason': '批内重复（同目录同名）'})
            continue

        if not raw_name:
            results['failure'].append({'name': '(无名称)', 'reason': '缺少必需字段 name'})
            continue
        if not str(desc_raw).strip():
            results['failure'].append({'name': raw_name, 'reason': 'description 不能为空字符串'})
            continue

        if not validate_skill_name(normalized):
            results['failure'].append({
                'name': raw_name,
                'reason': f'名称 "{normalized}" 不符合规范（应小写字母开头，仅含字母/数字/短横线）',
            })
            seen_keys.add(dedup_key)
            continue

        version_val = item.get('version')
        if version_val is not None:
            version_str = str(version_val).strip()
            if version_str and not validate_version(version_str):
                results['failure'].append({
                    'name': raw_name,
                    'reason': f'版本号 "{version_str}" 不符合语义化版本格式（应为 x.y.z）',
                })
                seen_keys.add(dedup_key)
                continue

        if (target_root / normalized).exists():
            results['skip'].append({'name': raw_name, 'reason': '目标目录已存在'})
            seen_keys.add(dedup_key)
            continue

        seen_keys.add(dedup_key)

        params = {
            'name': raw_name,
            'description': desc_raw,
            'version': item.get('version'),
            'author': item.get('author'),
            'tags': item.get('tags'),
            'output': raw_output,
        }

        print(f"\n{'─'*40}")
        print(f"▶ 创建：{raw_name}")
        print('─' * 40)

        result_info: dict = {}
        try:
            rc = create_skill(params, _out=result_info)
            if rc == 0:
                results['success'].append({
                    'name': result_info.get('skill_name', normalized),
                    'score': result_info.get('score'),
                })
            else:
                reason = result_info.get('failure_reason') or f'创建失败（退出码 {rc}）'
                results['failure'].append({'name': raw_name, 'reason': reason})
        except ValueError as e:
            results['failure'].append({'name': raw_name, 'reason': str(e)})
        except Exception as e:
            results['failure'].append({'name': raw_name, 'reason': f'未知异常：{e}'})

    total = len(skills_list)
    n_success = len(results['success'])
    n_failure = len(results['failure'])
    n_skip = len(results['skip'])

    print(f"\n{'='*40}")
    print("📊 批量创建报告")
    print('=' * 40)
    print(f"总计: {total} | 成功: {n_success} | 失败: {n_failure} | 跳过: {n_skip}")

    if results['success']:
        print("\n✅ 成功:")
        for s in results['success']:
            score_str = f" (评分: {s['score']}/100)" if s.get('score') is not None else ""
            print(f"  - {s['name']}{score_str}")

    if results['failure']:
        print("\n❌ 失败:")
        for f_item in results['failure']:
            print(f"  - {f_item['name']} (原因: {f_item['reason']})")

    if results['skip']:
        print("\n⏭️  跳过:")
        for s in results['skip']:
            print(f"  - {s['name']} (原因: {s['reason']})")

    return 1 if n_failure > 0 else 0
