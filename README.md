# skill-creator 项目

OpenClaw Skill 生命周期管理工具集，支持创建、验证、归档、批量处理 Skill。

## 安装

**环境要求**：Python ≥ 3.9，Windows / macOS / Linux

### 用户安装（仅使用）

将内层 `skill-creator/` 目录复制到 OpenClaw 的 skills 目录下即可：

```bash
# 复制 Skill 到 skills 目录
cp -r skill-creator/ ~/.openclaw/workspace/skills/skill-creator/

# 安装运行依赖
pip install -r ~/.openclaw/workspace/skills/skill-creator/requirements.txt

# 使用
cd ~/.openclaw/workspace/skills/skill-creator
python run.py create --interactive
```

`skill-creator/` 是最小完整运行单元，不依赖项目根目录的 `tests/`、`.agent_team/` 等文件。

### 开发者安装（贡献/测试）

```bash
git clone <repo-url> skill-creator
cd skill-creator

# 安装全部依赖（运行 + 开发）
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/ -v --tb=short
```

### 环境变量（可选）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENCLAW_SKILLS_TEMP` | 覆盖临时 skill 输出目录 | 自动检测（见下方） |
| `OPENCLAW_SKILLS_DIR` | 覆盖 skill 归档目录 | 自动检测（见下方） |
| `SKILL_CREATOR_DEV` | 设为 `1` 强制开发模式 | 未设置（自动检测） |

**路径自动检测**：未设置 `OPENCLAW_*` 环境变量时，根据目录结构自动判定运行模式：

- **开发模式**（parent 下有 `.git/` + `tests/`）：输出到 `<repo>/skills-temp/`，归档到 `<repo>/skills/`
- **安装模式**（默认）：输出到 `skill-creator/.skills-temp/`（内部隐藏目录），归档到 skills 父目录

