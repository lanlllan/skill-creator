"""Phase 17b 测试：工具链打磨"""
import argparse
import re
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skill-creator'))

import pytest
from creator.scorer import PLACEHOLDER_PATTERNS
from creator.examples import copy_example, EXAMPLES_DIR
from creator.state_manager import _cleanup_old_backups


class TestPlaceholderPatternsExpansion:
    def test_todo_implement(self):
        text = "TODO: implement this feature"
        assert any(p.search(text) for p in PLACEHOLDER_PATTERNS)

    def test_todo_implement_no_colon(self):
        text = "TODO implement the handler"
        assert any(p.search(text) for p in PLACEHOLDER_PATTERNS)

    def test_your_xxx_here(self):
        text = "your_api_key_here"
        assert any(p.search(text) for p in PLACEHOLDER_PATTERNS)

    def test_change_me(self):
        text = "value = CHANGE_ME"
        assert any(p.search(text) for p in PLACEHOLDER_PATTERNS)

    def test_placeholder_word(self):
        text = "This is a placeholder text"
        assert any(p.search(text) for p in PLACEHOLDER_PATTERNS)

    def test_existing_patterns_preserved(self):
        assert any(p.search('场景1') for p in PLACEHOLDER_PATTERNS)
        assert any(p.search('能力2') for p in PLACEHOLDER_PATTERNS)

    def test_normal_text_not_matched(self):
        text = "这是正常的功能描述，不包含占位符"
        assert not any(p.search(text) for p in PLACEHOLDER_PATTERNS)


class TestArchiveForce:
    def test_archive_force_backup_and_overwrite(self, tmp_path):
        from creator.commands.archive import main_archive

        source_dir = tmp_path / 'source'
        dest_dir = tmp_path / 'dest'
        skill_name = 'my-skill'

        src = source_dir / skill_name
        src.mkdir(parents=True)
        (src / 'SKILL.md').write_text('---\nname: my-skill\n---', encoding='utf-8')

        dst = dest_dir / skill_name
        dst.mkdir(parents=True)
        (dst / 'SKILL.md').write_text('old content', encoding='utf-8')

        args = argparse.Namespace(
            name=skill_name,
            source=str(source_dir),
            dest=str(dest_dir),
            force=True,
            dry_run=False,
        )
        code = main_archive(args)
        assert code == 0
        assert (dest_dir / skill_name / 'SKILL.md').exists()
        backups = list(dest_dir.glob(f'{skill_name}.bak.*'))
        assert len(backups) == 1

    def test_archive_no_force_existing(self, tmp_path, capsys):
        from creator.commands.archive import main_archive

        source_dir = tmp_path / 'source'
        dest_dir = tmp_path / 'dest'
        skill_name = 'my-skill'

        (source_dir / skill_name).mkdir(parents=True)
        (source_dir / skill_name / 'SKILL.md').write_text('x', encoding='utf-8')
        (dest_dir / skill_name).mkdir(parents=True)

        args = argparse.Namespace(
            name=skill_name,
            source=str(source_dir),
            dest=str(dest_dir),
            force=False,
            dry_run=False,
        )
        code = main_archive(args)
        assert code == 1
        output = capsys.readouterr().out
        assert '--force' in output


class TestExamplesCopyConflict:
    def test_copy_overwrite(self, tmp_path):
        name = 'file-analyzer'
        target = tmp_path / name
        target.mkdir()
        (target / 'dummy.txt').write_text('old', encoding='utf-8')

        ok, msg = copy_example(name, tmp_path, conflict='overwrite')
        assert ok is True
        assert (target / 'SKILL.md').exists()

    def test_copy_rename(self, tmp_path):
        name = 'file-analyzer'
        target = tmp_path / name
        target.mkdir()

        ok, msg = copy_example(name, tmp_path, conflict='rename')
        assert ok is True
        assert (tmp_path / f'{name}-1').exists()

    def test_copy_error_default(self, tmp_path):
        name = 'file-analyzer'
        target = tmp_path / name
        target.mkdir()

        ok, msg = copy_example(name, tmp_path)
        assert ok is False
        assert '已存在' in msg


class TestBackupCleanup:
    def test_keep_1_remove_old(self, tmp_path):
        for i in range(3):
            (tmp_path / f'README.md.bak.2026010{i}120000').write_text(
                f'backup-{i}', encoding='utf-8')

        _cleanup_old_backups(tmp_path, keep=1)
        remaining = list(tmp_path.glob('README.md.bak.*'))
        assert len(remaining) == 1

    def test_no_backups(self, tmp_path):
        _cleanup_old_backups(tmp_path, keep=1)

    def test_keep_0(self, tmp_path):
        (tmp_path / 'README.md.bak.20260101120000').write_text('x', encoding='utf-8')
        _cleanup_old_backups(tmp_path, keep=0)
        remaining = list(tmp_path.glob('README.md.bak.*'))
        assert len(remaining) == 0
