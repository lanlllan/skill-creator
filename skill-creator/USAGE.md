# Skill Creator - 使用指南

用于快速创建、验证 OpenClaw Skill 的脚手架工具。

---

## 🔰 运行环境

支持 **Windows / macOS / Linux**，使用系统 Python（≥ 3.9）。

```bash
pip install pyyaml jinja2
```

## ⭐ 推荐工作流

最高效的 Skill 开发路径：交互式创建自动触发需求细化，一步生成高质量骨架。

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  交互式创建      │ ──▶ │  需求细化（自动触发）   │ ──▶ │  验证 + 归档     │
│  create -i       │     │  规约骨架 → 填充       │     │  validate → archive │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
```

```bash
cd skill-creator

# 1. 交互式创建（推荐，自动引导需求细化）
python run.py create --interactive

# 2. 检查产出、编辑业务逻辑
#    - 将 run.py 中的 TODO 注释替换为真实实现
#    - 完善 SKILL.md 的各章节

# 3. 验证
python run.py validate ./path/to/my-skill

# 4. 归档到正式目录
python run.py archive my-skill
```

> **提示**：直接使用 `create -n xxx -d "描述"` 也可以快速创建，但产物为通用模板，需要更多手工定制。推荐首次创建时使用 `--interactive`。

---

## 🚀 快速开始

### 1. 交互式创建（推荐）

```bash
cd ~/.openclaw/workspace/skills/skill-creator
python run.py create --interactive
```

按照提示输入：
- Skill 名称（如 `log-analyzer`）
- 描述（如 "分析应用日志并生成报告"）
- 版本（默认 1.0.0）
- 作者
- 标签（如 `logging,analysis`）

交互模式会自动进行需求细化，生成包含 TODO 注释的业务骨架（而非通用模板）。

### 2. 快速创建

```bash
python run.py create \
  --name "test-runner" \
  --description "测试环境配置工具" \
  --version "1.0.0" \
  --author "Your Name" \
  --tags "testing,go,wsl"
```

**输出**：
```
📁 创建目录：<skills-temp 解析路径>/test-runner
📝 生成文件...
✅ 已创建：SKILL.md
✅ 已创建：run.py          # Shell 类型时为 run.sh
✅ 已创建：USAGE.md
✅ 已创建：README.md

📊 Skill 质量评分报告
...

✅ Skill 'test-runner' 创建完成！
   位置：<skills-temp 解析路径>/test-runner
   下一步：检查文档并确认后归档到 skills 目录
```

---

## 📋 命名规范

### Skill 名称规则

✅ **正确**：
- `test-runner`
- `log-analyzer`
- `wps-calendar`
- `deploy-tool`

❌ **错误**：
- `TestRunner`（大写）
- `test_runner`（下划线）
- `my skill`（空格）
- `test.runner`（点号）

**规则**：
- 全部小写字母
- 使用短横线 `-` 分隔单词
- 以字母开头
- 只允许字母、数字、短横线

正则：`^[a-z][a-z0-9-]*$`

---

## 🔧 命令参考

### `create` - 创建新 skill

| 参数 | 短 | 说明 | 必填 |
|------|---|------|------|
| `--name` | `-n` | Skill 名称（小写、短横线） | 非交互模式必填 |
| `--description` | `-d` | 简短描述 | 非交互模式必填 |
| `--version` | `-v` | 版本号（默认 1.0.0） | 否 |
| `--author` | `-a` | 作者（默认 OpenClaw Assistant） | 否 |
| `--tags` | `-t` | 标签，逗号分隔 | 否 |
| `--output` | `-o` | 输出目录（默认自动检测，见[路径解析](#-路径解析)） | 否 |
| `--interactive` | `-i` | ⭐ 交互式模式（推荐，自动触发需求细化） | 否 |
| `--type` | | Skill 类型：`python`（默认）或 `shell` | 否 |
| `--template-dir` | | 自定义模板目录路径（覆盖内置模板） | 否 |
| `--guided` | | 高级模式：仅生成规约骨架供手动编辑（适合需要精细控制规约内容的高级用户） | 否 |
| `--spec` | | 从已有规约文件创建（`.skill-spec.yaml` 路径），自动使用富内容模板 | 否 |
| `--strict` | | 严格模式：规约验证有任何问题时阻断创建 | 否 |
| `--skip-deepen` | | 跳过意图深化（交互模式下直接用标准模板） | 否 |

**互斥规则**：`--guided` 与 `--spec` 互斥。`--spec` 模式下 `--interactive` 无效。

**富模板路由**：`--spec` 路径自动使用 `python-guided/` 或 `shell-guided/` 模板（若存在），生成内容丰富的产物（规约 commands 映射为 argparse 子命令、Result 数据类、TODO 步骤注释、dependencies 前置依赖等）。若 guided 模板目录不存在则降级到标准模板。

**示例**：
```bash
# 最简单
python run.py create -n my-skill -d "描述"

