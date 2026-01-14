"""
📧 EMAIL UTILITIES FOR AUTHENTICATION
Handles sending emails for signup, password reset, email verification, etc.
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

try:
    from celery import shared_task
except ImportError:
    # Fallback if Celery is not installed
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class AuthEmailService:
    """Service for sending authentication-related emails"""

    @staticmethod
    def send_welcome_email(user):
        """
        📧 Send welcome email to new user after signup
        
        WHY: Welcome users, confirm their account
        WHEN: After successful registration
        HOW: Async task via Celery for non-blocking operation
        """
        try:
            subject = f"🎬 Welcome to MovieBooking, {user.first_name or user.username}!"
            
            site_url = settings.SITE_URL or 'http://localhost:8000'
            context = {
                'user': user,
                'username': user.first_name or user.username,
                'signup_date': user.date_joined,
                'site_url': site_url,
            }
            
            # Render HTML and text versions
            html_message = render_to_string('auth/welcome_email.html', context)
            text_message = render_to_string('auth/welcome_email.txt', context)
            
            # Create email with both versions
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            
            result = email.send(fail_silently=False)
            
            logger.info(f"✅ Welcome email sent to {user.email} | Result: {result}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send welcome email to {user.email}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_password_reset_email(user):
        """
        🔑 Send password reset email with secure token
        
        WHY: Allow users to securely reset forgotten passwords
        WHEN: User clicks "Forgot Password"
        HOW: Generate token, create reset link, send async
        """
        try:
            # Generate secure token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            site_url = settings.SITE_URL or 'http://localhost:8000'
            reset_link = f"{site_url}/accounts/reset/{uid}/{token}/"
            
            subject = "🔐 Reset Your MovieBooking Password"
            
            context = {
                'user': user,
                'reset_link': reset_link,
                'username': user.first_name or user.username,
                'expiry_hours': 24,  # Token expires in 24 hours
                'site_url': site_url,
            }
            
            # Render HTML and text versions
            html_message = render_to_string('auth/password_reset_email.html', context)
            text_message = render_to_string('auth/password_reset_email.txt', context)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            
            result = email.send(fail_silently=False)
            
            logger.info(f"✅ Password reset email sent to {user.email} | Result: {result}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send password reset email to {user.email}: {str(e)}", exc_info=True)
            return False
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            
            email.send(fail_silently=False)
            
            logger.info(f"✅ Password reset email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send password reset email to {user.email}: {str(e)}")
            return False

    @staticmethod
    def send_email_verification_email(user):
        """
        ✉️ Send email verification OTP (6-digit code, expires in 5 minutes)
        
        WHY: Confirm user's email address is valid
        WHEN: After signup
        HOW: Generate OTP, send via email
        """
        try:
            # Generate OTP and save to user profile
            from accounts.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            otp = profile.generate_otp()
            
            subject = "✉️ Your Email Verification OTP - MovieBooking"
            
            context = {
                'user': user,
                'otp': otp,
                'username': user.first_name or user.username,
                'expiry_minutes': 5,
                'site_url': settings.SITE_URL or 'http://localhost:8000',
            }
            
            # Simple text email with OTP
            message = f"""
Hello {user.first_name or user.username},

Welcome to MovieBooking! 🎬

Please verify your email address using the OTP below:

    {otp}

This OTP will expire in 5 minutes.

If you didn't create an account, please ignore this email.

Happy watching!
MovieBooking Team
            """
            
            # Send the email
            result = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"✅ Email verification OTP sent to {user.email} | OTP: {otp} | Result: {result}")
            print("\n" + "="*60)
            print("📧 OTP VERIFICATION EMAIL SENT")
            print("="*60)
            print(f"   Email: {user.email}")
            print(f"   OTP: {otp}")
            print(f"   Expires in: 5 minutes")
            print("="*60 + "\n")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email verification OTP to {user.email}: {str(e)}", exc_info=True)
            print(f"\n⚠️ EMAIL FAILED: {str(e)}\n")
            return False

    @staticmethod
    def send_password_changed_email(user):
        """
        ✅ Send confirmation email after password change
        
        WHY: Notify user of security change
        WHEN: User successfully changes password
        HOW: Simple confirmation email
        """
        try:
            subject = "🔒 Your Password Has Been Changed - MovieBooking"
            
            site_url = settings.SITE_URL or 'http://localhost:8000'
            context = {
                'user': user,
                'username': user.first_name or user.username,
                'changed_at': timezone.now(),
                'site_url': site_url,
            }
            
            # Render HTML and text versions
            html_message = render_to_string('auth/password_changed_email.html', context)
            text_message = render_to_string('auth/password_changed_email.txt', context)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            
            result = email.send(fail_silently=False)
            
            logger.info(f"✅ Password changed confirmation sent to {user.email} | Result: {result}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send password changed email to {user.email}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_account_deactivation_email(user):
        """
        🚫 Send account deactivation confirmation email
        
        WHY: Notify user account has been deactivated
        WHEN: User deactivates their account
        HOW: Confirmation email with reactivation info
        """
        try:
            site_url = settings.SITE_URL or 'http://localhost:8000'
            subject = "📵 Your Account Has Been Deactivated - MovieBooking"
            
            context = {
                'user': user,
                'username': user.first_name or user.username,
                'reactivate_link': f"{site_url}/accounts/reactivate/",
                'site_url': site_url,
            }
            
            # Render HTML and text versions
            html_message = render_to_string('auth/account_deactivation.html', context)
            text_message = render_to_string('auth/account_deactivation.txt', context)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            
            result = email.send(fail_silently=False)
            
            logger.info(f"✅ Account deactivation email sent to {user.email} | Result: {result}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send account deactivation email to {user.email}: {str(e)}", exc_info=True)
            return False


# ========== ASYNC CELERY TASKS ==========
# These tasks run in background to avoid blocking the request

@shared_task(bind=True, max_retries=3)
def send_welcome_email_task(self, user_id):
    """Async task to send welcome email"""
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        AuthEmailService.send_welcome_email(user)
    except Exception as exc:
        logger.error(f"❌ Error sending welcome email for user {user_id}: {str(exc)}")
        # Retry up to 3 times with exponential backoff
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email_task(self, user_id):
    """Async task to send password reset email"""
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        AuthEmailService.send_password_reset_email(user)
    except Exception as exc:
        logger.error(f"❌ Error sending password reset email for user {user_id}: {str(exc)}")
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_email_verification_task(self, user_id):
    """Async task to send email verification"""
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        AuthEmailService.send_email_verification_email(user)
    except Exception as exc:
        logger.error(f"❌ Error sending email verification for user {user_id}: {str(exc)}")
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_password_changed_email_task(self, user_id):
    """Async task to send password changed confirmation"""
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        AuthEmailService.send_password_changed_email(user)
    except Exception as exc:
        logger.error(f"❌ Error sending password changed email for user {user_id}: {str(exc)}")
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_account_deactivation_email_task(self, user_id):
    """Async task to send account deactivation confirmation"""
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        AuthEmailService.send_account_deactivation_email(user)
    except Exception as exc:
        logger.error(f"❌ Error sending account deactivation email for user {user_id}: {str(exc)}")
        self.retry(exc=exc, countdown=60)
