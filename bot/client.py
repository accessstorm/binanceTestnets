"""
client.py
---------
Thin wrapper around the python-binance Client, pre-configured to target
the Binance USDT-M Futures **Testnet** exclusively.

The testnet base URL is hard-coded here so that no production funds can
ever be accidentally touched.
"""

import os
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException

from bot.logging_config import logger


# Hard-coded testnet endpoint – NEVER change this to the live URL
FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


def _load_credentials() -> tuple[str, str]:
    """
    Load API key and secret from the .env file located in the project root.

    Returns:
        Tuple of (api_key, api_secret).

    Raises:
        EnvironmentError: If either credential is missing.
    """
    # Resolve .env relative to the project root (one level above bot/)
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("BINANCE_TESTNET_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET", "").strip()

    if not api_key or not api_secret:
        raise EnvironmentError(
            "API credentials not found. Please set BINANCE_TESTNET_API_KEY "
            "and BINANCE_TESTNET_API_SECRET in your .env file."
        )

    return api_key, api_secret


def get_client() -> Client:
    """
    Build and return an authenticated Binance Client pointed at the testnet.

    The client uses `testnet=True` in conjunction with the futures testnet
    base URL so that all futures endpoints resolve correctly.

    Returns:
        An authenticated binance.client.Client instance.

    Raises:
        EnvironmentError: Propagated from _load_credentials().
        BinanceAPIException: If the initial connection / key validation fails.
    """
    api_key, api_secret = _load_credentials()

    logger.info("Initialising Binance client → testnet: %s", FUTURES_TESTNET_BASE_URL)

    client = Client(
        api_key=api_key,
        api_secret=api_secret,
        testnet=True,
    )

    # Override the futures base URL to the testnet endpoint explicitly
    client.FUTURES_URL = FUTURES_TESTNET_BASE_URL + "/fapi"

    logger.info("Binance testnet client initialised successfully.")
    return client
