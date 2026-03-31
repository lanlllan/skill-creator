# skill-creator 项目

OpenClaw Skill 生命周期管理工具集，支持创建、验证、归档、批量处理 Skill。

## 项目结构

```
skill-creator/                          ← Git 仓库根目录
├── skill-creator/                      # Skill 本体（最小完整运行单元）
│   ├── run.py                          # CLI 入口（纯 argparse + dispatch）
│   ├── creator/                        # 业务逻辑模块包
│   │   ├── paths.py                    # 路径解析
│   │   ├── validators.py              # 名称/版本校验
│   │   ├── templates.py              # 模板引擎（Jinja2 + 发现 + 回退）
│   │   ├── scorer.py                  # 质量评分器（6 维度，含 content 维度）
│   │   ├── state_manager.py           # .state.json 结构化状态管理
│   │   ├── readme_manager.py          # 兼容层（转发到 state_manager）
│   │   ├── security.py               # 安全扫描引擎
│   │   ├── packager.py               # 打包引擎
│   │   ├── spec.py                    # 规约引擎
│   │   ├── examples.py               # 参考实现库
│   │   └── commands/                  # 各 CLI 命令实现
│   ├── templates/                     # Jinja2 模板目录
│   ├── examples/                      # 内置参考样例
│   ├── SKILL.md                       # 技能元数据
│   ├── USAGE.md                       # 使用指南
│   └── README.md                      # 工具说明与更新记录
├── tests/                             # pytest 测试套件（项目根级）
├── .agent_team/                       # 团队协作文档
├── requirements.txt                   # 运行依赖
├── requirements-dev.txt               # 开发依赖
├── tmp/                               # 本地测试临时目录（不提交）
└── README.md                          # 本文件
```

## 快速使用

```bash
cd skill-creator

# ⭐ 推荐：交互式创建（自动触发需求细化，生成高质量骨架）
python run.py create --interactive

# 快速创建（跳过交互，直接生成模板）
python run.py create -n my-skill -d "描述"

# 批量创建
python run.py batch --file skills.yaml

# 验证
python run.py validate ./path/to/skill

# 安全扫描
python run.py scan ./path/to/skill

# 打包
python run.py package ./path/to/skill

# 规约骨架生成
python run.py spec -n my-skill -d "描述"

# 从规约创建
python run.py create --spec .skill-spec.yaml

# 查看内置参考样例
python run.py examples

# 复制样例到当前目录
python run.py examples --copy simple-greeter -o .

# 归档
python run.py archive my-skill
```

详细使用说明见 [skill-creator/USAGE.md](skill-creator/USAGE.md)。

## 安装

**Python 版本**：≥ 3.9

```bash
# 安装运行依赖
pip install -r requirements.txt

# 安装开发依赖（含 pytest）
pip install -r requirements-dev.txt
```

**环境变量（可选）**：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENCLAW_SKILLS_TEMP` | 临时 skill 输出目录 | `<repo>/skills-temp/` |
| `OPENCLAW_SKILLS_DIR` | 归档目标目录 | `<repo>/skills/` |

## 测试约定

所有测试均在项目根目录的 `tmp/` 下进行：

```bash
cd skill-creator

# 推荐：交互式创建（自动引导需求细化）
python run.py create --interactive -o ../tmp

