# BSC Token Scanner

BSC 链上新代币扫描器。直接扫描链上 [Four.meme](https://four.meme) 和 [Flap](https://flap.sh/bnb) 合约的 `TokenCreated` 事件发现新代币，采用**队列淘汰制**持续跟踪，自动剔除弃盘币，对存活代币执行精筛，支持**可选自动交易**。

## 两种运行模式

本项目有两个独立的入口文件，分别对应不同的运行场景：

### 入口 1：GitHub Actions 前端展示模式

**文件**: `src/scan.py`

通过 GitHub Actions + 外部cron 定时触发（每 15 分钟），执行扫描并推送到 `data` 分支供前端展示：

```bash
python3 src/scan.py
```

特点：

- 单次执行，不常驻
- 不执行自动交易
- 输出 JSON 到 data/ 目录
- 构建前端 site/
- 部署到 GitHub Pages（或自定义域名）
- 扫描数据不会无限膨胀

### 入口 2：服务器交易模式

**文件**: `src/scanner.py`

在服务器上常驻运行，同时支持扫描和自动交易：

```bash
python3 src/scanner.py
```

特点：

- 常驻运行，持续扫描
- 执行自动交易（需配置 `trading.enabled=true`）
- 启动持仓监控线程
- queue.json 定期清理（保留 48 小时内）
- 服务器上只pull代码，不push数据

## 架构：极速扫描

```
每 15 分钟执行一次 (GitHub Actions) 或 持续运行 (服务器):

1. 链上发现 (~1s)
   BSC RPC eth_getLogs → four.meme + flap TokenCreated 事件 → 新代币地址

2. 入场筛 (~数秒)
   four.meme Detail API + flap.sh 页面 SSR 社交数据 + 链上 totalSupply
   → 淘汰总量≠10亿 / 币龄>48h (社交仅供展示, 不作为淘汰条件)

3. 淘汰检查 (~数秒)
   DexScreener 批量查价(含交易量/买卖笔数/涨跌幅/Boost) + four.meme Detail API
   → 永久淘汰弃盘币

4. 精筛 (瞬时)
   币龄<=1h && 当前价<=0.00001 && 最高价<=0.00002 && KOL/聪明钱任一>=3% && KOL和聪明钱均>=1% && Top10持仓<=20%
   → 全部条件 AND

5. 仿盘检测
   本地统计同名代币数量 (零 API 调用)
```

## 代币来源

两个平台都使用 bonding curve 机制，买走 80% 供应量后迁移到 PancakeSwap。

| 平台      | 合约                                   | 代币后缀        | Detail API                                        |
| --------- | -------------------------------------- | --------------- | ------------------------------------------------- |
| four.meme | `0x5c952063...` (TokenManagerOriginal) | `4444` / `ffff` | 社交链接/持币数/进度/募资额 |
| flap      | `0xe2cE6ab0...` (Portal)               | `8888` / `7777` | IPFS + flap.sh 社交媒体 + 链上 getToken() 进度 |

## 数据源

| 数据源                    | 用途                                                  | 限流                        |
| ------------------------- | ----------------------------------------------------- | --------------------------- |
| BSC RPC (publicnode)      | 链上 TokenCreated 事件发现 + flap getToken() 进度查询 + 持币数统计(Transfer事件) | 无硬限制                    |
| four.meme Detail API      | 社交链接/持币数(bonding curve阶段)/进度/募资额        | ~5 req/s                    |
| flap IPFS + flap.sh 页面   | flap 代币社交媒体 (twitter/telegram/website)          | ~5 req/s                    |
| DexScreener API           | 批量价格+流动性+交易量+买卖笔数+涨跌幅+Boost          | ~300 req/min                |
| Ethereum RPC (publicnode) | ETH Gas 大盘指数 (eth_feeHistory gasUsedRatio)        | 无硬限制                    |
| Solana RPC (mainnet-beta) | SOL TPS 大盘指数 (getRecentPerformanceSamples)        | 无硬限制                    |
| 本地队列统计              | 仿盘检测：同名/近似名代币数量                        | 无                          |

> 注意：当前已禁用所有 GeckoTerminal 请求。

### 原始数据格式示例

以下是各数据源的原始响应格式（使用真实链上代币数据）：

#### 1. BSC RPC `eth_getLogs` — four.meme TokenCreated 事件

```json
{
  "address": "0x5c952063c7fc8610ffdb798152d69f0b9550762b",
  "topics": [
    "0x0a5575b3648bae2210cee56bf33254cc1ddfbc7bf637c0af2ac18b14fb1bae19",
    "0x000000000000000000000000a1b2c3d4e5f6789012345678901234567890abcd"
  ],
  "data": "0x0000000000000000000000000000000000000000000000000000000000000000" +
          "000000000000000000000a1b2c3d4e5f6789012345678901234567890abcd" +
          "0000000000000000000000000000000000000000000000000000000000000000" +
          "0000000000000000000000000000000000000000000000000000000000000000" +
          "0000000000000000000000000000000000000000000000000000000000000000" +
          "0000000000000000000000000000000000000000000000000000000000000000" +
          "0000000000000000000000000000000000000000000000000000000000000000" +
          "0000000000000000000000000000000000000000000000000000000000000000",
  "blockNumber": "0x1a2b3c4d",
  "transactionHash": "0xabcd1234...",
  "logIndex": "0x0"
}
```

**解析后字段:**

- `address`: 代币合约地址 (topics[1] 后 40 字符)
- `creator`: 创建者钱包地址 (data 前 64 字符偏移)
- `createdAt`: 创建时间戳 (从 data 解析，旧版有，新版需 detail API 补全)
- `source`: "four.meme"

---

#### 2. BSC RPC `eth_getLogs` — flap TokenCreated 事件

```json
{
  "address": "0xe2ce6ab80874fa9fa2aae65d277dd6b8e65c9de0",
  "topics": [
    "0x504e7f360b2e5fe33cbaaae4c593bc55305328341bf79009e43e0e3b7f699603"
  ],
  "data": "0x0000000000000000000000000000000000000000000000000067b8e4f1000000" +  // ts: 17364879040
          "000000000000000000000000a1b2c3d4e5f6789012345678901234567890abcd" +  // creator
          "0000000000000000000000000000000000000000000000000000000000000123" +  // nonce
          "00000000000000000000000000000000000000000000000000000000dead8888" +  // token (以8888结尾)
          "00000000000000000000000000000000000000000000000000000000000000c0" +  // name offset
          "0000000000000000000000000000000000000000000000000000000000000100" +  // symbol offset
          "0000000000000000000000000000000000000000000000000000000000000140" +  // meta offset
          // 动态字符串数据...
          "000000000000000000000000000000000000000000000000000000000000000d" +  // name len = 13
          "436f696e50756572790000000000000000000000000000000000000000000000" +  // "CoinPuer"
          "0000000000000000000000000000000000000000000000000000000000000008" +  // symbol len = 8
          "434f494e34383838000000000000000000000000000000000000000000000000" +  // "COIN8888"
          "000000000000000000000000000000000000000000000000000000000000001d" +  // meta len = 29
          "6261666b72656962376b70706576746b7a3267746b6e3334786c766434387900"   // "bafkreib7kppev..."
  "blockNumber": "0x1a2b3c4e",
  "transactionHash": "0xef1234...",
  "logIndex": "0x1"
}
```

**解析后字段:**

- `address`: 代币合约地址 (必须以 8888 或 7777 结尾)
- `creator`: 创建者钱包地址
- `createdAt`: 创建时间戳 (毫秒)
- `name/symbol`: 从动态字符串解析
- `meta`: IPFS CID (存储社交链接等元数据)
- `source`: "flap"

---

#### 3. four.meme Detail API — `GET /meme-api/v1/private/token/get/v2?address=0xd001bc921198b70b4631ea75ff2fb744f23b4444`

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "name": "CoinPuer",
    "shortName": "COIN",
    "descr": "The best meme token on BSC",
    "totalAmount": "1000000000000000000000000000000",
    "launchTime": 1736487904000,
    "twitterUrl": "https://twitter.com/coinpuer",
    "telegramUrl": "https://t.me/coinpuer",
    "webUrl": "https://coinpuer.io",
    "tokenPrice": {
      "price": "0.000023400000000000",
      "holderCount": 156,
      "progress": 0.456,
      "day1Vol": "2345000.00",
      "liquidity": "567.89",
      "raisedAmount": "8901.23"
    }
  }
}
```

**提取后字段:**

```python
{
    "holders": 156,
    "price": 0.0000234,          # USD价格 (已转换)
    "totalSupply": 1_000_000_000, # 已除以decimals
    "socialCount": 3,             # 社交链接数量
    "socialLinks": {"twitter": "...", "telegram": "...", "website": "..."},
    "progress": 0.456,            # 0~1
    "liquidity": 567.89,
    "raisedAmount": 8901.23
}
```

---

#### 4. flap Portal `getTokenV5(address)` — RPC `eth_call`

**请求:**

```json
{
  "jsonrpc": "2.0",
  "method": "eth_call",
  "params": [
    {
      "to": "0xe2ce6ab80874fa9fa2aae65d277dd6b8e65c9de0",
      "data": "0x5c4bc504000000000000000000000000d001bc921198b70b4631ea75ff2fb744f23b4444"
    },
    "latest"
  ],
  "id": 1
}
```

**响应 (ABI解码前):**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": "0x0000000000000000000000000000000000000000000000000000000000000001" +  // status: 1=Tradable
            "00000000000000000000000000000000000000000000000000000000000003e8" +  // reserve: 1000 wei
            "0000000000000000000000000000000000000000000000000000000005f5e100" +  // supply
            "0000000000000000000000000000000000000000000000000000033b2e8c9f" +  // price: 0.00001 wei
            "0000000000000000000000000000000000000000000000000000000000000000" +  // flags
            "000000000000000000000000000000000000000000000000000b1a2bc2ec50000" +  // r: virtual quote
            "00000000000000000000000000000000000000000000000e8d4a51000000000" +  // h: virtual token
            "0000000000000000000000000000000000000000000021e19e0c9bab2400000" +  // K: constant product
            "000000000000000000000000000000000000000000000005af3107a40000000" +  // targetSupply
            "0000000000000000000000000000000000000000000000000000000000000000"   // quoteToken: BNB
}
```

