import logging
from decimal import Decimal
from time import sleep
import traceback

import requests
from web3 import Web3, HTTPProvider
from django.core.cache import cache
from django.db import DatabaseError, transaction
from pydantic import ValidationError

from eth_swap_indexer.celery import app
from app.models import Config, SwapEvent
from app.schemas import SwapEvent as SwapEventSchema

logger = logging.getLogger(__name__)

CHUNK_SIZE = 50
CACHE_TIMEOUT = 3600

def get_eth_to_usd_rate() -> float:
    response = requests.get(url="https://api.coinbase.com/v2/exchange-rates?currency=ETH").json()
    rate = response.get("data", {}).get("rates", {}).get("USD", 0)
    return rate


def get_conversion_rate() -> Decimal:
    # Retrived cached conversion rate
    cached_conversion_rate = cache.get("conversion_rate")
    if cached_conversion_rate:
        return cached_conversion_rate

    # Fetch ETH to USD conversion from Coinbase
    conversion_rate = get_eth_to_usd_rate()

    # Convert conversion rate into decimal, For consitency
    conversion_rate = round(Decimal(conversion_rate), 2)

    # Save conversion rate in cache
    cache.set("conversion_rate", conversion_rate, CACHE_TIMEOUT)

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

def create_swap_event(_w3: Web3, _config_obj: Config, _swap_event) -> None:
    event_data = _swap_event.args.__dict__
    tx_hash = _swap_event.transactionHash.hex()
    tx_index = _swap_event.transactionIndex
    block_number = _swap_event.blockNumber
    log_index = _swap_event.logIndex

    # Check cache for transaction data
    cached_tx_data = cache.get(tx_hash)
    if cached_tx_data:
        tx_data = cached_tx_data
    else:
        # Fetch the transasction details from the provider
        tx_data = get_transaction_details(_w3, tx_hash)
        cache.set(tx_hash, tx_data, CACHE_TIMEOUT)

    if not tx_data:
        logger.error({"msg": "No transaction data found", "config_id": _config_obj.id})
        return

    # Get ETH to USD converions rate
    usd_exchange_rate = get_conversion_rate()

    # Validate data format using pydantic schema
    # Continue with other swap events if any validation error is caught
    try:
        swap_event_obj = SwapEventSchema(
            block_number=block_number,
            log_index=log_index,
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
        return

    # Insert the swap event record in DB
    try:
        with transaction.atomic():
            SwapEvent.objects.create(config=_config_obj, **swap_event_obj.model_dump())
    except DatabaseError as e:
        logger.error({
            "msg": "Error while creating swap event record in DB",
            "error": e
        })


@app.task
def process_swap_events(config_id: str) -> None:
    try:
        config = Config.objects.get(id=config_id)

        # Initialize web3 object
        w3 = Web3(provider=HTTPProvider(endpoint_uri=config.http_provider))
        contract = w3.eth.contract(address=config.contract_address, abi=config.abi.get("ABI"))

        # Calculate the block number from where to pull the swap events
        curr_block_number = w3.eth.block_number
        from_block = curr_block_number - config.block_number

        # Fetch swap events
        swap_events = contract.events.Swap.get_logs(fromBlock=from_block)

        logger.info({
            "msg": f"Found {len(swap_events)} Swap Events",
            "from_block_number": from_block,
            "to_block_number": curr_block_number
        })

        # Iterate and create the swap events
        for idx, swap_event in enumerate(swap_events):
            create_swap_event(w3, config, swap_event)

            # Once we reach the threshold chunk size, Pause the execution
            # So that we don't get the rate limit error from the HTTP Provider
            if idx % CHUNK_SIZE == 0:
                sleep(5)
                logger.info(f"{CHUNK_SIZE} swap events are processed successfully, Pausing the execution for 5 seconds!")

    except Exception as e:
        logger.error({
            "msg": "Error caught while processing swap events",
            "error": e,
            "traceback": traceback.format_exc()
        })