# 完整参数
python run.py create -n log-analyzer -d "日志分析工具" -v 1.2.0 -a "DevTeam" -t "logging,analysis" -o ./custom-dir

# 创建 shell 类型 skill
python run.py create -n deploy-script -d "自动部署脚本" --type shell

# 使用自定义模板目录
python run.py create -n custom-skill -d "自定义模板" --template-dir ./my-templates

# 从已有规约文件创建
python run.py create --spec path/to/.skill-spec.yaml -o ./output

# 高级：引导式创建（先生成规约骨架，需手动填充后再渲染）
python run.py create --guided -n api-monitor -d "API 健康监控"

# 严格模式（规约验证必须全部通过才创建）
python run.py create --spec path/to/.skill-spec.yaml --strict
```

### `spec` - 规约骨架生成与验证

```bash
# 生成规约骨架
python run.py spec -n my-skill -d "描述" -o ./output-dir

# 验证规约文件
python run.py spec --validate path/to/.skill-spec.yaml
```

| 参数 | 短 | 说明 | 必填 |
|------|---|------|------|
| `--name` | `-n` | Skill 名称（生成模式下必填） | 生成模式 |
| `--description` | `-d` | 描述（生成模式下必填） | 生成模式 |
| `--version` | `-v` | 版本号（默认 1.0.0） | 否 |
| `--author` | `-a` | 作者 | 否 |
| `--tags` | `-t` | 标签，逗号分隔 | 否 |
| `--output` | `-o` | 规约输出目录（默认当前目录） | 否 |
| `--validate` | | 验证模式：指向 `.skill-spec.yaml` 路径 | 验证模式 |

**验证检查项**：
- error 级别：字段非空、非占位符复制
- warning 级别：长度合规、purpose.problem 与 meta.description 不完全相同

**规约文件格式**（`.skill-spec.yaml`）：

包含以下段：`meta`（基础信息）、`purpose`（问题/目标用户/场景）、`capabilities`（核心能力）、`commands`（子命令定义）、`error_handling`（错误处理）、`dependencies`（依赖）。每个字段附有 `[指令]`、`[好的示例]`、`[差的示例]` 注释引导。

---

### `validate` - 验证现有 skill

```bash
# 验证单个 skill
python run.py validate ~/.openclaw/workspace/skills/test-writer

# 批量验证多个 skill
python run.py validate ./skill-a ./skill-b ./skill-c

# 递归扫描目录下所有包含 SKILL.md 的子目录
python run.py validate --recursive ./skills/

# JSON 输出（便于 CI 集成）
python run.py validate --json ./my-skill

