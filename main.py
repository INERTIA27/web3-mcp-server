from fastapi import FastAPI
import requests
from requests.exceptions import RequestException, Timeout
import xml.etree.ElementTree as ET

app = FastAPI(title="Web3 MCP Tool Server", version="1.0.0")

REQUEST_TIMEOUT = 10  # seconds


@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Web3 MCP tool server is live",
        "endpoints": [
            "/tools/ping",
            "/tools/price?coin=ethereum",
            "/tools/global",
            "/tools/news",
            "/tools/trending"
        ]
    }


@app.get("/tools/ping")
def ping():
    return {"status": "ok", "message": "pong"}


@app.get("/tools/price")
def get_price(coin: str = "ethereum"):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()

        if coin not in data:
            return {"error": "coin not found", "coin": coin}

        return {
            "coin": coin,
            "usd_price": data[coin]["usd"]
        }
    except Timeout:
        return {"error": "API request timed out"}
    except RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except ValueError:
        return {"error": "Invalid JSON response from API"}


@app.get("/tools/global")
def global_market():
    try:
        url = "https://api.coingecko.com/api/v3/global"
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()

        market = data.get("data", {})

        return {
            "total_market_cap_usd": market.get("total_market_cap", {}).get("usd"),
            "total_volume_usd": market.get("total_volume", {}).get("usd"),
            "btc_dominance": market.get("market_cap_percentage", {}).get("btc"),
            "active_cryptocurrencies": market.get("active_cryptocurrencies")
        }
    except (Timeout, RequestException, ValueError) as e:
        return {"error": f"Failed to fetch global market data: {str(e)}"}


@app.get("/tools/news")
def crypto_news():
    try:
        rss_url = "https://cointelegraph.com/rss"
        r = requests.get(rss_url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()

        root = ET.fromstring(r.content)
        headlines = []

        # Parse RSS items properly
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            if title_elem is not None and title_elem.text:
                title = title_elem.text.strip()
                if "Cointelegraph" not in title:
                    headlines.append(title)

        return {
            "source": "cointelegraph rss",
            "headlines": headlines[:10]
        }
    except Timeout:
        return {"error": "RSS feed request timed out"}
    except (RequestException, ET.ParseError) as e:
        return {"error": f"Failed to fetch news: {str(e)}"}


@app.get("/tools/trending")
def trending_coins():
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()

        coins = []
        for item in data.get("coins", []):
            coin = item.get("item", {})
            coins.append({
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "id": coin.get("id")
            })

        return {
            "source": "coingecko",
            "trending": coins[:10]
        }
    except Timeout:
        return {"error": "Trending request timed out"}
    except (RequestException, ValueError) as e:
        return {"error": f"Failed to fetch trending coins: {str(e)}"}