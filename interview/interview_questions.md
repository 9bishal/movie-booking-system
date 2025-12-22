# Interview Preparation – MovieBooking System

## Django & Authentication

1. **Explain the Django authentication workflow** – how `register`, `login`, `logout`, and `profile` views interact with the auth system.

   - **Answer:** Django provides a built‑in authentication system. The **register** view creates a new `User` object, hashes the password and saves it. After registration we usually log the user in with `login(request, user)`. The **login** view checks the submitted username/password against the database using `authenticate()`. If valid, `login()` creates a session cookie so the browser knows the user is authenticated. The **logout** view simply calls `logout(request)`, which clears the session. The **profile** view is protected with `@login_required`; it reads the current `request.user` (the logged‑in user) and displays their details.

2. **What is the purpose of `@login_required` and how is it used in the `profile` view?**

   - **Answer:** `@login_required` is a decorator that forces a view to be accessed only by authenticated users. If an anonymous visitor tries to open the view, Django redirects them to the URL defined by `LOGIN_URL` (usually the login page). In `profile`, we add `@login_required` above the function so only logged‑in users can see their personal information.

3. **How does Django store passwords securely? Mention the hashing algorithm.**

   - **Answer:** Django never stores plain‑text passwords. When a password is set, Django runs it through a **PBKDF2** hash (by default) with a random salt and stores the resulting string in the `password` field. The format looks like `pbkdf2_sha256$260000$<salt>$<hash>`. This makes it computationally expensive to crack.

