# API Health Checker

检查 API 端点的健康状态，支持批量探测和超时重试。

## 安装

```bash
pip install pyyaml
```

## 使用

```bash
python run.py check --url https://httpbin.org/get
python run.py batch --config config.yaml
python run.py report --config config.yaml
```

详见 [USAGE.md](USAGE.md)。
