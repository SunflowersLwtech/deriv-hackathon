from django.urls import path

from . import views

urlpatterns = [
    path("callback/", views.OAuthCallbackView.as_view(), name="deriv-oauth-callback"),
    path("accounts/", views.DerivAccountListView.as_view(), name="deriv-accounts"),
    path("accounts/<uuid:pk>/", views.DerivAccountDeleteView.as_view(), name="deriv-account-delete"),
    path("accounts/<uuid:pk>/set-default/", views.SetDefaultAccountView.as_view(), name="deriv-set-default"),
    path("status/", views.DerivConnectionStatusView.as_view(), name="deriv-connection-status"),
]
