---
name: crypto_lookup
description: "Tra cứu giá thị trường hiện tại, biến động 24h và vốn hóa của các đồng tiền mã hóa (Bitcoin, Ethereum, Solana, v.v.) theo USD hoặc VND."
parameters:
  type: object
  properties:
    symbol:
      type: string
      description: "Ký hiệu hoặc tên đồng coin (ví dụ: 'BTC', 'ETH', 'SOL', 'bitcoin', 'ethereum')."
    vs_currency:
      type: string
      enum: [usd, vnd]
      default: usd
      description: "Đơn vị tiền tệ so sánh ('usd' hoặc 'vnd'). Mặc định là 'usd'."
  required:
    - symbol
---

# crypto_lookup

Tool tra cứu giá thị trường crypto thời gian thực qua CoinGecko API:
- Hỗ trợ các đồng tiền mã hóa phổ biến: BTC, ETH, SOL, DOGE, XRP...
- Trả về: `price`, `change_24h_pct`, `market_cap`
- Tự động fallback dữ liệu khi mất kết nối mạng.
