# skill-creator

创建符合 OpenClaw 规范的新 Skill 的脚手架工具。

## 快速开始

```bash
# 查看帮助
python run.py --help

# ⭐ 推荐：交互式创建（自动触发需求细化，生成高质量骨架）
python run.py create --interactive

# 快速创建（跳过交互，直接生成模板）
python run.py create -n my-skill -d "我的技能描述"

# 引导式创建（生成规约骨架 → 填充 → 渲染富内容）
python run.py create --guided -n api-monitor -d "API 健康监控"

# 从规约创建
python run.py create --spec .skill-spec.yaml

# 验证现有 skill
python run.py validate ./path/to/skill

# 安全扫描
python run.py scan ./path/to/skill

# 打包
python run.py package ./path/to/skill

# 查看内置参考样例
python run.py examples

# 批量创建
python run.py batch --file skills.yaml

# 归档 / 清理
python run.py archive my-skill
python run.py clean my-skill
```

## batch 命令 YAML 格式

```yaml
skills:
  - name: log-analyzer
    description: 日志分析工具
    version: 1.0.0
    author: DevTeam
    tags: [logging, analysis]
    output: /custom/path
  - name: config-sync
    description: 配置同步工具
```

## 详细文档

- **使用指南**：[USAGE.md](USAGE.md) — 完整命令参考、工作流、模板变量
- **技能元数据**：[SKILL.md](SKILL.md) — 核心能力、设计理念、技术实现
