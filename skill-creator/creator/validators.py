"""
命名与版本号校验工具函数
"""
import re


def validate_skill_name(name: str) -> bool:
    """验证 skill 名称是否符合规范（小写字母开头，仅含字母/数字/短横线）。"""
    return bool(re.match(r'^[a-z][a-z0-9-]*$', name))


def validate_version(version: str) -> bool:
    """验证版本号是否符合语义化版本格式（x.y.z）。"""
    return bool(re.fullmatch(r'\d+\.\d+\.\d+', version))
