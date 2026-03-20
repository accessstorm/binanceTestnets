"""
cli.py
------
Command-line interface entry point for the Binance Futures Testnet Trading Bot.

Usage examples:
  # Interactive mode (prompts for all fields)
  python -m bot.cli place-order

  # Market buy
  python -m bot.cli place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit sell
  python -m bot.cli place-order --symbol ETHUSDT --side SELL --type LIMIT \
      --quantity 0.01 --price 2500.00
"""

from __future__ import annotations
from typing import Optional
from decimal import Decimal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.prompt import Prompt, Confirm

from bot.client import get_client
from bot.validators import validate_order_inputs
from bot.orders import place_order
from bot.logging_config import logger
from binance.exceptions import BinanceAPIException, BinanceRequestException


app     = Console()
err_con = Console(stderr=True)
cli     = typer.Typer(
    name="trading-bot",
    help="[bold cyan]Binance USDT-M Futures Testnet[/bold cyan] — Simplified Trading Bot",
    rich_markup_mode="rich",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=True,
)


@cli.callback()
def _root_callback() -> None:
    """Binance USDT-M Futures Testnet — Simplified Trading Bot."""
    pass


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prompt_if_missing(value: Optional[str], prompt_text: str, choices: list[str] | None = None) -> str:
    """Return value if provided, otherwise interactively prompt the user."""
    if value:
        return value
    if choices:
        choices_str = "/".join(choices)
        return Prompt.ask(f"[bold yellow]{prompt_text}[/bold yellow] [dim]({choices_str})[/dim]")
    return Prompt.ask(f"[bold yellow]{prompt_text}[/bold yellow]")


def _render_request_summary(params: dict) -> None:
    """Print a formatted table summarising the order request parameters."""
    table = Table(
        title="[bold]Order Request Summary[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
    )
    table.add_column("Field",  style="cyan",  no_wrap=True)
    table.add_column("Value",  style="white")

    table.add_row("Symbol",     str(params["symbol"]))
    table.add_row("Side",       str(params["side"]))
    table.add_row("Order Type", str(params["order_type"]))
    table.add_row("Quantity",   str(params["quantity"]))

    price_display = str(params["price"]) if params["price"] else "[dim]N/A (MARKET)[/dim]"
    table.add_row("Price",      price_display)

    app.print(table)


