# skill-creator

创建符合 OpenClaw 规范的新 Skill 的脚手架工具。

## 快速开始

```bash
# 查看帮助
python run.py --help

# 创建 skill（非交互式）
python run.py create -n my-skill -d "我的技能描述"

# 交互式创建
python run.py create --interactive

# 验证现有 skill
python run.py validate ./path/to/skill

# 批量创建（从 YAML 文件）
python run.py batch --file skills.yaml

# 归档到正式目录
python run.py archive my-skill

# 清理临时目录
python run.py clean my-skill
```

## batch 命令 YAML 格式

```yaml
skills:
  - name: log-analyzer          # 必需
    description: 日志分析工具    # 必需
    version: 1.0.0              # 可选，默认 1.0.0
    author: DevTeam             # 可选
    tags: [logging, analysis]   # 可选
    output: /custom/path        # 可选，默认 skills-temp
  - name: config-sync
    description: 配置同步工具
```

## 测试

**单元测试（pytest）**：

```bash
cd skillCreator
python -m pytest tests/ -v --tb=short
```

**手动冒烟测试**（在项目根目录下执行）：

```bash
cd skillCreator

# create + validate + clean
python run.py create -n smoke-test -d "冒烟测试" -o ../tmp
python run.py validate ../tmp/smoke-test
python run.py clean smoke-test --source ../tmp

# batch 测试
python run.py batch --file ../tmp/test.yaml
```

## 更新记录

### v3.0.0（Phase 4）— 2026-03-25

**状态管理升级：README 表格 → .state.json 结构化存储**

核心变更：
- 新增 `creator/state_manager.py`：`.state.json` CRUD + 原子写入（`.tmp` + `os.replace`）+ 文件锁 + README 只读生成
- `skills-temp/README.md` 降级为只读视图，由 `.state.json` 自动生成（头部含"请勿手动编辑"标记）
- `creator/readme_manager.py` 降级为兼容层，内部转发到 `state_manager`

修复的已知缺陷：
- **archive 双写非原子**：原 `archive.py` 对 README 执行两次 `write_text()`，中间失败会丢失记录。现改为单次 `state_manager.archive_skill()` 原子操作
- **clean 全局行匹配**：原 `clean.py` 按 skill 名称匹配 README 全文，可能误删已归档记录。现通过 `state_manager.remove_skill()` 精确删除

新增功能：
- 迁移工具：首次运行自动从现有 README 解析并生成 `.state.json`（幂等，含备份）
- 锁机制：`.state.json.lock`（`O_CREAT | O_EXCL`），60 秒超时自动清理残留锁
- 查询接口：`get_skill()` / `list_skills(status=)` 支持按状态过滤

| 模块 | 职责变更 |
|------|---------|
| `creator/state_manager.py` | 新增：状态 CRUD、原子写入、锁、README 生成、迁移 |
| `creator/readme_manager.py` | 降级为兼容层（转发到 state_manager） |
| `creator/commands/create.py` | 改用 `state_manager.add_skill()` |
| `creator/commands/archive.py` | 改用 `state_manager.archive_skill()`（消除双写） |
| `creator/commands/clean.py` | 改用 `state_manager.remove_skill()`（消除全局匹配） |

测试：85 个用例全部通过（含 23 个新增 state_manager 测试，覆盖 CRUD / 原子写入 / README 生成 / 迁移幂等 / 锁机制 / 双写消除 / 全局匹配消除）。

### v2.0.0（Phase 2）— 2026-03-25

**模块化拆分：run.py → creator/ 包**

`run.py` 从 1274 行单文件重构为纯 CLI 入口（约 100 行），业务逻辑迁移至 `creator/` 包：

| 模块 | 职责 |
|------|------|
| `creator/paths.py` | 路径解析（env var > 脚本推断两级 fallback，显式 `project_root` 参数） |
| `creator/validators.py` | `validate_skill_name` / `validate_version` 纯函数 |
| `creator/templates.py` | `DEFAULT_TEMPLATES` + `generate_files()` |
| `creator/scorer.py` | `SkillScorer` 类（100 分评分器） |
| `creator/readme_manager.py` | `set_readme_entry` / `update_skills_temp_readme` |
| `creator/commands/create.py` | `create_skill()` + `main_create()` + `validate_skill()` |
| `creator/commands/validate.py` | `main_validate()` |
| `creator/commands/archive.py` | `main_archive()` |
| `creator/commands/clean.py` | `main_clean()` |
| `creator/commands/batch.py` | `main_batch()` |

CLI 接口完全不变，62 个单元测试全部通过（0.66s）。`run.py` 约 100 行。

### v1.2.0（Phase 1.2 + 1.3）— 2026-03-25

**Phase 1.3：引入 pytest 基础测试**

- 新增 `tests/` 目录，包含三个测试模块（共 62 个用例，全部通过）：
  - `test_validators.py`：`validate_skill_name` / `validate_version` 覆盖合法/非法边界
  - `test_create_skill.py`：`generate_files` 占位符全替换断言（DoD）+ `create_skill` 端到端
  - `test_batch.py`：null 拦截、复合去重键、失败原因粒度、YAML 格式错误
- `conftest.py` 提供 `skill_out` / `batch_yaml_factory` fixtures

**Phase 1.2：移除硬编码 WSL 路径**

- `get_skills_temp_dir()` 移除 `/mnt/d/qn/open-claw-files/skills-temp` 硬编码 fallback
- 仅保留两级查找：①环境变量 `OPENCLAW_SKILLS_TEMP` → ②脚本位置推断（`run.py` 上两级/`skills-temp`）
- 迁移方式：`$env:OPENCLAW_SKILLS_TEMP = "D:\your\path\skills-temp"`

**审查修复（review-v2.md Fix 1-3）**

- Fix 1：批内去重键改为 `(target_root, normalized_name)` 复合键，同名不同目录不再误跳过
- Fix 2：`name`/`description` 的 YAML `null` 显式拦截
- Fix 3：`create_skill` 各失败路径写入 `_out['failure_reason']`，批量报告原因结构化

### v1.1.0（Phase 1.1）— 2026-03-25

**核心重构：提取 `create_skill()` 纯函数**

- 新增 `create_skill(params: dict, _out: dict = None) -> int`：
  - `params` 字段契约（唯一来源）：`name / description / version / author / tags / output`
  - 入口校验：必需字段缺失抛 `ValueError`，未知字段打印警告后忽略
  - `tags` 同时支持 `list[str]` 和逗号分隔字符串，内部规范化为列表
  - `output=None` 自动回退到 `get_skills_temp_dir()`
- `main_create` 重构为薄层适配器，负责收集参数后调用 `create_skill()`
- **新增 `batch` 命令**（原为预留占位）：
  - 从 YAML 文件批量创建，单条失败不阻断整批
  - 批内重复名称自动跳过
  - 目标目录已存在自动跳过（幂等）
  - 汇总报告含成功评分/失败原因/跳过原因
  - 退出码：0=全部成功，1=有失败，2=YAML 解析错误
  - 参数 `--file / -f`（原占位参数 `--list` 已废弃）

### v1.0.0 — 2026-03-12

初始版本，实现 `create / validate / archive / clean` 命令。
