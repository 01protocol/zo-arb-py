import numpy as np
from solana.rpc.commitment import Processed
from zo import Zo

from .types import *


class ZoClearingHouse:
    __client: Zo
    positions: dict[str, Position] = {}
    market_symbols: list[str] = []
    markets: dict[str, MarketInfo] = {}
    indices: dict[str, float] = {}
    marks: dict[str, float] = {}
    orderbooks: dict[str, Orderbook] = {}
    FEE: float = 0.001

    def __init__(self, client) -> None:
        self.__client = client

        self.fetch_market_symbols()
        self.fetch_markets()

    async def init_data(self):
        await self.fetch_all()

        self.start_val = self.fetch_account_value()

    async def refresh(self) -> None:
        await self.__client.refresh(commitment=Processed)

    async def fetch_all(self) -> None:
        await self.__client.refresh()

        self.fetch_market_symbols()
        await self.fetch_orderbooks()
        self.fetch_markets()
        self.fetch_indices()
        self.fetch_positions()

    def fetch_market_symbols(self) -> list[str]:
        """Fetch all the available markets that can be traded on."""
        self.market_symbols = list(self.__client.markets.d.keys())

        return self.market_symbols

    def fetch_markets(self) -> dict[str, MarketInfo]:
        """Fetch and interpret all the markets and their properties."""
        if self.markets:
            return self.markets

        for market_symbol, market in self.__client.markets:

            price_lot_size = market.quote_lot_size / pow(10.0, market.quote_decimals)

            asset_lot_size = market.base_lot_size / pow(10.0, market.base_decimals)

            lot_price = price_lot_size / asset_lot_size

            self.markets[market_symbol] = MarketInfo(lot_price, asset_lot_size)

        return self.markets

    def fetch_positions(self) -> dict[str, Position]:
        """Fetch and interpret the current active positions (not open orders)."""
        self.total_notional = 0
        for symbol, position in self.__client.position:
            if symbol == "LUNA-PERP":
                continue

            size = position.size
            if position.side == "long":
                side = 1
            else:
                side = -1
            net_size = size * side

            if size != 0:
                entry_price = (position.value - position.realized_pnl) / size
            else:
                entry_price = 0

            self.total_notional += position.size * self.marks[symbol]

            self.positions[symbol] = Position(net_size, entry_price)

        return self.positions

    def fetch_indices(self) -> dict[str, float]:
        """Fetch the index price for all markets."""
        self.fetch_market_symbols()

        for market in self.market_symbols:
            self.indices[market] = self.__client.markets[market].index_price

        return self.indices

    async def fetch_orderbooks(self, markets=None) -> dict[str, Orderbook]:
        """Fetch the orderbook for all markets."""

        if markets is None:
            markets = self.market_symbols

        self.fetch_market_symbols()
        # TODO: Use the new sdk
        # await self.__client.refresh_orders()

        for market in self.market_symbols:
            refined_asks = []
            for ask in self.__client.orderbook[market].asks:
                refined_asks.append([ask.price, ask.size])

            refined_bids = []
            for bid in self.__client.orderbook[market].bids:
                refined_bids.append([bid.price, bid.size])

            self.orderbooks[market] = Orderbook(
                np.array(refined_asks), np.array(refined_bids)
            )

            self.marks[market] = (refined_asks[0][0] + refined_bids[0][0]) / 2

        return self.orderbooks

    async def place_order(self, order: Order) -> bool:
        """Place a limit order on the book."""
        if order.side == "long":
            side = "bid"
        elif order.side == "short":
            side = "ask"
        else:
            raise Exception("bruh")

        await self.__client.place_order(
            order.size,
            order.price,
            side,
            symbol=order.symbol,
            order_type="fok",
            limit=100,
            client_id=order.client_id,
        )

        return True

    async def cancel_order(self, order: Order) -> bool:
        """Cancel an open order on the book."""
        try:
            await self.__client.cancel_order_by_client_id(order.client_id, order.symbol)
        except Exception as e:
            print(e)  # TODO: Fix to proper logging
            return False

        return True

    async def close_position(self, market: str) -> bool:
        """Cancel all active positions for a specific market."""
        try:
            await self.__client.close_position(market)
        except Exception as e:
            print(e)
            return False

        return True

    def fetch_account_value(self):

        self.fetch_positions()
        val = self.__client.balance["USDC"]

        for market in self.positions:
            val += self.positions[market].net_size * (
                self.marks[market] - self.positions[market].entry_price
            )

        return val

    def get_pnl(self) -> float:
        return self.fetch_account_value() - self.start_val

    def can_open_position(self, market: str, max_notional: float) -> tuple[bool, bool]:

        if self.positions[market].net_size > 0:
            can_open_short = True
            can_open_long = self.total_notional < max_notional - 10
        else:
            can_open_long = True
            can_open_short = self.total_notional < max_notional - 10

        return can_open_long, can_open_short
