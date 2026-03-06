# ₿ CryptoWatch

**Never Miss a Pump** - 实时追踪币价，猎杀每个波动！

## 快速开始

```bash
# 查看主流币价格
node scripts/watch.mjs

# 查询特定币种
node scripts/watch.mjs btc
node scripts/watch.mjs btc,eth,sol

# 查看市值前 20 名
node scripts/watch.mjs --top 20
```

## 价格预警

```bash
# 设置 BTC 突破 $100,000 提醒
node scripts/alert.mjs btc --above 100000

# 设置 ETH 跌破 $3,000 提醒
node scripts/alert.mjs eth --below 3000

# 查看所有预警
node scripts/alert.mjs --list
```

## 支持币种

- BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX
- LINK, DOT, MATIC, LTC, UNI, ATOM, XLM, ETC
- NEAR, ALGO, FIL, ICP, VET, HBAR, APT, ARB, OP, SUI
- 以及 CoinGecko 支持的所有币种

## 数据源

- **CoinGecko API** - https://www.coingecko.com/en/api
- 免费 tier：10-50 calls/min，无需 API Key
- 数据延迟：< 30 秒

## 💰 定价 - 免费优先！

> 🎉 **每天 5 次免费查询** - 足够日常使用！

| 方案 | 价格 | 限制 |
|------|------|------|
| **免费版** | $0 | **5 次/天** |
| **赞助解锁** | 0.5 USDT 或 0.5 USDC | 无限使用 |

**如果觉得好用，欢迎赞助支持！** ₿

**赞助收款地址**:
- USDT (ERC20): `0x33f943e71c7b7c4e88802a68e62cca91dab65ad9`
- USDC (ERC20): `0xcb5173e3f5c2e32265fbbcaec8d26d49bf290e44`

💡 *赞助后请联系 @gztanht 获取无限使用权限*

## License

MIT © 2026 gztanht
