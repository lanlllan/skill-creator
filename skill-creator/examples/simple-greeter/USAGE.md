# Simple Greeter - 使用指南

根据姓名和语言生成个性化问候语。

---

## 🔰 运行环境

- Python >= 3.9
- 无第三方依赖

## 🚀 快速开始

```bash
# 中文问候（默认）
python run.py greet --name "张三"
# 输出：你好，张三！欢迎使用 OpenClaw。

# 英文问候
python run.py greet --name "Alice" --lang en
# 输出：Hello, Alice! Welcome to OpenClaw.

# 日文问候
python run.py greet --name "田中" --lang ja
# 输出：こんにちは、田中さん！OpenClawへようこそ。
```

## 🔧 命令参考

### `greet` - 生成问候语

| 参数 | 说明 | 必填 |
|------|------|------|
| `--name` | 要问候的姓名 | 是 |
| `--lang` | 语言代码：`zh`（中文）、`en`（英文）、`ja`（日文），默认 `zh` | 否 |

**退出码**：`0` = 成功，`1` = 失败（如姓名为空）

## 🐛 故障排除

### Q: 提示"不支持的语言"？

**A**: 当前支持 `zh`、`en`、`ja` 三种语言代码，不在列表中的语言会自动回退到英文。

### Q: 姓名中包含特殊字符？

**A**: 姓名会自动去除首尾空白。Unicode 字符（如中日韩文字）均可正常使用。
