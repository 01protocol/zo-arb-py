from dataclasses import dataclass
from typing import Annotated, Literal

from numpy.typing import NDArray


@dataclass
class Position:
    """Class for storing position information."""

    net_size: float = 0.0
    entry_price: float = 0.0


@dataclass
class MarketInfo:
    """Class for storing market information."""

    price_increment: float = 0.0
    size_increment: float = 0.0


@dataclass
class Orderbook:
    """Class for storing orderbook infermation.
    Store [price, size]
    """

    asks: Annotated[NDArray[float], Literal["N", 2]]
    bids: Annotated[NDArray[float], Literal["N", 2]]


@dataclass
class Order:
    """Class for storing order information."""

    size: float
    price: float
    side: Literal["long", "short"]
    symbol: str
    client_id: int
