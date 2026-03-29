# -*- coding: utf-8 -*-
"""
Ahrefs DR 批量查询工具 — CLI 入口

用法:
    # 查询单个域名
    python main.py --domains "example.com"

    # 查询多个域名（逗号分隔）
    python main.py --domains "example.com,google.com,github.com"

    # 从文件读取域名（每行一个）
    python main.py --file domains.txt

    # 指定国家代码
    python main.py --domains "example.com" --country br

    # 导出 CSV
    python main.py --domains "example.com,google.com" --output results.csv

    # 获取完整概览数据
    python main.py --domains "example.com" --overview

    # 手动指定代理（覆盖配置）
    python main.py --domains "example.com" --proxy "socks5://127.0.0.1:1080"
"""

import argparse
import csv
import json
import sys

from config import SOCKS5_PROXY, DEFAULT_COUNTRY, AHREFS_COOKIE, HUBSTUDIO_API_BASE, APP_ID, APP_SECRET, CONTAINER_CODE, MANUAL_COOKIES
from ahrefs import AhrefsClient
from hubstudio import HubStudioClient


def parse_args():
    parser = argparse.ArgumentParser(
        description="Ahrefs Domain Rating 批量查询工具"
    )

    # 域名输入
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--domains", "-d",
        type=str,
        help="域名列表，逗号分隔 (如: example.com,google.com)",
    )
    group.add_argument(
        "--file", "-f",
        type=str,
        help="域名文件路径，每行一个域名",
    )

    # 可选参数
    parser.add_argument(
        "--country", "-c",
        type=str,
        default=DEFAULT_COUNTRY,
        help=f"国家代码 (默认: {DEFAULT_COUNTRY})",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出 CSV 文件路径",
    )
    parser.add_argument(
        "--overview",
        action="store_true",
        help="获取完整概览数据（而非仅 DR）",
    )
    parser.add_argument(
        "--proxy", "-p",
        type=str,
        default="",
        help="手动指定 SOCKS5 代理 (如: socks5://127.0.0.1:1080)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="请求间隔秒数 (默认使用配置值)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="以 JSON 格式输出结果",
    )

    return parser.parse_args()


def load_domains(args):
    """从命令行参数或文件加载域名列表"""
    if args.domains:
        domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    else:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except FileNotFoundError:
            print(f"[错误] 文件不存在: {args.file}")
            sys.exit(1)

    if not domains:
        print("[错误] 未提供有效域名")
        sys.exit(1)

    return domains


def setup_client(args):
    """初始化 Ahrefs 客户端"""
    cookie = None
    proxy_url = args.proxy or SOCKS5_PROXY

    # 优先从 HubStudio 获取 Cookie 和代理
    if CONTAINER_CODE and APP_ID and APP_SECRET:
        try:
            hub = HubStudioClient()

            print("[HubStudio] 正在重启浏览器以启用 CDP...")
            # 先关闭浏览器
            try:
                hub.stop_browser(CONTAINER_CODE)
                print("[HubStudio] 浏览器已关闭")
                import time
                time.sleep(2)  # 等待浏览器完全关闭
            except:
                pass  # 如果浏览器未运行，忽略错误

            # 启动浏览器（带 CDP 参数，并打开 ahrefs.com）
            browser_info = hub.start_browser(
                CONTAINER_CODE,
                enable_cdp=True,
                open_url="https://app.ahrefs.com"
            )
            debugging_port = browser_info.get("debuggingPort")

            if debugging_port:
                print(f"[HubStudio] 浏览器已启动，调试端口: {debugging_port}")
                print("[HubStudio] 等待页面加载...")
                import time
                time.sleep(5)  # 等待页面完全加载

                print("[HubStudio] 通过 CDP 获取 Cookie（包括 HttpOnly）...")
                # 通过 CDP 获取所有 Cookie
                cookies = hub.get_cookies_via_cdp(debugging_port, "ahrefs.com")

                if cookies:
                    cookie = hub.build_cookie_header(cookies)
                    httponly_count = sum(1 for c in cookies if c.get('httpOnly'))
                    print(f"[HubStudio] 成功获取 {len(cookies)} 个 Cookie（含 {httponly_count} 个 HttpOnly）")
                else:
                    print("[HubStudio] 未获取到 Cookie，回退到 API 方式")
                    cookies = hub.export_cookies(CONTAINER_CODE)
                    if cookies:
                        cookie = hub.build_cookie_header(cookies)
                        print(f"[HubStudio] API 获取到 {len(cookies)} 个 Cookie")
            else:
                print("[HubStudio] 未获取到调试端口，使用 API 方式")
                cookies = hub.export_cookies(CONTAINER_CODE)
                if cookies:
                    cookie = hub.build_cookie_header(cookies)
                    print(f"[HubStudio] 成功获取 Cookie ({len(cookies)} 个)")

            # 如果未手动指定代理，从 HubStudio 获取
            if not proxy_url:
                proxy_url = hub.get_proxy_for_env(CONTAINER_CODE)
                if proxy_url:
                    print(f"[HubStudio] 获取到代理配置")

        except Exception as e:
            print(f"[HubStudio] 获取失败: {e}")
            print("[HubStudio] 将使用 cookies.txt 中的配置")

    # 回退到 cookies.txt
    if not cookie:
        cookie = AHREFS_COOKIE
        if not cookie:
            print("[错误] 未配置 Cookie")
            print("请配置 HubStudio (config.py) 或手动填写 cookies.txt")
            sys.exit(1)

    if proxy_url:
        print(f"[代理] 使用: {proxy_url}")
    else:
        print("[代理] 未配置，直接连接")

    return AhrefsClient(cookie_header=cookie, proxy_url=proxy_url)


