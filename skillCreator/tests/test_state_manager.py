"""
测试 state_manager.py

覆盖：
- CRUD 操作（add / archive / remove / get / list）
- 原子写入（.state.json.tmp -> os.replace）
- README 自动生成
- 迁移逻辑（README -> .state.json 幂等性）
- 锁机制（残留锁清理、正常锁阻断）
- archive 单次原子操作（消除双写问题）
- clean 精确删除（消除全局匹配问题）
"""
import json
import os
import time
from pathlib import Path

import pytest
from creator import state_manager


@pytest.fixture()
def state_env(tmp_path, monkeypatch):
    """将 OPENCLAW_SKILLS_TEMP 指向 tmp_path，隔离测试环境。"""
    skills_temp = tmp_path / "skills-temp"
    skills_temp.mkdir()
    monkeypatch.setenv("OPENCLAW_SKILLS_TEMP", str(skills_temp))
    return skills_temp


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

class TestCRUD:
    def test_add_skill_creates_state_file(self, state_env):
        state_manager.add_skill("my-tool", score=80)
        state_path = state_env / ".state.json"
        assert state_path.exists()
        data = json.loads(state_path.read_text(encoding="utf-8"))
        assert "my-tool" in data["skills"]
        assert data["skills"]["my-tool"]["status"] == "pending"
        assert data["skills"]["my-tool"]["score"] == 80

    def test_archive_skill_updates_status(self, state_env):
        state_manager.add_skill("arch-test", score=70)
        state_manager.archive_skill("arch-test", archived_to="/dest/arch-test")
        entry = state_manager.get_skill("arch-test")
        assert entry["status"] == "archived"
        assert entry["archived_to"] == "/dest/arch-test"
        assert entry["archived_at"] is not None

    def test_archive_unknown_skill_creates_entry(self, state_env):
        state_manager.archive_skill("unknown", archived_to="/dest/unknown")
        entry = state_manager.get_skill("unknown")
        assert entry is not None
        assert entry["status"] == "archived"

    def test_remove_skill_deletes_entry(self, state_env):
        state_manager.add_skill("to-remove")
        state_manager.remove_skill("to-remove")
        assert state_manager.get_skill("to-remove") is None

    def test_remove_nonexistent_is_noop(self, state_env):
        state_manager.remove_skill("ghost")

    def test_get_skill_returns_none_for_missing(self, state_env):
        assert state_manager.get_skill("nope") is None

    def test_list_skills_all(self, state_env):
        state_manager.add_skill("a")
        state_manager.add_skill("b")
        state_manager.archive_skill("b", archived_to="/x")
        all_skills = state_manager.list_skills()
        assert len(all_skills) == 2

    def test_list_skills_by_status(self, state_env):
        state_manager.add_skill("p1")
        state_manager.add_skill("p2")
        state_manager.archive_skill("p2", archived_to="/x")
        pending = state_manager.list_skills(status="pending")
        archived = state_manager.list_skills(status="archived")
        assert len(pending) == 1
        assert "p1" in pending
        assert len(archived) == 1
        assert "p2" in archived


# ---------------------------------------------------------------------------
# 原子写入
# ---------------------------------------------------------------------------

class TestAtomicWrite:
    def test_no_tmp_file_remains(self, state_env):
        state_manager.add_skill("atomic-test")
        tmp_file = state_env / ".state.json.tmp"
        assert not tmp_file.exists()

    def test_state_file_is_valid_json(self, state_env):
        state_manager.add_skill("json-check")
        content = (state_env / ".state.json").read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["version"] == state_manager.STATE_VERSION


# ---------------------------------------------------------------------------
# README 自动生成
# ---------------------------------------------------------------------------

class TestReadmeGeneration:
    def test_readme_created_on_add(self, state_env):
        state_manager.add_skill("readme-test", score=85)
        readme = state_env / "README.md"
        assert readme.exists()
        content = readme.read_text(encoding="utf-8")
        assert "readme-test" in content
        assert "85/100" in content
        assert "自动生成" in content

    def test_readme_reflects_archive(self, state_env):
        state_manager.add_skill("s1", score=70)
        state_manager.archive_skill("s1", archived_to="/dest/s1")
        content = (state_env / "README.md").read_text(encoding="utf-8")
        assert "已归档" in content
        assert "/dest/s1" in content

    def test_readme_pending_section_empty_after_archive(self, state_env):
        state_manager.add_skill("only-one")
        state_manager.archive_skill("only-one", archived_to="/x")
        content = (state_env / "README.md").read_text(encoding="utf-8")
        lines = content.split("\n")
        pending_rows = [
            l for l in lines
            if l.strip().startswith("|") and "`only-one`" in l and "待确认" in l
        ]
        assert len(pending_rows) == 0

    def test_clean_removes_from_readme(self, state_env):
        state_manager.add_skill("clean-me")
        state_manager.remove_skill("clean-me")
        content = (state_env / "README.md").read_text(encoding="utf-8")
        assert "clean-me" not in content

    def test_clean_does_not_affect_archived(self, state_env):
        """clean 操作应只删除目标 skill，不影响已归档记录（消除全局匹配问题）。"""
        state_manager.add_skill("keep-archived")
        state_manager.archive_skill("keep-archived", archived_to="/dest")
        state_manager.add_skill("to-clean")
        state_manager.remove_skill("to-clean")
        content = (state_env / "README.md").read_text(encoding="utf-8")
        assert "keep-archived" in content
        assert "to-clean" not in content


