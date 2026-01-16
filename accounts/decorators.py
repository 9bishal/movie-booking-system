"""
Custom decorators for user authentication and verification.
"""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def email_verified_required(view_func):
    """
    Decorator to ensure user has verified their email before accessing a view.
    
    Usage:
        @email_verified_required
        def my_view(request):
            ...
    
    If user is not verified, redirects to OTP verification page with a message.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            messages.error(request, '⚠️ Please complete your profile setup.')
            return redirect('verify_otp')
        
        # Check if email is verified
        if not request.user.profile.is_email_verified:
            messages.warning(
                request,
                '📧 Please verify your email address to access this feature. '
                'Check your inbox for the verification code.'
            )
            return redirect('verify_otp')
        
        # User is verified, proceed to view
        return view_func(request, *args, **kwargs)
    
    return wrapper
