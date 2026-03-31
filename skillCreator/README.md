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

### v11.0.0（Phase 13）— 2026-03-30

**参考实现库（Reference Library）**

核心变更：
- 内置 3 个高质量样例 Skill，均通过 validate + scan，评分 ≥ 85：
  - `simple-greeter`（入门）：问候工具，演示 argparse 子命令 + Result 数据类
  - `file-analyzer`（中等）：文件分析器，演示文件系统遍历 + 统计报告
  - `api-health-checker`（进阶）：API 健康检查，演示网络请求 + 批量检测 + YAML 配置
- 新增 `examples` 子命令：列出所有样例（按复杂度排序）、查看样例详情（`--show`）、复制样例到目标目录（`--copy`）
- `create --spec` 联动：创建时自动推荐与规约最相似的内置样例（Jaccard 关键词相似度，阈值 0.15）
- `create --guided` 联动：生成规约骨架后提示查看 `examples` 命令

新增文件：`examples/` 目录（3 个样例）、`creator/examples.py`、`creator/commands/examples_cmd.py`、`tests/test_examples_phase13.py`
修改文件：`run.py`、`creator/commands/create.py`
测试：367 → 405 passed（+38 新增，含 7 个审查修复回归用例）

---

### v10.0.0（Phase 12）— 2026-03-30

**内容感知评分（Content-Aware Scoring）**

核心变更：
- 新增 `content` 评分维度（20 分），原有 5 维度权重同步调整（structure 20→15, functionality 30→25, quality 25→20, docs 15→10, standard 10→10）
- `content` 维度包含 5 个子评分项：
  - 占位符残留率（6 分）：检测 SKILL.md 中 "场景1/能力1" 等未替换占位符，阈值 0/20/50%
  - 内容多样性（4 分）：SKILL.md "适用场景" 与 "核心能力" 段落项 bigram Jaccard 相似度去重
  - 函数实质性（4 分）：入口脚本有效代码行数（排除 pass/import/shebang 等 trivial 语句）
  - USAGE.md 示例完整性（3 分）：非占位符代码块计数
  - 规约覆盖率（3 分）：`.skill-spec.yaml` 字段填充率（无 spec 文件时满分）
- 评分报告新增 content 维度建议（低于满分时提示改进方向）
- 基线兼容：高/中/低质量 skill 总分偏差 ≤ 5 分

修改文件：`creator/scorer.py`
新增文件：`tests/test_scoring_phase12.py`
测试：323 → 367 passed（+44 新增，含 1 个审查修复回归用例）

---

### v9.0.0（Phase 11）— 2026-03-30

**富内容模板（Rich Content Templates）**

核心变更：
- 新增 `templates/python-guided/` 模板目录（4 个 .j2）：`create --spec` 自动使用，规约字段驱动生成内容丰富的产物
- 新增 `templates/shell-guided/` 模板目录（4 个 .j2）：Shell 类型规约驱动模板（case/shift 参数解析）
- `generate_files` 新增 `guided` 参数：控制模板路由，guided 模板降级策略（目录不存在时降级到标准模板）
- `_expand_variables` 增加 `tags_list` 保留原始标签列表
- `spec_to_template_vars` 增加 `name_snake`、`dispatch_entries`、`arg_flag` 预处理
- `create_skill` 新增 `spec_variables` 参数：规约扩展变量传递
- `_create_from_spec` 传递 `spec_variables` 启用富模板渲染
- Python 模板：Result 数据类（含 `__bool__`）+ argparse 子命令自动生成 + TODO 步骤注释 + dispatch dict
- Shell 模板：set -euo pipefail + 分级日志 + case/shift 参数解析（boolean shift 1 / 非 boolean shift 2）
- dependencies 字段消费：SKILL.md 前置依赖段 + USAGE.md 环境要求段
- 向后兼容：不加 --spec 时产物与旧版一致

新增文件：`templates/python-guided/` 4 个 .j2、`templates/shell-guided/` 4 个 .j2、`tests/test_rich_templates_phase11.py`
修改文件：`creator/spec.py`、`creator/templates.py`、`creator/commands/create.py`
测试：290 → 323 passed（+33 新增，含 3 个审查修复回归用例）

---

### v8.0.0（Phase 10）— 2026-03-30

**规约系统（Skill Specification）**

核心变更：
- 新增 `spec` 子命令：生成 `.skill-spec.yaml` 规约骨架（含结构化注释和填写引导）
- `spec --validate`：验证规约完整性（非空、非占位符复制、长度合规、非 description 复制）
- `create --guided`：引导式创建（生成规约骨架 → 提示填充 → 用 `--spec` 渲染）
- `create --spec`：从已有规约文件创建 Skill（加载 → 验证 → 模板渲染 → 复制规约到产出）
- `--strict` 模式：规约验证 error 或 warning 均阻断创建
- 规约 schema 冻结兼容：旧代码忽略新字段，新代码缺失字段使用默认值
- batch 集成：YAML 条目支持 `spec` 字段指定规约文件路径
- packager 白名单：`.skill-spec.yaml` 豁免 dotfile 排除，打包后保留在包内
- 互斥规则：`--guided` / `--spec` 互斥；`--spec` 模式下忽略 `--interactive`

新增文件：`creator/spec.py`、`creator/commands/spec_cmd.py`、`tests/test_spec_phase10.py`
修改文件：`run.py`、`creator/commands/create.py`、`creator/commands/batch.py`、`creator/packager.py`
测试：251 → 290 passed（+39 新增）