# 跳过安全扫描
python run.py validate ./my-skill --no-security
```

| 参数 | 短 | 说明 |
|------|---|------|
| `paths` | | skill 目录路径（位置参数，支持多个） |
| `--recursive` | `-r` | 递归扫描目录下包含 SKILL.md 的一级子目录 |
| `--json` | | JSON 格式输出（`{skills: [{name, score, errors, warnings}]}`） |
| `--no-security` | | 跳过安全扫描（默认开启） |

**检查项**：
- [ ] SKILL.md 存在
- [ ] 包含 YAML front matter
- [ ] front matter 包含必需字段（name, description, version）
- [ ] name 格式正确
- [ ] version 符合语义化版本格式（x.y.z）
- [ ] 入口脚本存在（Python: `run.py` / Shell: `run.sh`）
- [ ] 入口脚本可执行权限
- [ ] 安全扫描（默认开启，发现以 warning 形式展示，不影响退出码）
- [ ] 入口脚本 shebang 检查（warning）
- [ ] 入口脚本模块文档字符串或头部注释（warning）
- [ ] 入口脚本异常处理（warning）
- [ ] 入口脚本退出码处理（warning）
- [ ] 文档完整性：USAGE.md 存在性及 SKILL.md 章节完整性（warning）
- [ ] 占位符残留检测 `{{...}}`（error）
- [ ] Markdown 本地链接有效性（warning）

**输出示例**：
```
🔍 验证 skill：<skill 目录路径>

🔒 安全扫描：
  ⚠️  [security] [DANGEROUS_EVAL] run.py:42
     检测到动态执行调用

📊 正在进行质量评分...
📊 Skill 质量评分报告
...
✅ Skill 验证通过！
```

### `scan` - 安全扫描 skill 目录

```bash
# 文本报告
python run.py scan ./my-skill

# JSON 格式输出（适合 CI/管道消费）
python run.py scan ./my-skill --json
```

| 参数 | 说明 |
|------|------|
| `path` | skill 目录路径（位置参数） |
| `--json` | JSON 格式输出 |

**检测规则（6 类）**：

| 类别 | 严重度 | 说明 |
|------|--------|------|
| API 密钥模式 | error | `sk-`、`AKIA`、`ghp_`、`glpat-` 前缀 |
| 硬编码凭证赋值 | warning | `api_key=`、`password=` 等 |
| 敏感文件 | error | `.env`、`credentials.json`、`*.pem`、`*.key` |
| 动态执行 | warning | `eval()`、`exec()`、`__import__()` |
| shell=True | warning | `subprocess` + `shell=True` |
| os.system() | warning | `os.system()` 调用 |

**退出码**：`0`=无发现或仅 info 级别，`1`=存在 warning 或 error

### `archive` - 归档 skill 到正式目录

```bash
# 最简用法：省略 --dest，程序自动推导 skills/ 目录
python run.py archive my-skill

# 显式指定目标目录
python run.py archive my-skill --dest ~/.openclaw/workspace/skills

# 当 create 使用了 --output 自定义目录时，建议显式指定 --source
python run.py archive my-skill --source ./custom-dir

# 仅演练，不实际移动
python run.py archive my-skill --dry-run
```

### `clean` - 清理待确认目录中的 skill

```bash
# 默认源目录（由程序自动推导）
python run.py clean my-skill

# 自定义源目录
python run.py clean my-skill --source ./custom-dir

# 仅演练，不实际删除
python run.py clean my-skill --source ./custom-dir --dry-run
```

### `package` - 打包 skill 为 .skill 文件

将验证通过的 skill 目录打包为 `.skill` 格式 zip 包：

```bash
# 基本用法
python run.py package ./my-skill

# 指定输出目录
python run.py package ./my-skill --output ./dist

# 强制打包（即使 validate/scan 有 error）
python run.py package ./my-skill --force
```

| 参数 | 短 | 说明 | 必填 |
|------|---|------|------|
| `path` | | skill 目录路径（位置参数） | 是 |
| `--output` | `-o` | 包输出目录（默认 skill 同级目录） | 否 |
| `--force` | | 即使检查有 error 也强制打包 | 否 |

**打包流程**：
1. 前置检查：自动执行 `validate` + `scan`，error 级发现阻断打包（`--force` 覆盖）
2. 加载 `.skillignore`：排除用户指定的文件
3. 收集文件：排除 dotfiles、`__pycache__`、`.git`、`*.pyc`、`*.skill` 等
4. 创建 zip 包：内部保持 `skill-name/` 顶层目录，路径统一 POSIX 格式
5. 计算 SHA256 校验和

**输出示例**：
```
📦 打包 skill：my-skill
🔍 前置检查...
  ✅ 检查通过
