#!/usr/bin/env python3
"""
GeckoTerminal API 测试脚本 - 独立运行版
放在 src/ 目录下，与 scanner.py 同目录
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time

# 明确禁用代理
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

GT_BASE = "https://api.geckoterminal.com/api/v2"
GT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.geckoterminal.com/",
    "Origin": "https://www.geckoterminal.com",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def gt_request(url, max_retries=3):
    """发送 GeckoTerminal API 请求"""
    for attempt in range(max_retries):
        try:
            print(f"  请求 [{attempt+1}/{max_retries}]: {url[-60:]}")
            # 明确禁用代理
            resp = requests.get(url, headers=GT_HEADERS, timeout=15, proxies={
                'http': None,
                'https': None
            })
            print(f"  状态码: {resp.status_code}")

            if resp.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"  ⚠️ 429 限流，等待 {wait}s")
                time.sleep(wait)
                continue

            if resp.status_code == 404:
                print(f"  ❌ 404 未找到")
                return None

            resp.raise_for_status()
            data = resp.json()
            print(f"  ✅ 成功")
            return data

        except requests.exceptions.RequestException as e:
            print(f"  ❌ 请求失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
    print(f"  ❌ 最终失败")
    return None


def test_token_pools(token_addr):
    """测试获取代币的池子列表"""
    print(f"\n{'='*60}")
    print(f"测试 1: 获取代币的池子列表")
    print(f"代币地址: {token_addr}")
    print(f"代币地址长度: {len(token_addr)}")
    print(f"{'='*60}")

    url = f"{GT_BASE}/networks/bsc/tokens/{token_addr}/pools"
    data = gt_request(url)

    if not data:
        print("❌ 无法获取池子数据")
        return None

    print(f"\n返回数据结构:")
    print(f"  type: {type(data)}")
    if isinstance(data, dict):
        print(f"  keys: {list(data.keys())[:10]}")

    pools = data.get("data", [])
    print(f"\n池子数量: {len(pools)}")

    if pools and isinstance(pools, list):
        first_pool = pools[0]
        print(f"\n第一个池子:")
        if isinstance(first_pool, dict):
            print(f"  keys: {list(first_pool.keys())}")
            pool_id = first_pool.get("id", "")
            print(f"  id: {pool_id}")
            print(f"  id 长度: {len(pool_id)}")
            print(f"  id 类型: {type(pool_id)}")

            # 提取池子地址
            if "pools/" in pool_id:
                pool_addr = pool_id.split("pools/")[-1]
                print(f"  提取的池子地址: {pool_addr}")
                print(f"  池子地址长度: {len(pool_addr)}")
            else:
                print(f"  ⚠️ id 格式不符合预期: {pool_id}")

    return pools


def test_pool_ohlcv(pool_addr, aggregate=15):
    """测试获取池子的 OHLCV 数据"""
    print(f"\n{'='*60}")
    print(f"测试 2: 获取池子 OHLCV 数据")
    print(f"池子地址: {pool_addr}")
    print(f"池子地址长度: {len(pool_addr)}")
    print(f"聚合: {aggregate} 分钟")
    print(f"{'='*60}")

    if aggregate == 1:
        url = f"{GT_BASE}/networks/bsc/pools/{pool_addr}/ohlcv/minute?aggregate=1&limit=30"
    elif aggregate == 15:
        url = f"{GT_BASE}/networks/bsc/pools/{pool_addr}/ohlcv/minute?aggregate=15&limit=48"
    else:
        url = f"{GT_BASE}/networks/bsc/pools/{pool_addr}/ohlcv/hour?aggregate=1&limit=24"

    data = gt_request(url)

    if not data:
        print("❌ 无法获取 OHLCV 数据")
        return None

    print(f"\n返回数据结构:")
    print(f"  type: {type(data)}")
    if isinstance(data, dict):
        print(f"  keys: {list(data.keys())[:10]}")

    # 尝试找到 ohlcv_list
    if "data" in data:
        data_field = data["data"]
        if isinstance(data_field, dict):
            attrs = data_field.get("attributes", {})
            ohlcv = attrs.get("ohlcv_list", [])
            print(f"\ndata.data.attributes 内容:")
            print(f"  keys: {list(attrs.keys())[:10]}")
            if ohlcv:
                print(f"\n✅ OHLCV 数据:")
                print(f"  K线数量: {len(ohlcv)}")
                print(f"  第一根K线: {ohlcv[0]}")
                print(f"  最后一根K线: {ohlcv[-1]}")
                return ohlcv
        elif data_field is None:
            print(f"\n❌ data.data 为 null")

    # 检查 included
    if "included" in data:
        included = data["included"]
        print(f"\nincluded 数量: {len(included)}")
        if included:
            first = included[0]
            if isinstance(first, dict) and "attributes" in first:
                attrs = first["attributes"]
                ohlcv = attrs.get("ohlcv_list", [])
                if ohlcv:
                    print(f"\n✅ OHLCV 数据 (在 included 中):")
                    print(f"  K线数量: {len(ohlcv)}")
                    print(f"  第一根K线: {ohlcv[0]}")
                    return ohlcv

    print("❌ 未找到 OHLCV 数据")
    return None


def test_direct_token_address(token_addr):
    """测试直接用代币地址查询 OHLCV"""
    print(f"\n{'='*60}")
    print(f"测试 3: 直接用代币地址查询 OHLCV")
    print(f"代币地址: {token_addr}")
    print(f"代币地址长度: {len(token_addr)}")
    print(f"{'='*60}")

    url = f"{GT_BASE}/networks/bsc/pools/{token_addr}/ohlcv/hour?aggregate=1&limit=24"
    data = gt_request(url)

    if not data:
        print("❌ 直接用代币地址查询失败")
        return None

    print(f"\n返回数据结构:")
    if isinstance(data, dict):
        print(f"  keys: {list(data.keys())[:10]}")

    # 检查是否返回 404 或空数据
    if "data" in data and data["data"] is None:
        print("❌ data 为 null（404 或无效地址）")
        return None

    if "data" in data:
        data_field = data["data"]
        if isinstance(data_field, dict):
            attrs = data_field.get("attributes", {})
            ohlcv = attrs.get("ohlcv_list", [])
            if ohlcv:
                print(f"\n✅ 直接用代币地址查询成功!")
                print(f"  K线数量: {len(ohlcv)}")
                return ohlcv

    print("❌ 未找到 OHLCV 数据")
    return None


def test_token_info(token_addr):
    """测试获取代币信息"""
    print(f"\n{'='*60}")
    print(f"测试 4: 获取代币信息")
    print(f"代币地址: {token_addr}")
    print(f"{'='*60}")

    url = f"{GT_BASE}/networks/bsc/tokens/{token_addr}/info"
    data = gt_request(url)

    if not data:
        print("❌ 无法获取代币信息")
        return None

    if isinstance(data, dict):
        print(f"  keys: {list(data.keys())[:10]}")
        if "data" in data:
            data_field = data["data"]
            if isinstance(data_field, dict):
                attrs = data_field.get("attributes", {})
                print(f"  attributes keys: {list(attrs.keys())[:10]}")
                if "holders" in attrs:
                    holders = attrs["holders"]
                    print(f"  holders: {holders}")

    return data


def main():
    print("="*60)
    print("GeckoTerminal API 测试")
    print("="*60)

    # 测试用例 - 使用日志中出现的有问题的地址
    test_tokens = [
        # flap 代币地址 (从日志中获取的)
        ("0x311623ece2f58bc05d4ca4aae3063bf4a0674444", "flap 代币"),
        ("0xfcb54d2b664f00", "flap 代币 (截断)"),
        ("0xf9be5696b177df", "flap 代币"),

        # 规范化后的地址
        ("0x311623ece2f58bc05d4ca4aae3063bf4a0674444", "flap 代币 (完整)"),
    ]

    for token_addr, desc in test_tokens:
        print(f"\n\n{'#'*60}")
        print(f"## 测试代币: {token_addr}")
        print(f"## 描述: {desc}")
        print(f"## 地址长度: {len(token_addr)}")
        print(f"{'#'*60}")

        # 测试 4: 获取代币信息
        test_token_info(token_addr)
        time.sleep(1)

        # 测试 1: 获取池子列表
        pools = test_token_pools(token_addr)

        if pools and isinstance(pools, list) and len(pools) > 0:
            first_pool = pools[0]
            if isinstance(first_pool, dict):
                pool_id = first_pool.get("id", "")
                if "pools/" in pool_id:
                    pool_addr = pool_id.split("pools/")[-1]

                    # 测试 2: 用池子地址查询 OHLCV
                    test_pool_ohlcv(pool_addr, aggregate=15)
                    time.sleep(1)
                    test_pool_ohlcv(pool_addr, aggregate=1)
                else:
                    print(f"\n⚠️ pool_id 格式不符合预期: {pool_id}")
        else:
            print("\n❌ 没有找到池子")

        # 测试 3: 直接用代币地址查询
        test_direct_token_address(token_addr)

        time.sleep(2)

    print("\n\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    main()
