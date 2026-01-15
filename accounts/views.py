"""
🔐 AUTHENTICATION VIEWS FOR MOVIEBOOKING
Handles user registration, login, logout, email verification, and password management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .forms import CustomUserCreationForm
from .models import UserProfile
from .email_utils import AuthEmailService
import json
import logging

logger = logging.getLogger(__name__)

def register(request):
    """
    🔐 User Registration with Email Verification
    
    PROCESS:
    1. User fills registration form
    2. Create user account (inactive)
    3. Generate OTP and send to email
    4. Redirect to OTP verification page
    5. Enhanced feedback and loading states
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Create user but don't activate yet
                user = form.save(commit=False)
                user.is_active = False  # Account inactive until email verified
                user.email = form.cleaned_data.get('email')
                user.save()
                
                # Create or get user profile
                profile, created = UserProfile.objects.get_or_create(user=user)
                logger.info(f"User registration started for: {user.email}")
                
                # Generate OTP and send email
                otp = profile.generate_otp()
                
                # Send verification email (async task)
                try:
                    email_sent = AuthEmailService.send_email_verification_email(user)
                    if email_sent:
                        messages.success(request, 
                            f'🎉 Account created successfully! A 6-digit verification code has been sent to {user.email}. Please check your inbox (and spam folder) and enter the code on the next page.')
                        logger.info(f"Verification email sent to: {user.email}")
                    else:
                        messages.warning(request, 
                            '⚠️ Account created, but we had trouble sending the verification email. You can try resending it on the next page.')
                        logger.warning(f"Failed to send verification email to: {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send verification email to {user.email}: {e}")
                    messages.warning(request, 
                        '⚠️ Account created, but we had trouble sending the verification email. You can try resending it on the next page.')
                
                # Store user ID in session for OTP verification
                request.session['pending_user_id'] = user.id
                return redirect('verify_otp')
                
            except Exception as e:
                logger.error(f"Registration error for {form.cleaned_data.get('email', 'unknown')}: {e}")
                messages.error(request, 
                    '❌ Registration failed due to a system error. Please try again or contact support if the problem persists.')
        else:
            # Enhanced form error messages
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        error_messages.append(f"❌ {error}")
                    else:
                        field_name = field.replace('_', ' ').title()
                        error_messages.append(f"❌ {field_name}: {error}")
            
            if error_messages:
                for msg in error_messages:
                    messages.error(request, msg)
            else:
                messages.error(request, '❌ Please correct the errors in the form and try again.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    """
    🔐 Custom Login View
    
    Handles user authentication with email and password:
    - Uses email instead of username for login
    - Email verification status check
    - Account activation status
    - Enhanced feedback and loading states
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'registration/login.html')
        
        # Use custom authentication backend that supports email
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Check if user account is active
            if not user.is_active:
                messages.error(request, 
                    'Your account is not activated. Please check your email for the activation link.')
                return render(request, 'registration/login.html')
            
            # Check if user has verified email
            try:
                profile = user.profile
                if not profile.is_email_verified:
                    messages.warning(request, 
                        '📧 Please verify your email address before logging in. Check your inbox for the verification code.')
                    request.session['pending_user_id'] = user.id
                    return redirect('verify_otp')
            except UserProfile.DoesNotExist:
                # Create profile if doesn't exist (for existing users)
                UserProfile.objects.create(user=user, is_email_verified=True)
                logger.info(f"Created profile for existing user: {user.username}")
            
            # Successful login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            welcome_name = user.first_name or user.username
            messages.success(request, 
                f'🎉 Welcome back, {welcome_name}! You have been logged in successfully.')
            
            # Redirect to next page or home
            next_page = request.GET.get('next', 'home')
            logger.info(f"User {user.username} logged in successfully")
            return redirect(next_page)
        else:
            messages.error(request, 
                '❌ Invalid email or password. Please check your credentials and try again.')
    
    return render(request, 'registration/login.html')

def logout_view(request):
    """
    🔐 Logout View
    """
    username = request.user.username if request.user.is_authenticated else "User"
    logout(request)
    messages.success(request, f'Goodbye {username}! You have been logged out successfully.')
    return redirect('home')

