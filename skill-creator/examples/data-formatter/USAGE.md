# Data Formatter - 使用指南

在 JSON、CSV、YAML 格式之间转换数据，并验证文件结构合法性。

---

## 🔰 运行环境

- Python >= 3.9
- PyYAML（仅 YAML 相关操作需要，可选）

## 🚀 快速开始

```bash
# JSON 转 CSV
python run.py convert --input data.json --to csv --output result.csv

# CSV 转 YAML（输出到 stdout）
python run.py convert --input users.csv --to yaml

# 校验 JSON 文件结构
python run.py validate --input config.json
```

## 🔧 命令参考

### `convert` - 格式转换

| 参数 | 说明 | 必填 |
|------|------|------|
| `--input` | 源文件路径 | 是 |
| `--to` | 目标格式（json / csv / yaml） | 是 |
| `--output` | 输出文件路径（不指定则输出到 stdout） | 否 |

**支持的转换路径**：

| 源格式 → 目标格式 | 说明 |
|-------------------|------|
| JSON → CSV | 将对象数组展开为表格行 |
| JSON → YAML | 保持嵌套结构不变 |
| CSV → JSON | 每行转为一个 JSON 对象 |
| CSV → YAML | 每行转为一个 YAML 映射 |
| YAML → JSON | 保持结构不变 |
| YAML → CSV | 仅支持扁平映射列表 |

**示例输出**：
```
✅ 转换完成：50 条记录 → users.csv
```

### `validate` - 格式校验

| 参数 | 说明 | 必填 |
|------|------|------|
| `--input` | 待校验的文件路径 | 是 |

**示例输出**：
```
✅ config.yaml — 格式合法
   格式: YAML
   记录数: 3
   字段: name, host, port, debug
```

## 🐛 故障排除

### Q: 提示"无法识别源文件格式"？

**A**: 程序根据文件扩展名推断格式。确保文件扩展名为 `.json`、`.csv`、`.yaml` 或 `.yml` 之一。

### Q: YAML 相关命令报 ImportError？

**A**: YAML 功能依赖 PyYAML。运行 `pip install pyyaml` 安装后重试。

### Q: CSV 转换后数据丢失？

**A**: 嵌套的 JSON/YAML 结构转为 CSV 时会被序列化为字符串。建议仅对扁平数据使用 CSV 输出。
