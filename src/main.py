import asyncio
import json
import os
import sys
from arb import Arbitragoor

from solana.keypair import Keypair
from solana.rpc.commitment import Processed, Confirmed, Finalized
from solana.rpc.types import TxOpts
from zo import Zo

from ftx_house import FtxClearingHouse
from zo_house import ZoClearingHouse


async def main():
    priv_key = json.loads(os.environ["PRIVATE_KEY"])
    key = Keypair.from_secret_key(bytes(priv_key))

    zo_client = await Zo.new(
        cluster=os.environ["CLUSTER"],
        payer=key,
        url=os.environ["RPC_URL"],
        tx_opts=TxOpts(
            max_retries=None,
            preflight_commitment=Processed,
            skip_confirmation=False,
            skip_preflight=False,
        ),
    )

    zo_house = ZoClearingHouse(zo_client)

    ftx_house = FtxClearingHouse(
        os.environ["API_KEY"], os.environ["API_SECRET"], os.environ["SUBACCOUNT"]
    )

    arber = Arbitragoor(
        zo_house,
        ftx_house,
        os.environ["MARKET"],
        os.environ["MIN_PROFIT"],
        os.environ["ORDER_SIZE"],
        os.environ["MAX_NOTIONAL"],
    )

    await arber.run()


if __name__ == "__main__":
    asyncio.run(main())