def print_results_table(results):
    """以表格格式打印结果"""
    print(f"\n{'='*60}")
    print(f"  查询结果")
    print(f"{'='*60}")
    print(f"\n{'域名':<40} {'DR':<8} {'AR':<10} {'状态'}")
    print("-" * 70)

    for r in results:
        domain = r["domain"][:38]
        dr = r.get("domain_rating", "-")
        ar = r.get("ahrefs_rank", "-")
        error = r.get("error", "")

        if dr is not None and not error:
            dr_str = str(dr)
            ar_str = str(ar) if ar else "-"
            status = "[OK]"
        else:
            dr_str = "-"
            ar_str = "-"
            status = f"[FAIL] {error}" if error else "[FAIL]"

        print(f"  {domain:<38} {dr_str:<8} {ar_str:<10} {status}")

    success = sum(1 for r in results if r.get("domain_rating") is not None)
    print(f"\n  总计: {len(results)} 个域名, 成功: {success}, 失败: {len(results) - success}")
    print(f"{'='*60}\n")


def export_csv(results, filepath):
    """导出结果为 CSV 文件"""
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["域名", "DR", "DR变化", "AR", "AR变化", "错误"])

        for r in results:
            writer.writerow([
                r["domain"],
                r.get("domain_rating", ""),
                r.get("dr_delta", ""),
                r.get("ahrefs_rank", ""),
                r.get("ar_delta", ""),
                r.get("error", ""),
            ])

    print(f"[导出] 结果已保存到: {filepath}")


def main():
    args = parse_args()

    domains = load_domains(args)
    print(f"[域名] 已加载 {len(domains)} 个域名")

    ahrefs_client = setup_client(args)

    if args.overview:
        results = []
        for domain in domains:
            print(f"\n--- 获取概览: {domain} ---")
            overview = ahrefs_client.get_overview_data(domain, country=args.country)
            results.append(overview)

        if args.json_output:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for r in results:
                print(f"\n{'='*40}")
                print(f"  {r['domain']}")
                print(f"{'='*40}")
                print(json.dumps(r, indent=2, ensure_ascii=False)[:2000])

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n[导出] 完整数据已保存到: {args.output}")
    else:
        results = ahrefs_client.batch_get_domain_rating(
            domains, country=args.country, delay=args.delay
        )

        if args.json_output:
            clean = [{k: v for k, v in r.items() if k != "raw_response"} for r in results]
            print(json.dumps(clean, indent=2, ensure_ascii=False))
        else:
            print_results_table(results)

        if args.output:
            export_csv(results, args.output)


if __name__ == "__main__":
    main()