**解码后字段:**

```python
{
    "reserve": 0.0000000000000001000,    # BNB amount raised
    "progress": 0.342,                   # reserve / target_reserve
    "price_native": 0.000000000000003334, # BNB price per token
    "quote_token": "0x0000...0000",       # BNB计价
    "graduated": False                    # status != 4
}
```

---

#### 5. DexScreener API — `GET /tokens/v1/bsc/{address}`

```json
{
  "pairs": [
    {
      "chainId": "bsc",
      "dexId": "pancakeswap",
      "pairAddress": "0x16e4d3c7d27c4e34a45f6d1b3c8f9b0b2e3d4c5a",
      "baseToken": {
        "address": "0xd001bc921198b70b4631ea75ff2fb744f23b4444",
        "name": "CoinPuer",
        "symbol": "COIN"
      },
      "quoteToken": {
        "address": "0x55d398326f99059ff775485246999027b3197955",
        "symbol": "USDT"
      },
      "priceUsd": "0.00002340",
      "priceNative": "0.0000000034",
      "liquidity": {
        "usd": 567.89,
        "base": 23456.78,
        "quote": 890.12
      },
      "volume": {
        "h24": 12345.67,
        "h6": 5678.9,
        "h1": 123.45,
        "m5": 12.34
      },
      "priceChange": {
        "m5": 2.34,
        "h1": 5.67,
        "h6": -3.21,
        "h24": 12.45
      },
      "txns": {
        "h24": { "buys": 45, "sells": 23 },
        "h6": { "buys": 12, "sells": 6 },
        "h1": { "buys": 3, "sells": 1 },
        "m5": { "buys": 0, "sells": 1 }
      },
      "boosts": {
        "active": 0,
        "spent": "0"
      }
    }
  ]
}
```

