#!/usr/bin/env python3
"""修复 output_scan_json 函数，添加 enrich_token 处理"""

import re

with open('/workspace/src/scanner.py', 'r') as f:
    content = f.read()

# 找到 output_scan_json 函数并替换
old_func = '''def output_scan_json(queue_state: dict, eliminated_this_round: list = None,
                    rejected_at_entry: list = None, quality_results: list = None):
    """输出扫描结果到 JSON 文件（用于 GitHub Actions 前端展示模式）"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    utc_now = datetime.now(timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    beijing_now = utc_now.astimezone(beijing_tz)
    scan_time_str = beijing_now.strftime("%Y-%m-%dT%H-%M-%S")

    output = {
        "scanTime": beijing_now.strftime("%Y-%m-%d %H:%M:%S"),
        "tokens": quality_results or [],
        "queue": queue_state.get("tokens", []),
        "eliminatedThisRound": eliminated_this_round or [],
        "rejectedAtEntry": rejected_at_entry or [],
        "lastBlock": queue_state.get("lastBlock", 0),
        "lastScanTime": queue_state.get("lastScanTime", 0),
        "scanRound": queue_state.get("scanRound", 0),
        "marketSentiment": queue_state.get("marketSentiment", 0),
        "totalTokens": queue_state.get("totalTokens", 0),
        "filteredTokens": queue_state.get("filteredTokens", 0),
        "newDiscovered": queue_state.get("newDiscovered", 0),
        "newAdmitted": queue_state.get("newAdmitted", 0),
        "eliminatedCount": queue_state.get("eliminatedCount", 0),
        "eliminatedTotal48h": queue_state.get("eliminatedTotal48h", 0),
        "queueSize": queue_state.get("queueSize", len(queue_state.get("tokens", []))),
        "breakthroughTokens": queue_state.get("breakthroughTokens", []),
    }

    out_path = DATA_DIR / f"{scan_time_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log.info("📄 扫描结果已保存: %s", out_path)'''

new_func = '''def output_scan_json(queue_state: dict, eliminated_this_round: list = None,
                    rejected_at_entry: list = None, quality_results: list = None):
    """输出扫描结果到 JSON 文件（用于 GitHub Actions 前端展示模式）"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    utc_now = datetime.now(timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    beijing_now = utc_now.astimezone(beijing_tz)
    scan_time_str = beijing_now.strftime("%Y-%m-%dT%H-%M-%S")

    def enrich_token(t):
        """为代币补充前端需要的字段"""
        t = t.copy()
        price = t.get("price", 0)
        kline_high = t.get("klineHigh", 0)
        peak_price = t.get("peakPrice", 0)
        
        max_price = kline_high if kline_high > 0 else peak_price
        t["max_price"] = max_price
        
        if max_price > 0 and price > 0:
            t["price_ratio"] = price / max_price
        else:
            t["price_ratio"] = 0
        
        t["peak_holders"] = t.get("peakHolders", 0)
        t["age_hours"] = t.get("_age_hours", 0)
        bonus_tags = t.get("_bonus_tags", []).copy()
        t["bonus_tags"] = bonus_tags
        t["bonus_score"] = t.get("_bonus_score", 0)
        t["social_links"] = t.get("socialLinks", {})
        t["is_copycat"] = t.get("isCopycat", False)
        t["copycat_count"] = t.get("copycat", {}).get("count", 0)
        t["wallet_signals"] = t.get("wallet_signals", [])
        t["is_quality_developer"] = t.get("is_quality_developer", False)
        t["reason"] = t.get("elimReason", "")
        t["created_at"] = t.get("createdAt", 0)
        t["ath"] = t.get("max_price") or t.get("peakPrice", 0)
        t["social_count"] = t.get("socialCount", 0)
        t["total_supply"] = t.get("totalSupply", 0)
        t["raised_amount"] = t.get("raisedAmount", 0)
        t["market_cap"] = t.get("marketCap", 0)
        t["price_change_h1"] = t.get("priceChangeH1", 0)
        t["price_change_h24"] = t.get("priceChangeH24", 0)
        t["boosts"] = t.get("boosts", 0)
        
        if not t.get("_kline_missing") and (t.get("_kline_highest") or t.get("klineHigh")):
            bonus_tags.append("通过k线筛")
            t["bonus_tags"] = bonus_tags
        
        return t

    def format_rejected(r):
        token = r.get("token", {})
        detail = r.get("detail") or {}
        elim_reason = f"入场拒绝: {r.get('reason', '')}"
        return {
            "address": token.get("address", ""),
            "name": detail.get("name") or token.get("name", ""),
            "symbol": detail.get("shortName") or token.get("symbol", ""),
            "elimReason": elim_reason,
            "reason": elim_reason,
            "eliminatedAt": queue_state.get("lastScanTime", 0),
            "createdAt": token.get("createdAt", 0),
            "created_at": token.get("createdAt", 0),
        }

    enriched_tokens = [enrich_token(t) for t in (quality_results or [])]
    enriched_queue = [enrich_token(t) for t in (queue_state.get("tokens", []))]
    enriched_eliminated = [enrich_token(t) for t in (eliminated_this_round or [])]
    enriched_rejected = [format_rejected(r) for r in (rejected_at_entry or [])]
    
    log.info("📄 输出扫描结果: 精筛 %d, 队列 %d, 本轮淘汰 %d, 入场淘汰 %d",
             len(enriched_tokens), len(enriched_queue), len(enriched_eliminated), len(enriched_rejected))

    output = {
        "scanTime": beijing_now.strftime("%Y-%m-%d %H:%M:%S"),
        "tokens": enriched_tokens,
        "queue": enriched_queue,
        "eliminatedThisRound": enriched_eliminated,
        "rejectedAtEntry": enriched_rejected,
        "lastBlock": queue_state.get("lastBlock", 0),
        "lastScanTime": queue_state.get("lastScanTime", 0),
        "scanRound": queue_state.get("scanRound", 0),
        "marketSentiment": queue_state.get("marketSentiment", 0),
        "totalTokens": queue_state.get("totalTokens", 0),
        "filteredTokens": queue_state.get("filteredTokens", 0),
        "newDiscovered": queue_state.get("newDiscovered", 0),
        "newAdmitted": queue_state.get("newAdmitted", 0),
        "eliminatedCount": queue_state.get("eliminatedCount", 0),
        "eliminatedTotal48h": queue_state.get("eliminatedTotal48h", 0),
        "queueSize": queue_state.get("queueSize", len(queue_state.get("tokens", []))),
        "breakthroughTokens": queue_state.get("breakthroughTokens", []),
    }

    out_path = DATA_DIR / f"{scan_time_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log.info("📄 扫描结果已保存: %s", out_path)'''

if old_func in content:
    content = content.replace(old_func, new_func)
    with open('/workspace/src/scanner.py', 'w') as f:
        f.write(content)
    print("✅ 成功修复 output_scan_json 函数")
else:
    print("❌ 未找到目标代码")
