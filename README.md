# Binance Futures Testnet — Trading Bot

A simplified command-line trading bot for placing **Market** and **Limit** orders on the **Binance USDT-M Futures Testnet**.

> ⚠️ **Testnet only** — this bot is hard-coded to `https://testnet.binancefuture.com` and will never touch real funds.

---

## Table of Contents

- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [CLI Reference](#cli-reference)
- [Project Structure](#project-structure)
- [Logging](#logging)
- [Assumptions & Decisions](#assumptions--decisions)

---

## Requirements

| Dependency | Version | Purpose |
|---|---|---|
| Python | ≥ 3.10 | Runtime |
| `python-binance` | 1.0.19 | Binance REST API wrapper |
| `python-dotenv` | 1.0.1 | `.env` credential loading |
| `typer` | 0.12.3 | CLI framework |
| `rich` | 13.7.1 | Terminal UI / formatting |
| `requests` | 2.31.0 | HTTP transport |

---

## Setup

### 1. Clone or navigate to the project

```bash
cd binance_future_testnets
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API credentials

Open `.env` and insert your testnet keys:

```dotenv
BINANCE_TESTNET_API_KEY=<your_testnet_api_key>
BINANCE_TESTNET_API_SECRET=<your_testnet_api_secret>
```

Get free testnet keys at → **<https://testnet.binancefuture.com>**

---

## Running the Bot

All commands are run from the **project root** (`binance_future_testnets/`).

### Interactive mode (prompted)

```bash
python -m bot.cli place-order
```

The bot will prompt for symbol, side, order type, quantity, and price (if LIMIT).

### Non-interactive — Market order

```bash
python -m bot.cli place-order \
  --symbol BTCUSDT \
  --side   BUY \
  --type   MARKET \
  --quantity 0.001
```

### Non-interactive — Limit order

```bash
python -m bot.cli place-order \
  --symbol   BTCUSDT \
  --side     SELL \
  --type     LIMIT \
  --quantity 0.001 \
  --price    80000.00
```

### Help

```bash
python -m bot.cli --help
python -m bot.cli place-order --help
```

---

## CLI Reference

```
Usage: python -m bot.cli place-order [OPTIONS]

Options:
  -s, --symbol    TEXT    Trading pair (e.g. BTCUSDT)
      --side      TEXT    BUY or SELL
  -t, --type      TEXT    MARKET or LIMIT
  -q, --quantity  FLOAT   Quantity to trade (e.g. 0.001)
  -p, --price     FLOAT   Limit price — required for LIMIT orders
      --help              Show this message and exit.
```

---

## Project Structure

```
binance_future_testnets/
├── .env                    # API credentials (git-ignored)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── bot.log                 # Auto-created on first run (rotating, 5 MB × 3)
└── bot/
    ├── __init__.py         # Package metadata
    ├── client.py           # Testnet-pinned Binance client
    ├── orders.py           # Market & Limit order placement logic
    ├── validators.py       # Input validation for all order parameters
    ├── logging_config.py   # Rotating file + console logging
    └── cli.py              # Typer/Rich CLI entry point
```

---

## Logging

Logs are written to `bot.log` (created automatically in the project root).

| Handler | Level | Notes |
|---------|-------|-------|
| File (`bot.log`) | DEBUG | All API requests, responses, errors |
| Console (stderr) | WARNING | Only problems shown in the terminal |

The file rotates at **5 MB** and keeps **3 backups** (`bot.log.1`, `bot.log.2`, `bot.log.3`).

---

## Assumptions & Decisions

| Area | Decision |
|---|---|
| **Testnet URL** | Hard-coded to `https://testnet.binancefuture.com` — cannot be overridden via config to prevent accidental live trading. |
| **Time-in-force** | LIMIT orders use `GTC` (Good-Till-Cancelled) — most commonly expected behaviour. |
| **Quantity precision** | Quantities and prices are formatted to **8 decimal places** with trailing zeros stripped to satisfy Binance's `LOT_SIZE` filters for common pairs. You may need to adjust precision for specific symbols. |
| **Credential loading** | `python-dotenv` loads `.env` relative to `bot/client.py`, so the project root `.env` is always found regardless of the working directory. |
| **Error surfacing** | `BinanceAPIException` and `BinanceRequestException` are caught at every layer and re-raised with human-readable messages; full stack traces go to `bot.log` only. |
| **Python version** | Requires Python ≥ 3.10 for `match`/`case` readiness and `X \| Y` union type hints (though the current code uses `Optional` for ≥ 3.9 compatibility). |
| **No live trading** | The `python-binance` `testnet=True` flag is set and `client.FUTURES_URL` is overridden for belt-and-suspenders testnet safety. |