**提取后字段:**

```python
{
    "price": 0.00002340,
    "liquidity": 567.89,
    "volume24h": 12345.67,
    "volumeH1": 123.45,
    "buysH1": 3, "sellsH1": 1,
    "buysH24": 45, "sellsH24": 23,
    "priceChangeM5": 2.34,
    "priceChangeH1": 5.67,
    "priceChangeH6": -3.21,
    "priceChangeH24": 12.45,
    "boosts": 0
}
```

---

### 正常价区间

正常价区间: 0.000001 ~ 0.1。10亿总量的代币，价格0.000001，市值就是1000u；价格0.1，市值就是1亿u。

### 峰值价格说明

峰值价格（peakPrice）是代币在队列存活期间记录到的最高价格。每轮通过 DexScreener 实时价快照更新：

1. DexScreener 实时价快照取 max（每轮必做）

### 价格单位与数据源

- 价格统一保存为 USD/USDT 单位。
- DexScreener 有多个交易池时，使用 USD 流动性最大的池的 `priceUsd`，避免尘埃池或旧池异常价格。
- Four.meme bonding curve 的 BNB/WBNB 原生报价（包括缺失计价字段的响应）乘以实时 BNB/USD；稳定币报价直接使用。
- 无法识别计价币时不使用原始价格，等待 DexScreener USD 价格，防止原生报价被误当成 USD。

