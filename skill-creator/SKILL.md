---
name: skill-creator
description: 创建符合 OpenClaw 规范的新 Skill，自动化生成目录结构、模板文件和文档
version: 14.1.0
author: Zhiheng Yang
tags: [tooling, scaffolding, development]
---

# Skill Creator - Skill 开发脚手架

> 自动化创建、初始化 OpenClaw Skill 的完整工具，包含规范检查、模板生成和验证功能

---

## 📋 Skill 概述

**技能名称**：`skill-creator`  
**用途**：根据 OpenClaw Skill 规范，快速创建、初始化新的 Skill，生成完整的目录结构和模板文件  
**适用场景**：
- 需要开发新的 Skill 功能
- 创建符合规范的 Skill 项目骨架
- 学习 Skill 开发流程
- 批量创建 Skill 原型

---

## 🎯 核心能力

### 1. 项目脚手架
- 生成标准 Skill 目录结构
- 创建必需的 `SKILL.md`（含 front matter）
- 生成入口脚本模板（Python: `run.py` / Shell: `run.sh`）
- 生成配置文件、模板等可选文件

### 2. 规范检查
- 验证 SKILL.md front matter 完整性
- 检查必需字段（name, description, version）
- 验证入口脚本基本结构（`run.py` 或 `run.sh`）
- 检测常见配置错误

### 3. 模板系统
- Jinja2 模板引擎，支持条件渲染（`if/for`）
- 内置类型：`python`（默认）、`shell`
- 模板发现优先级：`--template-dir` 用户目录 > 内置 `templates/<type>/` > `DEFAULT_TEMPLATES` 回退
- `--type` 参数选择 Skill 类型，`--template-dir` 参数覆盖内置模板
- 完全向后兼容：不指定参数时产物与旧版一致
- **富内容模板**（Phase 11）：`create --spec` 路径自动使用 `python-guided/` 或 `shell-guided/` 模板，规约字段驱动生成内容丰富的产物
- 规约驱动：命令自动映射为 argparse 子命令、Result 数据类内联、TODO 步骤注释、dependencies 消费

### 4. 打包与分发
- `package` 命令：将 skill 打包为 `.skill` 格式 zip 包
- 打包前自动执行 validate + scan 前置检查（error 阻断，`--force` 覆盖）
- `.skillignore` 文件支持（fnmatch 基础语法）排除不需要打包的文件
- 自动排除 dotfiles、`__pycache__`、`.git`、`*.pyc`、`*.skill` 等（`.skill-spec.yaml` 白名单豁免）
- SHA256 校验和输出，包大小超 10MB 发出 warning
- zip 内保持 `skill-name/` 顶层目录结构，路径统一 POSIX 格式

### 5. 规约系统（Skill Specification）
- `spec` 命令：生成 `.skill-spec.yaml` 规约骨架，含结构化注释和填写引导
- `spec --validate`：验证规约完整性（非空、非占位符复制、长度合规、非 description 复制）
- `create --guided`：引导式创建（生成规约骨架 → 提示填充 → 用 `--spec` 渲染）
- `create --spec`：从已有规约文件创建 Skill（加载 → 验证 → 模板渲染 → 复制规约到产出）
- `--strict` 模式：规约验证有任何 error 或 warning 时阻断创建
- 规约 schema 冻结：旧代码兼容新版 spec（忽略未知字段），新代码兼容旧版 spec（使用默认值）
- batch 集成：YAML 条目支持 `spec` 字段指定规约文件路径

### 7. 参考实现库（Reference Library）
- 内置 3 个高质量样例 Skill（均通过 validate + scan，评分 ≥ 85）：
  - `simple-greeter`（入门）：问候工具，演示基本 argparse 子命令 + Result 数据类
  - `file-analyzer`（中等）：文件分析器，演示文件系统遍历 + 统计报告
  - `api-health-checker`（进阶）：API 健康检查，演示网络请求 + 批量检测 + YAML 配置
- `examples` 命令：列出、查看、复制内置样例
- `create --spec` 联动：创建时自动推荐相似样例（Jaccard 关键词相似度）
- `create --guided` 联动：生成规约骨架后提示查看内置样例

