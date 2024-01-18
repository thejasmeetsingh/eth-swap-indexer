from ast import mod
import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, db_index=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Config(BaseModel):
    contract_address = models.CharField(max_length=255, unique=True)
    abi = models.JSONField(default=dict, verbose_name="ABI", help_text="<b>Add ABI JSON</b>")
    http_provider = models.URLField()
    block_number = models.PositiveBigIntegerField(default=0, help_text="<b>Block number from where you want to fetch back the swap events.<br>For e.g: If you enter 2000 then swap events will be fetched from -> current block number - 2000</b>")

    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "config"

    def __str__(self):
        return self.contract_address


class SwapEvent(BaseModel):
    config = models.ForeignKey(Config, on_delete=models.CASCADE, related_name="config_swap_events")
    block_number = models.PositiveBigIntegerField()
    event = models.JSONField(default=dict)
    log_index = models.PositiveBigIntegerField()

    # Transaction Details
    tx_hash = models.CharField(max_length=255, unique=True, verbose_name="Transaction Hash")
    tx_index = models.PositiveBigIntegerField(verbose_name="Transaction Index")
    gas_used = models.PositiveBigIntegerField()
    gas_price = models.PositiveBigIntegerField()

    # Store ETH to USD exchange rate at the time of creating a swap event.
    # This will be used to convert all ETH cost to USD
    usd_exchange_rate = models.DecimalField(max_digits=7, decimal_places=2)

    execution_price_eth = models.DecimalField(max_digits=200, decimal_places=50)
    execution_price_usd = models.DecimalField(max_digits=200, decimal_places=50)

    tx_eth_cost = models.DecimalField(max_digits=200, decimal_places=50, verbose_name="Transaction ETH Cost")  # Transaction ETH cost is: (gas_used * gas_price) / 1e18
    tx_usd_cost = models.DecimalField(max_digits=200, decimal_places=50, verbose_name="Transaction USD Cost")

    swapped_eth_cost = models.DecimalField(max_digits=200, decimal_places=50)
    swapped_usd_cost = models.DecimalField(max_digits=200, decimal_places=50)

    class Meta:
        ordering = ('block_number',)

        # This will ensure that we don't save duplicate transactions
        constraints = [
            models.UniqueConstraint(name="unique_tx_event", fields=("tx_hash", "log_index"))
        ]

    def __str__(self):
        return str(self.block_number)
