#!/usr/bin/env python3
"""API Health Checker — 检查 API 端点的健康状态，支持批量探测和超时重试。"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class Result:
    """命令执行结果。"""
    success: bool
    message: str = ""

    def __bool__(self):
        return self.success


@dataclass
class EndpointResult:
    """单个端点的检查结果。"""
    name: str
    url: str
    status_code: int
    response_time_ms: float
    healthy: bool
    error: str = ""


def _check_endpoint(url: str, timeout: int = 5) -> EndpointResult:
    """发送 HTTP GET 请求检查端点健康状态。"""
    start = time.time()
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "api-health-checker/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            elapsed = (time.time() - start) * 1000
            return EndpointResult(
                name="", url=url, status_code=status,
                response_time_ms=round(elapsed, 1),
                healthy=(200 <= status < 300),
            )
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000
        return EndpointResult(
            name="", url=url, status_code=e.code,
            response_time_ms=round(elapsed, 1),
            healthy=False, error=str(e.reason),
        )
    except urllib.error.URLError as e:
        elapsed = (time.time() - start) * 1000
        return EndpointResult(
            name="", url=url, status_code=0,
            response_time_ms=round(elapsed, 1),
            healthy=False, error=f"unreachable: {e.reason}",
        )
    except TimeoutError:
        elapsed = (time.time() - start) * 1000
        return EndpointResult(
            name="", url=url, status_code=0,
            response_time_ms=round(elapsed, 1),
            healthy=False, error=f"timeout after {timeout}s",
        )
    except Exception as exc:
        elapsed = (time.time() - start) * 1000
        return EndpointResult(
            name="", url=url, status_code=0,
            response_time_ms=round(elapsed, 1),
            healthy=False, error=str(exc),
        )


def _load_config(config_path: str) -> list[dict]:
    """从 YAML 配置文件加载端点列表。"""
    if yaml is None:
        raise ImportError("PyYAML 未安装，请运行 pip install pyyaml")
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在：{path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "endpoints" not in data:
        raise ValueError("配置文件格式错误：缺少 'endpoints' 键")
    return data["endpoints"]


def validate_url(url: str) -> Result:
    """校验 URL 格式有效性。"""
    if not url:
        return Result(success=False, message="错误：--url 不能为空")
    if not url.startswith(("http://", "https://")):
        return Result(success=False, message=f"错误：URL 必须以 http:// 或 https:// 开头 — {url}")
    return Result(success=True)


def format_result_line(r: EndpointResult) -> str:
    """将单个端点结果格式化为一行输出。"""
    icon = "✅" if r.healthy else "❌"
    detail = f"  {r.status_code}  {r.response_time_ms}ms"
    if r.error:
        detail += f"  ({r.error})"
    label = r.name if r.name else r.url
    return f"  {icon} {label}: {detail}"


def cmd_check(args) -> Result:
    """检查单个 API 端点的健康状态。"""
    url_check = validate_url(args.url)
    if not url_check:
        return url_check

    verbose = getattr(args, "verbose", False)
    timeout = getattr(args, "timeout", 5) or 5
    if verbose:
        print(f"📋 检查端点: {args.url} (超时: {timeout}s)")

    result = _check_endpoint(args.url, timeout)
    if result.healthy:
        msg = f"✅ {args.url}\n   状态码: {result.status_code}  响应时间: {result.response_time_ms}ms"
    else:
        detail = f"  错误: {result.error}" if result.error else ""
        code_info = f"  状态码: {result.status_code}" if result.status_code else ""
        msg = f"❌ {args.url}\n  {code_info}{detail}  响应时间: {result.response_time_ms}ms"
    return Result(success=result.healthy, message=msg)


def cmd_batch(args) -> Result:
    """从配置文件批量检查端点。"""
    try:
        endpoints = _load_config(args.config)
    except (FileNotFoundError, ValueError, ImportError) as e:
        return Result(success=False, message=f"错误：{e}")

    verbose = getattr(args, "verbose", False)
    results = []
    for ep in endpoints:
        name = ep.get("name", ep["url"])
        timeout = ep.get("timeout", 5)
        if verbose:
            print(f"📋 正在检查: {name} ({ep['url']})")
        r = _check_endpoint(ep["url"], timeout)
        r.name = name
        results.append(r)

    healthy_count = sum(1 for r in results if r.healthy)
    total = len(results)
    pass_rate = (healthy_count / total * 100) if total else 0

    lines = ["📊 批量健康检查报告", ""]
    for r in results:
        lines.append(format_result_line(r))
    lines.append("")
    lines.append(f"  通过率: {healthy_count}/{total} ({pass_rate:.0f}%)")

    all_healthy = healthy_count == total
    return Result(success=all_healthy, message="\n".join(lines))


def cmd_report(args) -> Result:
    """生成 JSON 格式的健康报告。"""
    try:
        endpoints = _load_config(args.config)
    except (FileNotFoundError, ValueError, ImportError) as e:
        return Result(success=False, message=f"错误：{e}")

    results = []
    for ep in endpoints:
        name = ep.get("name", ep["url"])
        timeout = ep.get("timeout", 5)
        r = _check_endpoint(ep["url"], timeout)
        r.name = name
        results.append(asdict(r))

    report_json = json.dumps(results, ensure_ascii=False, indent=2)

    output_path = getattr(args, "output", None)
    if output_path:
        Path(output_path).write_text(report_json, encoding="utf-8")
        return Result(success=True, message=f"✅ 报告已写入 {output_path}")
    return Result(success=True, message=report_json)


def main():
    """CLI 入口：参数解析与命令分发。"""
    parser = argparse.ArgumentParser(description="API Health Checker - 端点健康检查")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="检查单个端点")
    check_parser.add_argument("--url", required=True, help="API 端点 URL")
    check_parser.add_argument("--timeout", type=int, default=5,
                              help="超时秒数（默认 5）")

    batch_parser = subparsers.add_parser("batch", help="批量检查端点")
    batch_parser.add_argument("--config", required=True,
                              help="端点配置文件路径（YAML 格式）")

    report_parser = subparsers.add_parser("report", help="生成 JSON 健康报告")
    report_parser.add_argument("--config", required=True,
                               help="端点配置文件路径（YAML 格式）")
    report_parser.add_argument("--output", help="报告输出文件路径")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    dispatch = {"check": cmd_check, "batch": cmd_batch, "report": cmd_report}
    try:
        result = dispatch[args.command](args)
        print(result.message)
        return 0 if result.success else 1
    except FileNotFoundError as exc:
        print(f"❌ 文件未找到：{exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"❌ 执行失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
