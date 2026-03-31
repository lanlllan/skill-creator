"""
tests/test_security.py — 安全扫描引擎测试

覆盖 4 层：规则引擎单元测试、扫描引擎测试、format_report 测试、边界测试
"""
import json
import pytest
from pathlib import Path

from creator.security import (
    ScanFinding, DEFAULT_RULES, MAX_FILE_SIZE, SEVERITY_ORDER,
    scan_directory, format_report, _is_binary, _match_filename,
)


# ─── 夹具 ───────────────────────────────────────────────────

@pytest.fixture
def empty_skill(tmp_path):
    d = tmp_path / "empty-skill"
    d.mkdir()
    return d


@pytest.fixture
def clean_skill(tmp_path):
    d = tmp_path / "clean-skill"
    d.mkdir()
    (d / "run.py").write_text('print("hello")', encoding='utf-8')
    (d / "README.md").write_text('# Test', encoding='utf-8')
    return d


def _make_file(skill_dir, name, content=''):
    p = skill_dir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    return p


# ═══ 第一层：规则引擎单元测试 ═══════════════════════════════

class TestSecretApiKey:
    """SECRET_API_KEY 规则：已知云服务密钥前缀"""

    def test_sk_prefix(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "config.py", 'KEY = "sk-' + 'a' * 30 + '"')
        findings = scan_directory(d)
        assert any(f.rule_id == 'SECRET_API_KEY' for f in findings)

    def test_akia_prefix(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "config.py", 'AWS_KEY = "AKIA' + 'A' * 16 + '"')
        findings = scan_directory(d)
        assert any(f.rule_id == 'SECRET_API_KEY' for f in findings)

    def test_ghp_prefix(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "config.py", 'GH = "ghp_' + 'a' * 36 + '"')
        findings = scan_directory(d)
        assert any(f.rule_id == 'SECRET_API_KEY' for f in findings)

    def test_glpat_prefix(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "config.py", 'GL = "glpat-' + 'a' * 20 + '"')
        findings = scan_directory(d)
        assert any(f.rule_id == 'SECRET_API_KEY' for f in findings)

    def test_short_prefix_no_match(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "config.py", 'x = "sk-short"')
        findings = scan_directory(d)
        assert not any(f.rule_id == 'SECRET_API_KEY' for f in findings)

    def test_akia_too_short_no_match(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "config.py", 'x = "AKIA1234"')
        findings = scan_directory(d)
        assert not any(f.rule_id == 'SECRET_API_KEY' for f in findings)


class TestSecretAssignment:
    """SECRET_ASSIGNMENT 规则：硬编码凭证赋值"""

    def test_api_key_long(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "c.py", 'api_key = "reallylong_secret_key"')
        findings = scan_directory(d)
        assert any(f.rule_id == 'SECRET_ASSIGNMENT' for f in findings)

    def test_password_long(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "c.py", "password = 'super_secret_password'")
        findings = scan_directory(d)
        assert any(f.rule_id == 'SECRET_ASSIGNMENT' for f in findings)

    def test_token_long(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "c.py", 'token = "abcdefghijklmnop"')
        findings = scan_directory(d)
        assert any(f.rule_id == 'SECRET_ASSIGNMENT' for f in findings)

    def test_short_value_no_match(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "c.py", 'password = "test"')
        findings = scan_directory(d)
        assert not any(f.rule_id == 'SECRET_ASSIGNMENT' for f in findings)

    def test_placeholder_no_match(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "c.py", 'api_key = "change"')
        findings = scan_directory(d)
        assert not any(f.rule_id == 'SECRET_ASSIGNMENT' for f in findings)