### 6. 工作流管理
- 创建 → 确认 → 归档 流程
- 结构化状态管理：`.state.json` 原子写入，README.md 自动生成（只读视图）
- 支持 `archive/clean --source` 处理自定义源目录
- `batch --file` 命令：从 YAML 文件批量创建，含批内去重、幂等检查、汇总报告
- 锁机制防止并发写入冲突，自动清理超时残留锁

---

## 📁 Skill 结构

```
skill-creator/                  # Skill 本体（最小完整运行单元，不含测试）
├── run.py                      # CLI 入口（纯 argparse + dispatch）
├── creator/                    # 业务逻辑模块包
│   ├── paths.py                # 路径解析
│   ├── validators.py           # 名称/版本校验
│   ├── templates.py            # 模板渲染（Jinja2 + 回退）
│   ├── scorer.py               # 质量评分器（6 维度：structure/functionality/quality/docs/standard/content）
│   ├── security.py             # 安全扫描引擎
│   ├── packager.py             # 打包引擎（.skillignore / zip / SHA256）
│   ├── spec.py                 # 规约引擎（SkillSpec / 骨架生成 / 加载 / 验证）
│   ├── examples.py             # 参考实现库（样例列出 / 查看 / 复制 / 相似推荐）
│   ├── state_manager.py        # .state.json 结构化状态管理
│   ├── readme_manager.py       # 兼容层（转发到 state_manager）
│   └── commands/               # 子命令：create / validate / ... / examples
├── examples/                   # 内置参考样例（Phase 13）
│   ├── simple-greeter/         # 入门样例：问候工具
│   ├── file-analyzer/          # 中等样例：文件分析器
│   └── api-health-checker/     # 进阶样例：API 健康检查
├── templates/                  # Jinja2 模板目录
│   ├── python/                 # Python 类型模板（*.j2）
│   ├── python-guided/          # Python 规约驱动富模板（*.j2）
│   ├── shell/                  # Shell 类型模板（*.j2）
│   └── shell-guided/           # Shell 规约驱动富模板（*.j2）
├── SKILL.md                    # 技能说明
└── USAGE.md                    # 使用指南
```

> **注意**：测试代码（`tests/`）位于项目根目录而非 `skill-creator/` 内部，确保 Skill 目录仅含运行必需文件。

---

## 🔧 使用方式

### 推荐：交互式创建

```bash
# ⭐ 推荐方式：自动引导需求细化，生成高质量骨架
python skill-creator/run.py create --interactive
```

交互模式会：
1. 逐项引导输入名称、描述、版本、作者、标签
2. 自动触发需求细化，生成规约骨架
3. 渲染为包含 TODO 注释的业务骨架（而非通用模板）

### 引导式创建（规约驱动）

```bash
# 先生成规约骨架
python skill-creator/run.py create --guided -n api-monitor -d "API 健康监控"

# 填充规约后，从规约创建
python skill-creator/run.py create --spec .skill-spec.yaml -o ./output
```

### 快速创建

```bash
# 快速创建（跳过交互，直接生成通用模板）
python skill-creator/run.py create --name "my-skill" --description "我的新技能"

# 创建 Shell 类型
python skill-creator/run.py create -n deploy-script -d "自动部署脚本" --type shell
```

### 其他命令

```bash
# 验证现有 skill
python skill-creator/run.py validate ~/.openclaw/workspace/skills/existing-skill

# 归档 skill（省略 --dest 时自动推导 skills/ 目录）
python skill-creator/run.py archive my-skill

# 清理临时技能目录
python skill-creator/run.py clean my-skill

# 批量创建（从 YAML 文件）
python skill-creator/run.py batch --file skills-to-create.yaml

# 查看内置参考样例
python skill-creator/run.py examples

# 复制样例到当前目录
python skill-creator/run.py examples --copy file-analyzer -o .
```

---

## 📋 Skill 开发规范（本 skill 的产出）

### 1. 目录结构规范

**Python 类型（默认）**：
```
skill-name/
├── SKILL.md                    # 必需：技能说明（含 YAML front matter）
├── run.py                      # 必需：Python 主入口（可执行）
├── USAGE.md                    # 推荐：使用指南
└── README.md                   # 推荐：快速上手
```

**Shell 类型**（`--type shell`）：
```
skill-name/
├── SKILL.md                    # 必需：技能说明（含 YAML front matter，type: shell）
├── run.sh                      # 必需：Shell 脚本入口（可执行）
├── USAGE.md                    # 推荐：使用指南
└── README.md                   # 推荐：快速上手
```

