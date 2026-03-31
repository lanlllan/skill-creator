"""
Phase 8 打包与分发 — 测试套件

覆盖维度（28 用例）：
  1. .skillignore 解析
  2. 文件收集与排除
  3. 前置检查（validate + scan）
  4. zip 包结构
  5. SHA256 校验和
  6. 包大小检测
  7. 输出目录
  8. CLI 集成
"""
import hashlib
import os
import subprocess
import sys
import zipfile

import pytest
from pathlib import Path

from helpers import SKILL_ROOT

from creator.packager import (
    load_skillignore,
    collect_files,
    compute_sha256,
    create_package,
    PackageResult,
    ALWAYS_EXCLUDE_DIRS,
    ALWAYS_EXCLUDE_PATTERNS,
)

VALID_SKILL_MD = """\
---
name: test-skill
description: A test skill
version: 1.0.0
---

## 概述

测试技能。

## 核心能力

- 功能 A

## 使用方式

运行 run.py。

## 示例

```bash
python run.py example
```
"""

VALID_RUN_PY = """\
#!/usr/bin/env python3
\"\"\"测试技能入口脚本。\"\"\"
import sys

def main():
    try:
        print("ok")
    except Exception as e:
        print(f"error: {e}")
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
"""

VALID_USAGE_MD = """\
# test-skill - 使用指南

## 快速开始

运行 `python run.py example`。
"""


def _make_valid_skill(base: Path, name: str = "test-skill") -> Path:
    """在 base 下创建一个可通过 validate + scan 的合法 skill 目录。"""
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD, encoding="utf-8")
    (skill_dir / "run.py").write_text(VALID_RUN_PY, encoding="utf-8")
    (skill_dir / "USAGE.md").write_text(VALID_USAGE_MD, encoding="utf-8")
    (skill_dir / "README.md").write_text("# test-skill\n\n测试。\n", encoding="utf-8")

    entry = skill_dir / "run.py"
    try:
        os.chmod(entry, 0o755)
    except OSError:
        pass

    return skill_dir


# ============================================================
# TestSkillignore — .skillignore 解析（5 用例）
# ============================================================

class TestSkillignore:
    def test_no_skillignore_returns_empty(self, tmp_path):
        assert load_skillignore(tmp_path) == []

    def test_empty_file(self, tmp_path):
        (tmp_path / ".skillignore").write_text("", encoding="utf-8")
        assert load_skillignore(tmp_path) == []

    def test_comments_and_blank_lines(self, tmp_path):
        content = "# this is a comment\n\n# another comment\n\n"
        (tmp_path / ".skillignore").write_text(content, encoding="utf-8")
        assert load_skillignore(tmp_path) == []

    def test_basic_patterns(self, tmp_path):
        content = "*.log\nbuild/\ntemp_*\n"
        (tmp_path / ".skillignore").write_text(content, encoding="utf-8")
        patterns = load_skillignore(tmp_path)
        assert patterns == ["*.log", "build/", "temp_*"]

    def test_mixed_content(self, tmp_path):
        content = "# ignore logs\n*.log\n\n# ignore build\nbuild\n  \ndata/*.csv\n"
        (tmp_path / ".skillignore").write_text(content, encoding="utf-8")
        patterns = load_skillignore(tmp_path)
        assert "*.log" in patterns
        assert "build" in patterns
        assert "data/*.csv" in patterns
        assert len(patterns) == 3


# ============================================================
# TestFileCollection — 文件收集与排除（5 用例）
# ============================================================

