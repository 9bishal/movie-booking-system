# URLs for the accounts app: registration, login, logout, and profile routes
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Email verification with OTP
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('verification-pending/', views.verification_pending, name='verification_pending'),
    path('verification-success/', views.verification_success, name='verification_success'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    
    # Password reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset/<uidb64>/<token>/', views.reset_password, name='reset_password'),
]