### 持币数查询方案

持币数是筛选和淘汰的核心指标，但 four.meme 代币的生命周期跨越 bonding curve 和 DEX 两个阶段，没有单一数据源能覆盖全程。当前采用多源互补策略：

**优先级: BSCScan 网页爬取 > four.meme Detail API > RPC Transfer 事件统计 > 缓存**

| 数据源                              | 覆盖阶段           | 说明                         |
| ---------------------------------- | ------------------ | ---------------------------- |
| BSCScan 网页爬取                   | 已毕业 (DEX 阶段)  | 首选                         |
| four.meme Detail API `holderCount` | Bonding curve 阶段 | 平台内部记账，毕业后返回 0   |
| RPC `eth_getLogs` Transfer 事件统计 | 已毕业 (DEX 阶段)  | 兜底：统计持币地址数量         |
| 队列缓存                            | 兜底               | 上一轮的持币数，避免数据断档 |

注意：只对已毕业代币（progress ≥ 1）发起 BSCScan 查询，未毕业代币直接用 detail API，避免浪费请求。

## 淘汰规则（永久剔除）

满足任一条件即从队列中永久移除:

| #   | 条件                            | 说明                                         |
| --- | ------------------------------- | -------------------------------------------- |
| 0   | 蹭名币 (symbol/name 命中黑名单) | USDT/BTC/ETH 等知名币种同名, 100% 假币       |
| 1   | 价格从峰值跌 95%+               | 暴跌弃盘 (当前价格<1e-7 视为 API 异常, 跳过) |
| 1b  | 单根K线跌幅 > 55%               | 过山车币 (暴涨后暴跌)                        |
| 2   | 流动性跌破 $100 (仅已毕业)      | 流动性枯竭                                   |
| 3   | 进度 < 1% 且币龄 > 1h           | bonding curve 上的死币                       |
| 3b  | 进度 < 5% 且币龄 > 2h           | 进度停滞                                     |
| 3c  | 进度 < 10% 且币龄 > 4h          | 进度停滞                                     |
| 3d  | 进度 < 15% 且币龄 > 8h          | 进度停滞                                     |
| 4   | 进度从峰值跌 50 个百分点+        | 热度消退 (加减法)                            |
| 5   | 币龄 > 48h                      | 超出关注窗口                                 |
| 6   | 诈骗代币黑名单                   | 代币合约地址黑名单                           |
| 7   | 诈骗开发者黑名单                 | 开发者钱包地址黑名单                         |

> 注: 社交媒体仅供前端展示, 不作为淘汰条件
> 注: 诈骗代币黑名单超过 48h 自动清理，避免无限增长

## 精筛规则（当前开仓策略）

从队列存活币中筛选符合当前开仓条件的代币。

| #   | 条件        | 说明             |
| --- | ----------- | ---------------- |
| 1 | 币龄 | ≤ 1h |
| 2 | 当前价 | ≤ 0.00001 |
| 3 | 最高价 | ≤ 0.00002 |
| 4 | 关键持仓 | KOL 或聪明钱任一 ≥ 3%，且 KOL ≥ 1% 且聪明钱 ≥ 1% |
| 5 | Top10 持仓 | 币安 Web3 数据 ≤ 20% |

## 自动交易策略（可选功能）

### 交易平台支持

- PancakeSwap V2（已毕业代币）
- four.meme Bonding Curve
- flap Bonding Curve（通过 Router 合约）

### 交易架构（USDT 为本位）

