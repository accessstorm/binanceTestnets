"""
validators.py
-------------
Input validation for all order parameters. Each validator raises a
ValueError with a descriptive message on invalid input so callers can
surface clean error messages to the user.
"""

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Optional

from bot.logging_config import logger


# ── Allowed values ────────────────────────────────────────────────────────────

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

# Minimum symbol length guard (e.g. "BTCUSDT" = 7 chars)
MIN_SYMBOL_LENGTH = 6


# ── Individual validators ─────────────────────────────────────────────────────

def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise a futures trading pair symbol.

    Args:
        symbol: Raw input string (e.g. 'btcusdt', 'BTCUSDT').

    Returns:
        Upper-cased symbol string.

    Raises:
        ValueError: If the symbol is blank or too short.
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty. Example: BTCUSDT")

    normalised = symbol.strip().upper()

    if len(normalised) < MIN_SYMBOL_LENGTH:
        raise ValueError(
            f"Symbol '{normalised}' is too short. "
            f"Expected a valid pair like BTCUSDT or ETHUSDT."
        )

    if not normalised.isalpha():
        raise ValueError(
            f"Symbol '{normalised}' contains invalid characters. "
            "Only letters are allowed (e.g. BTCUSDT)."
        )

    logger.debug("Symbol validated: %s", normalised)
    return normalised


def validate_side(side: str) -> str:
    """
    Validate trading side.

    Args:
        side: 'BUY' or 'SELL' (case-insensitive).

    Returns:
        Upper-cased side string.

    Raises:
        ValueError: If side is not BUY or SELL.
    """
    if not side or not side.strip():
        raise ValueError("Side cannot be empty. Use BUY or SELL.")

    normalised = side.strip().upper()

    if normalised not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{normalised}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )

    logger.debug("Side validated: %s", normalised)
    return normalised


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: 'MARKET' or 'LIMIT' (case-insensitive).

    Returns:
        Upper-cased order type string.

    Raises:
        ValueError: If order type is not MARKET or LIMIT.
    """
    if not order_type or not order_type.strip():
        raise ValueError("Order type cannot be empty. Use MARKET or LIMIT.")

    normalised = order_type.strip().upper()

    if normalised not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{normalised}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )

    logger.debug("Order type validated: %s", normalised)
    return normalised


def validate_quantity(quantity: str | float) -> Decimal:
    """
    Validate and parse order quantity.

    Args:
        quantity: Numeric value (string or float) representing units to trade.

    Returns:
        Positive Decimal quantity.

    Raises:
        ValueError: If quantity is non-numeric, zero, or negative.
    """
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(
            f"Invalid quantity '{quantity}'. Must be a positive number (e.g. 0.001)."
        )

    if qty <= 0:
        raise ValueError(
            f"Quantity must be greater than zero. Got: {qty}"
        )

    logger.debug("Quantity validated: %s", qty)
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Validate price — required for LIMIT orders, must be absent for MARKET orders.

    Args:
        price:      Numeric value (or None) for the order price.
        order_type: Already-validated order type ('MARKET' or 'LIMIT').

    Returns:
        Positive Decimal price for LIMIT orders, None for MARKET orders.

    Raises:
        ValueError: If price is missing for LIMIT or invalid.
    """
    if order_type == "MARKET":
        if price is not None:
            logger.debug(
                "Price %s supplied for MARKET order — will be ignored.", price
            )
        return None

    # LIMIT path
    if price is None or str(price).strip() == "":
        raise ValueError("Price is required for LIMIT orders.")

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValueError(
            f"Invalid price '{price}'. Must be a positive number (e.g. 30000.50)."
        )

    if p <= 0:
        raise ValueError(f"Price must be greater than zero. Got: {p}")

    logger.debug("Price validated: %s", p)
    return p


# ── Aggregate validator ───────────────────────────────────────────────────────

def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
) -> dict:
    """
    Run all individual validators and return a clean, typed parameter dict.

    Args:
        symbol:     Trading pair symbol (e.g. 'BTCUSDT').
        side:       'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity:   Units to trade.
        price:      Limit price (required for LIMIT orders).

    Returns:
        Dict with keys: symbol, side, order_type, quantity, price.

    Raises:
        ValueError: Raised by any failing individual validator.
    """
    validated_type = validate_order_type(order_type)

    return {
        "symbol":     validate_symbol(symbol),
        "side":       validate_side(side),
        "order_type": validated_type,
        "quantity":   validate_quantity(quantity),
        "price":      validate_price(price, validated_type),
    }