class TestSensitiveFile:
    """SENSITIVE_FILE 规则：敏感文件名匹配"""

    def test_dot_env(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, ".env", "SECRET=x")
        findings = scan_directory(d)
        assert any(f.rule_id == 'SENSITIVE_FILE' for f in findings)

    def test_credentials_json(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "credentials.json", "{}")
        findings = scan_directory(d)
        assert any(f.rule_id == 'SENSITIVE_FILE' for f in findings)

    def test_pem_file(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "server.pem", "cert")
        findings = scan_directory(d)
        assert any(f.rule_id == 'SENSITIVE_FILE' for f in findings)

    def test_key_file(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "private.key", "key")
        findings = scan_directory(d)
        assert any(f.rule_id == 'SENSITIVE_FILE' for f in findings)

    def test_env_example_no_match(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, ".env.example", "KEY=placeholder")
        findings = scan_directory(d)
        assert not any(f.rule_id == 'SENSITIVE_FILE' for f in findings)

    def test_readme_no_match(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "readme.md", "# Hi")
        findings = scan_directory(d)
        assert not any(f.rule_id == 'SENSITIVE_FILE' for f in findings)


class TestDangerousEval:
    """DANGEROUS_EVAL 规则：动态执行调用"""

    def test_eval_call(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "result = eval(user_input)")
        findings = scan_directory(d)
        assert any(f.rule_id == 'DANGEROUS_EVAL' for f in findings)

    def test_exec_call(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "exec(code_string)")
        findings = scan_directory(d)
        assert any(f.rule_id == 'DANGEROUS_EVAL' for f in findings)

    def test_import_call(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "mod = __import__('os')")
        findings = scan_directory(d)
        assert any(f.rule_id == 'DANGEROUS_EVAL' for f in findings)

    def test_comment_eval_still_matches(self, tmp_path):
        """注释中的 eval() 调用形态仍被正则命中（已知行为）"""
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "# eval(something)")
        findings = scan_directory(d)
        assert any(f.rule_id == 'DANGEROUS_EVAL' for f in findings)

    def test_variable_name_eval_no_match(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "variable_name_eval = 1")
        findings = scan_directory(d)
        assert not any(f.rule_id == 'DANGEROUS_EVAL' for f in findings)

    def test_string_eval_no_match(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", 'msg = "use eval carefully"')
        findings = scan_directory(d)
        assert not any(f.rule_id == 'DANGEROUS_EVAL' for f in findings)


class TestDangerousShellTrue:
    """DANGEROUS_SHELL_TRUE 规则：shell=True 调用"""

    def test_subprocess_call_shell_true(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "subprocess.call('ls', shell=True)")
        findings = scan_directory(d)
        assert any(f.rule_id == 'DANGEROUS_SHELL_TRUE' for f in findings)

    def test_subprocess_run_shell_true(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "subprocess.run(cmd, shell=True)")
        findings = scan_directory(d)
        assert any(f.rule_id == 'DANGEROUS_SHELL_TRUE' for f in findings)

    def test_subprocess_shell_false_no_match(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "subprocess.run(cmd, shell=False)")
        findings = scan_directory(d)
        assert not any(f.rule_id == 'DANGEROUS_SHELL_TRUE' for f in findings)


class TestDangerousOsSystem:
    """DANGEROUS_OS_SYSTEM 规则：os.system() 调用"""

    def test_os_system_call(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", 'os.system("ls -la")')
        findings = scan_directory(d)
        assert any(f.rule_id == 'DANGEROUS_OS_SYSTEM' for f in findings)

    def test_comment_os_system_still_matches(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "# os.system(cmd)")
        findings = scan_directory(d)
        assert any(f.rule_id == 'DANGEROUS_OS_SYSTEM' for f in findings)


# ═══ 第二层：扫描引擎测试 ════════════════════════════════════

class TestScanEngine:

    def test_empty_directory(self, empty_skill):
        findings = scan_directory(empty_skill)
        assert findings == []

    def test_binary_file_skipped(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        binfile = d / "data.bin"
        binfile.write_bytes(b'\x00' * 100 + b'api_key = "reallylong_secret"')
        findings = scan_directory(d)
        assert not any(f.rule_id == 'SECRET_ASSIGNMENT' for f in findings)

    def test_pycache_skipped(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        cache = d / "__pycache__"
        cache.mkdir()
        (cache / "bad.py").write_text('eval(x)', encoding='utf-8')
        findings = scan_directory(d)
        assert not any(f.rule_id == 'DANGEROUS_EVAL' for f in findings)

    def test_custom_rules(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, "run.py", "print('hello')")
        custom = [{'rule_id': 'CUSTOM', 'severity': 'info', 'message': 'found print',
                   'type': 'content', 'pattern': r'print\s*\('}]
        findings = scan_directory(d, rules=custom)
        assert len(findings) == 1
        assert findings[0].rule_id == 'CUSTOM'

    def test_results_sorted_by_severity(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        _make_file(d, ".env", "SECRET=x")
        _make_file(d, "run.py", "result = eval(user_input)")
        findings = scan_directory(d)
        severities = [f.severity for f in findings]
        assert severities == sorted(severities, key=lambda s: SEVERITY_ORDER.get(s, 99))

    def test_path_not_exists(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            scan_directory(tmp_path / "nonexistent")

    def test_path_not_directory(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        with pytest.raises(NotADirectoryError):
            scan_directory(f)

    def test_relative_paths_in_findings(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        sub = d / "src"
        sub.mkdir()
        _make_file(d, "src/config.py", 'api_key = "reallylong_secret_key_123"')
        findings = scan_directory(d)
        matched = [f for f in findings if f.rule_id == 'SECRET_ASSIGNMENT']
        assert len(matched) >= 1
        assert matched[0].file == 'src/config.py'

    def test_large_file_skipped(self, tmp_path):
        d = tmp_path / "s"; d.mkdir()
        big = d / "large.py"
        big.write_text('x' * (MAX_FILE_SIZE + 1), encoding='utf-8')
        findings = scan_directory(d)
        skipped = [f for f in findings if f.rule_id == 'LARGE_FILE_SKIPPED']
        assert len(skipped) == 1
        assert skipped[0].severity == 'info'
        assert skipped[0].line is None


# ═══ 第三层：format_report 测试 ══════════════════════════════

class TestFormatReport:

    def test_text_output(self):
        findings = [ScanFinding('SECRET_API_KEY', 'error', 'config.py', 15,
                                '检测到疑似 API 密钥', 'sk-' + 'a' * 30)]
        report = format_report(findings)
        assert '🔴' in report
        assert '[SECRET_API_KEY]' in report
        assert 'config.py:15' in report

    def test_json_output(self):
        findings = [ScanFinding('DANGEROUS_EVAL', 'warning', 'run.py', 10,
                                '检测到动态执行调用', 'eval(x)')]
        report = format_report(findings, json_output=True)
        data = json.loads(report)
        assert len(data) == 1
        assert data[0]['rule_id'] == 'DANGEROUS_EVAL'

    def test_line_none_no_line_suffix(self):
        findings = [ScanFinding('SENSITIVE_FILE', 'error', '.env', None,
                                '敏感文件', '.env')]
        report = format_report(findings)
        assert '.env' in report
        assert ':None' not in report

    def test_secret_sanitized(self):
        secret = 'sk-' + 'a' * 50
        findings = [ScanFinding('SECRET_API_KEY', 'error', 'c.py', 1,
                                '检测到疑似 API 密钥', secret)]
        report = format_report(findings)
        assert secret not in report
        assert '***' in report

    def test_empty_findings(self):
        report = format_report([])
        assert '无安全发现' in report


# ═══ 辅助函数测试 ═════════════════════════════════════════════

class TestHelpers:

    def test_is_binary_true(self, tmp_path):
        f = tmp_path / "bin"
        f.write_bytes(b'\x00\x01\x02')
        assert _is_binary(f) is True

    def test_is_binary_false(self, tmp_path):
        f = tmp_path / "txt"
        f.write_text("hello world", encoding='utf-8')
        assert _is_binary(f) is False

    def test_match_filename_env(self):
        assert _match_filename('.env', '.env|*.pem') is True

    def test_match_filename_pem(self):
        assert _match_filename('server.pem', '.env|*.pem') is True

    def test_match_filename_no_match(self):
        assert _match_filename('readme.md', '.env|*.pem') is False
