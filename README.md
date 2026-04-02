# skill-creator

OpenClaw Skill 创建与质量管理工具集。包含两个核心产出：

- **`rules/`** — 4 条 Cursor Rules，沉淀了 Skill 创建的结构规范、格式标准和质量标准，供 AI 直接遵循
- **`skill-creator/`** — CLI 工具，提供交互式创建、模板渲染、质量评分、安全扫描、打包归档等能力

## 使用方式

根据模型能力选择路径。两条路径**共享同一套质量标准**，区别在于"谁来生成文件"。

### 路径 A：Rules 驱动（强模型推荐）

AI 直接按规则创建 Skill 文件，CLI 工具只用于**校验**。

```
AI 读取 rules/ → 直接生成完整 Skill → validate + score 校验 → 根据报告修正
```

**1. 安装 Rules**

将 `rules/*.mdc` 复制到工作区的 `.cursor/rules/` 目录：

```bash
cp rules/*.mdc <your-workspace>/.cursor/rules/
```

**2. AI 按 Rules 生成 Skill**

模型参考 4 条规则即可生成目录结构、SKILL.md、run.py、README.md 等全部文件。无需 CLI 交互。

**3. 校验（需要安装 CLI 工具）**

```bash
cd skill-creator
python run.py validate <skill-dir>   # 结构 + 内容检查
python run.py scan <skill-dir>       # 安全扫描
python run.py score <skill-dir>      # 质量评分（6 维度，满分 100）+ 改进建议
```

**4. 迭代**

score 命令输出可操作的改进路径和预估提升分值，AI 据此修改后重新 score。

**优势**：省去 CLI 交互流程，强模型可一步产出高质量 Skill（评分 ≥ 80）。

### 路径 B：CLI 工具辅助（弱模型 / 人工推荐）

工具通过交互问答**引导生成骨架**，再由 AI 或人工**填充内容**。

```
CLI 交互 → 生成规约 + 骨架 → AI/人工填充 TODO → validate + score 校验 → 修正
```

**1. 交互式创建**

```bash
cd skill-creator
python run.py create --interactive
```

工具引导流程：收集 name + description → 11 个结构化问题深化需求 → 生成 `.skill-spec.yaml` → 渲染模板骨架 → 自动预填充 + TODO 升级

**2. 填充内容**

模型或人工根据生成的 TODO 注释和参考样例，补充实际业务逻辑。

**3. 校验 + 迭代**

```bash
python run.py validate <skill-dir>
python run.py score <skill-dir>
```

**优势**：交互流程降低门槛，模板和预填充为弱模型提供内容起点。

### 两条路径对比

| | 路径 A：Rules 驱动 | 路径 B：CLI 工具辅助 |
|---|---|---|
| 适用对象 | GPT-4、Claude 等强模型 | 能力有限的模型或人工开发者 |
| 文件生成方 | AI 直接创建 | CLI 工具生成骨架 |
| 需要安装 Rules | 是 | 否 |
| 需要安装 CLI 工具 | 仅校验时需要 | 是（创建 + 校验） |
| 交互流程 | 无 | 11 个问题引导 |
| 典型评分 | ≥ 80（一步到位） | 60-75（需填充后迭代） |

## Rules 规则说明

`rules/` 目录下 4 条 `.mdc` 文件，按主题拆分：

| 文件 | 作用域 | 内容 |
|------|--------|------|
| `skill-structure.mdc` | 目录结构 | 命名规范 `^[a-z][a-z0-9-]*$`、必需文件清单、`.skill-spec.yaml` 规约格式和字段约束 |
| `skill-md-format.mdc` | SKILL.md | YAML frontmatter 格式、5 大必需章节（概述/核心能力/使用方式/示例/故障排除）、评分关键点 |
| `skill-run-py.mdc` | run.py | Result 数据类、argparse 子命令模式、功能维度 25 分加分项速查表 |
| `skill-quality.mdc` | 质量标准 | 6 维度评分模型（满分 100）、安全扫描规则、5 大常见扣分陷阱、高分检查清单 |

这些规则沉淀了 17 个迭代阶段的核心经验，覆盖了 573 条测试验证过的质量标准。

## 安装

**环境要求**：Python ≥ 3.9，Windows / macOS / Linux

### 仅安装 Rules（路径 A）

```bash
# 将 rules 复制到目标工作区
cp rules/*.mdc <your-workspace>/.cursor/rules/
```

如需使用 validate / scan / score 校验命令，还需安装 CLI 工具（见下方）。

### 安装 CLI 工具

**方式一：作为 Skill 安装**（推荐路径 B 用户）

将 `skill-creator/` 目录复制到 OpenClaw 的 skills 目录：

```bash
cp -r skill-creator/ ~/.openclaw/workspace/skills/skill-creator/
pip install -r ~/.openclaw/workspace/skills/skill-creator/requirements.txt
```

