"""
spec 模块 — 规约核心引擎

提供 SkillSpec 数据结构、骨架生成、加载/保存、验证、模板变量转换。
"""
import yaml
from dataclasses import dataclass, field
from pathlib import Path

SPEC_VERSION = "1.0"
SPEC_FILENAME = ".skill-spec.yaml"

PLACEHOLDER_EXAMPLES = {
    "purpose.problem": "开发者在部署微服务后，缺少统一的方式来监控各服务 API 的健康状态，需要逐一手动检查，效率低且容易遗漏故障。",
    "purpose.target_user": "后端开发者和运维工程师",
    "purpose.scenarios": [
        "运维工程师在每日巡检时，用这个 skill 批量检查所有微服务端点的可用性",
        "开发者在上线新版本后，用这个 skill 验证各 API 的响应时间是否正常",
    ],
    "capabilities.name": "端点健康检查",
    "capabilities.description": "对指定 URL 发送 HTTP 请求，判断服务是否可用",
    "commands.name": "check",
    "commands.description": "检查指定 URL 的健康状态",
    "error_handling.scenario": "目标 URL 无法连接",
    "error_handling.cause": "网络不通或 URL 错误",
}

LENGTH_CONSTRAINTS = {
    "purpose.problem": (10, 200),
    "purpose.target_user": (2, 30),
    "purpose.scenarios.*": (10, 80),
    "capabilities.*.name": (2, 30),
    "capabilities.*.description": (5, 100),
    "capabilities.*.inputs": (3, 80),
    "capabilities.*.outputs": (3, 80),
    "commands.*.name": (1, 30),
    "commands.*.description": (3, 80),
    "error_handling.*.scenario": (3, 60),
}

# 架构定义的三种类型为 string/integer/boolean，float 为前向扩展
TYPE_MAPPING = {
    'string': 'str',
    'integer': 'int',
    'boolean': 'bool',
    'float': 'float',
}


@dataclass
class SkillSpec:
    """Skill 设计规约。"""
    spec_version: str = SPEC_VERSION
    meta: dict = field(default_factory=dict)
    purpose: dict = field(default_factory=dict)
    capabilities: list = field(default_factory=list)
    commands: list = field(default_factory=list)
    error_handling: list = field(default_factory=list)
    dependencies: dict = field(default_factory=dict)


def generate_spec_skeleton(params: dict) -> SkillSpec:
    """从基础参数生成规约骨架（purpose/capabilities 等为空壳）。"""
    name = str(params.get('name', ''))
    description = str(params.get('description', ''))
    version = str(params.get('version') or '1.0.0')
    author = str(params.get('author') or 'OpenClaw Assistant')
    raw_tags = params.get('tags') or []
    if isinstance(raw_tags, str):
        tags = [t.strip() for t in raw_tags.split(',') if t.strip()]
    else:
        tags = list(raw_tags)

    return SkillSpec(
        spec_version=SPEC_VERSION,
        meta={
            'name': name,
            'description': description,
            'version': version,
            'author': author,
            'tags': tags,
        },
        purpose={
            'problem': '',
            'target_user': '',
            'scenarios': ['', ''],
        },
        capabilities=[{
            'name': '',
            'description': '',
            'inputs': '',
            'outputs': '',
            'example': '',
        }],
        commands=[{
            'name': '',
            'description': '',
            'args': [{'name': '', 'description': ''}],
            'example': '',
            'expected_output': '',
        }],
        error_handling=[{
            'scenario': '',
            'cause': '',
            'solution': '',
        }],
        dependencies={
            'runtime': [],
            'external': [],
        },
    )


def _yaml_escape(value: str) -> str:
    """对 YAML 双引号字符串中的特殊字符进行转义。"""
    return value.replace('\\', '\\\\').replace('"', '\\"')