def _render_order_response(response: dict) -> None:
    """Print a formatted panel with key order response fields."""
    order_id    = str(response.get("orderId",     "N/A"))
    status      = str(response.get("status",      "N/A"))
    exec_qty    = str(response.get("executedQty", "0"))
    avg_price   = str(response.get("avgPrice",    "0"))
    symbol      = str(response.get("symbol",      "N/A"))
    side        = str(response.get("side",        "N/A"))
    order_type  = str(response.get("type",        "N/A"))
    client_id   = str(response.get("clientOrderId", "N/A"))

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Order ID",        order_id)
    table.add_row("Status",          f"[bold green]{status}[/bold green]")
    table.add_row("Symbol",          symbol)
    table.add_row("Side",            f"[{'green' if side == 'BUY' else 'red'}]{side}[/{'green' if side == 'BUY' else 'red'}]")
    table.add_row("Type",            order_type)
    table.add_row("Executed Qty",    exec_qty)
    table.add_row("Avg Fill Price",  avg_price if avg_price != "0" else "[dim]pending[/dim]")
    table.add_row("Client Order ID", client_id)

    app.print(
        Panel(
            table,
            title="[bold green]✓  Order Response[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


# ── Commands ──────────────────────────────────────────────────────────────────

@cli.command(name="place-order")
def place_order_cmd(
    symbol: Optional[str] = typer.Option(
        None, "--symbol", "-s",
        help="Trading pair, e.g. BTCUSDT",
        show_default=False,
    ),
    side: Optional[str] = typer.Option(
        None, "--side",
        help="BUY or SELL",
        show_default=False,
    ),
    order_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="MARKET or LIMIT",
        show_default=False,
    ),
    quantity: Optional[float] = typer.Option(
        None, "--quantity", "-q",
        help="Quantity to trade (e.g. 0.001)",
        show_default=False,
    ),
    price: Optional[float] = typer.Option(
        None, "--price", "-p",
        help="Limit price (required for LIMIT orders)",
        show_default=False,
    ),
) -> None:
    """
    Place a [bold]MARKET[/bold] or [bold]LIMIT[/bold] order on the
    [cyan]Binance USDT-M Futures Testnet[/cyan].

    If any parameter is omitted you will be prompted for it interactively.
    """

    app.rule("[bold cyan]Binance Futures Testnet — Trading Bot[/bold cyan]")
    app.print()

    # ── Interactive prompts for missing values ────────────────────────────────
    symbol_val     = _prompt_if_missing(symbol,     "Symbol     (e.g. BTCUSDT)")
    side_val       = _prompt_if_missing(side,       "Side", choices=["BUY", "SELL"])
    order_type_val = _prompt_if_missing(order_type, "Order type", choices=["MARKET", "LIMIT"])

    quantity_val: Optional[float]
    if quantity is None:
        raw_qty = Prompt.ask("[bold yellow]Quantity[/bold yellow] [dim](e.g. 0.001)[/dim]")
        try:
            quantity_val = float(raw_qty)
        except ValueError:
            err_con.print(f"[bold red]✗ Invalid quantity:[/bold red] '{raw_qty}'")
            raise typer.Exit(code=1)
    else:
        quantity_val = quantity

    price_val: Optional[float] = price
    if order_type_val.strip().upper() == "LIMIT" and price is None:
        raw_price = Prompt.ask("[bold yellow]Limit price[/bold yellow] [dim](e.g. 30000.50)[/dim]")
        try:
            price_val = float(raw_price)
        except ValueError:
            err_con.print(f"[bold red]✗ Invalid price:[/bold red] '{raw_price}'")
            raise typer.Exit(code=1)

    # ── Validation ────────────────────────────────────────────────────────────
    try:
        params = validate_order_inputs(
            symbol     = symbol_val,
            side       = side_val,
            order_type = order_type_val,
            quantity   = quantity_val,
            price      = price_val,
        )
    except ValueError as exc:
        app.print()
        err_con.print(
            Panel(
                f"[bold]{exc}[/bold]",
                title="[bold red]✗  Validation Error[/bold red]",
                border_style="red",
            )
        )
        logger.warning("Validation failed: %s", exc)
        raise typer.Exit(code=1)

    # ── Show request summary and confirm ──────────────────────────────────────
    app.print()
    _render_request_summary(params)
    app.print()

    confirmed = Confirm.ask(
        "[bold]Confirm order placement on testnet?[/bold]",
        default=True,
    )
    if not confirmed:
        app.print("[yellow]Order cancelled by user.[/yellow]")
        raise typer.Exit(code=0)

    # ── Place order ───────────────────────────────────────────────────────────
    app.print()
    with app.status("[bold cyan]Connecting to Binance Testnet…[/bold cyan]"):
        try:
            client   = get_client()
            response = place_order(
                client     = client,
                symbol     = params["symbol"],
                side       = params["side"],
                order_type = params["order_type"],
                quantity   = params["quantity"],
                price      = params["price"],
            )
        except EnvironmentError as exc:
            err_con.print(
                Panel(
                    str(exc),
                    title="[bold red]✗  Configuration Error[/bold red]",
                    border_style="red",
                )
            )
            logger.error("Configuration error: %s", exc)
            raise typer.Exit(code=1)
        except BinanceAPIException as exc:
            err_con.print(
                Panel(
                    f"[bold]Code:[/bold] {exc.code}\n[bold]Message:[/bold] {exc.message}",
                    title="[bold red]✗  Binance API Error[/bold red]",
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)
        except BinanceRequestException as exc:
            err_con.print(
                Panel(
                    str(exc),
                    title="[bold red]✗  Network Error[/bold red]",
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)
        except Exception as exc:
            err_con.print(
                Panel(
                    str(exc),
                    title="[bold red]✗  Unexpected Error[/bold red]",
                    border_style="red",
                )
            )
            logger.exception("Unexpected error: %s", exc)
            raise typer.Exit(code=1)

    # ── Print order response ──────────────────────────────────────────────────
    _render_order_response(response)
    app.print(
        f"\n[bold green]✓  Order placed successfully on the Binance Futures Testnet![/bold green]\n"
        f"[dim]Full response written to bot.log[/dim]\n"
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
