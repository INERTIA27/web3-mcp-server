from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import xml.etree.ElementTree as ET

app = FastAPI(title="Web3 MCP Tool Server", version="2.0.0")

# -----------------------------
# CORS (allow miniapp frontend)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUEST_TIMEOUT = 15


# -----------------------------
# ROOT
# -----------------------------
@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Web3 MCP tool server is live",
        "endpoints": [
            "/tools/ping",
            "/tools/price?symbol=BTC",
            "/tools/trending",
            "/tools/news",
            "/tools/wallet-tx?address=0x...&limit=5"
        ]
    }


# -----------------------------
# PING
# -----------------------------
@app.get("/tools/ping")
def ping():
    return {"status": "success", "message": "pong"}


# -----------------------------
# PRICE (Coinbase API)
# Example: /tools/price?symbol=BTC
# -----------------------------
@app.get("/tools/price")
def get_price(symbol: str = Query("BTC", description="Crypto symbol like BTC, ETH")):
    symbol = symbol.upper()

    product_id = f"{symbol}-USD"
    url = f"https://api.exchange.coinbase.com/products/{product_id}/ticker"

    try:
        res = requests.get(url, timeout=REQUEST_TIMEOUT)
        if res.status_code != 200:
            return {
                "status": "error",
                "error": "coinbase_failed",
                "symbol": symbol,
                "message": f"Coinbase returned {res.status_code}"
            }

        data = res.json()

        return {
            "status": "success",
            "source": "coinbase",
            "symbol": symbol,
            "price_usd": float(data["price"])
        }

    except Exception as e:
        return {
            "status": "error",
            "error": "coinbase_failed",
            "symbol": symbol,
            "message": str(e)
        }


# -----------------------------
# TRENDING (CoinGecko)
# -----------------------------
@app.get("/tools/trending")
def get_trending():
    url = "https://api.coingecko.com/api/v3/search/trending"

    try:
        res = requests.get(url, timeout=REQUEST_TIMEOUT)
        if res.status_code != 200:
            return {
                "status": "error",
                "error": "coingecko_failed",
                "message": f"CoinGecko returned {res.status_code}"
            }

        data = res.json()

        trending = []
        for item in data.get("coins", []):
            coin = item.get("item", {})
            trending.append({
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "id": coin.get("id"),
                "score": item.get("score")
            })

        return {
            "status": "success",
            "source": "coingecko",
            "trending": trending
        }

    except Exception as e:
        return {
            "status": "error",
            "error": "coingecko_failed",
            "message": str(e)
        }


# -----------------------------
# NEWS (CoinTelegraph RSS)
# -----------------------------
@app.get("/tools/news")
def get_news(limit: int = Query(10, description="Number of headlines")):
    rss_url = "https://cointelegraph.com/rss"

    try:
        res = requests.get(rss_url, timeout=REQUEST_TIMEOUT)
        if res.status_code != 200:
            return {
                "status": "error",
                "error": "rss_failed",
                "message": f"RSS returned {res.status_code}"
            }

        root = ET.fromstring(res.text)

        headlines = []
        for item in root.findall(".//item")[:limit]:
            title = item.find("title").text if item.find("title") is not None else "No title"
            link = item.find("link").text if item.find("link") is not None else ""
            headlines.append({
                "title": title,
                "link": link
            })

        return {
            "status": "success",
            "source": "cointelegraph_rss",
            "headlines": headlines
        }

    except Exception as e:
        return {
            "status": "error",
            "error": "rss_failed",
            "message": str(e)
        }


# -----------------------------
# WALLET TX (Etherscan API V2)
# Example:
# /tools/wallet-tx?address=0x...&limit=5
# -----------------------------
@app.get("/tools/wallet-tx")
def wallet_tx(address: str, limit: int = 5):
    api_key = os.getenv("ETHERSCAN_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "error": "missing_api_key",
            "message": "ETHERSCAN_API_KEY is not set in Render environment variables"
        }

    url = (
        f"https://api.etherscan.io/v2/api"
        f"?chainid=1"
        f"&module=account"
        f"&action=txlist"
        f"&address={address}"
        f"&startblock=0"
        f"&endblock=99999999"
        f"&page=1"
        f"&offset={limit}"
        f"&sort=desc"
        f"&apikey={api_key}"
    )

    try:
        r = requests.get(url, timeout=15)
        data = r.json()

        if data.get("status") != "1":
            return {
                "status": "error",
                "error": "etherscan_failed",
                "message": data.get("message"),
                "result": data.get("result")
            }

        txs = []
        for tx in data.get("result", []):
            txs.append({
                "hash": tx.get("hash"),
                "from": tx.get("from"),
                "to": tx.get("to"),
                "value_eth": int(tx.get("value", "0")) / 10**18,
                "timeStamp": tx.get("timeStamp")
            })

        return {
            "status": "success",
            "source": "etherscan_v2",
            "address": address,
            "transactions": txs
        }

    except Exception as e:
        return {
            "status": "error",
            "error": "etherscan_failed",
            "message": str(e)
        }


    try:
        res = requests.get(url, timeout=REQUEST_TIMEOUT)
        if res.status_code != 200:
            return {
                "status": "error",
                "error": "etherscan_failed",
                "message": f"Etherscan returned {res.status_code}"
            }

        data = res.json()

        if data.get("status") != "1":
            return {
                "status": "error",
                "error": "etherscan_failed",
                "message": data.get("message"),
                "result": data.get("result")
            }

        txs = []
        for tx in data.get("result", []):
            value_eth = int(tx.get("value", "0")) / 10**18

            txs.append({
                "hash": tx.get("hash"),
                "from": tx.get("from"),
                "to": tx.get("to"),
                "value_eth": value_eth,
                "timeStamp": tx.get("timeStamp")
            })

        return {
            "status": "success",
            "source": "etherscan_v2",
            "address": address,
            "transactions": txs
        }

    except Exception as e:
        return {
            "status": "error",
            "error": "etherscan_failed",
            "message": str(e)
        }
