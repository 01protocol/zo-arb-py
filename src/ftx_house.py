import ftx
import numpy as np

from trading_types import *


class FtxClearingHouse:
    __client: ftx.FtxClient
    positions: dict[str, Position] = {}
    market_symbols: list[str] = []
    markets: dict[str, MarketInfo] = {}
    marks: dict[str, float] = {}
    indices: dict[str, float] = {}
    orderbooks: dict[str, Orderbook] = {}
    FEE: float = 0.0007

    def __init__(self, api_key, api_secret, subaccount) -> None:
        self.__client = ftx.FtxClient(
            api_key=api_key, api_secret=api_secret, subaccount_name=subaccount
        )

        self.fetch_market_symbols()
        self.fetch_markets()
        self.start_value = self.fetch_account_value()

    async def refresh(self) -> None:
        pass

    async def fetch_all(self, markets: (list[str] | None) = None) -> None:
        self.fetch_positions()
        self.fetch_indices()
        self.fetch_orderbooks(markets)
        self.fetch_account_value()

    def fetch_market_symbols(self) -> list[str]:
        """Fetch all the available markets that can be traded on."""
        if self.market_symbols:
            return self.market_symbols

        for market in self.__client.get_futures():
            if "-PERP" in market["name"]:
                self.market_symbols.append(market["name"])

        return self.market_symbols

    def fetch_markets(self) -> dict[str, MarketInfo]:
        """Fetch and interpret all the markets and their properties."""
        if self.markets:
            return self.markets

        for market in self.__client.get_futures():
            if not market["name"] in self.fetch_market_symbols():
                continue

            price_increment = float(market["priceIncrement"])
            size_increment = float(market["sizeIncrement"])

            if not (market["ask"] == None or market["bid"] == None):
                self.marks[market["name"]] = (market["ask"] + market["bid"]) / 2

            self.markets[market["name"]] = MarketInfo(price_increment, size_increment)

        return self.markets

    def fetch_positions(self) -> dict[str, Position]:
        """Fetch and interpret the current active positions (not open orders)."""
        account = self.__client.get_account_info()

        self.account_value = account["totalAccountValue"]

        self.total_notional = account["totalPositionSize"]
        for position in account["positions"]:
            if (
                not "future" in position.keys()
                and not position["future"] in self.fetch_market_symbols()
            ):
                continue

            if position["netSize"] == 0.0:
                new_position = Position()
            else:
                new_position = Position(position["netSize"], position["entryPrice"])

            self.positions[position["future"]] = new_position

        return self.positions

    def fetch_account_value(self) -> float:
        return self.__client.get_account_info()["totalAccountValue"]

    def fetch_indices(self) -> dict[str, float]:
        """Fetch the index price for all markets."""
        for market in self.__client.get_futures():
            if not market["name"] in self.fetch_market_symbols():
                continue

            self.indices[market["name"]] = float(market["index"])

        return self.indices

    def fetch_orderbooks(self, markets=None) -> dict[str, Orderbook]:
        """Fetch the orderbook for all markets."""

        if markets is None:
            markets = self.market_symbols

        for market in markets:
            book = self.__client.get_orderbook(market, depth=100)

            self.orderbooks[market] = Orderbook(
                np.array(book["asks"]), np.array(book["bids"])
            )

            self.marks[market] = (
                self.orderbooks[market].asks[0, 0] + self.orderbooks[market].bids[0, 0]
            ) / 2

        return self.orderbooks

    async def place_order(self, order: Order) -> bool:
        """Place a limit order on the book."""
        if order.side == "long":
            side = "buy"
        else:
            side = "sell"

        return self.__client.place_order(
            order.symbol,
            side,
            order.price,
            order.size,
            ioc=False,
            client_id=order.client_id,
        )

    async def cancel_order(self, order: Order) -> bool:
        """Cancel an open order on the book."""
        return self.__client.cancel_order(str(order.client_id))["success"]

    async def close_position(self, market: str) -> bool:
        """Cancel all active positions for a specific market.
        Please fetch positions and indices before calling this method.
        """
        position = self.fetch_positions()[market]

        if position.net_size < 0:
            side = "buy"
        else:
            side = "sell"

        return self.__client.place_order(
            market,
            side,
            self.indices[market],
            abs(position.net_size),
            ioc=True,
            reduce_only=True,
            client_id=order.client_id,
        )["success"]

    def get_pnl(self) -> float:
        return self.fetch_account_value() - self.start_value

    def can_open_position(self, market: str, max_notional: float) -> tuple[bool, bool]:

        if self.positions[market].net_size > 0:
            can_open_short = True
            can_open_long = self.total_notional < max_notional
        else:
            can_open_long = True
            can_open_short = self.total_notional < max_notional

        return can_open_long, can_open_short