### 2. SKILL.md Front Matter 规范

```yaml
---
name: skill-name                # 必需，小写、短横线分隔，如 "test-runner"
description: 简短描述            # 必需，一句话说明用途
version: 1.0.0                  # 必需，语义化版本
author: Your Name              # 可选，作者
tags: [testing, go]            # 可选，标签数组
dependencies: []               # 可选，依赖的其他技能
---

# Skill Name - 详细标题

## 📋 Skill 概述

...

## 🎯 核心能力

...

## 📁 Skill 结构

...

## 🔧 使用方式

...

## 📝 示例

...
```

### 3. 入口脚本规范

**Python 类型**（`run.py`）— 内置 Result 数据类 + 验证流程 + 错误处理：
```python
#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Result:
    success: bool = True
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

def cmd_example(args) -> Result:
    result = validate_input(args)
    if not result.success:
        return result
    # 业务逻辑...
    return result
```

**Shell 类型**（`run.sh`）— 严格模式 + 日志函数 + 子命令分发：
```bash
#!/usr/bin/env bash
set -euo pipefail
log_info()  { echo "ℹ️  $*"; }
log_error() { echo "❌ $*" >&2; }
main() {
    local cmd="$1"; shift
    case "${cmd}" in
        example) cmd_example "$@" ;;
        *) log_error "未知命令: ${cmd}"; exit 1 ;;
    esac
}
main "$@"
```

### 4. 推荐实践

- ✅ **文档完整**：SKILL.md 包含使用示例和完整说明
- ✅ **错误处理**：入口脚本正确处理异常，返回非零退出码
- ✅ **参数校验**：验证输入参数，提供清晰错误信息
- ✅ **日志输出**：使用 print / echo，便于调试
- ✅ **返回值**：main() 返回整数退出码（0=成功，非0=失败）
- ✅ **可执行权限**：`chmod +x run.py` 或 `chmod +x run.sh`
- ✅ **README**：提供快速上手指南

---

## 🎯 本 Skill 的设计理念

### 发现问题
- 手动创建 Skill 容易遗漏 front matter
- 目录结构不规范
- 文档不完整
- 验证困难
- 归档与清理流程繁琐

### 解决方案
- **脚手架**：一键生成完整项目结构
- **模板化**：内置标准模板，降低重复劳动
- **验证器**：自动检查常见问题
- **归档工具**：内置 `archive` 命令自动移动并更新 README
- **清理工具**：内置 `clean` 命令清理临时目录并同步 README
- **工作流集成**：覆盖 创建 → 验证 → 归档 → 清理 全流程

---

## 📊 使用示例

### 示例 1：创建测试工具 skill

```bash
python skill-creator/run.py create \
  --name "load-tester" \
  --description "HTTP 负载测试工具" \
  --tags testing,http,performance
```

生成结构：
```
load-tester/
├── SKILL.md (含 front matter)
├── run.py (基本框架)
├── USAGE.md (使用说明模板)
└── utils/ (示例工具函数)
```

### 示例 2：验证现有 skill

```bash
python skill-creator/run.py validate ~/.openclaw/workspace/skills/test-writer
```

输出：
```
🔍 验证 skill：~/.openclaw/workspace/skills/test-writer
📊 正在进行质量评分...
📊 Skill 质量评分报告
...
✅ Skill 验证通过！
```

### 示例 3：批量创建

`skills.yaml`:
```yaml
skills:
  - name: log-analyzer
    description: 日志分析工具
    tags: [logging, analysis]
  - name: config-sync
    description: 配置同步工具
    tags: [config, sync]
```

```bash
python skill-creator/run.py batch --file skills.yaml
```

---

## 🔍 验证检查清单

创建后自动运行检查：

- [ ] SKILL.md 存在且包含 front matter
- [ ] front matter 包含 name、description、version
- [ ] name 符合规范（小写、短横线）
- [ ] version 符合语义化版本格式（x.y.z）
- [ ] 入口脚本存在（Python: `run.py`，Shell: `run.sh`）
- [ ] 入口脚本有 shebang 和执行权限
- [ ] 可选文件合理性（templates/, utils/ 等）
- [ ] 文档完整性（SKILL.md 有使用示例）
- [ ] 入口脚本 shebang 检查（validate：warning）
- [ ] 入口脚本模块文档字符串或头部注释（validate：warning）
- [ ] 入口脚本异常处理（validate：warning）
- [ ] 入口脚本退出码处理（validate：warning）
- [ ] 文档完整性：USAGE.md 存在性及 SKILL.md 章节完整性（validate：warning）
- [ ] 占位符残留检测 `{{...}}`（validate：error）
- [ ] Markdown 本地链接有效性（validate：warning）