---

### v7.0.0（Phase 8）— 2026-03-27

**打包与分发（Packaging & Distribution）**

核心变更：
- 新增 `package` 命令：将 skill 打包为 `.skill` 格式 zip 包
- 打包前自动执行 `validate` + `scan` 前置检查（error 阻断，`--force` 覆盖）
- `.skillignore` 文件支持（fnmatch 基础语法：`*`、`?`、`[seq]`），排除不需要的文件
- 自动排除 dotfiles、`__pycache__`、`.git`、`*.pyc`、`*.skill`（工具产物）等
- SHA256 校验和输出，包大小超 10MB 发出 warning
- zip 包内保持 `skill-name/` 顶层目录结构，路径统一 POSIX 格式

| 模块 | 职责变更 |
|------|---------|
| `creator/packager.py` | 新增：打包核心引擎（.skillignore 解析、文件收集、zip 创建、SHA256 计算） |
| `creator/commands/package.py` | 新增：package 子命令入口 |
| `run.py` | 修改：注册 package 子命令 + CLI 参数（`--output`、`--force`） |

测试：251 个用例全部通过（含 30 个新增打包测试）。无新增外部依赖。

### v6.0.0（Phase 7）— 2026-03-27

**验证能力增强（Validation Enhancement）**

核心变更：
- `validate` 新增 7 个检查维度：入口脚本 shebang；模块文档字符串/头部注释；异常处理；退出码；文档完整性（USAGE.md 存在 + SKILL.md 章节）；占位符 `{{...}}` 残留（error）；Markdown 本地链接有效性（前五项与链接为 warning）
- 评分器（`scorer.py`）：标准维度对占位符残留扣 3 分；文档维度对 Markdown 本地链接有效加 1 分

| 模块 | 职责变更 |
|------|---------|
| `creator/commands/validate.py` | 扩展：上述校验维度与严重度输出 |
| `creator/scorer.py` | 占位符扣分、文档链接加分 |

测试：221 个用例全部通过。

### v5.0.0（Phase 6）— 2026-03-27

**模板系统增强（Template Enhancement）**

核心变更：
- 引入 Jinja2 模板引擎，支持条件渲染（`if/for`）和模板继承
- 新增 `templates/` 目录，内置 `python` 和 `shell` 两种 Skill 类型模板
- 新增 `--type` 参数：选择 Skill 类型（`python` 默认 / `shell`）
- 新增 `--template-dir` 参数：用户自定义模板目录覆盖内置模板
- 模板发现优先级：用户目录 > 内置 `templates/<type>/` > `DEFAULT_TEMPLATES` 回退
- 完全向后兼容：不指定新参数时产物与旧版逐字节一致

Shell 类型模板特性：
- 生成 `run.sh`（含 `set -euo pipefail`、日志函数、子命令框架）
- SKILL.md 含 `type: shell` 标记
- 支持 `has_config` 条件渲染（控制 config.env 相关内容）

| 模块 | 职责变更 |
|------|---------|
| `creator/templates.py` | 重构：Jinja2 引擎 + 模板发现 + `_expand_variables` / `_discover_template_dir` / `_generate_jinja2` |
| `templates/python/*.j2` | 新增：Python 类型 Jinja2 模板（4 个文件） |
| `templates/shell/*.j2` | 新增：Shell 类型 Jinja2 模板（4 个文件） |
| `creator/commands/create.py` | 修改：传递 `skill_type` / `template_dir`；validate_skill 支持 run.sh |
| `run.py` | 修改：create 子命令新增 `--type` / `--template-dir` 参数 |

新增依赖：`jinja2>=3.1`

测试：186 个用例全部通过（含 40 个新增模板系统测试）。

### v4.0.0（Phase 5）— 2026-03-26

**安全扫描能力（Security Scanning）**

核心变更：
- 新增 `creator/security.py`：安全扫描核心引擎，6 类检测规则（模式表驱动）
- 新增 `scan` 子命令：独立安全扫描，支持 `--json` 输出
- `validate` 集成安全扫描：默认开启，发现以 warning 展示，不影响退出码（`--no-security` 跳过）
- `batch` 集成安全扫描：每个 skill 创建后自动扫描，`--fail-on-security` 将 error 级发现升级为失败

检测规则：

| 类别 | 规则 | 严重度 |
|------|------|--------|
| 密钥泄露 | API key 前缀（sk-、AKIA、ghp_、glpat-） | error |
| 密钥泄露 | 硬编码凭证赋值（api_key=、password= 等） | warning |
| 敏感文件 | .env、credentials.json、*.pem、*.key | error |
| 危险调用 | eval()、exec()、__import__() | warning |
| 危险调用 | subprocess + shell=True | warning |
| 危险调用 | os.system() | warning |

| 模块 | 职责变更 |
|------|---------|
| `creator/security.py` | 新增：ScanFinding dataclass + scan_directory + format_report |
| `creator/commands/scan.py` | 新增：scan 子命令入口 |
| `creator/commands/validate.py` | 修改：集成安全扫描 + --no-security + 非目录输入校验 |
| `creator/commands/batch.py` | 修改：安全扫描 + --fail-on-security + 汇总安全风险区域 |
| `creator/commands/create.py` | 修改：新增 skip_state 参数 |
| `run.py` | 修改：注册 scan 子命令 + 新增 CLI 参数 |

测试：141 个用例全部通过（含 56 个新增安全扫描测试）。无新增外部依赖。

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