安装模式下所有临时文件保持在 `skill-creator/` 内部，不外溢到 skills 共享目录。详见 [USAGE.md 路径解析](skill-creator/USAGE.md#-路径解析)。

## 项目结构

```
skill-creator/                          ← Git 仓库根目录
├── skill-creator/                      # Skill 本体（最小完整运行单元）
│   ├── run.py                          # CLI 入口（纯 argparse + dispatch）
│   ├── creator/                        # 业务逻辑模块包
│   │   ├── paths.py                    # 路径解析
│   │   ├── validators.py              # 名称/版本校验
│   │   ├── templates.py              # 模板引擎（Jinja2 + 发现 + 回退）
│   │   ├── scorer.py                  # 质量评分器（6 维度，含校准 + 改进报告）
│   │   ├── state_manager.py           # .state.json 结构化状态管理
│   │   ├── readme_manager.py          # 兼容层（转发到 state_manager）
│   │   ├── security.py               # 安全扫描引擎
│   │   ├── packager.py               # 打包引擎
│   │   ├── spec.py                    # 规约引擎
│   │   ├── examples.py               # 参考实现库（5 个内置样例）
│   │   ├── prefill.py                # 描述驱动预填充（样例匹配 + 内容适配）
│   │   ├── text_utils.py             # 文本工具（bigram / Jaccard / coverage）
│   │   └── commands/                  # 各 CLI 命令实现
│   ├── templates/                     # Jinja2 模板目录
│   ├── examples/                      # 内置参考样例（5 个）
│   ├── SKILL.md                       # 技能元数据
│   ├── USAGE.md                       # 使用指南
│   ├── README.md                      # 工具说明
│   └── requirements.txt               # 运行依赖（pyyaml, jinja2）
├── tests/                             # pytest 测试套件（项目根级）
│   ├── helpers.py                     # 路径常量统一提供
│   ├── conftest.py                    # pytest 配置
│   └── test_*.py                      # 各模块测试
├── .agent_team/                       # 团队协作文档
├── requirements-dev.txt               # 开发依赖（pytest + 引用 skill-creator/requirements.txt）
├── tmp/                               # 本地测试临时目录（不提交）
└── README.md                          # 本文件
```

## 快速使用

```bash
cd skill-creator

# ⭐ 推荐：交互式创建（自动触发需求细化，生成高质量骨架）
python run.py create --interactive

# 快速创建
python run.py create -n my-skill -d "描述"
```

完整命令参考见 [skill-creator/USAGE.md](skill-creator/USAGE.md)，工具概览见 [skill-creator/README.md](skill-creator/README.md)。

## 测试

```bash
# 从项目根目录执行
python -m pytest tests/ -v --tb=short
```

## 迭代状态

| Phase | 名称 | 状态 | 版本 |
|-------|------|------|------|
| 1.1 | batch 命令 + create_skill 提取 | ✅ | v1.1.0 |
| 1.2+1.3 | 移除硬编码 + pytest 基础测试 | ✅ | v1.2.0 |
| 2 | 模块化拆分（creator/ 包） | ✅ | v2.0.0 |
| 4 | 状态管理升级（.state.json） | ✅ | v3.0.0 |
| 5 | 安全扫描（Security Scanning） | ✅ | v4.0.0 |
| 6 | 模板系统增强（Jinja2） | ✅ | v5.0.0 |
| 7 | 验证能力增强 | ✅ | v6.0.0 |
| 8 | 打包与分发 | ✅ | v7.0.0 |
| 10 | 规约系统（Skill Specification） | ✅ | v8.0.0 |
| 11 | 富内容模板（Rich Content Templates） | ✅ | v9.0.0 |
| 12 | 内容感知评分（Content-Aware Scoring） | ✅ | v10.0.0 |
| 13 | 参考实现库（Reference Library） | ✅ | v11.0.0 |
| 14a | 项目结构规范化 | ✅ | v12.0.0 |
| 14b | 创建流程融合（意图深化） | ✅ | v13.0.0 |
| 14cd | 评分器校准 + 报告增强 | ✅ | v14.0.0 |
| 14e | 文档重组 | ✅ | v14.1.0 |
| 14f | 路径环境自适应 | ✅ | v14.2.0 |
| 15 | 内容质量下限保护 | ✅ | v15.0.0 |
| 16 | 创建流程收敛 + validate 批量 | ✅ | v16.0.0 |
| 17 | 深化鲁棒性增强 | ✅ | v17.0.0 |
| 17b | 工具链打磨 | ✅ | v17.1.0 |
| hotfix | 预填充匹配算法修复 | ✅ | v17.2.0 |
| 9 | 生态集成（ClawHub） | 🔲 远期 | — |

---

## 更新历史

### v17.2.0（Hotfix prefill-matching）— 2026-04-02

**预填充匹配算法修复**

- 新增 `bigram_coverage()` 替代 `bigram_jaccard()` 用于短描述 vs 长样例文本匹配（覆盖率算法）
- `find_similar_example` description 分支阈值从 0.3 下调至 0.25
- spec-based 关键词提取改为 `bigrams()` + `split()` 双模式，修复中文文本无法分词的问题
- 匹配逻辑从 `create_skill()` 上提至 `main_create()` 层：瀑布式匹配（spec → description 回退）
- `prefill_skill_content()` 新增 `matched_example` 参数，上游匹配结果单一来源透传
- 预填充命中率从 0% 恢复至正常水平

测试：571 → 573 passed

### v17.1.0（Phase 17b）— 2026-04-01

**工具链打磨**

- `archive --force`：已有同名 skill 时先备份再覆盖
- `examples --copy` 冲突处理：支持 overwrite / rename / cancel 三种策略
- `PLACEHOLDER_PATTERNS` 扩展英文模式（`TODO`, `FIXME`, `your ... here` 等）
- `state_manager` 备份清理：保留最近 1 个 `.state.json.bak`

### v17.0.0（Phase 17）— 2026-04-01

**深化鲁棒性增强**

- 按字段差异化阈值：`_FIELD_MIN_LENGTH` 替代全局 10 字阈值（如 `target_user` 仅 3 字）
- CJK 长度计算：`_effective_length()` 按字符计数（非 `len()`）
- 按字段组细粒度降级：`_clear_spec_group()` 支持 purpose / capabilities / commands / error_handling 独立回退
- `_check_answer_quality()` 答案质量预检整合差异化阈值

测试：531 → 565 passed

### v16.0.0（Phase 16）— 2026-04-01

**创建流程收敛 + validate 批量**

- CLI 帮助文案收敛：`--interactive` 标注"推荐"，`--guided` 标注"高级模式"
- `examples` 列表输出增加 `--interactive` 推荐提示
- `validate` 支持多路径批量验证、`--recursive` 递归扫描、`--json` 结构化输出
- 批量 validate 对不存在路径显式报错（纳入汇总 + JSON + 退出码 1）

测试：511 → 531 passed

### v15.0.0（Phase 15）— 2026-04-01

**内容质量下限保护**

- 描述驱动预填充：`prefill_skill_content()` 基于匹配样例自动填充 SKILL.md + README.md
- TODO 注释升级：`upgrade_todo_comments()` 注入匹配样例的步骤参考（Python/Shell 跨类型回退）
- 最低内容检测：content ≤ 5 分时输出逐行改进建议
- 深化问答扩展：新增 `error_cause` / `error_solution` / `dependencies_runtime` 3 个问题
- 深化答案质量预检：实时检测简短/重复/占位符回答，单次重试
- 样例库扩容：新增 `data-formatter` + `env-checker`
- 公共工具：`text_utils.py` 提供 `bigrams()` / `bigram_jaccard()` / `bigram_coverage()`
- 新增预填充模块：`prefill.py`（描述驱动预填充 + TODO 注释升级 + 跨类型回退）

### v14.2.0（Phase 14f）— 2026-04-01

**路径环境自适应**

- `paths.py` 新增 `_is_dev_mode()` 三级判定（环境变量 > .git+tests 双信号 > 安装模式默认）
- 安装模式下 `get_skills_temp_dir()` 指向 `skill-creator/.skills-temp/`（内部隐藏目录），不外溢
- 安装模式下 `get_skills_dir()` 指向 `skill-creator/` 的 parent（即 skills 目录本身）
- 新增 `SKILL_CREATOR_DEV=1` 环境变量强制开发模式
- 新增 `.skillignore` 排除 `.skills-temp/`

### v14.1.0（Phase 14e）— 2026-03-31

**文档重组**

- 项目级 README 增加安装方法、环境变量说明
- 详细 changelog 从 skill-creator/README.md 迁移到项目级 README
- skill-creator/README.md 精简为运行必需内容

### v14.0.0（Phase 14cd）— 2026-03-31

**评分器校准 + 报告增强**

- 新增模板原文检测：预生成基线文件（`_baseline_*.txt`），保留率 > 70% 时 content 封顶 5 分
- 新增内容相关性检查：SKILL.md 章节与 description 的 2-gram 覆盖率 < 20% 时 docs 扣 5 分
- 新增命令相关性检查：仅有 `example` 子命令时 functionality 扣 5 分，支持 Python 和 Shell 双类型
- 空壳 Skill 评分从 ~78 降至 55±5 分（Python 和 Shell 均适用）
- 评分报告升级为「可操作改进路径 + 预估提升分值」，按效果降序排列
- 高质量 Skill 评分偏差 ≤ 5 分（不受校准影响）

修改文件：`creator/scorer.py`
新增文件：`templates/*/baseline_*.txt`、`tests/test_calibration_phase14cd.py`

### v13.0.0（Phase 14b）— 2026-03-31

**创建流程融合（意图深化）**

- `create --interactive` 默认触发意图深化：收集 name+desc 后自动进入 8 个结构化问题引导
- 意图深化答案自动构建 `.skill-spec.yaml` → guided 模板渲染，一步生成高质量骨架
- 支持跳过深化（首问输入 `s` 或 `--skip-deepen`）
- validate 有 error 时自动降级到标准模板，保证创建必定成功
- `_interactive_deepen(reader=input)` + `build_spec_from_answers()` I/O 分离架构
- `--guided` 行为不变（两步语义冻结）

修改文件：`creator/commands/create.py`、`creator/spec.py`、`run.py`
新增文件：`tests/test_deepen_phase14b.py`

### v12.0.0（Phase 14a）— 2026-03-31

**项目结构规范化**

- 目录 `skillCreator/` 重命名为 `skill-creator/`（符合 `^[a-z][a-z0-9-]*$` 规范）
- 测试套件 `skill-creator/tests/` 迁出至项目根 `tests/`
- 新增 `tests/helpers.py` 统一路径常量，消除各测试文件分散计算
- `get_skills_temp_dir()` fallback 从 `parent.parent / "skills-temp"` 修正为 `parent / "skills-temp"`
- `get_skills_dir()` fallback 从 `parent` 修正为 `parent / "skills"`
- `archive` 命令新增旧路径迁移检测提示
- `.gitignore` 新增 `skills-temp/` 和 `skills/`

修改文件：`tests/conftest.py`、5 个 test_*.py、`creator/paths.py`、`creator/commands/archive.py`、`.gitignore`、两份 README
新增文件：`tests/helpers.py`

### v11.0.0（Phase 13）— 2026-03-30

**参考实现库（Reference Library）**

- 内置 5 个高质量样例 Skill（均通过 validate + scan，评分 ≥ 85）：
  - `simple-greeter`（入门）：问候工具
  - `file-analyzer`（中等）：文件分析器
  - `api-health-checker`（进阶）：API 健康检查
  - `data-formatter`（Phase 15 新增）：数据格式转换
  - `env-checker`（Phase 15 新增）：开发环境检查
- 新增 `examples` 子命令：列出、查看、复制内置样例
- `create --spec` 联动：自动推荐相似样例

新增文件：`examples/`、`creator/examples.py`、`tests/test_examples_phase13.py`
测试：367 → 405 passed

### v10.0.0（Phase 12）— 2026-03-30

**内容感知评分（Content-Aware Scoring）**

- 新增 `content` 评分维度（20 分），原有 5 维度权重调整
- content 子评分：占位符残留率、内容多样性、函数实质性、USAGE.md 示例完整性、规约覆盖率

修改文件：`creator/scorer.py`
新增文件：`tests/test_scoring_phase12.py`
测试：323 → 367 passed

### v9.0.0（Phase 11）— 2026-03-30

**富内容模板（Rich Content Templates）**

- 新增 `python-guided/` 和 `shell-guided/` 模板目录：`create --spec` 自动使用
- 规约字段驱动：命令映射为 argparse 子命令、Result 数据类、TODO 步骤注释
- `create_skill` 新增 `spec_variables` 参数启用富模板渲染

新增文件：`templates/python-guided/` 4 个 .j2、`templates/shell-guided/` 4 个 .j2
测试：290 → 323 passed

### v8.0.0（Phase 10）— 2026-03-30

**规约系统（Skill Specification）**

- 新增 `spec` 子命令：生成 `.skill-spec.yaml` 规约骨架
- `create --guided`：引导式创建（生成骨架 → 提示填充 → `--spec` 渲染）
- `create --spec`：从已有规约文件创建 Skill
- batch 集成：YAML 条目支持 `spec` 字段

新增文件：`creator/spec.py`、`tests/test_spec_phase10.py`
测试：251 → 290 passed

### v7.0.0（Phase 8）— 2026-03-27

**打包与分发（Packaging & Distribution）**

- 新增 `package` 命令：打包为 `.skill` 格式 zip 包
- 打包前自动 validate + scan，`.skillignore` 支持
- SHA256 校验和，包大小 > 10MB 警告

测试：251 用例通过（含 30 新增）

### v6.0.0（Phase 7）— 2026-03-27

**验证能力增强**

- `validate` 新增 7 个检查维度：shebang、文档字符串、异常处理、退出码、文档完整性、占位符残留、链接有效性

### v5.0.0（Phase 6）— 2026-03-27

**模板系统增强（Jinja2）**

- 引入 Jinja2 模板引擎，内置 `python` 和 `shell` 两种类型
- `--type` 和 `--template-dir` 参数，模板发现优先级

新增依赖：`jinja2>=3.1`
测试：186 用例通过

### v4.0.0（Phase 5）— 2026-03-26

**安全扫描能力**

- 新增 `scan` 子命令：6 类检测规则（密钥泄露、危险调用、敏感文件等）
- `validate` / `batch` 集成安全扫描

测试：141 用例通过

### v3.0.0（Phase 4）— 2026-03-25

**状态管理升级**

- 新增 `state_manager.py`：`.state.json` CRUD + 原子写入 + 文件锁
- 修复 archive 双写非原子和 clean 全局行匹配

### v2.0.0（Phase 2）— 2026-03-25

**模块化拆分**

- `run.py` 从 1274 行重构为 ~100 行 CLI 入口，业务逻辑迁移至 `creator/` 包

### v1.2.0（Phase 1.2+1.3）— 2026-03-25

- 引入 pytest 基础测试（62 用例）
- 移除硬编码 WSL 路径

### v1.1.0（Phase 1.1）— 2026-03-25

- 提取 `create_skill()` 纯函数
- 新增 `batch` 命令

### v1.0.0 — 2026-03-12

初始版本，实现 `create / validate / archive / clean` 命令。
