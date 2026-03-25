"""
结构化状态管理（.state.json）

取代 README Markdown 表格作为状态存储，提供原子写入、锁机制和 README 只读生成。
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

from creator.paths import get_skills_temp_dir, get_readme_path

STATE_FILENAME = ".state.json"
LOCK_FILENAME = ".state.json.lock"
LOCK_TIMEOUT_SECONDS = 60
STATE_VERSION = 1


def _state_path(project_root: Path = None) -> Path:
    return get_skills_temp_dir(project_root) / STATE_FILENAME


def _lock_path(project_root: Path = None) -> Path:
    return get_skills_temp_dir(project_root) / LOCK_FILENAME


class StateLock:
    """基于文件的互斥锁（O_CREAT | O_EXCL 语义）。

    超过 LOCK_TIMEOUT_SECONDS 的残留锁文件视为异常，自动清理后重试。
    """

    def __init__(self, project_root: Path = None):
        self._lock_file = _lock_path(project_root)
        self._fd = None

    def __enter__(self):
        self._acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._release()
        return False

    def _acquire(self):
        lock = self._lock_file
        lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if lock.exists():
                age = time.time() - lock.stat().st_mtime
                if age > LOCK_TIMEOUT_SECONDS:
                    print(f"⚠️  检测到残留锁文件（{age:.0f}s），自动清理")
                    lock.unlink(missing_ok=True)
                    self._fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    return
            raise RuntimeError(
                f"状态文件被锁定（{lock}），请稍后重试。"
                f"若确认无其他进程运行，可手动删除 {lock}"
            )

    def _release(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        self._lock_file.unlink(missing_ok=True)


def _empty_state() -> dict:
    return {"version": STATE_VERSION, "skills": {}}


def load_state(project_root: Path = None) -> dict:
    """读取 .state.json，不存在时返回空状态。"""
    path = _state_path(project_root)
    if not path.exists():
        return _empty_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "skills" not in data:
            return _empty_state()
        return data
    except (json.JSONDecodeError, OSError):
        print("⚠️  .state.json 格式异常，将重建")
        return _empty_state()


def save_state(state: dict, project_root: Path = None):
    """原子写入 .state.json（写临时文件后 os.replace）。"""
    path = _state_path(project_root)
    tmp_path = path.with_suffix(".json.tmp")
    path.parent.mkdir(parents=True, exist_ok=True)

    state.setdefault("version", STATE_VERSION)
    content = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False)
    tmp_path.write_text(content + "\n", encoding="utf-8")
    os.replace(str(tmp_path), str(path))


def add_skill(
    skill_name: str,
    score: int = None,
    project_root: Path = None,
):
    """新建 skill 后记录状态（pending）。"""
    with StateLock(project_root):
        state = load_state(project_root)
        state["skills"][skill_name] = {
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "score": score,
            "archived_at": None,
            "archived_to": None,
        }
        save_state(state, project_root)
    regenerate_readme(project_root)


def archive_skill(
    skill_name: str,
    archived_to: str,
    project_root: Path = None,
):
    """归档 skill：单次原子状态更新（消除双写问题）。"""
    with StateLock(project_root):
        state = load_state(project_root)
        entry = state["skills"].get(skill_name)
        if entry is None:
            state["skills"][skill_name] = {
                "status": "archived",
                "created_at": None,
                "score": None,
                "archived_at": datetime.now().strftime("%Y-%m-%d"),
                "archived_to": archived_to,
            }
        else:
            entry["status"] = "archived"
            entry["archived_at"] = datetime.now().strftime("%Y-%m-%d")
            entry["archived_to"] = archived_to
        save_state(state, project_root)
    regenerate_readme(project_root)


def remove_skill(skill_name: str, project_root: Path = None):
    """删除 skill 状态记录（clean 命令调用）。"""
    with StateLock(project_root):
        state = load_state(project_root)
        if skill_name in state["skills"]:
            del state["skills"][skill_name]
            save_state(state, project_root)
    regenerate_readme(project_root)


def get_skill(skill_name: str, project_root: Path = None) -> dict | None:
    """查询单个 skill 状态，不存在返回 None。"""
    state = load_state(project_root)
    return state["skills"].get(skill_name)


def list_skills(status: str = None, project_root: Path = None) -> dict:
    """列出所有 skill（可按 status 过滤）。"""
    state = load_state(project_root)
    if status is None:
        return dict(state["skills"])
    return {k: v for k, v in state["skills"].items() if v.get("status") == status}


def regenerate_readme(project_root: Path = None):
    """从 .state.json 生成只读 README.md（覆盖写入）。"""
    state = load_state(project_root)
    readme_path = get_readme_path(project_root)

    pending = {k: v for k, v in state["skills"].items() if v.get("status") == "pending"}
    archived = {k: v for k, v in state["skills"].items() if v.get("status") == "archived"}

    lines = [
        "# skills-temp 技能状态",
        "",
        "<!-- 此文件由 skill-creator 自动生成，请勿手动编辑 -->",
        "",
        "### 当前待确认技能",
        "",
        "| Skill 名称 | 状态 | 创建日期 | 备注 |",
        "|-----------|------|---------|------|",
    ]
    for name, info in sorted(pending.items()):
        date = info.get("created_at", "")
        score = info.get("score")
        comment = "新创建的 skill"
        if score is not None:
            comment += f" (评分: {score}/100)"
        lines.append(f"| `{name}` | ⏳ 待确认 | {date} | {comment} |")

    lines += [
        "",
        "### ✅ 已归档技能",
        "",
        "| Skill 名称 | 归档日期 | 归档路径 | 状态 |",
        "|-----------|---------|---------|------|",
    ]
    for name, info in sorted(archived.items()):
        date = info.get("archived_at", "")
        dest = info.get("archived_to", "")
        lines.append(f"| `{name}` | {date} | {dest} | 已归档 |")

    lines.append("")
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text("\n".join(lines), encoding="utf-8")


def migrate_from_readme(project_root: Path = None) -> bool:
    """从现有 README.md 解析状态并生成 .state.json（迁移协议）。

    幂等：如果 .state.json 已存在且 version >= STATE_VERSION，跳过迁移。
    返回 True 表示执行了迁移，False 表示跳过。
    """
    state_path = _state_path(project_root)
    readme_path = get_readme_path(project_root)

    if state_path.exists():
        try:
            existing = json.loads(state_path.read_text(encoding="utf-8"))
            if existing.get("version", 0) >= STATE_VERSION:
                return False
        except (json.JSONDecodeError, OSError):
            pass

    if not readme_path.exists():
        save_state(_empty_state(), project_root)
        return True

    backup_path = readme_path.with_suffix(
        f".md.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )

    try:
        content = readme_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"❌ 读取 README.md 失败：{e}")
        return False

    backup_path.write_text(content, encoding="utf-8")
    print(f"📦 已备份 README.md -> {backup_path.name}")

    state = _empty_state()
    lines = content.split("\n")

    section = None
    for line in lines:
        stripped = line.strip()
        if "当前待确认技能" in stripped:
            section = "pending"
            continue
        if "已归档技能" in stripped:
            section = "archived"
            continue
        if stripped.startswith("###"):
            section = None
            continue

        if section and stripped.startswith("|") and "`" in stripped:
            parts = [p.strip() for p in stripped.split("|")]
            parts = [p for p in parts if p]
            if len(parts) < 2:
                continue
            name = parts[0].strip("`").strip()
            if not name or name == "Skill 名称":
                continue

            if section == "pending":
                date = parts[2] if len(parts) > 2 else ""
                score = None
                comment = parts[3] if len(parts) > 3 else ""
                if "评分:" in comment or "评分：" in comment:
                    import re
                    m = re.search(r"(\d+)/100", comment)
                    if m:
                        score = int(m.group(1))
                state["skills"][name] = {
                    "status": "pending",
                    "created_at": date.strip(),
                    "score": score,
                    "archived_at": None,
                    "archived_to": None,
                }
            elif section == "archived":
                date = parts[1] if len(parts) > 1 else ""
                dest = parts[2] if len(parts) > 2 else ""
                state["skills"][name] = {
                    "status": "archived",
                    "created_at": None,
                    "score": None,
                    "archived_at": date.strip(),
                    "archived_to": dest.strip(),
                }

    with StateLock(project_root):
        save_state(state, project_root)

    regenerate_readme(project_root)
    skill_count = len(state["skills"])
    print(f"✅ 迁移完成：从 README.md 导入 {skill_count} 个 skill 状态")
    return True