📁 收集文件：12 个
📦 创建包：/path/to/my-skill.skill (45.2 KB)
🔑 SHA256: a1b2c3d4e5f6...
✅ 打包完成！
```

**退出码**：`0`=打包成功，`1`=打包失败

#### .skillignore 文件

在 skill 目录下创建 `.skillignore` 文件，列出打包时需要排除的文件模式：

```
# 排除测试数据
tests/
test_*.py

# 排除临时文件
*.log
*.tmp
temp_*

# 排除文档草稿
drafts/
```

**语法说明**：
- 支持 fnmatch 基础语法（`*` 匹配任意字符、`?` 匹配单个字符、`[seq]` 匹配字符集）
- `#` 开头为注释，空行忽略
- **不支持** `!` 反排除和 `**/` 递归匹配（gitignore 高级语法）
- `.skillignore` 文件自身不会被打包

**始终被排除的内容**（无论是否配置 `.skillignore`）：
- 所有 dotfiles（`.*`）—— `.git`、`.env`、`.venv` 等
- `__pycache__/`、`.pytest_cache/`、`node_modules/` 等系统目录
- `*.pyc`、`*.pyo` 编译文件
- `*.skill` 文件（工具产物不打包）

### `examples` - 查看内置参考样例

浏览、查看和复制内置的高质量样例 Skill：

```bash
# 列出所有内置样例（按复杂度排序）
python run.py examples

# 查看指定样例的详细说明（输出 SKILL.md 内容）
python run.py examples --show simple-greeter

# 复制样例到当前目录（作为新项目起点）
python run.py examples --copy file-analyzer -o .

# 复制样例到指定目录
python run.py examples --copy api-health-checker -o ./my-skills
```

| 参数 | 短 | 说明 | 必填 |
|------|---|------|------|
| `--show` | | 查看指定样例的详细说明 | 否 |
| `--copy` | | 复制指定样例到目标目录 | 否 |
| `--output` | `-o` | 复制目标目录（默认当前目录） | 否 |

**内置样例**：

| 样例名 | 复杂度 | 说明 |
|--------|--------|------|
| `simple-greeter` | 入门 | 问候工具，演示基本 argparse + Result 数据类 |
| `file-analyzer` | 中等 | 文件分析器，演示文件系统遍历 + 统计报告 |
| `api-health-checker` | 进阶 | API 健康检查，演示网络请求 + 批量检测 + YAML 配置 |
| `data-formatter` | 中等 | 数据格式转换工具 |
| `env-checker` | 中等 | 开发环境检查工具 |

**相似推荐联动**：创建时如果描述或规约内容与某个内置样例相似，会自动匹配并预填充参考内容。

---

### `batch` - 批量创建（从 YAML 文件）

从 YAML 文件批量创建多个 skill，单条失败不阻断整批：

`skills.yaml`:
```yaml
skills:
  - name: log-analyzer
    description: 日志分析工具
    tags: [logging, analysis]
    version: 1.0.0
  - name: config-sync
    description: 配置同步工具
    tags: [config, sync]
    output: ./custom-dir   # 可选，指定输出目录
```

```bash
# 基本用法
python run.py batch --file skills.yaml

# 启用安全扫描准入门禁
python run.py batch --file skills.yaml --fail-on-security
```

| 参数 | 说明 |
|------|------|
| `--file` / `-f` | 技能列表文件（YAML 格式，必填） |
| `--fail-on-security` | 安全扫描有 error 级别发现时计为失败 |

