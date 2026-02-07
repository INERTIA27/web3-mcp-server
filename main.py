from fastapi import FastAPI
import requests
import os
import xml.etree.ElementTree as ET
from requests.exceptions import RequestException, Timeout

app = FastAPI(title="Web3 MCP Tool Server", version="1.0.0")

REQUEST_TIMEOUT = 10  # seconds


# -----------------------------
# ROOT
# -----------------------------
@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Web3 MCP tool server is live (Binance API version)",
        "endpoints": [
            "/tools/ping",
            "/tools/price?symbol=BTCUSDT",
            "/tools/price?symbol=ETHUSDT",
            "/tools/global",
            "/tools/trending",
            "/tools/news",
            "/tools/wallet-tx?address=0xYOURWALLET&limit=5"
        ]
    }


# -----------------------------
# BASIC TOOL
# -----------------------------
@app.get("/tools/ping")
def ping():
    return {"status": "ok", "message": "pong"}


# -----------------------------
# BINANCE PRICE TOOL
# -----------------------------
@app.get("/tools/price")
def get_price(symbol: str = "BTCUSDT"):
    """
    Binance symbols format examples:
    BTCUSDT
    ETHUSDT
    SOLUSDT
    XRPUSDT
    """

    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
        r = requests.get(url, timeout=REQUEST_TIMEOUT)

        if r.status_code != 200:
            return {
                "status": "error",
                "error": "binance_failed",
                "symbol": symbol.upper(),
                "message": r.text
            }

        data = r.json()

        return {
            "status": "success",
            "source": "binance",
            "symbol": data.get("symbol"),
            "price": float(data.get("price"))
        }

    except Timeout:
        return {"status": "error", "error": "timeout", "message": "binance request timed out"}
    except RequestException as e:
        return {"status": "error", "error": "request_failed", "message": str(e)}


# -----------------------------
# GLOBAL MARKET TOOL (COINGECKO)
# -----------------------------
@app.get("/tools/global")
def global_market():
    try:
        url = "https://api.coingecko.com/api/v3/global"
        r = requests.get(url, timeout=REQUEST_TIMEOUT)

        if r.status_code == 429:
            return {
                "status": "error",
                "error": "rate_limited",
                "message": "CoinGecko rate limited this server. Try again later."
            }

        data = r.json()
        market = data.get("data", {})

        return {
            "status": "success",
            "source": "coingecko",
            "total_market_cap_usd": market.get("total_market_cap", {}).get("usd"),
            "total_volume_usd": market.get("total_volume", {}).get("usd"),
            "btc_dominance": market.get("market_cap_percentage", {}).get("btc"),
            "active_cryptocurrencies": market.get("active_cryptocurrencies")
        }

    except Timeout:
        return {"status": "error", "error": "timeout", "message": "coingecko request timed out"}
    except RequestException as e:
        return {"status": "error", "error": "request_failed", "message": str(e)}


# -----------------------------
# TRENDING COINS TOOL (COINGECKO)
# -----------------------------
@app.get("/tools/trending")
def trending_coins():
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        r = requests.get(url, timeout=REQUEST_TIMEOUT)

        if r.status_code == 429:
            return {
                "status": "error",
                "error": "rate_limited",
                "message": "CoinGecko rate limited this server. Try again later."
            }

        data = r.json()

        coins = []
        for item in data.get("coins", []):
            coin = item.get("item", {})
            coins.append({
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "id": coin.get("id"),
                "score": coin.get("score")
            })

        return {
            "status": "success",
            "source": "coingecko",
            "trending": coins[:10]
        }

    except Timeout:
        return {"status": "error", "error": "timeout", "message": "coingecko request timed out"}
    except RequestException as e:
        return {"status": "error", "error": "request_failed", "message": str(e)}


# -----------------------------
# CRYPTO NEWS TOOL (RSS)
# -----------------------------
@app.get("/tools/news")
def crypto_news():
    rss_url = "https://cointelegraph.com/rss"

    try:
        r = requests.get(rss_url, timeout=REQUEST_TIMEOUT)
        xml_text = r.text

        root = ET.fromstring(xml_text)

        headlines = []
        for item in root.findall(".//item"):
            title = item.find("title")
            link = item.find("link")

            if title is not None and link is not None:
                headlines.append({
                    "title": title.text,
                    "link": link.text
                })

        return {
            "status": "success",
            "source": "cointelegraph_rss",
            "headlines": headlines[:10]
        }

    except Timeout:
        return {"status": "error", "error": "timeout", "message": "rss request timed out"}
    except Exception as e:
        return {"status": "error", "error": "rss_parse_failed", "message": str(e)}


# -----------------------------
# WALLET TRANSACTIONS TOOL (ETHERSCAN)
# -----------------------------
@app.get("/tools/wallet-tx")
def wallet_transactions(address: str, limit: int = 5):
    api_key = os.getenv("ETHERSCAN_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "error": "missing_api_key",
            "message": "ETHERSCAN_API_KEY not set in Render environment variables"
        }

    try:
        url = (
            "https://api.etherscan.io/api"
            f"?module=account&action=txlist&address={address}"
            f"&startblock=0&endblock=99999999&sort=desc&apikey={api_key}"
        )

        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        data = r.json()

        if data.get("status") != "1":
            return {
                "status": "error",
                "error": "etherscan_failed",
                "message": data.get("message"),
                "result": data.get("result")
            }

        txs = data.get("result", [])[:limit]

        formatted = []
        for tx in txs:
            formatted.append({
                "hash": tx.get("hash"),
                "from": tx.get("from"),
                "to": tx.get("to"),
                "value_eth": int(tx.get("value", "0")) / 10**18,
                "timestamp": tx.get("timeStamp"),
                "blockNumber": tx.get("blockNumber")
            })

        return {
            "status": "success",
            "source": "etherscan",
            "address": address,
            "count": len(formatted),
            "transactions": formatted
        }

    except Timeout:
        return {"status": "error", "error": "timeout", "message": "etherscan request timed out"}
    except RequestException as e:
        return {"status": "error", "error": "request_failed", "message": str(e)}