# 快速创建
python run.py create -n test-skill -d "测试" -o ../tmp
python run.py validate ../tmp/test-skill
# 测试完成后清理
Remove-Item -Recurse -Force ../tmp/test-skill
```

单元测试（从项目根目录执行）：

```bash
python -m pytest tests/ -v --tb=short
```

## 迭代状态

| Phase | 名称 | 状态 | 说明 |
|-------|------|------|------|
| 1.1 | batch 命令 + create_skill 提取 | ✅ 已完成 | v1.1.0 |
| 1.3 | 基础测试（pytest，62 用例） | ✅ 已完成 | v1.2.0 |
| 1.2 | 移除硬编码 WSL 路径 | ✅ 已完成 | v1.2.0 |
| 2   | 模块化拆分（creator/ 包） | ✅ 已完成 | v2.0.0 |
| 4   | 状态管理升级（.state.json） | ✅ 已完成 | v3.0.0 |
| 5   | 安全扫描（Security Scanning） | ✅ 已完成 | v4.0.0 |
| 6   | 模板系统增强（Jinja2） | ✅ 已完成 | v5.0.0 |
| 7   | 验证能力增强 | ✅ 已完成 | v6.0.0 |
| 8   | 打包与分发 | ✅ 已完成 | v7.0.0 |
| 10  | 规约系统（Skill Specification） | ✅ 已完成 | v8.0.0 |
| 11  | 富内容模板（Rich Content Templates） | ✅ 已完成 | v9.0.0 |
| 12  | 内容感知评分（Content-Aware Scoring） | ✅ 已完成 | v10.0.0 |
| 13  | 参考实现库（Reference Library） | ✅ 已完成 | v11.0.0 |
| 14a | 项目结构规范化 | ✅ 已完成 | v12.0.0 |
| 14b | 创建流程融合（意图深化） | ✅ 已完成 | v13.0.0 |
| 14cd | 评分器校准 + 报告增强 | ✅ 已完成 | v14.0.0 |
| 14e | 文档重组 | ✅ 已完成 | v14.1.0 |
| 9   | 生态集成（ClawHub） | 🔲 远期 | API 就绪后 |

## 更新历史

### v14.1.0（Phase 14e）— 2026-03-31

**文档重组**：以 `--interactive` 为推荐创建路径，USAGE.md 新增"推荐工作流"章节，参数表标注推荐项，changelog 迁移到项目级 README。

### v14.0.0（Phase 14cd）— 2026-03-31

**评分器校准 + 报告增强**：
- 新增模板原文保留率检测（content 维度封顶 5/20，保留率 > 70%）
- 新增内容相关性检测（docs 维度 -5，description 2-gram 覆盖率 < 20%）
- 新增仅 example 命令检测（functionality -5）
- Shell `--verbose` 检测细化：仅 case 分支/变量赋值计分，排除 help 文本
- 报告新增可操作改进路径（按效果排序，标注 `[+N分]`）
- 空壳评分从 ~78 校准到 55±5

修改文件：`creator/scorer.py`（+222/-30）  
新增文件：`templates/*/_baseline_*.txt`（4 个基线）、`tests/test_calibration_phase14cd.py`（22 用例）  
测试：426 → 448 passed

### v13.0.0（Phase 14b）— 2026-03-31

**创建流程融合（意图深化）**：
- 交互式创建（`create --interactive`）自动触发需求细化
- 引导式创建（`create --guided`）直接进入规约编写
- 非交互模式行为不变（向后兼容）

### v12.0.0（Phase 14a）— 2026-03-31

**项目结构规范化**：
- `skillCreator/` 重命名为 `skill-creator/`
- `tests/` 迁移到项目根目录
- 路径解析去硬编码，统一使用 `paths.py` 解析
- `conftest.py` 路径公式修正

### v11.0.0（Phase 13）— 2026-03-30

**参考实现库（Reference Library）**：内置 3 个高质量样例 Skill（simple-greeter、file-analyzer、api-health-checker），新增 `examples` 子命令。测试：367 → 405 passed。

### v10.0.0（Phase 12）— 2026-03-30

**内容感知评分（Content-Aware Scoring）**：新增 content 评分维度（20 分），含 5 个子评分项。测试：323 → 367 passed。

### v9.0.0（Phase 11）— 2026-03-30

**富内容模板（Rich Content Templates）**：新增 `python-guided/` 和 `shell-guided/` 模板目录，规约驱动生成富内容产物。测试：290 → 323 passed。

### v8.0.0（Phase 10）— 2026-03-30

**规约系统（Skill Specification）**：新增 `spec` 子命令、`create --guided`、`create --spec`、`--strict` 模式。测试：251 → 290 passed。

### v7.0.0（Phase 8）— 2026-03-27

**打包与分发**：新增 `package` 命令，`.skillignore` 支持，SHA256 校验。测试：251 passed。

### v6.0.0（Phase 7）— 2026-03-27

**验证能力增强**：validate 新增 7 个检查维度，评分器增加占位符扣分和链接加分。测试：221 passed。

### v5.0.0（Phase 6）— 2026-03-27

**模板系统增强**：Jinja2 引擎，内置 python/shell 模板，`--type` / `--template-dir` 参数。测试：186 passed。

### v4.0.0（Phase 5）— 2026-03-26

**安全扫描**：新增 `scan` 子命令，6 类检测规则，validate/batch 集成。测试：141 passed。

### v3.0.0（Phase 4）— 2026-03-25

**状态管理升级**：`.state.json` 结构化存储，原子写入，文件锁机制。测试：85 passed。

### v2.0.0（Phase 2）— 2026-03-25

**模块化拆分**：`run.py` 重构为 CLI 入口，业务逻辑迁移到 `creator/` 包。测试：62 passed。

### v1.2.0（Phase 1.2 + 1.3）— 2026-03-25

**pytest 基础测试 + WSL 路径硬编码移除**。测试：62 passed。

### v1.1.0（Phase 1.1）— 2026-03-25

**核心重构**：提取 `create_skill()` 纯函数，新增 `batch` 命令。

### v1.0.0 — 2026-03-12

初始版本：`create / validate / archive / clean` 命令。
