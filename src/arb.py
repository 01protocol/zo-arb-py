import asyncio
from typing import Literal

import numpy as np

from ftx_house import FtxClearingHouse
from zo_house import ZoClearingHouse
from .types import *


class Arbitragoor:
    zo_house: ZoClearingHouse
    ftx_house: FtxClearingHouse
    MIN_PROFIT: float
    ORDER_SIZE: float
    MAX_NOTIONAL: float
    MARKET: str

    def __init__(
        self, zo_house, ftx_house, market, min_profit, order_size, max_notional
    ):
        self.zo_house = zo_house
        self.ftx_house = ftx_house

        self.MIN_PROFIT = min_profit
        self.ORDER_SIZE = order_size
        self.MAX_NOTIONAL = max_notional
        self.MARKET = market

    async def arb(self):
        await self.ftx_house.fetch_all()
        await self.zo_house.fetch_all()

        zo_mark = self.zo_house.marks[self.MARKET]
        ftx_mark = self.ftx_house.marks[self.MARKET]

        zo_open_notional = self.zo_house.positions[self.MARKET].net_size * zo_mark
        ftx_open_notional = self.ftx_house.positions[self.MARKET].net_size * ftx_mark

        diff = zo_mark - ftx_mark
        if diff > self.MIN_PROFIT:
            print(
                f"{self.MARKET}: Short 01 at {zo_mark} and Long FTX at {ftx_mark} arb opportunity"
            )
            if zo_open_notional < -self.MAX_NOTIONAL:
                print(
                    f"Have {abs(zo_open_notional)} short open already on 01, not arbing."
                )

            order_size = min(self.ORDER_SIZE, self.MAX_NOTIONAL - abs(zo_open_notional))
            print(f"\t Arbing for {order_size} {self.MARKET}")

            try:
                zo_short = Order(
                    size=order_size,
                    side="short",
                    symbol=self.MARKET,
                    price=0.999 * zo_mark,
                    client_id=0,
                )
                await self.zo_house.place_order(zo_short)

                ftx_long = Order(
                    size=order_size,
                    side="long",
                    symbol=self.MARKET,
                    price=1.001 * ftx_mark,
                    client_id=0,
                )
                await self.ftx_house.place_order(ftx_long)
            except Exception as e:
                print(e)
        elif diff < -self.MIN_PROFIT:
            print(
                f"{self.MARKET}: Long 01 at {zo_mark} and Short FTX at {ftx_mark} arb opportunity"
            )
            if zo_open_notional < self.MAX_NOTIONAL:
                print(
                    f"Have {abs(zo_open_notional)} long open already on 01, not arbing."
                )

            order_size = min(self.ORDER_SIZE, self.MAX_NOTIONAL - abs(zo_open_notional))
            print(f"\t Arbing for {order_size} {self.MARKET}")

            try:
                zo_long = Order(
                    size=order_size,
                    side="long",
                    symbol=self.MARKET,
                    price=1.001 * zo_mark,
                    client_id=0,
                )
                await self.zo_house.place_order(zo_long)

                ftx_short = Order(
                    size=order_size,
                    side="short",
                    symbol=self.MARKET,
                    price=0.999 * ftx_mark,
                    client_id=0,
                )
                await self.ftx_house.place_order(ftx_short)
            except Exception as e:
                print(e)

    async def run(self):
        while True:
            await self.arb()
            await asyncio.sleep(1)
