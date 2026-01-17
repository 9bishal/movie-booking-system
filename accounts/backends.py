"""
Custom Authentication Backend for Email-based Login
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address
    instead of username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user using email address
        
        Args:
            request: HttpRequest object
            username: Can be either username or email
            password: User's password
            **kwargs: Additional keyword arguments
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if username is None:
            username = kwargs.get('email')
        
        if username is None or password is None:
            return None
        
        try:
            # Try to find user by email first, then by username
            # Use filter().first() to handle duplicate users gracefully
            user = User.objects.filter(
                Q(email__iexact=username) | Q(username__iexact=username)
            ).order_by('-date_joined').first()
            
            if user is None:
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a non-existing user
                User().set_password(password)
                return None
            
            # Check if password is correct
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
            
            return None
        except Exception:
            # Handle any unexpected errors
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
