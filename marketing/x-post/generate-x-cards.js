const fs = require("fs");
const path = require("path");
const { chromium } = require("/Users/a1-6/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");

const outDir = path.join(__dirname, "dist");
fs.mkdirSync(outDir, { recursive: true });

const cards = [
  {
    file: "01-radar.png",
    kicker: "Token Trader",
    title: "链上新币雷达",
    subtitle: "给 BSC 新币交易者的开源扫描器",
    theme: "green",
    bullets: [
      "直接扫 four.meme / Flap 链上 TokenCreated 事件",
      "不是等别人整理列表，而是从源头捕获新币",
      "每 15 分钟刷新一次，适合盯早期机会",
    ],
    stats: [
      ["136", "最新一轮新发现"],
      ["276", "当前队列存活"],
      ["494", "累计扫描轮次"],
    ],
    foot: "前端: liuqinh2s.github.io/token_trader",
  },
  {
    file: "02-filter.png",
    kicker: "核心价值",
    title: "把噪音先砍掉",
    subtitle: "新币不是扫到就推荐，而是先进队列观察",
    theme: "blue",
    bullets: [
      "持续跟踪价格、持币数、流动性、进度、成交变化",
      "自动淘汰弃盘、暴跌、无人关注、仿盘泛滥等垃圾币",
      "队列存活列表更适合作为手动研究入口",
    ],
    stats: [
      ["19,646", "近 48h 已淘汰"],
      ["88", "最新一轮入队"],
      ["61", "最新一轮淘汰"],
    ],
    foot: "目标: 少看垃圾盘，多看值得继续研究的盘",
  },
  {
    file: "03-review.png",
    kicker: "复盘视角",
    title: "看哪些币真的跑出来过",
    subtitle: "涨幅榜和质量统计，比单次信号更有参考价值",
    theme: "orange",
    bullets: [
      "记录精筛后峰值涨幅，方便复盘题材和生命周期",
      "支持历史搜索，合约地址可回看多轮快照",
      "默认精筛策略只作参考，不承诺收益",
    ],
    stats: [
      ["99", "≥100% 涨幅样本"],
      ["5,180%", "近样本最高峰值涨幅"],
      ["14 / 154", "精筛样本命中 ≥100%"],
    ],
    foot: "非投资建议，DYOR",
  },
  {
    file: "04-build.png",
    kicker: "开源可改",
    title: "从看盘到自动交易",
    subtitle: "不只给页面，也给脚本和策略骨架",
    theme: "purple",
    bullets: [
      "提供默认精筛策略，可按自己的交易风格改规则",
      "内置可选自动交易脚本，支持快速搭建自己的 bot",
      "扫描、前端、交易模块都在项目里，适合二次开发",
    ],
    stats: [
      ["scan.py", "GitHub Actions 单次扫描"],
      ["scanner.py", "服务器常驻扫描"],
      ["trader.py", "自动交易模块"],
    ],
    foot: "GitHub / 前端入口: liuqinh2s.github.io/token_trader",
  },
];

const palettes = {
  green: {
    bg: "#f7fbf6",
    ink: "#102018",
    muted: "#52645b",
    accent: "#128c58",
    accent2: "#d7f0de",
    grid: "#dce8df",
  },
  blue: {
    bg: "#f6f9fd",
    ink: "#111b27",
    muted: "#526272",
    accent: "#1769aa",
    accent2: "#d9e9f8",
    grid: "#dde7f0",
  },
  orange: {
    bg: "#fffaf3",
    ink: "#24180e",
    muted: "#6b5c4b",
    accent: "#c25a16",
    accent2: "#f8e2c9",
    grid: "#eadfce",
  },
  purple: {
    bg: "#fbf8ff",
    ink: "#20162d",
    muted: "#62536f",
    accent: "#7a3fb1",
    accent2: "#eadbf6",
    grid: "#e6ddea",
  },
};