def save_spec(spec: SkillSpec, path: Path):
    """将规约写入 .skill-spec.yaml（含注释头和填写引导）。"""
    meta = spec.meta or {}
    purpose = spec.purpose or {}
    deps = spec.dependencies or {}

    tags_list = meta.get('tags', [])
    if tags_list:
        tags_str = '[' + ', '.join(f'"{_yaml_escape(str(t))}"' for t in tags_list) + ']'
    else:
        tags_str = '[]'

    scenarios = purpose.get('scenarios', ['', ''])
    scenarios_lines = []
    for s in scenarios:
        scenarios_lines.append(f'    - "{_yaml_escape(str(s))}"')
    scenarios_block = '\n'.join(scenarios_lines)

    caps = spec.capabilities or [{'name': '', 'description': '', 'inputs': '', 'outputs': '', 'example': ''}]
    caps_lines = []
    for c in caps:
        caps_lines.append(f'  - name: "{_yaml_escape(str(c.get("name", "")))}"')
        caps_lines.append(f'    description: "{_yaml_escape(str(c.get("description", "")))}"')
        caps_lines.append(f'    inputs: "{_yaml_escape(str(c.get("inputs", "")))}"')
        caps_lines.append(f'    outputs: "{_yaml_escape(str(c.get("outputs", "")))}"')
        caps_lines.append(f'    example: "{_yaml_escape(str(c.get("example", "")))}"')
    capabilities_block = '\n'.join(caps_lines)

    cmds = spec.commands or [{'name': '', 'description': '', 'args': [{'name': '', 'description': ''}], 'example': '', 'expected_output': ''}]
    cmds_lines = []
    for cmd in cmds:
        cmds_lines.append(f'  - name: "{_yaml_escape(str(cmd.get("name", "")))}"')
        cmds_lines.append(f'    description: "{_yaml_escape(str(cmd.get("description", "")))}"')
        cmds_lines.append('    args:')
        for arg in cmd.get('args', [{'name': '', 'description': ''}]):
            cmds_lines.append(f'      - name: "{_yaml_escape(str(arg.get("name", "")))}"')
            cmds_lines.append(f'        description: "{_yaml_escape(str(arg.get("description", "")))}"')
        cmds_lines.append(f'    example: "{_yaml_escape(str(cmd.get("example", "")))}"')
        cmds_lines.append(f'    expected_output: "{_yaml_escape(str(cmd.get("expected_output", "")))}"')
    commands_block = '\n'.join(cmds_lines)

    errs = spec.error_handling or [{'scenario': '', 'cause': '', 'solution': ''}]
    err_lines = []
    for eh in errs:
        err_lines.append(f'  - scenario: "{_yaml_escape(str(eh.get("scenario", "")))}"')
        err_lines.append(f'    cause: "{_yaml_escape(str(eh.get("cause", "")))}"')
        err_lines.append(f'    solution: "{_yaml_escape(str(eh.get("solution", "")))}"')
    error_handling_block = '\n'.join(err_lines)

    runtime = deps.get('runtime', [])
    external = deps.get('external', [])
    runtime_str = '[' + ', '.join(f'"{_yaml_escape(str(r))}"' for r in runtime) + ']' if runtime else '[]'
    external_str = '[' + ', '.join(f'"{_yaml_escape(str(e))}"' for e in external) + ']' if external else '[]'

    content = _SPEC_TEMPLATE.format(
        spec_version=_yaml_escape(spec.spec_version),
        name=_yaml_escape(str(meta.get('name', ''))),
        description=_yaml_escape(str(meta.get('description', ''))),
        version=_yaml_escape(str(meta.get('version', '1.0.0'))),
        author=_yaml_escape(str(meta.get('author', 'OpenClaw Assistant'))),
        tags=tags_str,
        problem=_yaml_escape(str(purpose.get('problem', ''))),
        target_user=_yaml_escape(str(purpose.get('target_user', ''))),
        scenarios_block=scenarios_block,
        capabilities_block=capabilities_block,
        commands_block=commands_block,
        error_handling_block=error_handling_block,
        runtime=runtime_str,
        external=external_str,
    )

    Path(path).write_text(content, encoding='utf-8')


