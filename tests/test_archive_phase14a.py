"""
Phase 14a 测试：archive 旧路径迁移提示

覆盖范围：
- 旧路径下存在归档 skill 时打印迁移提示
- 旧路径下无归档 skill 时无提示
- skill-creator/ 自身不触发提示

合计：3 用例
"""
from pathlib import Path

from creator.commands.archive import _check_legacy_archive_path


class TestLegacyArchivePathHint:
    def test_hint_shown_when_legacy_skills_exist(self, tmp_path, capsys):
        new_dest = tmp_path / "skills"
        new_dest.mkdir()
        legacy_skill = tmp_path / "my-old-skill"
        legacy_skill.mkdir()
        (legacy_skill / "SKILL.md").write_text("---\nname: my-old-skill\n---", encoding="utf-8")

        _check_legacy_archive_path(new_dest)

        captured = capsys.readouterr()
        assert "检测到" in captured.out
        assert "my-old-skill" in captured.out

    def test_no_hint_when_no_legacy_skills(self, tmp_path, capsys):
        new_dest = tmp_path / "skills"
        new_dest.mkdir()

        _check_legacy_archive_path(new_dest)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_skill_creator_excluded(self, tmp_path, capsys):
        new_dest = tmp_path / "skills"
        new_dest.mkdir()
        sc = tmp_path / "skill-creator"
        sc.mkdir()
        (sc / "SKILL.md").write_text("---\nname: skill-creator\n---", encoding="utf-8")

        _check_legacy_archive_path(new_dest)

        captured = capsys.readouterr()
        assert captured.out == ""