class TestFileCollection:
    def test_basic_collection(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        files = collect_files(skill, [])
        names = {f.name for f in files}
        assert "SKILL.md" in names
        assert "run.py" in names
        assert "USAGE.md" in names
        assert "README.md" in names

    def test_excludes_dotfiles(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        (skill / ".hidden").write_text("secret", encoding="utf-8")
        (skill / ".env").write_text("KEY=val", encoding="utf-8")
        files = collect_files(skill, [])
        names = {f.name for f in files}
        assert ".hidden" not in names
        assert ".env" not in names

    def test_excludes_system_dirs(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        cache = skill / "__pycache__"
        cache.mkdir()
        (cache / "module.cpython-311.pyc").write_bytes(b"\x00")
        git = skill / ".git"
        git.mkdir()
        (git / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")
        files = collect_files(skill, [])
        paths = {f.as_posix() for f in files}
        assert not any("__pycache__" in p for p in paths)
        assert not any(".git" in p for p in paths)

    def test_excludes_skillignore_patterns(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        (skill / "debug.log").write_text("log", encoding="utf-8")
        (skill / "temp_data.txt").write_text("tmp", encoding="utf-8")
        files = collect_files(skill, ["*.log", "temp_*"])
        names = {f.name for f in files}
        assert "debug.log" not in names
        assert "temp_data.txt" not in names

    def test_excludes_skill_files(self, tmp_path):
        """*.skill 产物始终被排除。"""
        skill = _make_valid_skill(tmp_path)
        (skill / "old-version.skill").write_bytes(b"PK\x03\x04fake")
        files = collect_files(skill, [])
        names = {f.name for f in files}
        assert "old-version.skill" not in names

    def test_skillignore_directory_pattern(self, tmp_path):
        """tests/ 目录模式应排除该目录下所有文件。"""
        skill = _make_valid_skill(tmp_path)
        tests_dir = skill / "tests"
        tests_dir.mkdir()
        (tests_dir / "sample.txt").write_text("test data", encoding="utf-8")
        (tests_dir / "test_main.py").write_text("# test", encoding="utf-8")
        files = collect_files(skill, ["tests/"])
        paths = {f.as_posix() for f in files}
        assert not any("tests/" in p for p in paths)

    def test_hidden_directory_contents_excluded(self, tmp_path):
        """隐藏目录内的普通文件也应被排除。"""
        skill = _make_valid_skill(tmp_path)
        secret_dir = skill / ".secret"
        secret_dir.mkdir()
        (secret_dir / "data.txt").write_text("sensitive", encoding="utf-8")
        files = collect_files(skill, [])
        paths = {f.as_posix() for f in files}
        assert not any(".secret" in p for p in paths)


# ============================================================
# TestPreCheck — 前置检查（4 用例）
# ============================================================

class TestPreCheck:
    def test_validate_error_blocks(self, tmp_path):
        """validate 有 error 时拒绝打包。"""
        skill = tmp_path / "bad-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("no front matter", encoding="utf-8")
        result = create_package(skill)
        assert not result.success
        assert any("error" in e.lower() or "❌" in e for e in result.errors)

    def test_scan_error_blocks(self, tmp_path):
        """scan 有 error（如敏感文件）时拒绝打包。"""
        skill = _make_valid_skill(tmp_path)
        (skill / ".env").write_text("SECRET=abc", encoding="utf-8")
        cred = skill / "credentials.json"
        cred.write_text('{"key": "value"}', encoding="utf-8")
        result = create_package(skill)
        assert not result.success
        assert any("SENSITIVE_FILE" in e for e in result.errors)

    def test_warnings_do_not_block(self, tmp_path):
        """validate warnings 不阻断打包。"""
        skill = _make_valid_skill(tmp_path)
        result = create_package(skill)
        assert result.success

    def test_force_overrides_errors(self, tmp_path):
        """--force 时即使有 error 也继续打包。"""
        skill = _make_valid_skill(tmp_path)
        cred = skill / "credentials.json"
        cred.write_text('{"key": "value"}', encoding="utf-8")
        result = create_package(skill, force=True)
        assert result.success
        assert result.package_path is not None
        assert result.package_path.exists()
        assert len(result.errors) > 0


# ============================================================
# TestZipCreation — zip 结构（4 用例）
# ============================================================

class TestZipCreation:
    def test_zip_top_level_directory(self, tmp_path):
        """zip 内所有文件在 skill-name/ 顶层目录下。"""
        skill = _make_valid_skill(tmp_path)
        result = create_package(skill)
        assert result.success
        with zipfile.ZipFile(result.package_path) as zf:
            for name in zf.namelist():
                assert name.startswith("test-skill/"), f"路径 {name} 不在顶层目录下"

    def test_zip_contains_all_files(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        result = create_package(skill)
        assert result.success
        with zipfile.ZipFile(result.package_path) as zf:
            entries = {Path(n).name for n in zf.namelist()}
        assert "SKILL.md" in entries
        assert "run.py" in entries
        assert "USAGE.md" in entries
        assert "README.md" in entries

    def test_zip_posix_paths(self, tmp_path):
        """zip 内路径使用 POSIX 格式（/），无反斜杠。"""
        skill = _make_valid_skill(tmp_path)
        sub = skill / "lib"
        sub.mkdir()
        (sub / "utils.py").write_text("# util", encoding="utf-8")
        result = create_package(skill)
        assert result.success
        with zipfile.ZipFile(result.package_path) as zf:
            for name in zf.namelist():
                assert "\\" not in name, f"路径含反斜杠：{name}"

    def test_zip_file_content_integrity(self, tmp_path):
        """zip 内文件内容与源文件一致（忽略平台换行差异）。"""
        skill = _make_valid_skill(tmp_path)
        result = create_package(skill)
        assert result.success
        with zipfile.ZipFile(result.package_path) as zf:
            zipped = zf.read("test-skill/SKILL.md").decode("utf-8")
        on_disk = (skill / "SKILL.md").read_bytes().decode("utf-8")
        assert zipped == on_disk


# ============================================================
# TestSHA256 — 校验和（2 用例）
# ============================================================

class TestSHA256:
    def test_sha256_matches(self, tmp_path):
        """compute_sha256 结果与 hashlib 直接计算一致。"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world" * 1000)
        expected = hashlib.sha256(b"hello world" * 1000).hexdigest()
        assert compute_sha256(f) == expected

    def test_package_sha256_consistent(self, tmp_path):
        """打包结果的 sha256 与包文件实际校验和一致。"""
        skill = _make_valid_skill(tmp_path)
        result = create_package(skill)
        assert result.success
        actual = compute_sha256(result.package_path)
        assert result.sha256 == actual


# ============================================================
# TestPackageSize — 包大小检测（2 用例）
# ============================================================

class TestPackageSize:
    def test_small_package_no_warning(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        result = create_package(skill)
        assert result.success
        size_warnings = [w for w in result.warnings if "超过推荐上限" in w]
        assert len(size_warnings) == 0

    def test_large_package_warning(self, tmp_path):
        """超过 10MB 时输出 warning。"""
        skill = _make_valid_skill(tmp_path)
        big = skill / "large_data.bin"
        big.write_bytes(os.urandom(11 * 1024 * 1024))
        result = create_package(skill)
        assert result.success
        size_warnings = [w for w in result.warnings if "超过推荐上限" in w]
        assert len(size_warnings) == 1


# ============================================================
# TestOutputDir — 输出目录（3 用例）
# ============================================================

class TestOutputDir:
    def test_default_output_is_parent(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        result = create_package(skill)
        assert result.success
        assert result.package_path.parent == skill.parent

    def test_custom_output_dir(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        custom = tmp_path / "dist"
        custom.mkdir()
        result = create_package(skill, output_dir=custom)
        assert result.success
        assert result.package_path.parent == custom

    def test_nonexistent_output_dir_created(self, tmp_path):
        """输出目录不存在时自动创建。"""
        skill = _make_valid_skill(tmp_path)
        custom = tmp_path / "new" / "output"
        assert not custom.exists()
        result = create_package(skill, output_dir=custom)
        assert result.success
        assert custom.exists()
        assert result.package_path.parent == custom


# ============================================================
# TestCLIIntegration — CLI 端到端（3 用例）
# ============================================================

class TestCLIIntegration:
    def test_package_cli_success(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        try:
            os.chmod(skill / "run.py", 0o755)
        except OSError:
            pass
        result = subprocess.run(
            [sys.executable, "run.py", "package", str(skill)],
            cwd=str(SKILL_ROOT),
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "SHA256" in result.stdout
        assert "打包完成" in result.stdout

    def test_package_cli_invalid_path(self, tmp_path):
        fake_path = tmp_path / "nonexistent"
        result = subprocess.run(
            [sys.executable, "run.py", "package", str(fake_path)],
            cwd=str(SKILL_ROOT),
            capture_output=True, text=True,
        )
        assert result.returncode == 1

    def test_package_cli_force(self, tmp_path):
        skill = _make_valid_skill(tmp_path)
        (skill / "credentials.json").write_text('{"k":"v"}', encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "run.py", "package", str(skill), "--force"],
            cwd=str(SKILL_ROOT),
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "打包完成" in result.stdout
