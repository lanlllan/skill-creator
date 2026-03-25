# skill-creator 项目

OpenClaw Skill 生命周期管理工具集，支持创建、验证、归档、批量处理 Skill。

## 项目结构

```
skill-creator/
├── skillCreator/                   # 主工具代码
│   ├── run.py                      # CLI 入口（约 100 行，纯 argparse + dispatch）
│   ├── creator/                    # 业务逻辑模块包（Phase 2 拆分）
│   │   ├── paths.py                # 路径解析
│   │   ├── validators.py           # 名称/版本校验
│   │   ├── templates.py            # 模板定义与渲染
│   │   ├── scorer.py               # 质量评分器
│   │   ├── state_manager.py        # .state.json 结构化状态管理
│   │   ├── readme_manager.py       # 兼容层（转发到 state_manager）
│   │   └── commands/               # 各 CLI 命令实现
│   │       ├── create.py           # create 命令
│   │       ├── validate.py         # validate 命令
│   │       ├── archive.py          # archive 命令
│   │       ├── clean.py            # clean 命令
│   │       └── batch.py            # batch 命令
│   ├── tests/                      # pytest 测试套件（85 用例）
│   ├── SKILL.md                    # 技能元数据
│   ├── USAGE.md                    # 使用指南
│   └── README.md                   # 工具说明与更新记录
├── .agent_team/                    # 团队协作文档
│   ├── architecture-plan.md        # 架构迭代方案
│   ├── review-v2.md                # 审查记录
│   └── ...
├── tmp/                            # 本地测试临时目录（不提交）
└── README.md                       # 本文件（项目说明）
```

## 快速使用

```bash
cd skillCreator

# 创建新 skill
python run.py create -n my-skill -d "描述"

# 批量创建
python run.py batch --file skills.yaml

# 验证
python run.py validate ./path/to/skill

# 归档
python run.py archive my-skill
```

详细使用说明见 [skillCreator/USAGE.md](skillCreator/USAGE.md)。

## 测试约定

所有测试均在项目根目录的 `tmp/` 下进行：

```bash
cd skillCreator
python run.py create -n test-skill -d "测试" -o ../tmp
python run.py validate ../tmp/test-skill
# 测试完成后清理
Remove-Item -Recurse -Force ../tmp/test-skill
```

单元测试：

```bash
cd skillCreator
python -m pytest tests/ -v --tb=short
# 85 个用例，覆盖 validators / create_skill / batch / state_manager
```

## 迭代状态

| Phase | 名称 | 状态 | 说明 |
|-------|------|------|------|
| 1.1 | batch 命令 + create_skill 提取 | ✅ 已完成 | v1.1.0 |
| 1.3 | 基础测试（pytest，62 用例） | ✅ 已完成 | v1.2.0 |
| 1.2 | 移除硬编码 WSL 路径 | ✅ 已完成 | v1.2.0 |
| 2   | 模块化拆分（creator/ 包） | ✅ 已完成 | v2.0.0 |
| 4   | 状态管理升级（.state.json） | ✅ 已完成 | v3.0.0 |
| 3   | 模板系统增强（Jinja2） | 🔲 条件触发 | 多语言需求时 |
| 5   | 生态集成（ClawHub） | 🔲 远期 | API 就绪后 |
