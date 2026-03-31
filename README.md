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
| `OPENCLAW_SKILLS_TEMP` | 临时 skill 输出目录 | `<安装目录>/../skills-temp/` |
| `OPENCLAW_SKILLS_DIR` | skill 归档目录 | `<安装目录>/../skills/` |

未设置时使用基于 `skill-creator/` 父目录的 fallback 路径，不依赖外部目录结构。

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
│   │   ├── examples.py               # 参考实现库
│   │   └── commands/                  # 各 CLI 命令实现
│   ├── templates/                     # Jinja2 模板目录
│   ├── examples/                      # 内置参考样例
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
| 9 | 生态集成（ClawHub） | 🔲 远期 | — |

---

## 更新历史

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

- 内置 3 个高质量样例 Skill（均通过 validate + scan，评分 ≥ 85）：
  - `simple-greeter`（入门）：问候工具
  - `file-analyzer`（中等）：文件分析器
  - `api-health-checker`（进阶）：API 健康检查
- 新增 `examples` 子命令：列出、查看、复制内置样例
- `create --spec` 联动：自动推荐相似样例（Jaccard 相似度）

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
