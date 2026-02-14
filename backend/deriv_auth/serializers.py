from rest_framework import serializers

from .models import DerivAccount


class DerivAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = DerivAccount
        fields = [
            "id",
            "deriv_login_id",
            "account_type",
            "currency",
            "is_active",
            "is_default",
            "created_at",
        ]
        # NEVER include encrypted_token in serialized output
