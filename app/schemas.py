from decimal import Decimal
from pydantic import BaseModel, Field


class SwapEvent(BaseModel):
    block_number: int
    event: dict

    tx_hash: str
    tx_index: str
    gas_used: int
    gas_price: int

    usd_exchange_rate: Decimal = Field(max_length=7, decimal_places=2)

    execution_price_eth: Decimal = Field(max_length=50, decimal_places=20)
    execution_price_usd: Decimal = Field(max_length=50, decimal_places=20)

    tx_eth_cost: Decimal = Field(max_length=50, decimal_places=20)
    tx_usd_cost: Decimal = Field(max_length=50, decimal_places=20)

    swapped_eth_cost: Decimal = Field(max_length=50, decimal_places=20)
    swapped_usd_cost: Decimal = Field(max_length=50, decimal_places=20)