4. **How would you add email verification to the registration flow?**

   - **Answer:** After creating the user, generate a signed token (e.g., using `itsdangerous` or Django's `PasswordResetTokenGenerator`). Send an email containing a link like `http://example.com/activate/<uid>/<token>/`. Create a view that validates the token, activates the user (`is_active = True`), and logs them in. Use Django's `EmailMessage` or the console backend during development.

5. **Describe how you would implement password reset functionality.**
   - **Answer:** Django already ships with a password‑reset system. You would:
   1. Add URLs for `PasswordResetView`, `PasswordResetConfirmView`, etc.
   2. Configure `EMAIL_BACKEND` (console for dev, SMTP for prod).
   3. Provide templates for the email and the reset forms.
   4. When a user submits their email, Django sends a link with a token; the user follows the link to set a new password.

## Project Structure & Apps

6. **Why did we separate the `accounts` app from the main project? What are the benefits of a modular app design?**

   - **Answer:** Splitting functionality into separate apps keeps code organized, reusable, and easier to test. The `accounts` app handles authentication only, while the main project can focus on other domains (movies, theaters, etc.). This modularity allows you to plug the app into another project or share it as a reusable package.

7. **How does Django discover templates in the `templates` directory? Explain the `DIRS` setting.**

   - **Answer:** In `settings.py`, the `TEMPLATES` configuration contains a `DIRS` list. By adding `BASE_DIR / "templates"` we tell Django to look for a top‑level `templates/` folder (outside any app). Django also automatically searches each app’s `templates/` subfolder when `APP_DIRS` is `True`. This lets us keep shared base templates in one place.

8. **What is the role of `BASE_DIR` and why do we use `pathlib.Path` for paths?**
   - **Answer:** `BASE_DIR` points to the project’s root directory. Using `pathlib.Path` gives us an object‑oriented way to build file system paths that work on Windows, macOS, and Linux without worrying about forward/backward slashes. For example, `BASE_DIR / "static"` creates a cross‑platform path to the `static` folder.

## URLs & Routing

9. **Explain the purpose of `include('accounts.urls')` in the project `urls.py`.**

   - **Answer:** `include()` tells Django to delegate any URL that starts with `accounts/` to the URL patterns defined in `accounts/urls.py`. This keeps the main `urls.py` tidy and lets each app manage its own routes.

10. **How would you add a namespace to the `accounts` URLs and why might that be useful?**
    - **Answer:** In `accounts/urls.py` add `app_name = 'accounts'` at the top and then use `path('accounts/', include('accounts.urls', namespace='accounts'))` in the project `urls.py`. Namespaces avoid name clashes when multiple apps have URL names like `login` or `register`. You can then reverse URLs with `reverse('accounts:login')`.

## Static & Media Files

11. **How are static files served during development vs production? Mention `STATIC_URL`, `STATIC_ROOT`, and `STATICFILES_DIRS`.**

    - **Answer:** During development, Django’s built‑in server serves static files automatically when `DEBUG=True`. `STATIC_URL` (e.g., `/static/`) is the URL prefix, `STATICFILES_DIRS` lists extra directories (like a global `static/` folder). For production, you run `python manage.py collectstatic` which copies all static files into `STATIC_ROOT`. A real web server (Nginx, Apache, or a CDN) then serves files from that directory.

12. **How would you configure media file handling for user‑uploaded content?**
    - **Answer:** Add `MEDIA_URL = '/media/'` and `MEDIA_ROOT = BASE_DIR / 'media'` in `settings.py`. In `urls.py` during development, append `+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` when `settings.DEBUG` is `True`. In production, configure the web server to serve files from `MEDIA_ROOT`.

## Settings & Environment

13. **What are the security considerations for `SECRET_KEY` and `DEBUG` in production?**

    - **Answer:** `SECRET_KEY` must never be exposed publicly; it signs cookies and tokens. In production, keep it secret (e.g., via environment variable). `DEBUG` must be set to `False` in production; otherwise detailed error pages can leak sensitive information and the static file handling changes.

14. **How can you use environment variables to keep sensitive settings out of source control?**
    - **Answer:** Store values like `SECRET_KEY`, database passwords, and email credentials in environment variables (e.g., using a `.env` file with `python-decouple` or `django-environ`). In `settings.py` read them with `os.getenv('SECRET_KEY')`. This way the actual secrets never appear in the repo.

## Testing & Deployment

15. **How would you write a unit test for the registration view?**

    - **Answer:** Use Django’s `TestCase`. Create a `client` POST request to `/accounts/register/` with a username and password. Assert that the response redirects (or renders success), that a `User` object now exists, and that the password is correctly hashed. Example:

    ```python
    class RegisterViewTests(TestCase):
        def test_register_creates_user(self):
            response = self.client.post('/accounts/register/', {
                'username': 'testuser',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
            })
            self.assertEqual(User.objects.count(), 1)
            user = User.objects.first()
            self.assertTrue(user.check_password('StrongPass123'))
    ```

16. **What steps are required to deploy this Django app to a cloud provider (e.g., Heroku, Render, or Docker)?**

    - **Answer:**

    1. Add a `Procfile` (e.g., `web: gunicorn moviebooking.wsgi`) for Heroku.
    2. Set `DEBUG=False` and configure allowed hosts.
    3. Use a production‑ready database (PostgreSQL) and configure `DATABASE_URL`.
    4. Collect static files (`python manage.py collectstatic`).
    5. Set environment variables for secret key, DB credentials, email, etc.
    6. Push code to the platform and run migrations.
    7. Optionally configure a CDN for static/media.

17. **Explain how you would set up a CI/CD pipeline for this project.**
    - **Answer:** Use GitHub Actions (or GitLab CI). Workflow steps:
    1. Checkout code.
    2. Set up Python, install dependencies (`pip install -r requirements.txt`).
    3. Run linting (`flake8`) and tests (`python manage.py test`).
    4. On merge to `main`, trigger a deployment step that pushes the new image to Docker Hub or runs `heroku container:push`.
    5. Use secret storage for environment variables.

## Performance & Scaling

18. **How can you improve the performance of static file delivery?**

    - **Answer:** Serve static files via a CDN or a dedicated web server (Nginx) with caching headers. Enable gzip compression, set far‑future `Cache‑Control` headers, and use `django-compressor` to minify CSS/JS.

19. **What caching strategies would you employ for a high‑traffic movie‑booking site?**
    - **Answer:**
    - **Database query caching** with Django’s `cache_page` decorator for views that don’t change often (e.g., movie listings).
    - **Template fragment caching** for parts of pages.
    - **Redis or Memcached** as the cache backend.
    - **Cache per‑user data** (like a user’s profile) with appropriate timeout.

## Extensibility

20. **If you were to add a `movies` app, what models and relationships would you define?**

    - **Answer:**

    ```python
    class Movie(models.Model):
        title = models.CharField(max_length=200)
        description = models.TextField()
        duration = models.PositiveIntegerField(help_text='Minutes')
        release_date = models.DateField()
        poster = models.ImageField(upload_to='posters/')

    class Theater(models.Model):
        name = models.CharField(max_length=100)
        location = models.CharField(max_length=200)

    class Show(models.Model):
        movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
        theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
        start_time = models.DateTimeField()
        available_seats = models.PositiveIntegerField()
    ```

    Relationships: `Show` links a `Movie` to a `Theater` at a specific time.

21. **How would you integrate a third‑party payment gateway for ticket purchases?**
    - **Answer:** Choose a provider (Stripe, PayPal). Install its SDK (`stripe`). Create a view that creates a payment intent on the server, returns a client secret to the frontend, and uses Stripe.js to collect card details securely. After successful payment, mark the ticket as paid and send a confirmation email.

---

_Feel free to ask for deeper explanations on any of these topics!_\_