_SPEC_TEMPLATE = '''\
spec_version: "{spec_version}"

# ============================================================
# 基础信息（由命令自动填入）
# ============================================================
meta:
  name: "{name}"
  description: "{description}"
  version: "{version}"
  author: "{author}"
  tags: {tags}

# ============================================================
# 以下内容需要你来填写。
# 每个字段都有 [指令]、[好的示例]、[差的示例]。
# 请参考"好的示例"的格式和详细程度来填写。
# ============================================================

purpose:
  # [指令] 用 1-2 句话描述这个 skill 要解决的具体问题。说清楚：谁遇到了什么困难。
  # [好的示例] "开发者在部署微服务后，缺少统一的方式来监控各服务 API 的健康状态..."
  # [差的示例] "监控 API" ← 太笼统，没有说明谁、什么情况、什么痛点
  problem: "{problem}"

  # [指令] 用 5-15 个字描述谁会使用这个 skill。
  # [好的示例] "后端开发者和运维工程师"
  # [差的示例] "用户" ← 太模糊，不知道是什么类型的用户
  target_user: "{target_user}"

  # [指令] 列举 2-3 个具体使用场景。每条格式："谁 + 在什么情况下 + 用这个 skill 做什么"，每条 15-40 字。
  # [好的示例]
  #   - "运维工程师在每日巡检时，用这个 skill 批量检查所有微服务端点的可用性"
  #   - "开发者在上线新版本后，用这个 skill 验证各 API 的响应时间是否正常"
  # [差的示例]
  #   - "监控服务" ← 没有说明谁、什么时候、做什么
  #   - "场景1" ← 占位符，无信息量
  scenarios:
{scenarios_block}

capabilities:
  # [指令] 列举 1-3 个这个 skill 的核心能力。每个能力用 "输入→处理→输出" 的结构描述。
  # [好的示例]
  #   - name: "端点健康检查"
  #     description: "对指定 URL 发送 HTTP 请求，判断服务是否可用"
  #     inputs: "一个或多个 API URL"
  #     outputs: "每个 URL 的状态码、响应时间、是否可用"
  #     example: "输入 https://api.example.com/health → 输出 '200 OK, 45ms, 可用'"
  # [差的示例]
  #   - name: "能力1"          ← 占位符
  #     description: "功能点1"  ← 占位符
{capabilities_block}

commands:
  # [指令] 列举这个 skill 需要的子命令。每个命令对应一个具体操作。至少 1 个。
  # [好的示例]
  #   - name: "check"
  #     description: "检查指定 URL 的健康状态"
  #     args:
  #       - name: "--url"
  #         description: "要检查的 API 端点 URL"
  #     example: "python run.py check --url https://api.example.com/health"
  #     expected_output: "✅ https://api.example.com/health — 200 OK (45ms)"
  # [差的示例]
  #   - name: "子命令"        ← 没有具体名称
  #     description: "命令的作用" ← 没有说明具体做什么
{commands_block}

error_handling:
  # [指令] 列举 1-3 个用户可能遇到的错误。格式：什么情况会出错 → 为什么 → 怎么解决。
  # [好的示例]
  #   - scenario: "目标 URL 无法连接"
  #     cause: "网络不通或 URL 错误"
  #     solution: "检查网络连接，确认 URL 是否正确且服务已启动"
  # [差的示例]
  #   - scenario: "错误1"  ← 占位符
  #     cause: "原因1"     ← 占位符
{error_handling_block}

dependencies:
  # [指令] 列出运行时需要的 Python 包（如无则留空列表）。
  # [好的示例] runtime: ["requests", "pyyaml"]
  # [差的示例] runtime: ["所有包"] ← 不具体，无法用于 pip install
  runtime: {runtime}
  # [指令] 列出需要的外部工具或服务（如无则留空列表）。
  # [好的示例] external: ["docker", "redis-server"]
  # [差的示例] external: ["系统工具"] ← 不具体，无法判断是否已安装
  external: {external}
'''


