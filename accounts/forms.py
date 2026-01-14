from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with email field and no username restrictions"""
    
    # Override username field to remove all validators and restrictions
    username = forms.CharField(
        max_length=150,
        required=True,
        help_text='',
        error_messages={
            'required': 'Please enter a username.',
            'max_length': 'Username is too long.',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        
        # Completely remove all username validators including Django's default ones
        self.fields['username'].validators = []
        # Remove help text for all fields
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
    
    def clean_username(self):
        """No restrictions on username - allow any characters and duplicates"""
        username = self.cleaned_data.get('username', '').strip()
        
        # Check if username is empty
        if not username:
            raise forms.ValidationError('Please enter a username.')
        
        # No uniqueness check - allow duplicate usernames
        return username
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email', '').strip()
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        
        return email
    
    def _post_clean(self):
        """Override to skip Django's model field validation for username"""
        # Store the username before calling parent's _post_clean
        username_from_clean = self.cleaned_data.get('username')
        
        super()._post_clean()
        
        # Restore username to cleaned_data if it was removed
        if username_from_clean and 'username' not in self.cleaned_data:
            self.cleaned_data['username'] = username_from_clean
        
        # Remove Django's character validation errors for username
        if 'username' in self._errors:
            username_errors = self._errors['username']
            error_list = list(username_errors)
            
            # Filter out Django's "Enter a valid username" error
            filtered_errors = []
            for error in error_list:
                error_str = str(error)
                # Skip Django's character restriction error message
                if 'letters, numbers, and' not in error_str and 'Enter a valid username' not in error_str:
                    filtered_errors.append(error)
            
            # Update or remove errors
            if filtered_errors:
                self._errors['username'] = self.error_class(filtered_errors)
            else:
                del self._errors['username']
    
    def save(self, commit=True):
        """Save the user with the provided username and email"""
        # Use UserCreationForm's save to handle password hashing properly
        user = super().save(commit=False)
        
        # Ensure email is set
        user.email = self.cleaned_data.get('email', '')
        
        if commit:
            user.save()
        
        return user
