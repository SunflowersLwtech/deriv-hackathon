from django.contrib import admin

from .models import DerivAccount


@admin.register(DerivAccount)
class DerivAccountAdmin(admin.ModelAdmin):
    list_display = ["deriv_login_id", "account_type", "currency", "is_active", "is_default", "user", "created_at"]
    list_filter = ["account_type", "is_active", "is_default"]
    search_fields = ["deriv_login_id", "user__email"]
    readonly_fields = ["id", "encrypted_token", "created_at", "updated_at"]