**安全扫描集成**：
- 每个 skill 创建成功后自动执行安全扫描
- 默认模式：安全发现不影响退出码（仅在汇总报告中展示）
- `--fail-on-security`：error 级安全发现的 skill 计为"失败"，目录保留但不写入状态

**退出码**：`0`=全部成功，`1`=有失败，`2`=YAML 格式错误  
**汇总报告**：输出成功（含评分）/ 失败（含原因）/ 跳过（重复或目录已存在）/ 安全风险 四类统计。

---

## 📂 生成的文件结构

### Python 类型（默认）

```
skill-name/
├── SKILL.md          # 技能说明（含 front matter）
├── run.py            # 主入口（可执行，755）
├── USAGE.md          # 使用指南
└── README.md         # 快速入门
```

### Shell 类型（`--type shell`）

```
skill-name/
├── SKILL.md          # 技能说明（含 front matter，type: shell）
├── run.sh            # Shell 脚本入口（可执行，755）
├── USAGE.md          # 使用指南
└── README.md         # 快速入门
```

### SKILL.md 模板

已自动填充：
- `name`: 你提供的名称
- `description`: 描述
- `version`: 版本号
- `author`: 作者
- `tags`: 标签列表
- `date`: 当前日期

### 入口脚本模板

**Python 类型**（`run.py`）包含：
- Shebang (`#!/usr/bin/env python3`)
- Result 数据类（结构化返回结果）
- 输入校验函数 `validate_input()`
- argparse 子命令分发
- 异常捕获与退出码

**Shell 类型**（`run.sh`）包含：
- Shebang (`#!/usr/bin/env bash`)
- `set -euo pipefail` 严格模式
- 分级日志函数（log_info / log_ok / log_warn / log_error）
- case/esac 子命令分发
- 参数解析与 usage 帮助

### USAGE.md 模板

使用指南模板，包含：
- 快速开始
- 命令参考表格
- 配置示例
- 故障排除

### README.md 模板

快速入门文档：
- 一句话介绍
- 安装步骤
- 文档链接

---

## ✅ 验证检查清单

创建完成后会自动运行验证：

- [x] SKILL.md 存在且包含 front matter
- [x] front matter 包含 name、description、version
- [x] name 符合命名规范（小写、短横线）
- [x] version 符合语义化版本格式（x.y.z，create 强制 / validate 警告）
- [x] 入口脚本存在（Python: `run.py` / Shell: `run.sh`）
- [x] 入口脚本有 shebang 和主函数
- [ ] 入口脚本有可执行权限（自动设置）
- [ ] .state.json 已更新（skills-temp/README.md 自动生成）
- [ ] 所有模板变量已替换

---

## 🔄 完整工作流程

```
1. 创建技能（推荐交互式，自动引导需求细化）
   python run.py create --interactive
   
   # 或快速创建（跳过交互）
   python run.py create -n my-skill -d "描述"
   
2. 检查生成的文件
   ls skills-temp/my-skill/
   
3. 编辑和定制
   - 将 run.py 中的 TODO 注释替换为真实业务逻辑
   - 完善 SKILL.md 的各个章节
   - 添加 templates/、utils/ 等目录（如需要）
   
4. 验证
   python run.py validate skills-temp/my-skill/
   
5. 查看评分报告中的改进建议
   （报告会列出具体改进路径和预估提升分值）
   
6. 归档（省略 --dest 自动推导目标目录）
   python run.py archive my-skill
   # 如需指定目标目录或自定义源目录，使用 --dest / --source
   
7. 验证归档成功
   openclaw skills list
   openclaw skills info my-skill
```

---

## 📁 路径解析

Skill Creator 根据运行环境自动选择路径策略，无需手动配置。

### 环境变量（最高优先级）

| 变量 | 说明 |
|------|------|
| `OPENCLAW_SKILLS_TEMP` | 显式覆盖临时 skill 输出目录 |
| `OPENCLAW_SKILLS_DIR` | 显式覆盖 skill 归档目录 |
| `SKILL_CREATOR_DEV` | 设为 `1` 强制开发模式 |

