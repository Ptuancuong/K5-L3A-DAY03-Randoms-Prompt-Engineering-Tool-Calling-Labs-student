from __future__ import annotations

import os
from typing import Any
import requests

from tools._shared import TIMEOUT

COIN_MAP = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "bnb": "binancecoin",
    "binance": "binancecoin",
    "doge": "dogecoin",
    "dogecoin": "dogecoin",
    "xrp": "ripple",
    "ripple": "ripple",
    "ada": "cardano",
    "cardano": "cardano",
    "ton": "the-open-network",
    "usdt": "tether",
    "tether": "tether",
}

# Tham chiếu dự phòng khi mạng offline hoặc CoinGecko bị 429 rate-limit
FALLBACK_BENCHMARKS = {
    "bitcoin": {"price_usd": 89500.0, "change_24h": 2.3, "market_cap_usd": 1770000000000},
    "ethereum": {"price_usd": 3150.0, "change_24h": 1.8, "market_cap_usd": 380000000000},
    "solana": {"price_usd": 195.0, "change_24h": 4.5, "market_cap_usd": 92000000000},
}


def lookup_crypto(symbol: str, vs_currency: str = "usd") -> dict[str, Any]:
    """Tra cứu giá, biến động 24h và vốn hóa thị trường của đồng tiền mã hóa (crypto).
    
    Hỗ trợ các đồng phổ biến: BTC, ETH, SOL, BNB, DOGE, XRP, ADA...
    """
    if not isinstance(symbol, str) or not symbol.strip():
        return {
            "tool": "crypto_lookup",
            "error": "ValueError",
            "message": "Ký hiệu đồng tiền mã hóa (symbol) không được để trống.",
        }

    clean_sym = symbol.strip().lower().replace("$", "")
    coin_id = COIN_MAP.get(clean_sym, clean_sym)
    curr = vs_currency.lower() if vs_currency else "usd"
    if curr not in ("usd", "vnd"):
        curr = "usd"

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin_id,
        "vs_currencies": curr,
        "include_24hr_change": "true",
        "include_market_cap": "true",
    }

    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if coin_id in data:
                coin_data = data[coin_id]
                price = coin_data.get(curr, 0.0)
                change = round(coin_data.get(f"{curr}_24h_change", 0.0), 2)
                cap = coin_data.get(f"{curr}_market_cap", 0.0)
                return {
                    "tool": "crypto_lookup",
                    "symbol": symbol.upper(),
                    "coin_id": coin_id,
                    "currency": curr.upper(),
                    "price": price,
                    "change_24h_pct": change,
                    "market_cap": cap,
                    "source": "CoinGecko API (live)",
                }
    except Exception:
        pass

    # Nếu offline hoặc lỗi kết nối, dùng benchmark hợp lý
    if coin_id in FALLBACK_BENCHMARKS:
        bench = FALLBACK_BENCHMARKS[coin_id]
        rate_vnd = 25400.0 if curr == "vnd" else 1.0
        price = bench["price_usd"] * rate_vnd
        cap = bench["market_cap_usd"] * rate_vnd
        return {
            "tool": "crypto_lookup",
            "symbol": symbol.upper(),
            "coin_id": coin_id,
            "currency": curr.upper(),
            "price": price,
            "change_24h_pct": bench["change_24h"],
            "market_cap": cap,
            "source": "Market Benchmark (fallback)",
        }

    return {
        "tool": "crypto_lookup",
        "error": "NotFoundError",
        "message": f"Không tìm thấy dữ liệu thị trường cho ký hiệu tiền mã hóa: '{symbol}'",
    }
