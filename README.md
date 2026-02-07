# Web3 MCP Server

A FastAPI-based server providing Web3 tools and cryptocurrency data.

## Features

- Cryptocurrency price data
- Global market statistics
- Trending coins
- Crypto news headlines
- Wallet transaction history

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `uvicorn main:app --reload`

## Endpoints

- `/` - Root endpoint with available tools
- `/tools/ping` - Health check
- `/tools/price?coin=ethereum` - Get coin price
- `/tools/global` - Global market data
- `/tools/news` - Crypto news
- `/tools/trending` - Trending coins
- `/tools/wallet-tx?address=<address>` - Wallet transactions (requires ETHERSCAN_API_KEY)

## Environment Variables

- `ETHERSCAN_API_KEY` - API key for Etherscan (required for wallet transactions)