---

## 🛠️ 技术实现

### 模板引擎
- Jinja2 渲染引擎（`templates/<type>/*.j2`），支持条件/循环语法
- 保留 `DEFAULT_TEMPLATES` 硬编码作为兜底回退（向后兼容）
- 模板发现：用户 `--template-dir` > 内置 `templates/<type>/` > `DEFAULT_TEMPLATES`
- 支持变量：`{{ name }}`、`{{ description }}`、`{{ name_title }}`、`{{ has_config }}` 等
- `tags` 在生成时输出为 YAML 数组（如 `[tag1, tag2]`）

### 验证器
- 解析 YAML front matter（`yaml.safe_load`）
- 检查必需字段：`name`、`description`、`version`
- 正则检查 name 格式：`^[a-z][a-z0-9-]*$`
- 文件存在性与入口脚本（`run.py` / `run.sh`）可执行权限检查

### 质量评分器（scorer）
- 6 维度评分体系，满分 100 分：
  - **structure**（15 分）：目录结构完整性
  - **functionality**（25 分）：入口脚本功能健壮性
  - **quality**（20 分）：代码质量（异常处理、退出码等）
  - **docs**（10 分）：文档完整性（SKILL.md 章节、USAGE.md 存在性、Markdown 链接有效性）
  - **standard**（10 分）：编码规范（shebang、模块注释、占位符残留）
  - **content**（20 分）：内容质量（Phase 12 新增）
- **content 维度子评分**：
  - 占位符残留率（6 分）：检测 SKILL.md 中 "场景1/能力1" 等未替换占位符
  - 内容多样性（4 分）：SKILL.md "适用场景" 与 "核心能力" 段落的语义去重（bigram Jaccard 相似度）
  - 函数实质性（4 分）：入口脚本有效代码行数（排除 trivial 语句）
  - USAGE.md 示例完整性（3 分）：非占位符代码块计数
  - 规约覆盖率（3 分）：`.skill-spec.yaml` 字段填充率（无 spec 文件时满分）
- **校准策略**（Phase 14cd）：模板原文保留率封顶、内容相关性检测、仅 example 命令扣分
- 自动生成评分报告，含分维度得分和**可操作改进路径**（按效果排序，标注预估提升分值）

### 路径管理
- `create` 写入 `--output`（默认由 `get_skills_temp_dir()` 解析，fallback 指向 `<repo>/skills-temp/`）
- `archive` 归档目标由 `get_skills_dir()` 解析（fallback 指向 `<repo>/skills/`）
- `archive/clean` 默认从 `get_skills_temp_dir()` 查找源目录
- 所有 fallback 路径不超出 git 仓库根目录（`<repo>/`），环境变量 `OPENCLAW_SKILLS_TEMP` / `OPENCLAW_SKILLS_DIR` 优先级最高
- 当输出目录自定义时，建议显式传入 `--source`

---

## 📈 未来增强

- [x] 支持更多模板类型（shell script skill — Phase 6 已实现）
- [x] 内置参考实现库（Phase 13 已实现，含 3 个样例 + 相似推荐）
- [ ] 支持更多模板类型（Go skill、composite skill）
- [ ] 集成 clawhub 发布流程
- [ ] 生成 CI/CD 配置文件（GitHub Actions）
- [ ] 自动生成技能文档网站
- [x] 支持插件系统（`--template-dir` 自定义模板 — Phase 6 已实现）
- [ ] 集成测试框架（自动生成测试用例）

---

## 🔗 相关资源

- **OpenClaw Skill 开发指南**：https://docs.openclaw.ai/skills
- **YAML Front Matter 规范**：https://jekyllrb.com/docs/front-matter/
- **Jinja2 模板引擎**：https://jinja.palletsprojects.com/
- **ClawHub CLI**：`npx clawhub` 搜索、安装、同步 skills

---

*Skill 版本：v14.1.0*  
*最后更新：2026-03-31*  
*状态：生效中*