function html(card) {
  const p = palettes[card.theme];
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0;
    width: 1600px;
    height: 2000px;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Microsoft YaHei", Arial, sans-serif;
    background: ${p.bg};
    color: ${p.ink};
  }
  .card {
    position: relative;
    width: 1600px;
    height: 2000px;
    padding: 112px 116px 96px;
    overflow: hidden;
    background:
      linear-gradient(90deg, ${p.grid} 1px, transparent 1px) 0 0 / 80px 80px,
      linear-gradient(${p.grid} 1px, transparent 1px) 0 0 / 80px 80px,
      radial-gradient(circle at 1180px 240px, ${p.accent2} 0, transparent 420px),
      ${p.bg};
  }
  .top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 86px;
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 22px;
    font-size: 34px;
    font-weight: 800;
    letter-spacing: 0;
  }
  .mark {
    width: 54px;
    height: 54px;
    border-radius: 16px;
    background: ${p.accent};
    box-shadow: 12px 12px 0 ${p.accent2};
  }
  .kicker {
    color: ${p.accent};
    font-size: 32px;
    font-weight: 800;
  }
  h1 {
    margin: 0;
    max-width: 1180px;
    font-size: 132px;
    line-height: 1.03;
    letter-spacing: 0;
  }
  .subtitle {
    margin-top: 38px;
    max-width: 1160px;
    color: ${p.muted};
    font-size: 52px;
    line-height: 1.34;
    font-weight: 650;
  }
  .stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 28px;
    margin-top: 98px;
  }
  .stat {
    min-height: 246px;
    padding: 34px 30px;
    border: 4px solid ${p.ink};
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.62);
    box-shadow: 12px 12px 0 ${p.accent2};
  }
  .num {
    font-size: 66px;
    line-height: 1.05;
    font-weight: 900;
    color: ${p.accent};
    word-break: break-word;
  }
  .label {
    margin-top: 18px;
    font-size: 30px;
    line-height: 1.25;
    font-weight: 720;
  }
  .bullets {
    margin-top: 98px;
    display: grid;
    gap: 34px;
    max-width: 1320px;
  }
  .bullet {
    display: grid;
    grid-template-columns: 44px 1fr;
    gap: 24px;
    align-items: start;
    font-size: 42px;
    line-height: 1.38;
    font-weight: 680;
  }
  .dot {
    width: 28px;
    height: 28px;
    margin-top: 16px;
    border-radius: 999px;
    background: ${p.accent};
  }
  .footer {
    position: absolute;
    left: 116px;
    right: 116px;
    bottom: 86px;
    display: flex;
    justify-content: space-between;
    gap: 32px;
    align-items: flex-end;
    color: ${p.muted};
    font-size: 28px;
    font-weight: 700;
  }
  .url {
    color: ${p.ink};
    font-weight: 850;
  }
</style>
</head>
<body>
  <main class="card">
    <div class="top">
      <div class="brand"><span class="mark"></span><span>Token Trader</span></div>
      <div class="kicker">${card.kicker}</div>
    </div>
    <h1>${card.title}</h1>
    <div class="subtitle">${card.subtitle}</div>
    <section class="stats">
      ${card.stats.map(([num, label]) => `<div class="stat"><div class="num">${num}</div><div class="label">${label}</div></div>`).join("")}
    </section>
    <section class="bullets">
      ${card.bullets.map((b) => `<div class="bullet"><span class="dot"></span><span>${b}</span></div>`).join("")}
    </section>
    <footer class="footer">
      <span>${card.foot}</span>
      <span class="url">BSC 新币扫描 / 队列淘汰 / 精筛策略 / 自动交易</span>
    </footer>
  </main>
</body>
</html>`;
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  });
  const page = await browser.newPage({ viewport: { width: 1600, height: 2000 }, deviceScaleFactor: 1 });
  for (const card of cards) {
    await page.setContent(html(card), { waitUntil: "networkidle" });
    await page.screenshot({ path: path.join(outDir, card.file), fullPage: false });
  }
  await browser.close();
  console.log(`Generated ${cards.length} cards in ${outDir}`);
})();