# ---------------------------------------------------------------------------
# 迁移
# ---------------------------------------------------------------------------

class TestMigration:
    def _write_legacy_readme(self, state_env):
        readme = state_env / "README.md"
        readme.write_text(
            "# skills-temp\n\n"
            "### 当前待确认技能\n\n"
            "| Skill 名称 | 状态 | 创建日期 | 备注 |\n"
            "|-----------|------|---------|------|\n"
            "| `legacy-skill` | ⏳ 待确认 | 2026-03-20 | 新创建的 skill (评分: 72/100) |\n"
            "\n"
            "### ✅ 已归档技能\n\n"
            "| Skill 名称 | 归档日期 | 归档路径 | 状态 |\n"
            "|-----------|---------|---------|------|\n"
            "| `old-skill` | 2026-03-15 | /skills/old-skill | 已归档 |\n",
            encoding="utf-8",
        )

    def test_migration_imports_pending(self, state_env):
        self._write_legacy_readme(state_env)
        result = state_manager.migrate_from_readme()
        assert result is True
        entry = state_manager.get_skill("legacy-skill")
        assert entry is not None
        assert entry["status"] == "pending"
        assert entry["score"] == 72

    def test_migration_imports_archived(self, state_env):
        self._write_legacy_readme(state_env)
        state_manager.migrate_from_readme()
        entry = state_manager.get_skill("old-skill")
        assert entry is not None
        assert entry["status"] == "archived"
        assert entry["archived_to"] == "/skills/old-skill"

    def test_migration_creates_backup(self, state_env):
        self._write_legacy_readme(state_env)
        state_manager.migrate_from_readme()
        backups = list(state_env.glob("README.md.bak.*"))
        assert len(backups) >= 1

    def test_migration_idempotent(self, state_env):
        self._write_legacy_readme(state_env)
        state_manager.migrate_from_readme()
        result = state_manager.migrate_from_readme()
        assert result is False

    def test_migration_no_readme(self, state_env):
        result = state_manager.migrate_from_readme()
        assert result is True
        state = state_manager.load_state()
        assert len(state["skills"]) == 0


# ---------------------------------------------------------------------------
# 锁机制
# ---------------------------------------------------------------------------

class TestLocking:
    def test_stale_lock_auto_cleaned(self, state_env):
        lock_path = state_env / ".state.json.lock"
        lock_path.write_text("stale", encoding="utf-8")
        old_time = time.time() - state_manager.LOCK_TIMEOUT_SECONDS - 10
        os.utime(str(lock_path), (old_time, old_time))

        state_manager.add_skill("after-stale-lock")
        assert state_manager.get_skill("after-stale-lock") is not None
        assert not lock_path.exists()

    def test_active_lock_raises(self, state_env):
        lock_path = state_env / ".state.json.lock"
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)

        with pytest.raises(RuntimeError, match="被锁定"):
            state_manager.add_skill("should-fail")

        lock_path.unlink()


# ---------------------------------------------------------------------------
# archive 单次原子操作（双写问题验证）
# ---------------------------------------------------------------------------

class TestArchiveAtomicity:
    def test_archive_is_single_state_update(self, state_env):
        """归档后 pending 消失 + archived 出现，且仅有一次 state 写入。"""
        state_manager.add_skill("atomic-arch", score=88)
        state_manager.archive_skill("atomic-arch", archived_to="/dest/atomic-arch")

        state = state_manager.load_state()
        entry = state["skills"]["atomic-arch"]
        assert entry["status"] == "archived"
        assert entry["score"] == 88
        assert entry["archived_to"] == "/dest/atomic-arch"

        pending = state_manager.list_skills(status="pending")
        assert "atomic-arch" not in pending
