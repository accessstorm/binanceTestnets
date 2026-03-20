"""
orders.py
---------
Order placement logic for USDT-M Futures on the Binance Testnet.

Supports:
  - MARKET orders
  - LIMIT orders (GTC time-in-force)

All Binance API errors and network failures are caught and re-raised as
human-readable exceptions, with full detail written to the log file.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.logging_config import logger


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_decimal(value: Decimal) -> str:
    """Strip trailing zeros from a Decimal for API submission."""
    return f"{value:.8f}".rstrip("0").rstrip(".")


# ── Order placement ───────────────────────────────────────────────────────────

def place_market_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: Decimal,
) -> dict:
    """
    Place a MARKET order on USDT-M Futures testnet.

    Args:
        client:   Authenticated Binance testnet client.
        symbol:   Trading pair (e.g. 'BTCUSDT').
        side:     'BUY' or 'SELL'.
        quantity: Number of contracts/units.

    Returns:
        Raw API response dict from Binance.

    Raises:
        BinanceAPIException:     Binance rejected the order.
        BinanceRequestException: Network / connectivity failure.
        RuntimeError:            Any other unexpected error.
    """
    qty_str = _format_decimal(quantity)

    logger.info(
        "Placing MARKET order → symbol=%s side=%s quantity=%s",
        symbol, side, qty_str,
    )

    try:
        response = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty_str,
        )
    except BinanceAPIException as exc:
        logger.error(
            "BinanceAPIException on MARKET order: code=%s message=%s",
            exc.code, exc.message,
        )
        raise BinanceAPIException(
            exc.response, exc.status_code,
            f"Binance rejected the MARKET order: [{exc.code}] {exc.message}",
        ) from exc
    except BinanceRequestException as exc:
        logger.error("Network error placing MARKET order: %s", exc)
        raise BinanceRequestException(
            f"Network failure when placing MARKET order: {exc}"
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error placing MARKET order: %s", exc)
        raise RuntimeError(f"Unexpected error: {exc}") from exc

    logger.info(
        "MARKET order placed successfully → orderId=%s status=%s",
        response.get("orderId"), response.get("status"),
    )
    return response


def place_limit_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> dict:
    """
    Place a LIMIT order on USDT-M Futures testnet.

    Args:
        client:        Authenticated Binance testnet client.
        symbol:        Trading pair (e.g. 'BTCUSDT').
        side:          'BUY' or 'SELL'.
        quantity:      Number of contracts/units.
        price:         Limit price.
        time_in_force: GTC (Good-Till-Cancelled) by default.

    Returns:
        Raw API response dict from Binance.

    Raises:
        BinanceAPIException:     Binance rejected the order.
        BinanceRequestException: Network / connectivity failure.
        RuntimeError:            Any other unexpected error.
    """
    qty_str   = _format_decimal(quantity)
    price_str = _format_decimal(price)

    logger.info(
        "Placing LIMIT order → symbol=%s side=%s quantity=%s price=%s tif=%s",
        symbol, side, qty_str, price_str, time_in_force,
    )

    try:
        response = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            quantity=qty_str,
            price=price_str,
            timeInForce=time_in_force,
        )
    except BinanceAPIException as exc:
        logger.error(
            "BinanceAPIException on LIMIT order: code=%s message=%s",
            exc.code, exc.message,
        )
        raise BinanceAPIException(
            exc.response, exc.status_code,
            f"Binance rejected the LIMIT order: [{exc.code}] {exc.message}",
        ) from exc
    except BinanceRequestException as exc:
        logger.error("Network error placing LIMIT order: %s", exc)
        raise BinanceRequestException(
            f"Network failure when placing LIMIT order: {exc}"
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error placing LIMIT order: %s", exc)
        raise RuntimeError(f"Unexpected error: {exc}") from exc

    logger.info(
        "LIMIT order placed successfully → orderId=%s status=%s",
        response.get("orderId"), response.get("status"),
    )
    return response


def place_order(
    client: Client,
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Optional[Decimal] = None,
) -> dict:
    """
    Dispatch to the appropriate order placement function.

    Args:
        client:     Authenticated Binance testnet client.
        symbol:     Trading pair (e.g. 'BTCUSDT').
        side:       'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity:   Number of contracts/units.
        price:      Required for LIMIT orders; ignored for MARKET.

    Returns:
        Raw API response dict from Binance.

    Raises:
        ValueError: If LIMIT order is requested but price is not provided.
    """
    if order_type == "MARKET":
        return place_market_order(client, symbol, side, quantity)

    if order_type == "LIMIT":
        if price is None:
            raise ValueError("Price must be provided for LIMIT orders.")
        return place_limit_order(client, symbol, side, quantity, price)

    raise ValueError(f"Unsupported order type: '{order_type}'")
