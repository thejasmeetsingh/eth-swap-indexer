import logging
from decimal import Decimal
import traceback

import requests
from web3 import Web3, HTTPProvider
from django.core.cache import caches
from django.db import DatabaseError, transaction
from pydantic import ValidationError

from eth_swap_indexer.celery import app
from app.models import Config, SwapEvent
from app.schemas import SwapEvent as SwapEventSchema

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
CACHE_TIMEOUT = 3600

def get_eth_to_usd_rate() -> float:
    response = requests.get(url="https://api.coinbase.com/v2/exchange-rates?currency=ETH").json()
    rate = response.get("data", {}).get("rates", {}).get("USD", 0)
    return rate


def get_conversion_rate() -> Decimal:
    # Retrived cached conversion rate
    cached_conversion_rate = caches.get("conversion_rate")
    if cached_conversion_rate:
        return cached_conversion_rate

    # Fetch ETH to USD conversion from Coinbase
    conversion_rate = get_eth_to_usd_rate()

    # Convert conversion rate into decimal, For consitency
    conversion_rate = Decimal(conversion_rate)

    # Save conversion rate in cache
    caches.set("conversion_rate", conversion_rate, CACHE_TIMEOUT)

    return conversion_rate


def to_eth_wei(amount: Decimal) -> Decimal:
    wei = Decimal(1e18)
    return amount / wei


def get_transaction_details(_w3: Web3, _tx_hash: str) -> dict:
    try:
        # Fetch transaction details
        tx_data = _w3.eth.get_transaction(_tx_hash)

        execution_price_hex = tx_data.input.hex()[10+64:10+64+64]
        execution_price = Decimal(int(execution_price_hex, 16))
        swapped_amount = Decimal(tx_data.value)
        tx_cost = Decimal(tx_data.gas * tx_data.gasPrice)

        return {
            "gas_used": tx_data.gas,
            "gas_price": tx_data.gasPrice,
            "execution_price_eth": to_eth_wei(execution_price),
            "swapped_eth_cost": to_eth_wei(swapped_amount),
            "tx_eth_cost": to_eth_wei(tx_cost)
        }

    except Exception as e:
        logging.error({
            "msg": "Error caugh while fetching transaction details",
            "error": e,
            "traceback": traceback.format_exc(),
            "tx_hash": _tx_hash,
        })
        return {}


@app.task
def create_swap_event(config_id: str) -> None:
    config = Config.objects.get(id=config_id)

    # Initialize web3 object
    w3 = Web3(provider=HTTPProvider(endpoint_uri=config.http_provider))
    contract = w3.eth.contract(address=config.contract_address, abi=config.abi.get("ABI"))

    # Calculate the block number from where to pull the swap events
    curr_block_number = w3.eth.block_number
    from_block = curr_block_number - config.block_number

    swap_events = contract.events.Swap.get_logs(fromBlock=from_block)

    logger.info({
        "msg": f"Found {len(swap_events)} Swap Events",
        "from_block_number": from_block,
        "to_block_number": curr_block_number
    })

    swap_event_objs = []

    # Iterate and create the swap events in chunks
    for swap_event in swap_events:
        event_data = swap_event.args.__dict__
        tx_hash = swap_event.transactionHash.hex()
        tx_index = swap_event.transactionIndex
        block_number = swap_event.block_number

        tx_data = get_transaction_details(w3, tx_hash)
        if not tx_data:
            logger.error({"msg": "No transaction data found", "config": config.__dict__})
            continue

        # Get ETH to USD converions rate
        usd_exchange_rate = get_conversion_rate()

        # Validate data format using pydantic schema
        try:
            swap_event_obj = SwapEventSchema(
                block_number=block_number,
                event=event_data,
                tx_hash=tx_hash,
                tx_index=tx_index,
                gas_used=tx_data["gas_used"],
                gas_price=tx_data["gas_price"],
                usd_exchange_rate=usd_exchange_rate,
                execution_price_eth=tx_data["execution_price_eth"],
                execution_price_usd=tx_data["execution_price_eth"] * usd_exchange_rate,
                tx_eth_cost=tx_data["tx_eth_cost"],
                tx_usd_cost=tx_data["tx_eth_cost"] * usd_exchange_rate,
                swapped_eth_cost=tx_data["swapped_eth_cost"],
                swapped_usd_cost=tx_data["swapped_eth_cost"] * usd_exchange_rate
            )
        except ValidationError as e:
            logger.error({
                "msg": "Error while validating swap event data",
                "error": e.errors()
            })
            continue

        swap_event_objs.append(SwapEvent(config=config, **swap_event_obj.model_dump()))

        # Check swap event container length and bulk insert the records in DB to save DB calls
        if len(swap_event_objs) % CHUNK_SIZE:
            try:
                with transaction.atomic():
                    SwapEvent.objects.bulk_create(swap_event_objs)
            except DatabaseError as e:
                logger.error({
                    "msg": "Error while creating swap event record in DB",
                    "error": e
                })
            swap_event_objs.clear()
