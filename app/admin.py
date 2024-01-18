from typing import Any
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.http.request import HttpRequest

from app.models import Config, SwapEvent
from app.tasks import process_swap_events

admin.site.site_header = 'ETH Swap Indexer'
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ("contract_address", "created_at")

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        super().save_model(request, obj, form, change)

        # Call the process_swap_events task (async way), Only when a config record is added.
        if not change:
            process_swap_events.apply_async(kwargs={"config_id": str(obj.id)})


@admin.register(SwapEvent)
class SwapEventAdmin(admin.ModelAdmin):
    list_display = (
        "tx_hash",
        "config",
        "block_number"
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
    
    def has_change_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        return False
    
    def has_delete_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        return False
