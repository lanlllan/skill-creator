# Env Checker

检查开发环境的依赖配置，验证 Python 版本、必备工具和环境变量是否就绪。

## 安装

无需额外安装，使用 Python 标准库即可运行。

## 使用

```bash
python run.py check
python run.py check --tools git,docker,node --python-min 3.10
python run.py report --format json
```

详见 [USAGE.md](USAGE.md)。
