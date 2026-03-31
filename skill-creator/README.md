# skill-creator

创建符合 OpenClaw 规范的新 Skill 的脚手架工具。

## 快速开始

```bash
# ⭐ 推荐：交互式创建（自动引导需求细化）
python run.py create --interactive

# 快速创建（跳过交互）
python run.py create -n my-skill -d "我的技能描述"

# 验证现有 skill
python run.py validate ./path/to/skill

# 归档到正式目录
python run.py archive my-skill
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

## 文档索引

- **[SKILL.md](SKILL.md)** — 技能元数据与核心能力说明
- **[USAGE.md](USAGE.md)** — 完整命令参考与使用指南
- **[项目 README](../README.md)** — 安装方法、测试约定、更新历史
