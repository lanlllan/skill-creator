# Skill Creator - 使用指南

用于快速创建、验证 OpenClaw Skill 的脚手架工具。

---

## 🔰 运行环境

支持 **Windows / macOS / Linux**，使用系统 Python（≥ 3.9）。无需安装额外依赖（仅需 `pyyaml`，已在 `requirements.txt` 中列出）。

```bash
pip install pyyaml
```

## 🚀 快速开始

### 1. 交互式创建

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
✅ 已创建：run.py
✅ 已创建：USAGE.md
✅ 已创建：README.md
⚠️  skills-temp/README.md 不存在或缺少技能表格，跳过更新

✅ Skill 'test-runner' 创建完成！
   位置：<skills-temp 解析路径>/test-runner
   下一步：确认后归档到 skills/ 目录
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
| `--output` | `-o` | 输出目录（默认由程序自动解析 skills-temp 路径） | 否 |
| `--interactive` | `-i` | 交互式模式 | 否 |

**示例**：
```bash
# 最简单
python run.py create -n my-skill -d "描述"

# 完整参数
python run.py create -n log-analyzer -d "日志分析工具" -v 1.2.0 -a "DevTeam" -t "logging,analysis" -o ./custom-dir
```

### `validate` - 验证现有 skill

```bash
python run.py validate ~/.openclaw/workspace/skills/test-writer
```

**检查项**：
- [ ] SKILL.md 存在
- [ ] 包含 YAML front matter
- [ ] front matter 包含必需字段（name, description, version）
- [ ] name 格式正确
- [ ] version 符合语义化版本格式（x.y.z）
- [ ] run.py 存在
- [ ] run.py 可执行权限

**输出示例**：
```
🔍 验证 skill：<skill 目录路径>

📊 正在进行质量评分...
📊 Skill 质量评分报告
...
✅ Skill 验证通过！
```

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
python run.py batch --file skills.yaml
```

**退出码**：`0`=全部成功，`1`=有失败，`2`=YAML 格式错误  
**汇总报告**：输出成功（含评分）/ 失败（含原因）/ 跳过（重复或目录已存在）三类统计。

---

## 📂 生成的文件结构

```
skill-name/
├── SKILL.md          # 技能说明（含 front matter）
├── run.py            # 主入口（可执行，755）
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

### run.py 模板

包含：
- Shebang (`#!/usr/bin/env python3`)
- 基本 argparse 结构
- 子命令示例
- 错误处理框架

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
- [x] run.py 存在
- [x] run.py 有 shebang 和 main() 函数
- [ ] run.py 有可执行权限（自动设置）
- [ ] .state.json 已更新（skills-temp/README.md 自动生成）
- [ ] 所有模板变量已替换

---

## 🔄 完整工作流程

```
1. 创建技能
   python run.py create -n my-skill -d "描述"
   
2. 检查生成的文件
   ls skills-temp/my-skill/
   
3. 编辑和定制
   - 修改 run.py 实现具体逻辑
   - 完善 SKILL.md 的各个章节
   - 添加 templates/、utils/ 等目录（如需要）
   
4. 验证
   python run.py validate skills-temp/my-skill/
   
5. 用户确认
   （用户查看并确认技能设计）
   
6. 归档（省略 --dest 自动推导目标目录）
   python run.py archive my-skill
   # 如需指定目标目录或自定义源目录，使用 --dest / --source
   
7. 验证归档成功
   openclaw skills list
   openclaw skills info my-skill
```

---

## 🐛 常见问题

### Q: 创建时提示"名称不符合规范"？

**A**: 确保名称：
- 全部小写
- 以字母开头
- 只含字母、数字、短横线
- 示例：`log-analyzer` ✅，`LogAnalyzer` ❌

### Q: 如何添加自定义模板？

**A**: 模板定义在 `creator/templates.py` 的 `DEFAULT_TEMPLATES` 字典中。可直接修改模板文本，变量使用 `{{variable}}` 格式。

### Q: run.py 缺少可执行权限怎么办？

**A**: Skill Creator 会自动设置 `chmod +x`。如果失败，手动：
```bash
chmod +x skill-name/run.py
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
5. **错误处理**：run.py 妥善处理异常，返回明确错误信息

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

---

## 🔗 相关资源

- **OpenClaw 技能规范**：https://docs.openclaw.ai/skills
- **YAML Front Matter**：https://jekyllrb.com/docs/front-matter/
- **Python argparse**：https://docs.python.org/3/library/argparse.html
- **ClawHub CLI**：`npx clawhub` 技能发布和管理

---

*Skill Creator 版本：v3.0.0*  
*最后更新：2026-03-25*