def verify_otp(request):
    """
    📧 Email Verification with OTP
    
    PROCESS:
    1. User enters 6-digit OTP
    2. Validate OTP and expiry
    3. Activate user account
    4. Auto-login user
    """
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, 'No pending verification found.')
        return redirect('register')
    
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, 'Invalid verification session.')
        return redirect('register')
    
    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()
        
        if profile.is_otp_valid(otp):
            # Verify user
            profile.is_email_verified = True
            profile.email_verified_at = timezone.now()
            profile.email_otp = None  # Clear OTP
            profile.save()
            
            # Activate user
            user.is_active = True
            user.save()
            
            # Clear session
            del request.session['pending_user_id']
            
            # Auto-login with backend specified (required when multiple backends are configured)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            # Send welcome email
            try:
                AuthEmailService.send_welcome_email(user)
            except Exception as e:
                logger.error(f"Failed to send welcome email: {e}")
            
            messages.success(request, 
                f'🎉 Email verified successfully! Welcome to MovieBooking, {user.username}!')
            return redirect('verification_success')
        else:
            messages.error(request, 'Invalid or expired OTP. Please try again.')
            
            # Check if too many attempts
            if profile.otp_attempts >= 3:
                messages.error(request, 
                    'Too many failed attempts. Please request a new verification code.')
                return redirect('resend_verification')
    
    context = {
        'user': user,
        'otp_attempts': profile.otp_attempts,
    }
    return render(request, 'accounts/verify_otp.html', context)

def verification_pending(request):
    """📧 Show verification pending page"""
    return render(request, 'accounts/verification_pending.html')

def verification_success(request):
    """✅ Show verification success page"""
    return render(request, 'accounts/verification_success.html')

def resend_verification_email(request):
    """
    📧 Resend Verification Email
    """
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, 'No pending verification found.')
        return redirect('register')
    
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        # Generate new OTP
        otp = profile.generate_otp()
        
        # Send email
        email_sent = AuthEmailService.send_email_verification_email(user)
        if email_sent:
            messages.success(request, 
                f'📧 New verification code sent to {user.email}. Please check your inbox and enter the 6-digit code.')
        else:
            messages.error(request, 'Failed to send verification email. Please try again.')
        
    except Exception as e:
        logger.error(f"Failed to resend verification email: {e}")
        messages.error(request, 'Failed to send verification email. Please try again.')
    
    return redirect('verify_otp')

def forgot_password(request):
    """
    🔒 Forgot Password - Send Reset Email
    Enhanced with better feedback and loading states
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, '❌ Please enter your email address.')
            return render(request, 'accounts/forgot_password.html')
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Send password reset email (generates token internally)
            email_sent = AuthEmailService.send_password_reset_email(user)
            
            if email_sent:
                messages.success(request, 
                    f'🔐 Password reset instructions have been sent to {email}. Please check your inbox (and spam folder) and follow the link to reset your password. The link will expire in 24 hours.')
                logger.info(f"Password reset email sent to: {email}")
            else:
                messages.error(request, 
                    '❌ Failed to send password reset email. Please try again or contact support if the problem persists.')
                logger.error(f"Failed to send password reset email to: {email}")
                
            return redirect('login')
            
        except User.DoesNotExist:
            # Don't reveal whether email exists or not for security
            messages.success(request, 
                f'🔐 If an account with {email} exists, password reset instructions have been sent. Please check your inbox. If you don\'t receive an email, the address may not be registered.')
            logger.info(f"Password reset attempted for non-existent email: {email}")
            return redirect('login')
        except Exception as e:
            logger.error(f"Password reset error for {email}: {e}")
            messages.error(request, 
                '❌ Failed to send password reset email due to a system error. Please try again.')
    
    return render(request, 'accounts/forgot_password.html')

def reset_password(request, uidb64, token):
    """
    🔒 Password Reset with Token Validation
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')  # Changed from new_password1
            password2 = request.POST.get('password2')  # Changed from new_password2
            
            if password1 and password2:
                if password1 == password2:
                    user.set_password(password1)
                    user.save()
                    
                    # Send password changed confirmation email
                    try:
                        AuthEmailService.send_password_changed_email(user)
                    except Exception as e:
                        logger.error(f"Failed to send password changed email: {e}")
                    
                    messages.success(request, 
                        '🔒 Password reset successfully! You can now log in with your new password.')
                    return redirect('login')
                else:
                    messages.error(request, 'Passwords do not match.')
            else:
                messages.error(request, 'Please fill in both password fields.')
        
        return render(request, 'accounts/reset_password.html', {'validlink': True})
    else:
        messages.error(request, 'Password reset link is invalid or has expired.')
        return render(request, 'accounts/reset_password.html', {'validlink': False})

@login_required
def profile(request):
    """
    👤 User Profile View
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user, is_email_verified=True)
    
    context = {
        'user': request.user,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def change_password(request):
    """
    🔒 Change Password View
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})