def load_spec(path: Path) -> SkillSpec:
    """从 .skill-spec.yaml 加载规约。

    schema 冻结兼容：忽略未知字段，缺失字段使用默认值。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"规约文件不存在：{path}")

    raw = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        raise ValueError("规约文件格式错误：顶层应为字典")

    return SkillSpec(
        spec_version=str(raw.get('spec_version', SPEC_VERSION)),
        meta=raw.get('meta', {}),
        purpose=raw.get('purpose', {}),
        capabilities=raw.get('capabilities', []),
        commands=raw.get('commands', []),
        error_handling=raw.get('error_handling', []),
        dependencies=raw.get('dependencies', {}),
    )


def validate_spec(spec: SkillSpec) -> tuple[list[str], list[str]]:
    """验证规约完整性，返回 (errors, warnings)。"""
    errors: list[str] = []
    warnings: list[str] = []

    _check_non_empty(spec, errors)
    _check_not_placeholder(spec, errors)
    _check_length(spec, warnings)

    problem = (spec.purpose or {}).get('problem', '')
    desc = (spec.meta or {}).get('description', '')
    if problem and desc and problem.strip() == desc.strip():
        warnings.append("purpose.problem 与 meta.description 完全相同（应是扩展而非复制）")

    return errors, warnings


def _check_non_empty(spec: SkillSpec, errors: list[str]):
    """字段非空检查（error 级别）。"""
    purpose = spec.purpose or {}

    if not str(purpose.get('problem', '')).strip():
        errors.append("purpose.problem 不能为空")
    if not str(purpose.get('target_user', '')).strip():
        errors.append("purpose.target_user 不能为空")

    scenarios = purpose.get('scenarios', [])
    if not scenarios or not any(str(s).strip() for s in scenarios):
        errors.append("purpose.scenarios 至少需要 1 个非空场景")

    caps = spec.capabilities or []
    if not caps or not any(str(c.get('name', '')).strip() for c in caps if isinstance(c, dict)):
        errors.append("capabilities 至少需要 1 个能力的 name 非空")
    if not caps or not any(str(c.get('description', '')).strip() for c in caps if isinstance(c, dict)):
        errors.append("capabilities 至少需要 1 个能力的 description 非空")

    cmds = spec.commands or []
    if not cmds or not any(str(c.get('name', '')).strip() for c in cmds if isinstance(c, dict)):
        errors.append("commands 至少需要 1 个命令的 name 非空")
    if not cmds or not any(str(c.get('description', '')).strip() for c in cmds if isinstance(c, dict)):
        errors.append("commands 至少需要 1 个命令的 description 非空")

    errs = spec.error_handling or []
    if not errs or not any(str(e.get('scenario', '')).strip() for e in errs if isinstance(e, dict)):
        errors.append("error_handling 至少需要 1 个错误场景的 scenario 非空")


def _check_not_placeholder(spec: SkillSpec, errors: list[str]):
    """非占位符复制检查（error 级别）。"""
    purpose = spec.purpose or {}

    _match_placeholder(purpose.get('problem', ''), 'purpose.problem', errors)
    _match_placeholder(purpose.get('target_user', ''), 'purpose.target_user', errors)

    for s in purpose.get('scenarios', []):
        if isinstance(s, str) and s.strip():
            for example in PLACEHOLDER_EXAMPLES.get('purpose.scenarios', []):
                if s.strip() == example.strip():
                    errors.append(f"purpose.scenarios 中 \"{s[:30]}...\" 是示例原文的复制")
                    break

    for cap in (spec.capabilities or []):
        if isinstance(cap, dict):
            _match_placeholder(cap.get('name', ''), 'capabilities.name', errors)
            _match_placeholder(cap.get('description', ''), 'capabilities.description', errors)

    for cmd in (spec.commands or []):
        if isinstance(cmd, dict):
            _match_placeholder(cmd.get('name', ''), 'commands.name', errors)
            _match_placeholder(cmd.get('description', ''), 'commands.description', errors)

    for eh in (spec.error_handling or []):
        if isinstance(eh, dict):
            _match_placeholder(eh.get('scenario', ''), 'error_handling.scenario', errors)
            _match_placeholder(eh.get('cause', ''), 'error_handling.cause', errors)


def _match_placeholder(value, key: str, errors: list[str]):
    """检查单个值是否为占位符示例的复制。"""
    if not value or not str(value).strip():
        return
    example = PLACEHOLDER_EXAMPLES.get(key)
    if example is None:
        return
    if isinstance(example, str) and str(value).strip() == example.strip():
        errors.append(f"{key} 是示例原文的复制（请替换为你自己的内容）")


def _check_length(spec: SkillSpec, warnings: list[str]):
    """长度合规检查（warning 级别）。"""
    purpose = spec.purpose or {}

    _check_field_length(purpose.get('problem', ''), 'purpose.problem', warnings)
    _check_field_length(purpose.get('target_user', ''), 'purpose.target_user', warnings)

    for s in purpose.get('scenarios', []):
        if str(s).strip():
            _check_field_length(s, 'purpose.scenarios.*', warnings)

    for cap in (spec.capabilities or []):
        if isinstance(cap, dict):
            for fld in ('name', 'description', 'inputs', 'outputs'):
                val = cap.get(fld, '')
                if str(val).strip():
                    _check_field_length(val, f'capabilities.*.{fld}', warnings)

    for cmd in (spec.commands or []):
        if isinstance(cmd, dict):
            for fld in ('name', 'description'):
                val = cmd.get(fld, '')
                if str(val).strip():
                    _check_field_length(val, f'commands.*.{fld}', warnings)

    for eh in (spec.error_handling or []):
        if isinstance(eh, dict):
            val = eh.get('scenario', '')
            if str(val).strip():
                _check_field_length(val, 'error_handling.*.scenario', warnings)


def _check_field_length(value, constraint_key: str, warnings: list[str]):
    """检查单个字段长度是否在约束范围内。"""
    constraint = LENGTH_CONSTRAINTS.get(constraint_key)
    if constraint is None:
        return
    min_len, max_len = constraint
    length = len(str(value).strip())
    if length < min_len:
        warnings.append(f"{constraint_key} 长度 {length} 低于建议最小值 {min_len}")
    elif length > max_len:
        warnings.append(f"{constraint_key} 长度 {length} 超过建议最大值 {max_len}")


def spec_to_template_vars(spec: SkillSpec) -> dict:
    """将规约转换为模板变量字典。

    注意：此函数会就地修改 spec.commands 中的 args 字典
    （添加 type_python / argparse_action / required 字段）。
    """
    meta = spec.meta or {}
    variables = {
        'name': meta.get('name', ''),
        'description': meta.get('description', ''),
        'version': meta.get('version', '1.0.0'),
        'author': meta.get('author', 'OpenClaw Assistant'),
        'tags': meta.get('tags', []),
    }

    for cmd in (spec.commands or []):
        cmd['name_snake'] = cmd.get('name', '').replace('-', '_')
        for arg in cmd.get('args', []):
            raw_type = arg.get('type', 'string')
            arg['type_python'] = TYPE_MAPPING.get(raw_type, 'str')
            if raw_type == 'boolean':
                arg['argparse_action'] = 'store_true'
                arg['required'] = False
            else:
                arg['argparse_action'] = None
                if 'required' not in arg:
                    arg['required'] = True
            name = arg.get('name', '')
            if name and not name.startswith('--'):
                arg['arg_flag'] = f'--{name}'
            else:
                arg['arg_flag'] = name

    variables['purpose'] = spec.purpose or {}
    variables['capabilities'] = spec.capabilities or []
    variables['commands'] = spec.commands or []
    variables['error_handling'] = spec.error_handling or []
    variables['dependencies'] = spec.dependencies or {}

    variables['dispatch_entries'] = [
        {'name': cmd.get('name', ''), 'name_snake': cmd.get('name_snake', '')}
        for cmd in (spec.commands or [])
        if cmd.get('name', '').strip()
    ]

    return variables
