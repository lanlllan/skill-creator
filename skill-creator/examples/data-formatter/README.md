# Data Formatter

在 JSON、CSV、YAML 格式之间转换数据，并验证文件结构合法性。

## 安装

JSON 和 CSV 功能使用 Python 标准库，无需额外安装。YAML 功能需要 PyYAML：

```bash
pip install pyyaml
```

## 使用

```bash
python run.py convert --input data.json --to csv --output data.csv
python run.py validate --input config.yaml
```

详见 [USAGE.md](USAGE.md)。
