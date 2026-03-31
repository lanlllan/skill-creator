"""
security 模块 — 安全扫描核心引擎

提供规则定义、目录扫描、报告格式化三项能力。
规则表驱动（list of dict），支持扩展和测试。
"""
import json
import os
import re
from dataclasses import dataclass, asdict
from fnmatch import fnmatch
from pathlib import Path

MAX_FILE_SIZE = 1_048_576  # 1MB，超过此大小的文件跳过内容扫描

SKIP_DIRS = frozenset({
    '__pycache__', '.git', '.pytest_cache', 'node_modules', '.venv', 'venv',
})

SEVERITY_ORDER = {'error': 0, 'warning': 1, 'info': 2}


@dataclass
class ScanFinding:
    rule_id: str
    severity: str
    file: str
    line: int | None
    message: str
    matched: str


DEFAULT_RULES: list[dict] = [
    {
        'rule_id': 'SECRET_API_KEY',
        'severity': 'error',
        'message': '检测到疑似 API 密钥',
        'type': 'content',
        'pattern': r'(?:sk-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16}|ghp_[a-zA-Z0-9]{36}|glpat-[a-zA-Z0-9\-]{20,})',
    },
    {
        'rule_id': 'SECRET_ASSIGNMENT',
        'severity': 'warning',
        'message': '检测到疑似硬编码凭证赋值',
        'type': 'content',
        'pattern': r'''(?:api_key|secret|password|token)\s*=\s*["'][^"']{8,}["']''',
    },
    {
        'rule_id': 'SENSITIVE_FILE',
        'severity': 'error',
        'message': '敏感文件不应包含在 Skill 中',
        'type': 'filename',
        'pattern': '.env|credentials.json|*.pem|*.key',
    },
    {
        'rule_id': 'DANGEROUS_EVAL',
        'severity': 'warning',
        'message': '检测到动态执行调用',
        'type': 'content',
        'pattern': r'(?:eval|exec|__import__)\s*\(',
    },
    {
        'rule_id': 'DANGEROUS_SHELL_TRUE',
        'severity': 'warning',
        'message': '检测到 shell=True 调用',
        'type': 'content',
        'pattern': r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
    },
    {
        'rule_id': 'DANGEROUS_OS_SYSTEM',
        'severity': 'warning',
        'message': '检测到 os.system() 调用',
        'type': 'content',
        'pattern': r'os\.system\s*\(',
    },
]


def _is_binary(file_path: Path, sample_size: int = 8192) -> bool:
    """启发式检测：读取前 sample_size 字节，含 NUL 则判定为二进制。"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(sample_size)
        return b'\x00' in chunk
    except (OSError, PermissionError):
        return True


def _match_filename(name: str, pattern: str) -> bool:
    """pattern 按 | 分割后逐个 fnmatch，任一匹配即返回 True。"""
    return any(fnmatch(name, p.strip()) for p in pattern.split('|'))


def _scan_file_names(
    file_path: Path, root: Path, rules: list[dict],
) -> list[ScanFinding]:
    findings = []
    rel_path = str(file_path.relative_to(root)).replace('\\', '/')
    name = file_path.name

    for rule in rules:
        if rule['type'] != 'filename':
            continue
        if _match_filename(name, rule['pattern']):
            findings.append(ScanFinding(
                rule_id=rule['rule_id'],
                severity=rule['severity'],
                file=rel_path,
                line=None,
                message=rule['message'],
                matched=name,
            ))
    return findings


def _scan_file_content(
    file_path: Path, root: Path, rules: list[dict],
) -> list[ScanFinding]:
    findings = []
    rel_path = str(file_path.relative_to(root)).replace('\\', '/')
    content_rules = [r for r in rules if r['type'] == 'content']
    if not content_rules:
        return findings

    compiled = [(r, re.compile(r['pattern'])) for r in content_rules]

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line_text in enumerate(f, start=1):
                for rule, regex in compiled:
                    m = regex.search(line_text)
                    if m:
                        findings.append(ScanFinding(
                            rule_id=rule['rule_id'],
                            severity=rule['severity'],
                            file=rel_path,
                            line=line_num,
                            message=rule['message'],
                            matched=m.group(0),
                        ))
    except (OSError, PermissionError):
        pass

    return findings


def scan_directory(
    path: Path, rules: list[dict] | None = None,
) -> list[ScanFinding]:
    """扫描目录中所有文本文件，检测安全风险模式。

    Args:
        path: 扫描根目录（绝对路径）
        rules: 规则表，None 时使用 DEFAULT_RULES

    Returns:
        扫描发现列表，按 severity 排序（error 在前）
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"路径不存在：{path}")
    if not path.is_dir():
        raise NotADirectoryError(f"不是目录：{path}")

    if rules is None:
        rules = DEFAULT_RULES

    findings: list[ScanFinding] = []

    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            file_path = Path(dirpath) / fname

            findings.extend(_scan_file_names(file_path, path, rules))

            try:
                file_size = file_path.stat().st_size
            except OSError:
                continue

            if file_size > MAX_FILE_SIZE:
                rel = str(file_path.relative_to(path)).replace('\\', '/')
                findings.append(ScanFinding(
                    rule_id='LARGE_FILE_SKIPPED',
                    severity='info',
                    file=rel,
                    line=None,
                    message=f'文件大小 {file_size} 字节超过阈值 {MAX_FILE_SIZE}，已跳过内容扫描',
                    matched=fname,
                ))
                continue

            if _is_binary(file_path):
                continue

            findings.extend(_scan_file_content(file_path, path, rules))

    findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 99))
    return findings


def _sanitize_matched(matched: str, rule_id: str, max_len: int = 40) -> str:
    """脱敏处理：密钥类只显示前缀 + ***，其余截断。"""
    if rule_id == 'SECRET_API_KEY':
        prefix_len = min(6, len(matched))
        return matched[:prefix_len] + '***'
    if len(matched) > max_len:
        return matched[:max_len] + '...'
    return matched


def format_report(
    findings: list[ScanFinding], json_output: bool = False,
) -> str:
    """格式化扫描报告。

    文本模式：emoji + [rule_id] + 路径(:行号) + 描述
    JSON 模式：序列化为 list[dict]
    """
    if json_output:
        return json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2)

    if not findings:
        return '✅ 无安全发现'

    severity_emoji = {'error': '🔴', 'warning': '🟡', 'info': 'ℹ️'}
    lines = []

    for f in findings:
        emoji = severity_emoji.get(f.severity, '❓')
        loc = f"{f.file}:{f.line}" if f.line is not None else f.file
        sanitized = _sanitize_matched(f.matched, f.rule_id)
        lines.append(f"{emoji} [{f.rule_id}] {loc}")
        lines.append(f"   {f.message}：{sanitized}")
        lines.append('')

    return '\n'.join(lines).rstrip()
