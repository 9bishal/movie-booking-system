from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

class UserProfile(models.Model):
    """
    Extended user profile to track email verification status with OTP
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_email_verified = models.BooleanField(default=False, help_text="Whether user has verified their email")
    email_verified_at = models.DateTimeField(null=True, blank=True, help_text="When email was verified")
    
    # OTP fields for email verification
    email_otp = models.CharField(max_length=6, null=True, blank=True, help_text="6-digit OTP for email verification")
    otp_created_at = models.DateTimeField(null=True, blank=True, help_text="When OTP was generated")
    otp_attempts = models.IntegerField(default=0, help_text="Number of failed OTP verification attempts")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_userprofile'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def generate_otp(self):
        """Generate a 6-digit OTP and set expiry time"""
        self.email_otp = ''.join(random.choices(string.digits, k=6))
        self.otp_created_at = timezone.now()
        self.otp_attempts = 0
        self.save()
        return self.email_otp
    
    def is_otp_valid(self, otp):
        """Check if OTP is valid and not expired (5 minutes)"""
        if not self.email_otp or not self.otp_created_at:
            return False
        
        # Check if OTP matches
        if self.email_otp != otp:
            self.otp_attempts += 1
            self.save()
            return False
        
        # Check if OTP is expired (5 minutes = 300 seconds)
        time_elapsed = (timezone.now() - self.otp_created_at).total_seconds()
        if time_elapsed > 300:  # 5 minutes
            return False
        
        return True
    
    def mark_email_verified(self):
        """Mark email as verified and clear OTP"""
        self.is_email_verified = True
        self.email_verified_at = timezone.now()
        self.email_otp = None
        self.otp_created_at = None
        self.otp_attempts = 0
        self.save()
