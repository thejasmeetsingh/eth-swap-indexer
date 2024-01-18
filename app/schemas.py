from decimal import Decimal
from pydantic import BaseModel, Field


class SwapEvent(BaseModel):
    block_number: int
    log_index: int
    event: dict

    tx_hash: str
    tx_index: int
    gas_used: int
    gas_price: int

    usd_exchange_rate: Decimal = Field(max_digits=7, decimal_places=2)

    execution_price_eth: Decimal = Field(max_digits=200, decimal_places=50)
    execution_price_usd: Decimal = Field(max_digits=200, decimal_places=50)

    tx_eth_cost: Decimal = Field(max_digits=200, decimal_places=50)
    tx_usd_cost: Decimal = Field(max_digits=200, decimal_places=50)

    swapped_eth_cost: Decimal = Field(max_digits=200, decimal_places=50)
    swapped_usd_cost: Decimal = Field(max_digits=200, decimal_places=50)
