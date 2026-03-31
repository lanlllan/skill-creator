"""
测试 main_batch()

覆盖重点：
- name/description 为 null 时的显式拦截（Fix 2）
- 同名不同目录不被误跳过（Fix 1 复合键）
- 同名同目录批内重复跳过
- 失败原因粒度（Fix 3）
- 正常成功路径
- YAML 格式错误的早退
"""
import argparse
from pathlib import Path

import pytest
import yaml
from creator.commands.batch import main_batch


def _args(yaml_path: str) -> argparse.Namespace:
    return argparse.Namespace(file=yaml_path)


def _write_yaml(path: Path, content: dict) -> Path:
    p = path / "batch.yaml"
    p.write_text(yaml.dump(content, allow_unicode=True), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 成功路径
# ---------------------------------------------------------------------------

class TestBatchSuccess:
    def test_single_skill_created(self, tmp_path):
        yaml_file = _write_yaml(tmp_path, {"skills": [
            {"name": "success-skill", "description": "成功用例", "output": str(tmp_path / "out")},
        ]})
        rc = main_batch(_args(str(yaml_file)))
        assert rc == 0
        assert (tmp_path / "out" / "success-skill").is_dir()

    def test_returns_0_when_all_success(self, tmp_path):
        yaml_file = _write_yaml(tmp_path, {"skills": [
            {"name": "skill-a", "description": "A", "output": str(tmp_path / "out")},
            {"name": "skill-b", "description": "B", "output": str(tmp_path / "out")},
        ]})
        rc = main_batch(_args(str(yaml_file)))
        assert rc == 0


# ---------------------------------------------------------------------------
# Fix 1：同名不同目录不应互相干扰
# ---------------------------------------------------------------------------

class TestBatchDedupByDirectory:
    def test_same_name_different_dirs_both_created(self, tmp_path):
        """同名 skill 写入不同输出目录时，两者均应被创建。"""
        out1 = tmp_path / "out1"
        out2 = tmp_path / "out2"
        yaml_file = _write_yaml(tmp_path, {"skills": [
            {"name": "shared-name", "description": "目录1", "output": str(out1)},
            {"name": "shared-name", "description": "目录2", "output": str(out2)},
        ]})
        rc = main_batch(_args(str(yaml_file)))
        assert rc == 0
        assert (out1 / "shared-name").is_dir(), "out1 中的 shared-name 应被创建"
        assert (out2 / "shared-name").is_dir(), "out2 中的 shared-name 应被创建"

    def test_same_name_same_dir_second_skipped(self, tmp_path):
        """同名同目录的第二条应被标记为批内重复跳过，整体返回 0。"""
        out = tmp_path / "out"
        yaml_file = _write_yaml(tmp_path, {"skills": [
            {"name": "dup-skill", "description": "第一条", "output": str(out)},
            {"name": "dup-skill", "description": "批内重复", "output": str(out)},
        ]})
        rc = main_batch(_args(str(yaml_file)))
        assert rc == 0
        assert (out / "dup-skill").is_dir()


# ---------------------------------------------------------------------------
# Fix 2：null 字段显式拦截
# ---------------------------------------------------------------------------

class TestBatchNullFields:
    def test_name_null_causes_failure(self, tmp_path):
        """name 为 null 时应被拦截为 failure，不创建目录。"""
        yaml_file = tmp_path / "batch.yaml"
        # PyYAML dump 会将 None 写成 null
        yaml_file.write_text(
            "skills:\n  - name: null\n    description: 测试\n",
            encoding="utf-8"
        )
        rc = main_batch(_args(str(yaml_file)))
        assert rc == 1  # 有失败则返回 1

    def test_name_null_no_none_directory_created(self, tmp_path):
        """name 为 null 时，不得创建名为 'none' 或 'None' 的目录。"""
        out = tmp_path / "out"
        out.mkdir()
        yaml_file = tmp_path / "batch.yaml"
        yaml_file.write_text(
            f"skills:\n  - name: null\n    description: 测试\n    output: {out}\n",
            encoding="utf-8"
        )
        main_batch(_args(str(yaml_file)))
        assert not (out / "none").exists(), "不应创建 name=none 的目录"
        assert not (out / "None").exists(), "不应创建 name=None 的目录"

    def test_description_null_causes_failure(self, tmp_path):
        """description 为 null 时应被拦截为 failure。"""
        yaml_file = tmp_path / "batch.yaml"
        yaml_file.write_text(
            "skills:\n  - name: my-skill\n    description: null\n",
            encoding="utf-8"
        )
        rc = main_batch(_args(str(yaml_file)))
        assert rc == 1


# ---------------------------------------------------------------------------
# Fix 3：失败原因粒度
# ---------------------------------------------------------------------------

class TestBatchFailureReasons:
    def test_invalid_name_reported(self, tmp_path, capsys):
        """名称非法时汇总报告中应出现明确说明（含'规范'或'不符合'字样）。"""
        yaml_file = _write_yaml(tmp_path, {"skills": [
            {"name": "123invalid", "description": "名称不合法"},
        ]})
        main_batch(_args(str(yaml_file)))
        captured = capsys.readouterr()
        assert "规范" in captured.out or "不符合" in captured.out

    def test_invalid_version_reported(self, tmp_path, capsys):
        """版本号非法时汇总报告中应出现明确说明（含'版本号'字样）。"""
        yaml_file = _write_yaml(tmp_path, {"skills": [
            {"name": "good-name", "description": "版本非法", "version": "abc"},
        ]})
        main_batch(_args(str(yaml_file)))
        captured = capsys.readouterr()
        assert "版本号" in captured.out

    def test_existing_dir_reported_as_skip(self, tmp_path, capsys):
        """目标目录已存在时应标记为跳过，汇总中出现'已存在'字样。"""
        out = tmp_path / "out"
        (out / "pre-exist").mkdir(parents=True)
        yaml_file = _write_yaml(tmp_path, {"skills": [
            {"name": "pre-exist", "description": "目录预存在", "output": str(out)},
        ]})
        main_batch(_args(str(yaml_file)))
        captured = capsys.readouterr()
        assert "已存在" in captured.out


# ---------------------------------------------------------------------------
# YAML 格式错误的早退（退出码 2）
# ---------------------------------------------------------------------------

class TestBatchYamlErrors:
    def test_file_not_found_returns_2(self, tmp_path):
        rc = main_batch(_args(str(tmp_path / "nonexistent.yaml")))
        assert rc == 2

    def test_missing_skills_key_returns_2(self, tmp_path):
        yaml_file = _write_yaml(tmp_path, {"data": []})
        rc = main_batch(_args(str(yaml_file)))
        assert rc == 2

    def test_empty_skills_list_returns_2(self, tmp_path):
        yaml_file = _write_yaml(tmp_path, {"skills": []})
        rc = main_batch(_args(str(yaml_file)))
        assert rc == 2
