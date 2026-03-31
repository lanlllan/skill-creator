"""
packager 模块 — 打包核心引擎

提供 .skillignore 解析、文件收集、zip 创建、SHA256 计算四项能力。
"""
import hashlib
import zipfile
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

ALWAYS_EXCLUDE_DIRS = frozenset({
    '.git', '__pycache__', '.pytest_cache', 'node_modules',
    '.venv', 'venv', '.mypy_cache', '.tox',
})

ALWAYS_EXCLUDE_PATTERNS = frozenset({
    '.*',
    '*.pyc',
    '*.pyo',
    '*.skill',
})

DOTFILE_WHITELIST = frozenset({
    '.skill-spec.yaml',
})

MAX_PACKAGE_SIZE = 10 * 1024 * 1024  # 10MB


@dataclass
class PackageResult:
    """打包结果。"""
    success: bool = True
    package_path: Path | None = None
    sha256: str = ""
    file_count: int = 0
    package_size: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def load_skillignore(skill_dir: Path) -> list[str]:
    """解析 .skillignore 文件，返回 fnmatch 模式列表。

    语法规则：
      - # 开头为注释
      - 空行忽略
      - 支持 fnmatch 基础语法（*, ?, [seq]）
      - 不支持 ! 反排除和 ** 递归匹配
    """
    ignore_file = skill_dir / '.skillignore'
    if not ignore_file.exists():
        return []
    try:
        text = ignore_file.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return []
    patterns = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        patterns.append(line)
    return patterns


def _is_excluded(rel_path: str, patterns: list[str]) -> bool:
    """检查相对路径是否匹配任一排除模式。

    支持三种匹配方式：
      1. 文件名匹配：pattern 直接与文件名比较（如 *.log 匹配 debug.log）
      2. 完整路径匹配：pattern 与完整相对路径比较
      3. 目录模式：pattern 去除尾部 / 后，与路径中任一目录组件比较
         （如 tests/ 匹配 tests/sample.txt）
    """
    p = Path(rel_path)
    name = p.name
    parts = p.parts

    for pattern in patterns:
        if fnmatch(name, pattern) or fnmatch(rel_path, pattern):
            return True
        stripped = pattern.rstrip('/')
        if stripped != pattern:
            if any(fnmatch(part, stripped) for part in parts[:-1]):
                return True
        else:
            if any(fnmatch(part, pattern) for part in parts[:-1]):
                return True
    return False


def collect_files(skill_dir: Path, ignore_patterns: list[str]) -> list[Path]:
    """收集待打包文件列表。

    排除顺序：
      1. ALWAYS_EXCLUDE_DIRS（系统目录）
      2. ALWAYS_EXCLUDE_PATTERNS（dotfiles、*.pyc、*.skill 等）
      3. ignore_patterns（用户 .skillignore）
      4. .skillignore 文件自身

    Returns:
        相对路径列表（相对于 skill_dir），已排序。
    """
    result = []
    for f in skill_dir.rglob('*'):
        if not f.is_file():
            continue
        rel = f.relative_to(skill_dir)
        parts = rel.parts

        if any(p in ALWAYS_EXCLUDE_DIRS for p in parts):
            continue

        if any(fnmatch(f.name, pat) for pat in ALWAYS_EXCLUDE_PATTERNS):
            if f.name not in DOTFILE_WHITELIST:
                continue

        if any(part.startswith('.') for part in parts[:-1]):
            continue

        if f.name == '.skillignore':
            continue

        rel_posix = rel.as_posix()
        if _is_excluded(rel_posix, ignore_patterns):
            continue

        result.append(rel)
    return sorted(result)


def compute_sha256(file_path: Path) -> str:
    """计算文件 SHA256 校验和，返回十六进制字符串。"""
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _create_zip(skill_dir: Path, files: list[Path], output_path: Path) -> int:
    """创建 zip 包，返回包大小（字节）。"""
    skill_name = skill_dir.name
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            src = skill_dir / rel
            arcname = f"{skill_name}/{rel.as_posix()}"
            zf.write(src, arcname)
    return output_path.stat().st_size


def create_package(skill_dir: Path,
                   output_dir: Path | None = None,
                   force: bool = False) -> PackageResult:
    """打包主函数。

    流程：路径验证 → validate + scan 前置检查 → 加载 .skillignore
    → 收集文件 → 创建 zip → 包大小检查 → SHA256 计算

    validate_skill 导入自 creator.commands.create（已确认无循环依赖：
    create.py 不导入 packager.py）。
    """
    result = PackageResult()
    skill_dir = Path(skill_dir).resolve()

    if not skill_dir.exists():
        result.success = False
        result.errors.append(f"路径不存在：{skill_dir}")
        return result
    if not skill_dir.is_dir():
        result.success = False
        result.errors.append(f"不是目录：{skill_dir}")
        return result

    from creator.commands.create import validate_skill
    from creator.security import scan_directory, ScanFinding

    val_errors, val_warnings = validate_skill(skill_dir)
    result.warnings.extend(val_warnings)

    try:
        findings = scan_directory(skill_dir)
    except Exception as e:
        result.errors.append(f"安全扫描异常：{e}")
        if not force:
            result.success = False
            return result
        findings = []

    scan_errors = [f for f in findings if f.severity == 'error']
    scan_warnings = [f for f in findings if f.severity != 'error']
    result.warnings.extend(f"[{f.rule_id}] {f.file}: {f.message}" for f in scan_warnings)

    blocking_errors = val_errors + [
        f"[{f.rule_id}] {f.file}: {f.message}" for f in scan_errors
    ]

    if blocking_errors and not force:
        result.success = False
        result.errors.extend(blocking_errors)
        return result
    elif blocking_errors:
        result.errors.extend(blocking_errors)

    ignore_patterns = load_skillignore(skill_dir)
    files = collect_files(skill_dir, ignore_patterns)

    if not files:
        result.success = False
        result.errors.append("无可打包文件")
        return result

    result.file_count = len(files)

    if output_dir is None:
        output_dir = skill_dir.parent
    else:
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

    package_name = f"{skill_dir.name}.skill"
    package_path = output_dir / package_name

    try:
        pkg_size = _create_zip(skill_dir, files, package_path)
    except PermissionError:
        result.success = False
        result.errors.append(f"无写入权限：{output_dir}")
        return result
    except Exception as e:
        result.success = False
        result.errors.append(f"创建 zip 失败：{e}")
        return result

    result.package_path = package_path
    result.package_size = pkg_size

    if pkg_size > MAX_PACKAGE_SIZE:
        size_mb = pkg_size / (1024 * 1024)
        result.warnings.append(f"包大小 {size_mb:.1f} MB 超过推荐上限 10 MB")

    result.sha256 = compute_sha256(package_path)
    return result
