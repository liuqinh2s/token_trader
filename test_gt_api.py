#!/usr/bin/env python3
"""
GeckoTerminal API 测试脚本
"""
import requests
import json
import time

GT_BASE = "https://api.geckoterminal.com/api/v2"

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.geckoterminal.com/",
    "Origin": "https://www.geckoterminal.com",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

def test_api(url, name):
    """测试 API 并返回结果"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        print(f"状态码: {resp.status_code}")

        if resp.status_code == 429:
            print("❌ 429 限流")
            return None

        if resp.status_code == 404:
            print("❌ 404 未找到")
            return None

        resp.raise_for_status()
        data = resp.json()

        # 检查数据结构
        if isinstance(data, dict):
            print(f"类型: dict")
            print(f"顶层 keys: {list(data.keys())[:10]}")

            # 检查 data 字段
            if "data" in data:
                data_field = data["data"]
                if isinstance(data_field, list):
                    print(f"data 数组长度: {len(data_field)}")
                    if data_field:
                        first_item = data_field[0]
                        print(f"第一个元素 keys: {list(first_item.keys()) if isinstance(first_item, dict) else type(first_item)}")
                        print(f"第一个元素 id: {first_item.get('id', 'N/A')[:80] if isinstance(first_item, dict) else 'N/A'}")
                elif isinstance(data_field, dict):
                    print(f"data dict keys: {list(data_field.keys())[:10]}")
                    # 检查 attributes
                    if "attributes" in data_field:
                        attrs = data_field["attributes"]
                        print(f"attributes keys: {list(attrs.keys())[:10]}")
                        if "ohlcv_list" in attrs:
                            ohlcv = attrs["ohlcv_list"]
                            print(f"✅ ohlcv_list 长度: {len(ohlcv)}")
                            if ohlcv:
                                print(f"   第一根K线: {ohlcv[0]}")
                                return ohlcv

            # 检查 included
            if "included" in data:
                included = data["included"]
                print(f"included 长度: {len(included)}")
                if included:
                    print(f"included[0] keys: {list(included[0].keys())}")
                    first = included[0]
                    if "attributes" in first:
                        attrs = first["attributes"]
                        print(f"included[0].attributes keys: {list(attrs.keys())[:10]}")
                        if "ohlcv_list" in attrs:
                            ohlcv = attrs["ohlcv_list"]
                            print(f"✅ included ohlcv_list 长度: {len(ohlcv)}")
                            if ohlcv:
                                print(f"   第一根K线: {ohlcv[0]}")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"响应内容: {resp.text[:200]}")
        return None

def main():
    # 测试地址
    test_cases = [
        # flap 代币地址
        ("0x311623ece2f58bc05d4ca4aae3063bf4a0674444", "flap 代币 token address"),

        # 一个已知有效的 BSC 池子地址（从 PancakeSwap）
        ("0x16b9a82891338f9bA279E685D1ff94Ed5712cB8d", "PancakeSwap BNB-USDT 池子"),

        # DexScreener 返回的格式异常的地址
        ("0x311623ece2f58bc05d4ca4aae3063bf4a0674444:4meme", "带来源标识的地址"),
    ]

    for addr, desc in test_cases:
        print(f"\n{'#'*60}")
        print(f"# 测试地址: {addr}")
        print(f"# 描述: {desc}")
        print(f"# 长度: {len(addr)}")
        print(f"{'#'*60}")

        # 1. 测试 token info API
        url1 = f"{GT_BASE}/networks/bsc/tokens/{addr}/info"
        test_api(url1, "Token Info API")

        time.sleep(1)

        # 2. 测试 token pools API
        url2 = f"{GT_BASE}/networks/bsc/tokens/{addr}/pools"
        pools_data = test_api(url2, "Token Pools API")

        if pools_data and "data" in pools_data:
            pools = pools_data["data"]
            if pools and isinstance(pools, list):
                pool_id = pools[0].get("id", "")
                print(f"\n找到池子 ID: {pool_id}")

                time.sleep(1)

                # 3. 测试 pool OHLCV API (使用返回的 pool id)
                if pool_id:
                    # pool_id 格式可能是:
                    #   旧: "networks/bsc/pools/0x..."
                    #   新: "bsc_0x..."
                    if "pools/" in pool_id:
                        pool_addr = pool_id.split("pools/")[-1]
                    elif "_0x" in pool_id:
                        pool_addr = "0x" + pool_id.split("_0x", 1)[-1]
                    else:
                        pool_addr = pool_id

                    # 也尝试从 attributes.address 获取
                    attrs = pools[0].get("attributes", {})
                    attr_addr = attrs.get("address", "")
                    if attr_addr:
                        print(f"  从 attributes 获取地址: {attr_addr}")
                        pool_addr = attr_addr

                    url3 = f"{GT_BASE}/networks/bsc/pools/{pool_addr}/ohlcv/hour?aggregate=1&limit=24"
                    test_api(url3, "Pool OHLCV (hour) API")

                    time.sleep(1)

                    # 4. 测试 minute OHLCV
                    url4 = f"{GT_BASE}/networks/bsc/pools/{pool_addr}/ohlcv/minute?aggregate=15&limit=48"
                    test_api(url4, "Pool OHLCV (15min) API")

        time.sleep(2)

if __name__ == "__main__":
    main()