`skill-creator/` 是最小完整运行单元，不依赖项目根的 `tests/`、`rules/`、`.agent_team/` 等文件。

**方式二：开发者安装**（贡献/测试）

```bash
git clone <repo-url> skill-creator
cd skill-creator
pip install -r requirements-dev.txt
python -m pytest tests/ -v --tb=short
```

### 环境变量（可选）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENCLAW_SKILLS_TEMP` | 覆盖临时 skill 输出目录 | 自动检测 |
| `OPENCLAW_SKILLS_DIR` | 覆盖 skill 归档目录 | 自动检测 |
| `SKILL_CREATOR_DEV` | 设为 `1` 强制开发模式 | 未设置（自动检测） |

**路径自动检测**：未设置环境变量时，根据目录结构判定运行模式：

- **开发模式**（parent 下有 `.git/` + `tests/`）：输出到 `<repo>/skills-temp/`
- **安装模式**（默认）：输出到 `skill-creator/.skills-temp/`（内部隐藏目录，不外溢）

## CLI 命令速查

```bash
cd skill-creator

# 创建
python run.py create --interactive       # 推荐：交互式创建
python run.py create -n my-skill -d "描述"  # 快速创建
python run.py create --spec spec.yaml    # 从规约文件创建

# 质量
python run.py validate <skill-dir>       # 结构 + 内容验证
python run.py validate <dir1> <dir2> --recursive  # 批量验证
python run.py score <skill-dir>          # 质量评分 + 改进建议
python run.py scan <skill-dir>           # 安全扫描

# 参考
python run.py examples                   # 列出 5 个内置样例
python run.py examples --show <name>     # 查看样例内容
python run.py examples --copy <name>     # 复制样例到当前目录

# 管理
python run.py archive <skill-dir>        # 归档到 skills 目录
python run.py package <skill-dir>        # 打包为 .skill 文件
python run.py batch <yaml-file>          # 批量创建
python run.py clean                      # 清理临时文件
```

完整命令参考见 [skill-creator/USAGE.md](skill-creator/USAGE.md)。

## 项目结构

```
skill-creator/                          ← Git 仓库根目录
├── rules/                             # Cursor Rules（可独立使用）
│   ├── skill-structure.mdc            # 目录结构 + 命名规范
│   ├── skill-md-format.mdc            # SKILL.md 格式标准
│   ├── skill-run-py.mdc              # run.py 入口脚本模式
│   └── skill-quality.mdc             # 评分维度 + 安全 + 陷阱
├── skill-creator/                      # CLI 工具（最小完整运行单元）
│   ├── run.py                          # CLI 入口
│   ├── creator/                        # 业务逻辑模块包
│   │   ├── paths.py                    # 路径解析
│   │   ├── validators.py              # 名称/版本校验
│   │   ├── templates.py              # 模板引擎（Jinja2）
│   │   ├── scorer.py                  # 质量评分器（6 维度）
│   │   ├── state_manager.py           # .state.json 状态管理
│   │   ├── security.py               # 安全扫描引擎
│   │   ├── packager.py               # 打包引擎
│   │   ├── spec.py                    # 规约引擎
│   │   ├── examples.py               # 参考实现库（5 个内置样例）
│   │   ├── prefill.py                # 描述驱动预填充
│   │   ├── text_utils.py             # 文本工具
│   │   └── commands/                  # 各 CLI 命令实现
│   ├── templates/                     # Jinja2 模板
│   ├── examples/                      # 内置参考样例（5 个）
│   ├── SKILL.md / USAGE.md / README.md
│   └── requirements.txt               # 运行依赖
├── tests/                             # pytest 测试套件（573 passed）
├── .agent_team/                       # 团队协作文档
├── requirements-dev.txt               # 开发依赖
└── README.md                          # 本文件
```

## 测试

```bash
python -m pytest tests/ -v --tb=short
```

## 迭代状态

### v2.x — Rules 驱动（当前）

| Phase | 名称 | 状态 | 版本 |
|-------|------|------|------|
| rules | Cursor Rules 经验沉淀 | ✅ | v2.0.0 |
| 9 | 生态集成（ClawHub） | 🔲 远期 | — |

### v1.x — CLI 工具开发

