# Views for the accounts app – handles registration, login, logout, and profile
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# ========== REGISTER VIEW ==========
def register(request):
    """
    Handle user registration
    Simple form with username, password1, password2
    """
    # If already logged in, go to profile
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in!')
        return redirect('profile')
    
    if request.method == 'POST':
        # Get form data
        form = UserCreationForm(request.POST)
        
        if form.is_valid():
            # Save user
            user = form.save()
            
            # SIMULATE EMAIL SENDING (print to console)
            print("\n" + "="*60)
            print("🎬 MOVIEBOOKING - NEW USER REGISTERED!")
            print("="*60)
            print(f"Username: {user.username}")
            print(f"User ID: {user.id}")
            print(f"Email verification needed for: {user.email if user.email else 'No email provided'}")
            print("Verification link: http://127.0.0.1:8000/accounts/verify/{token}/")
            print("="*60 + "\n")
            
            # Auto login after registration
            login(request, user)
            
            # Success message
            messages.success(request, f'🎉 Welcome {user.username}! Registration successful!')
            
            return redirect('profile')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Empty form for GET request
        form = UserCreationForm()
    
    context = {
        'form': form,
        'title': 'Create Account',
        'page_title': 'Join MovieBooking',
        'page_subtitle': 'Create your account to book tickets',
    }
    return render(request, 'accounts/register.html', context)

# ========== LOGIN VIEW ==========
def login_view(request):
    """
    Handle user login
    """
    # If already logged in, go to profile
    if request.user.is_authenticated:
        messages.info(request, f'Welcome back, {request.user.username}!')
        return redirect('profile')
    
    if request.method == 'POST':
        # Get username and password
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login successful
            login(request, user)
            messages.success(request, f'🎬 Welcome back, {username}!')
            return redirect('profile')
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