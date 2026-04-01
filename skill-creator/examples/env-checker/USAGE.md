# Env Checker - 使用指南

检查开发环境的依赖配置，验证 Python 版本、必备工具和环境变量是否就绪。

---

## 🔰 运行环境

- Python >= 3.9
- 无第三方依赖

## 🚀 快速开始

```bash
# 使用默认规则检查环境
python run.py check

# 自定义检查项
python run.py check --tools git,docker,node --python-min 3.10

# 生成环境快照报告
python run.py report
```

## 🔧 命令参考

### `check` - 环境检查

| 参数 | 说明 | 必填 |
|------|------|------|
| `--tools` | 必须存在的工具（逗号分隔） | 否（默认 git,python3） |
| `--env-vars` | 必须设置的环境变量（逗号分隔） | 否（默认 PATH,HOME） |
| `--python-min` | Python 最低版本要求 | 否（默认 3.9） |

**示例输出**：
```
🔍 环境检查

  ✅ Python 版本: 3.11.4 (要求 >= 3.9)

  📦 命令行工具:
    ✅ git
    ❌ docker — 未找到

  🔑 环境变量:
    ✅ PATH
    ✅ HOME

  ⚠️  部分检查未通过，请修复上述标记 ❌ 的项目
```

### `report` - 环境报告

| 参数 | 说明 | 必填 |
|------|------|------|
| `--format` | 输出格式（text / json，默认 text） | 否 |

## 🐛 故障排除

### Q: 工具明明已安装，但检查失败？

**A**: `check` 命令使用 `shutil.which()` 查找工具，只会搜索 PATH 环境变量中的目录。请确认工具所在目录已添加到 PATH。

### Q: 如何检查自定义工具列表？

**A**: 使用 `--tools` 参数指定，多个工具用逗号分隔：`python run.py check --tools git,docker,kubectl,helm`。

### Q: report 输出太长，如何机器解析？

**A**: 使用 `--format json` 输出 JSON 格式，便于程序解析：`python run.py report --format json | python -m json.tool`。