- 所有买入以 USDT 计价，不持有过多 BNB 避免价格波动风险
- BNB 仅作为 gas 和交易中转，保持在 $5~$10 区间
- 买入流程: USDT → BNB (如需要) → 目标代币
- 卖出流程: 目标代币 → BNB → USDT

### 止盈止损策略

| #   | 策略            | 条件                                                            | 说明                                 |
| --- | --------------- | --------------------------------------------------------------- | ------------------------------------ |
| 1   | 固定开仓        | 每次买入固定 1.4U                                                | 不按仓位比例浮动                     |
| 2   | 100倍止盈       | 每小时扫描持仓，检测到价格达到买入价 100 倍即平仓                | 抓极端涨幅                           |
| 3   | 时间平仓        | 持仓超过 7 天自动平仓                                            | 止盈止损主要按时间退出               |
| 4   | 重买冷却        | 盈利平仓后 6h, 亏损平仓后 12h                                   | 避免反复追同一个币                   |

旧版中点/10%分段止盈策略已在代码中备份为 `check_sell_conditions_legacy_v18`, 当前不参与卖出。

## 前端功能

五个 Tab 视图：

- **精筛结果**：通过全部筛选条件的推荐代币
- **队列存活**：当前队列中所有存活代币（含价格/持币/流动性/峰值等）
- **本轮淘汰**：本轮被淘汰的代币及淘汰原因
- **入场淘汰**：新发现但未通过入场筛的代币及原因（币龄不合格，进度不合格，总量不符等）

搜索功能覆盖全部四个 Tab 的历史数据，任何代币都可以搜到并查看淘汰原因。用合约地址搜索时，会展示该代币在所有历史扫描时间点的快照（价格、持币数、流动性等变化），方便追踪代币的完整生命周期。

## 使用方法

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### 2. 配置

```bash
cp config.example.json config.json
```

编辑 `config.json`，填入以下配置：

- `dingtalk_webhook` / `dingtalk_secret`：钉钉机器人 Webhook（可选，用于错误推送）
- `bscscan_api_key`：BSCScan API Key（精筛后防线需要）
- `trading.enabled`：是否启用自动交易
- `trading.private_key`：交易钱包私钥（自动交易需要）

### 3. 运行

```bash
# 服务器交易模式（常驻运行）
python3 src/scanner.py

# GitHub Actions 模式（单次扫描）
python3 src/scan.py

# 构建前端（GitHub Actions 自动执行）
npm run build
```

## 配置参数

### 扫描参数

| 参数                    | 默认值 | 说明             |
| ----------------------- | ------ | ---------------- |
| `scan_interval_minutes` | 15     | 扫描间隔（分钟） |
| `max_push_count`        | 100    | 每轮最多推送数量 |
| `max_age_hours`         | 48     | 关注窗口（小时） |
| `queue_recent_1h_only`  | false  | 开启后队列存活只保留币龄 1h 内代币，超过 1h 直接淘汰 |
| `bscscan_api_key`       | -      | BSCScan API Key  |

### 交易参数

| 参数                     | 默认值 | 说明                |
| ------------------------ | ------ | ------------------- |
| `trading.enabled`        | false  | 是否启用自动交易    |
| `trading.private_key`    | -      | 钱包私钥            |
| `trading.slippage_pct`   | 12     | 滑点（%）           |
| `trading.fixed_buy_usd`  | 1.4    | 固定开仓金额（USD） |
| `trading.max_hold_days`  | 7      | 最大持仓天数        |
| `trading.take_profit_multiple` | 100 | 止盈倍数（价格/买入价） |
| `trading.monitor_interval_sec` | 3600 | 持仓扫描间隔（秒） |

## 项目结构

```
├── src/
│   ├── scanner.py        # 扫描主脚本
│   ├── trader.py         # 交易模块
│   ├── error_handler.py  # 异常处理+钉钉推送
│   └── build.js          # 前端构建脚本
├── public/
│   └── index.html        # 前端页面源文件
├── site/                 # 构建产物（GitHub Pages）
├── data/                 # 扫描数据（gitignore）
│   ├── queue.json        # 队列状态（断点续扫）
│   └── *.json            # 每轮扫描结果
├── config.example.json   # 配置模板
├── config.json           # 本地配置（gitignore）
├── requirements.txt      # Python依赖
└── package.json
```

## License

ISC
