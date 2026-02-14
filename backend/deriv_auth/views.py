import logging

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .encryption import encrypt_token
from .models import DerivAccount
from .serializers import DerivAccountSerializer

logger = logging.getLogger(__name__)


def _get_user_profile(request):
    """Extract the UserProfile from the authenticated request."""
    user = request.user
    if hasattr(user, "profile"):
        return user.profile
    # SupabaseUser stores profile directly
    if hasattr(user, "id"):
        from behavior.models import UserProfile

        try:
            return UserProfile.objects.get(id=user.id)
        except UserProfile.DoesNotExist:
            return None
    return None


def _classify_account(login_id: str) -> str:
    """Determine account type from Deriv login ID prefix."""
    prefix = login_id.upper()
    if prefix.startswith("CR") or prefix.startswith("MF"):
        return "real"
    return "demo"


class OAuthCallbackView(APIView):
    """Receives parsed OAuth tokens from frontend callback page."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = _get_user_profile(request)
        if not profile:
            return Response(
                {"detail": "User profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        accounts_data = request.data.get("accounts", [])
        if not accounts_data:
            return Response(
                {"detail": "No accounts provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        saved_accounts = []
        with transaction.atomic():
            for acct in accounts_data:
                login_id = acct.get("login_id", "").strip()
                token = acct.get("token", "").strip()
                currency = acct.get("currency", "USD").strip().upper()

                if not login_id or not token:
                    continue

                account_type = _classify_account(login_id)
                encrypted = encrypt_token(token)

                obj, _created = DerivAccount.objects.update_or_create(
                    user=profile,
                    deriv_login_id=login_id,
                    defaults={
                        "account_type": account_type,
                        "currency": currency,
                        "encrypted_token": encrypted,
                        "is_active": True,
                    },
                )
                saved_accounts.append(obj)

            # Set default: prefer first real account, else first demo
            if saved_accounts:
                # Clear existing defaults for this user
                DerivAccount.objects.filter(user=profile).update(is_default=False)

                real_accounts = [a for a in saved_accounts if a.account_type == "real"]
                default_account = real_accounts[0] if real_accounts else saved_accounts[0]
                default_account.is_default = True
                default_account.save(update_fields=["is_default"])

        all_accounts = DerivAccount.objects.filter(user=profile, is_active=True)
        serializer = DerivAccountSerializer(all_accounts, many=True)
        return Response({"accounts": serializer.data}, status=status.HTTP_200_OK)


class DerivAccountListView(APIView):
    """List user's connected Deriv accounts."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = _get_user_profile(request)
        if not profile:
            return Response(
                {"detail": "User profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        accounts = DerivAccount.objects.filter(user=profile, is_active=True)
        serializer = DerivAccountSerializer(accounts, many=True)
        return Response({"accounts": serializer.data})


class DerivAccountDeleteView(APIView):
    """Disconnect a specific Deriv account."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        profile = _get_user_profile(request)
        if not profile:
            return Response(
                {"detail": "User profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            account = DerivAccount.objects.get(id=pk, user=profile)
        except DerivAccount.DoesNotExist:
            return Response(
                {"detail": "Account not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        account.is_active = False
        account.is_default = False
        account.save(update_fields=["is_active", "is_default"])

        # If this was the default, set a new default
        remaining = DerivAccount.objects.filter(user=profile, is_active=True)
        if remaining.exists() and not remaining.filter(is_default=True).exists():
            new_default = remaining.first()
            new_default.is_default = True
            new_default.save(update_fields=["is_default"])

        return Response({"detail": "Account disconnected."}, status=status.HTTP_200_OK)


class SetDefaultAccountView(APIView):
    """Set which account is the user's default."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = _get_user_profile(request)
        if not profile:
            return Response(
                {"detail": "User profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            account = DerivAccount.objects.get(id=pk, user=profile, is_active=True)
        except DerivAccount.DoesNotExist:
            return Response(
                {"detail": "Account not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            DerivAccount.objects.filter(user=profile).update(is_default=False)
            account.is_default = True
            account.save(update_fields=["is_default"])

        serializer = DerivAccountSerializer(account)
        return Response(serializer.data)


class DerivConnectionStatusView(APIView):
    """Quick check if user has any connected Deriv accounts."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = _get_user_profile(request)
        if not profile:
            return Response({"connected": False, "account_count": 0})

        accounts = DerivAccount.objects.filter(user=profile, is_active=True)
        default = accounts.filter(is_default=True).first()
        return Response({
            "connected": accounts.exists(),
            "account_count": accounts.count(),
            "default_account": DerivAccountSerializer(default).data if default else None,
        })
