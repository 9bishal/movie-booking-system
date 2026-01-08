# Views for the accounts app – handles registration, login, logout, and profile
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from utils.rate_limit import login_limiter
# ========== REGISTER VIEW ==========
from utils.rate_limit import RateLimiter

# Views for the accounts app – handles registration, login, logout, and profile
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from utils.rate_limit import login_limiter
from accounts.forms import CustomUserCreationForm
# ========== REGISTER VIEW ==========
from utils.rate_limit import RateLimiter

registration_limiter = RateLimiter(rate='3/h', key_prefix='register')

@registration_limiter.rate_limit_view
def register(request):
    """
    Handle user registration with email
    """
    # If already logged in, go to home
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in!')
        return redirect('home')
    
    if request.method == 'POST':
        # Get form data
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            # Save user
            user = form.save()
            
            # Send welcome email
            try:
                subject = '🎬 Welcome to MovieBooking!'
                message = f"""
Hello {user.username},

Welcome to MovieBooking! Your account has been created successfully.

Email: {user.email}
Username: {user.username}

You can now log in and start booking movie tickets!

Happy watching!
MovieBooking Team
                """
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
                print(f"\n✉️ Welcome email sent to {user.email}")
            except Exception as e:
                print(f"❌ Error sending email: {e}")
            
            # Print to console for testing
            print("\n" + "="*60)
            print("🎬 MOVIEBOOKING - NEW USER REGISTERED!")
            print("="*60)
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"User ID: {user.id}")
            print("="*60 + "\n")
            
            # Auto login after registration
            login(request, user)
            
            # Success message
            messages.success(request, f'🎉 Welcome {user.username}! Registration successful! Check your email for confirmation.')
            
            return redirect('home')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Empty form for GET request
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'title': 'Create Account',
        'page_title': 'Join MovieBooking',
        'page_subtitle': 'Create your account to book tickets',
    }
    return render(request, 'accounts/register.html', context)

# ========== LOGIN VIEW ==========
@login_limiter.rate_limit_view
def login_view(request):
    """
    Handle user login
    """
    # If already logged in, go to home
    if request.user.is_authenticated:
        messages.info(request, f'Welcome back, {request.user.username}!')
        return redirect('home')
    
    if request.method == 'POST':
        # Get username and password
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login successful
            login(request, user)
            
            # Send login notification email
            try:
                subject = f'🎬 Login Notification - MovieBooking'
                message = f"""
Hello {user.username},

You have successfully logged into your MovieBooking account.

If this wasn't you, please change your password immediately.

Account Email: {user.email}
Login Time: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Happy watching!
MovieBooking Team
                """
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"❌ Error sending login email: {e}")
            
            messages.success(request, f'🎬 Welcome back, {username}!')
            return redirect('home')
        else:
            # Login failed
            messages.error(request, '❌ Invalid username or password. Please try again.')
    
    context = {
        'title': 'Login',
        'page_title': 'Welcome Back',
        'page_subtitle': 'Login to your account',
    }
    return render(request, 'accounts/login.html', context)

# ========== LOGOUT VIEW ==========
def logout_view(request):
    """
    Handle user logout
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'👋 Goodbye {username}! You have been logged out.')
    else:
        messages.info(request, 'You were not logged in.')
    
    return redirect('login')

# ========== PROFILE VIEW ==========
@login_required
def profile(request):
    """
    Show user profile (protected - login required)
    """
    user = request.user
    
    # User info
    context = {
        'title': 'My Profile',
        'page_title': f'Hello, {user.username}!',
        'page_subtitle': 'Your MovieBooking Profile',
        'user': user,
        'username': user.username,
        'email': user.email if user.email else 'Not provided',
        'date_joined': user.date_joined.strftime('%B %d, %Y'),
        'last_login': user.last_login.strftime('%B %d, %Y %I:%M %p') if user.last_login else 'Never',
        'is_staff': 'Yes' if user.is_staff else 'No',
        'is_superuser': 'Yes' if user.is_superuser else 'No',
    }
    
    return render(request, 'accounts/profile.html', context)