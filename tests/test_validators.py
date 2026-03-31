"""
测试 validate_skill_name() 和 validate_version()
"""
import pytest
from creator.validators import validate_skill_name, validate_version


class TestValidateSkillName:
    # ---- 合法名称 ----
    @pytest.mark.parametrize("name", [
        "my-skill",
        "log-analyzer",
        "a",
        "abc123",
        "test-runner-v2",
        "x1",
    ])
    def test_valid(self, name):
        assert validate_skill_name(name) is True

    # ---- 非法名称 ----
    @pytest.mark.parametrize("name, reason", [
        ("",          "空字符串"),
        ("123abc",    "数字开头"),
        ("-abc",      "短横线开头"),
        ("My-Skill",  "含大写字母"),
        ("my skill",  "含空格"),
        ("my_skill",  "含下划线"),
        ("my.skill",  "含点号"),
        ("none",      "保留字 none（规范名但应能通过，此处验证小写字母开头合法）"),
    ])
    def test_invalid(self, name, reason):
        # "none" 本身是合法格式（小写字母开头），仅用于确认不因名称本身被拒绝
        if name == "none":
            assert validate_skill_name(name) is True, f"'none' 应通过格式校验：{reason}"
        else:
            assert validate_skill_name(name) is False, f"应拒绝：{reason}"

    def test_uppercase_rejected(self):
        assert validate_skill_name("MySkill") is False

    def test_leading_digit_rejected(self):
        assert validate_skill_name("1-skill") is False


class TestValidateVersion:
    # ---- 合法版本 ----
    @pytest.mark.parametrize("version", [
        "1.0.0",
        "0.0.1",
        "10.20.30",
        "1.2.3",
        "100.200.300",
    ])
    def test_valid(self, version):
        assert validate_version(version) is True

    # ---- 非法版本 ----
    @pytest.mark.parametrize("version, reason", [
        ("1.0",      "缺少 patch 字段"),
        ("1",        "只有 major"),
        ("1.0.0.0",  "多余字段"),
        ("v1.0.0",   "含 v 前缀"),
        ("1.0.a",    "含非数字"),
        ("",         "空字符串"),
        ("abc",      "纯文本"),
        ("1.0.0-rc", "含预发布标识"),
    ])
    def test_invalid(self, version, reason):
        assert validate_version(version) is False, f"应拒绝：{reason}"