### 自动模式检测

未设置环境变量时，根据目录结构自动判定：

| 模式 | 判定条件 | `get_skills_temp_dir` | `get_skills_dir` |
|------|---------|----------------------|------------------|
| 开发模式 | parent 下有 `.git/` 且 `tests/` | `<repo>/skills-temp/` | `<repo>/skills/` |
| 安装模式 | 默认（安全侧倒） | `skill-creator/.skills-temp/` | `skill-creator/` 的 parent |

**安装模式示例**（skill-creator 作为独立 Skill 安装到 OpenClaw）：

```
~/.openclaw/workspace/skills/         ← get_skills_dir() 指向此处
├── skill-creator/
│   ├── .skills-temp/                 ← get_skills_temp_dir()（内部隐藏，不外溢）
│   │   └── new-skill/
│   └── run.py
├── other-skill/
└── archived-skill/                   ← archive 归档到此处
```

安装模式下所有临时文件存放在 `skill-creator/.skills-temp/` 内部，不会污染 skills 共享目录。

---

## 🐛 常见问题

### Q: 创建时提示"名称不符合规范"？

**A**: 确保名称：
- 全部小写
- 以字母开头
- 只含字母、数字、短横线
- 示例：`log-analyzer` ✅，`LogAnalyzer` ❌

### Q: 如何添加自定义模板？

**A**: 使用 `--template-dir` 参数指定自定义模板目录。目录中放置 `.j2` 后缀的 Jinja2 模板文件（如 `SKILL.md.j2`、`run.py.j2`）。变量使用 `{{ variable }}` 格式，支持 `{% if %}` / `{% for %}` 条件和循环语法。

```bash
python run.py create -n my-skill -d "描述" --template-dir ./my-templates
```

### Q: 入口脚本缺少可执行权限怎么办？

**A**: Skill Creator 会自动设置 `chmod +x`。如果失败，手动：
```bash
chmod +x skill-name/run.py   # Python 类型
chmod +x skill-name/run.sh   # Shell 类型
```

### Q: 如何批量创建多个 skill？

**A**: 使用 `batch --file` 命令，传入 YAML 格式的列表文件：
```bash
python run.py batch --file skills.yaml
```
详见 [batch 命令](#batch---批量创建从-yaml-文件) 章节。

---

## 🎯 最佳实践

1. **先验证后归档**：使用 `validate` 检查技能完整性
2. **遵循命名规范**：保持 skill 名称一致性
3. **文档先行**：SKILL.md 完整描述功能和用法
4. **示例代码**：提供可运行的代码片段
5. **错误处理**：入口脚本妥善处理异常，返回明确错误信息

---

## 📊 模板变量参考

| 变量 | 来源 | 说明 |
|------|------|------|
| `{{name}}` | 参数 | Skill 名称 |
| `{{description}}` | 参数 | 描述 |
| `{{version}}` | 参数 | 版本号，默认 1.0.0 |
| `{{author}}` | 参数 | 作者，默认 OpenClaw Assistant |
| `{{tags}}` | 参数 | 标签列表 |
| `{{date}}` | 自动 | 当前日期（YYYY-MM-DD） |
| `{{name_title}}` | 自动 | 标题格式名称（如 `my-skill` -> `My Skill`） |
| `{{has_config}}` | 可选 | 布尔值，shell 类型中控制是否生成配置文件相关内容 |

---

## 🔗 相关资源

- **OpenClaw 技能规范**：https://docs.openclaw.ai/skills
- **YAML Front Matter**：https://jekyllrb.com/docs/front-matter/
- **Python argparse**：https://docs.python.org/3/library/argparse.html
- **ClawHub CLI**：`npx clawhub` 技能发布和管理

---

*Skill Creator 版本：v2.0.0*  
*最后更新：2026-04-02*
