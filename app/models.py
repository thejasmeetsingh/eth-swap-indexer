import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, db_index=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Config(BaseModel):
    contract_address = models.CharField(max_length=255)
    abi = models.JSONField(default=dict, help_text="<b>Contract ABI in JSON</b>")
    http_provider = models.URLField()
    block_number = models.PositiveBigIntegerField(default=0, help_text="<b>Block number from where you want to fetch back the swap events. For e.g: If you enter 2000 then swap events will be fetched from -> current block number - 2000</b>")

    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = ("config",)

    def __str__(self):
        return self.contract_address


class SwapEvent(BaseModel):
    config = models.ForeignKey(Config, on_delete=models.CASCADE, related_name="config_swap_events")
    block_number = models.PositiveBigIntegerField()
    event = models.JSONField(default=dict)

    # Transaction Details
    tx_hash = models.CharField(max_length=255, verbose_name="Transaction Hash")
    tx_index = models.PositiveBigIntegerField(verbose_name="Transaction Index")
    gas_used = models.PositiveBigIntegerField()
    gas_price = models.PositiveBigIntegerField()
    execution_price = models.DecimalField(max_digits=50, decimal_places=20)

    # Store ETH to USD exchange rate at the time of creating a swap event.
    # This will be used to convert all ETH cost to USD
    usd_exchange_rate = models.DecimalField(max_digits=7, decimal_places=2)

    tx_eth_cost = models.DecimalField(max_digits=50, decimal_places=20, verbose_name="Transaction ETH Cost")  # Transaction ETH cost is: (gas_used * gas_price) / 1e18
    tx_usd_cost = models.DecimalField(max_digits=50, decimal_places=20, verbose_name="Transaction USD Cost")

    swapped_eth_cost = models.DecimalField(max_digits=50, decimal_places=20)
    swapped_usd_cost = models.DecimalField(max_digits=50, decimal_places=20)

    class Meta:
        ordering = ('block_number',)

    def __str__(self):
        return self.block_number
