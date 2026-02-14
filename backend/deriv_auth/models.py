import uuid

from django.db import models

from behavior.models import UserProfile


class DerivAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="deriv_accounts",
        db_column="user_id",
    )
    deriv_login_id = models.CharField(max_length=50)  # e.g. "CR123456" or "VRTC789"
    account_type = models.CharField(
        max_length=10, choices=[("real", "Real"), ("demo", "Demo")]
    )
    currency = models.CharField(max_length=10)  # e.g. "USD"
    encrypted_token = models.TextField()  # Fernet encrypted Deriv API token
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)  # User's preferred account
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "deriv_accounts"
        unique_together = [("user", "deriv_login_id")]
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.deriv_login_id} ({self.account_type}) - {self.user.email}"

    @property
    def token(self):
        from .encryption import decrypt_token

        return decrypt_token(self.encrypted_token)

    @token.setter
    def token(self, value):
        from .encryption import encrypt_token

        self.encrypted_token = encrypt_token(value)
