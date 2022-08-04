import asyncio
import json
import os
from dotenv import load_dotenv

from solana.keypair import Keypair
from solana.rpc.commitment import Confirmed, Finalized, Processed
from solana.rpc.types import TxOpts
from zo import Zo

from src import Arbitragoor
from src import FtxClearingHouse
from src import ZoClearingHouse


async def main():
    load_dotenv()

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

    await zo_house.init_data()

    ftx_house = FtxClearingHouse(
        os.environ["API_KEY"], os.environ["API_SECRET"], os.environ["SUBACCOUNT"]
    )

    arber = Arbitragoor(
        zo_house,
        ftx_house,
        os.environ["MARKET"],
        float(os.environ["MIN_PROFIT"]),
        float(os.environ["ORDER_SIZE"]),
        float(os.environ["MAX_NOTIONAL"]),
    )

    await arber.run()


if __name__ == "__main__":
    asyncio.run(main())