| Phase | 名称 | 状态 | 版本 |
|-------|------|------|------|
| 1.1 | batch 命令 + create_skill 提取 | ✅ | v1.1 |
| 1.2+1.3 | 移除硬编码 + pytest 基础测试 | ✅ | v1.2 |
| 2 | 模块化拆分（creator/ 包） | ✅ | v1.3 |
| 4 | 状态管理升级（.state.json） | ✅ | v1.4 |
| 5 | 安全扫描（Security Scanning） | ✅ | v1.5 |
| 6 | 模板系统增强（Jinja2） | ✅ | v1.6 |
| 7 | 验证能力增强 | ✅ | v1.7 |
| 8 | 打包与分发 | ✅ | v1.8 |
| 10 | 规约系统（Skill Specification） | ✅ | v1.9 |
| 11 | 富内容模板（Rich Content Templates） | ✅ | v1.10 |
| 12 | 内容感知评分（Content-Aware Scoring） | ✅ | v1.11 |
| 13 | 参考实现库（Reference Library） | ✅ | v1.12 |
| 14a | 项目结构规范化 | ✅ | v1.13 |
| 14b | 创建流程融合（意图深化） | ✅ | v1.14 |
| 14cd | 评分器校准 + 报告增强 | ✅ | v1.15 |
| 14e | 文档重组 | ✅ | v1.16 |
| 14f | 路径环境自适应 | ✅ | v1.17 |
| 15 | 内容质量下限保护 | ✅ | v1.18 |
| 16 | 创建流程收敛 + validate 批量 | ✅ | v1.19 |
| 17 | 深化鲁棒性增强 | ✅ | v1.20 |
| 17b | 工具链打磨 | ✅ | v1.21 |
| hotfix | 预填充匹配算法修复 | ✅ | v1.22 |

---

## 更新历史

### v2.0.0 — 2026-04-02

**Rules 驱动 — 经验沉淀为 Cursor Rules**

- 新增 `rules/` 目录：4 条 `.mdc` 文件，沉淀 17 个迭代阶段的核心经验
- README 重构：双路径使用推荐（Rules 驱动 / CLI 辅助）
- 项目定位从"CLI 工具"演进为"Rules + 校验工具集"

### v1.22（Hotfix）— 2026-04-02

**预填充匹配算法修复**

- 新增 `bigram_coverage()` 替代 `bigram_jaccard()` 用于短描述 vs 长样例匹配
- spec-based 关键词提取改为 `bigrams()` + `split()` 双模式，修复中文分词问题
- 匹配逻辑上提至 `main_create()` 层：瀑布式匹配（spec → description 回退）
- `prefill_skill_content()` 新增 `matched_example` 参数，单一来源透传

### v1.21（Phase 17b）— 2026-04-01

**工具链打磨** — `archive --force`、`examples --copy` 冲突处理、占位符模式扩展

### v1.20（Phase 17）— 2026-04-01

**深化鲁棒性增强** — 按字段差异化阈值、CJK 长度计算、细粒度降级

### v1.19（Phase 16）— 2026-04-01

**创建流程收敛 + validate 批量** — `--interactive` 推荐标注、批量验证 + `--json`

### v1.18（Phase 15）— 2026-04-01

**内容质量下限保护** — 预填充、TODO 升级、答案预检、样例库扩容至 5 个

### v1.17（Phase 14f）— 2026-04-01

**路径环境自适应** — `_is_dev_mode()` 三级判定、安装模式隔离

### v1.16（Phase 14e）— 2026-03-31

**文档重组**

### v1.15（Phase 14cd）— 2026-03-31

**评分器校准** — 空壳评分 78→55、模板保留检测、可操作改进报告

### v1.14（Phase 14b）— 2026-03-31

**创建流程融合** — `--interactive` 11 问引导 + 自动构建规约

### v1.13（Phase 14a）— 2026-03-31

**项目结构规范化** — 目录重命名、测试迁出、路径修正

### v1.12（Phase 13）— 2026-03-30

**参考实现库** — 5 个内置样例（评分 ≥ 85）+ `examples` 子命令

### v1.11（Phase 12）— 2026-03-30

**内容感知评分** — 新增 content 维度（20 分）

### v1.10（Phase 11）— 2026-03-30

**富内容模板** — 规约字段驱动的 guided 模板

### v1.9（Phase 10）— 2026-03-30

**规约系统** — `spec` 子命令 + `--guided` + `--spec` 创建模式

### v1.8（Phase 8）— 2026-03-27

**打包与分发** — `package` 命令，`.skill` 格式

### v1.7（Phase 7）— 2026-03-27

**验证能力增强** — 7 个检查维度

### v1.6（Phase 6）— 2026-03-27

**模板系统增强** — Jinja2 引擎，python + shell 双类型

### v1.5（Phase 5）— 2026-03-26

**安全扫描** — 6 类检测规则

### v1.4（Phase 4）— 2026-03-25

**状态管理升级** — `.state.json` CRUD + 原子写入

### v1.3（Phase 2）— 2026-03-25

**模块化拆分** — `run.py` 从 1274 行重构为 CLI 入口 + `creator/` 包

### v1.2（Phase 1.2+1.3）— 2026-03-25

pytest 基础测试 + 移除硬编码

### v1.1（Phase 1.1）— 2026-03-25

`create_skill()` 提取 + `batch` 命令

### v1.0 — 2026-03-12

初始版本：`create / validate / archive / clean` 命令
