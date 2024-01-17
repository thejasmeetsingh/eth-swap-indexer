# Generated by Django 5.0.1 on 2024-01-17 16:58

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Config",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("contract_address", models.CharField(max_length=255)),
                (
                    "abi",
                    models.JSONField(
                        default=dict, help_text="<b>Contract ABI in JSON</b>"
                    ),
                ),
                ("http_provider", models.URLField()),
                (
                    "block_number",
                    models.PositiveBigIntegerField(
                        default=0,
                        help_text="<b>Block number from where you want to fetch back the swap events. For e.g: If you enter 2000 then swap events will be fetched from -> current block number - 2000</b>",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": ("config",),
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="SwapEvent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("block_number", models.PositiveBigIntegerField()),
                ("event", models.JSONField(default=dict)),
                (
                    "tx_hash",
                    models.CharField(max_length=255, verbose_name="Transaction Hash"),
                ),
                (
                    "tx_index",
                    models.PositiveBigIntegerField(verbose_name="Transaction Index"),
                ),
                ("gas_used", models.PositiveBigIntegerField()),
                ("gas_price", models.PositiveBigIntegerField()),
                (
                    "usd_exchange_rate",
                    models.DecimalField(decimal_places=2, max_digits=7),
                ),
                (
                    "execution_price_eth",
                    models.DecimalField(decimal_places=20, max_digits=50),
                ),
                (
                    "execution_price_usd",
                    models.DecimalField(decimal_places=20, max_digits=50),
                ),
                (
                    "tx_eth_cost",
                    models.DecimalField(
                        decimal_places=20,
                        max_digits=50,
                        verbose_name="Transaction ETH Cost",
                    ),
                ),
                (
                    "tx_usd_cost",
                    models.DecimalField(
                        decimal_places=20,
                        max_digits=50,
                        verbose_name="Transaction USD Cost",
                    ),
                ),
                (
                    "swapped_eth_cost",
                    models.DecimalField(decimal_places=20, max_digits=50),
                ),
                (
                    "swapped_usd_cost",
                    models.DecimalField(decimal_places=20, max_digits=50),
                ),
                (
                    "config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="config_swap_events",
                        to="app.config",
                    ),
                ),
            ],
            options={
                "ordering": ("block_number",),
            },
        ),
    ]
