---
name: api-health-checker
description: 检查 API 端点的健康状态，支持批量探测和超时重试
version: 1.0.0
author: OpenClaw Team
tags: [api, monitoring, health-check]
date: 2026-03-30
type: python
---

# API Health Checker

> 检查 API 端点的健康状态，支持单端点检查、批量探测和 JSON 健康报告。

---

## 概述

API Health Checker 是一个进阶级 Skill 示例，演示了网络 I/O、重试容错、YAML 配置文件消费和 JSON 报告生成。包含 3 个子命令，展示了完整的错误处理模式和结构化输出。

## 适用场景

- 运维工程师在每日巡检时批量检查微服务集群中各服务的健康状态
- 部署新版本后快速验证所有 API 端点是否正常响应
- 集成到 CI/CD 流水线中，作为部署后的冒烟测试

## 核心能力

### 1. 单端点检查

- 发送 HTTP GET 请求检查指定 URL 的可用性
- 报告状态码和响应时间（毫秒）
- 支持自定义超时时间，默认 5 秒

### 2. 批量探测

- 从 YAML 配置文件读取端点列表，逐一检查
- 网络不可达或超时的端点不影响其他端点的检查
- 输出汇总报告：成功/失败数量和整体通过率

### 3. 健康报告

- 以 JSON 格式输出每个端点的详细检查结果
- 包含 URL、状态码、响应时间、健康状态
- 支持写入文件或输出到 stdout，便于管道消费

## 使用方式

```bash
# 检查单个端点
python run.py check --url https://httpbin.org/get

# 设置超时
python run.py check --url https://httpbin.org/delay/10 --timeout 3

# 批量检查（需要配置文件）
python run.py batch --config endpoints.yaml

# 生成 JSON 报告
python run.py report --config endpoints.yaml --output report.json
```

### 配置文件格式（endpoints.yaml）

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

## 示例

```bash
$ python run.py check --url https://httpbin.org/get
✅ https://httpbin.org/get
   状态码: 200  响应时间: 342.5ms

$ python run.py batch --config config.yaml
📊 批量健康检查报告

  ✅ httpbin GET:   200  156.3ms
  ✅ httpbin 状态 200:   200  89.2ms
  ❌ httpbin 延迟 1s:   0  3001.4ms  (timeout after 3s)

  通过率: 2/3 (67%)

$ python run.py report --config config.yaml --output report.json
✅ 报告已写入 report.json
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 全部显示 timeout | 网络不可达或防火墙阻拦 | 检查网络连接，增大 --timeout |
| PyYAML 未安装 | 缺少依赖 | 运行 `pip install pyyaml` |
| 配置文件格式错误 | 缺少 endpoints 键 | 参照配置文件格式章节 |

## 前置依赖

- Python >= 3.9
- PyYAML（配置文件解析）

## 📁 Skill 结构

```
api-health-checker/
├── SKILL.md              # 技能说明（本文件）
├── run.py                # 主入口（3 个子命令：check / batch / report）
├── config.yaml           # 示例配置文件
├── .skill-spec.yaml      # 规约文件
├── USAGE.md              # 使用指南
└── README.md             # 快速入门
```
