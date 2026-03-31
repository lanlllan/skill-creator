# API Health Checker - 使用指南

检查 API 端点的健康状态，支持单端点检查、批量探测和 JSON 健康报告。

---

## 🔰 运行环境

- Python >= 3.9
- PyYAML（`pip install pyyaml`）

## 🚀 快速开始

```bash
# 检查单个端点
python run.py check --url https://httpbin.org/get

# 从配置文件批量检查
python run.py batch --config config.yaml

# 生成 JSON 报告
python run.py report --config config.yaml --output report.json
```

## 🔧 命令参考

### `check` - 检查单个端点

| 参数 | 说明 | 必填 |
|------|------|------|
| `--url` | API 端点 URL | 是 |
| `--timeout` | 超时秒数（默认 5） | 否 |

**示例输出**：
```
✅ https://httpbin.org/get
   状态码: 200  响应时间: 342.5ms
```

### `batch` - 批量检查端点

| 参数 | 说明 | 必填 |
|------|------|------|
| `--config` | 端点配置文件路径（YAML 格式） | 是 |

**示例输出**：
```
📊 批量健康检查报告

  ✅ 主页:   200  156.3ms
  ✅ 健康检查:   200  89.2ms
  ❌ 慢接口:   0  3001.4ms  (timeout after 3s)

  通过率: 2/3 (67%)
```

### `report` - 生成 JSON 健康报告

| 参数 | 说明 | 必填 |
|------|------|------|
| `--config` | 端点配置文件路径 | 是 |
| `--output` | 报告输出文件路径（不指定则输出到 stdout） | 否 |

### 配置文件格式

```yaml
endpoints:
  - name: "主页"
    url: "https://httpbin.org/get"
  - name: "健康检查"
    url: "https://httpbin.org/status/200"
  - name: "慢接口"
    url: "https://httpbin.org/delay/2"
    timeout: 3
```

每个端点支持的字段：
- `name`（可选）：端点显示名称
- `url`（必填）：端点 URL
- `timeout`（可选）：该端点的超时秒数，覆盖默认值

## 🐛 故障排除

### Q: 提示 PyYAML 未安装？

**A**: 运行 `pip install pyyaml` 安装。

### Q: 全部显示 timeout？

**A**: 检查网络连接和防火墙设置。也可以尝试增大 `--timeout` 参数。

### Q: 如何在 CI 中使用？

**A**: `batch` 命令的退出码为 `1` 表示有端点不健康，可直接用于 CI 流水线的断言。
