from django.urls import path
from .views import LoginView,PasswordResetRequestView, RegisterView, SetPasswordView, VerifyEmail

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<str:uid>/<str:token>/', VerifyEmail.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('reset-password/<str:uid>/<str:token>/', SetPasswordView.as_view(), name='password_reset_confirm'),
]