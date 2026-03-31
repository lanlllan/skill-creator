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
│   │   ├── templates.py            # 模板引擎（Jinja2 + 发现 + 回退）
│   │   ├── scorer.py               # 质量评分器（6 维度，含 content 维度）
│   │   ├── state_manager.py        # .state.json 结构化状态管理
│   │   ├── readme_manager.py       # 兼容层（转发到 state_manager）
│   │   ├── security.py             # 安全扫描引擎（Phase 5）
    │   │   ├── packager.py             # 打包引擎（Phase 8）
│   │   ├── spec.py                 # 规约引擎（Phase 10）
│   │   ├── examples.py             # 参考实现库（Phase 13）
│   │   └── commands/               # 各 CLI 命令实现
│   │       ├── create.py           # create 命令
│   │       ├── validate.py         # validate 命令
│   │       ├── archive.py          # archive 命令
│   │       ├── clean.py            # clean 命令
│   │       ├── batch.py            # batch 命令
│   │       ├── scan.py             # scan 命令（安全扫描）
│   │       ├── package.py          # package 命令（打包）
│   │       ├── spec_cmd.py         # spec 命令（规约生成与验证）
│   │       └── examples_cmd.py     # examples 命令（参考样例）
│   ├── templates/                  # Jinja2 模板目录（Phase 6 + Phase 11）
│   │   ├── python/                 # Python 类型模板（4 个 .j2）
│   │   ├── python-guided/          # Python 规约驱动富模板（4 个 .j2，Phase 11）
│   │   ├── shell/                  # Shell 类型模板（4 个 .j2）
│   │   └── shell-guided/           # Shell 规约驱动富模板（4 个 .j2，Phase 11）
│   ├── examples/                   # 内置参考样例（Phase 13）
│   │   ├── simple-greeter/         # 入门样例
│   │   ├── file-analyzer/          # 中等样例
│   │   └── api-health-checker/     # 进阶样例
│   ├── tests/                      # pytest 测试套件（405 用例）
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
# 405 个用例，覆盖 validators / create_skill / batch / state_manager / security / scan / templates / Phase 7 验证增强 / Phase 8 打包 / Phase 10 规约系统 / Phase 11 富内容模板 / Phase 12 内容感知评分 / Phase 13 参考实现库
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
| 9   | 生态集成（ClawHub） | 🔲 远期 | API 就绪后 |
