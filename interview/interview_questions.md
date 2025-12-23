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

## Models & Databases (Movies App)

22. **What is a `SlugField` and why do we use `slugify` in the `save()` method?**

    - **Answer:** A `SlugField` stores a URL-friendly version of a string (e.g., "The Dark Knight" -> "the-dark-knight"). We override the `save()` method to automatically generate this slug from the `title` or `name` field using Django's `slugify` utility. This ensures every object has a valid URL identifier without manual input.

23. **Explain `ManyToManyField` vs `ForeignKey`. Why do we use M2M for Genres but ForeignKey for Language?**

    - **Answer:**
      - **ForeignKey (One-to-Many):** Used when an object belongs to primarily _one_ other entity. A movie typically has _one_ primary language, so we use `ForeignKey`.
      - **ManyToManyField (Many-to-Many):** Used when an object can belong to multiple categories, and those categories can contain multiple objects. A movie can be both "Action" and "Thriller", and the "Action" genre contains many movies. Thus, `ManyToManyField` is correct for genres.

24. **What does `on_delete=models.SET_NULL` do?**

    - **Answer:** It defines what happens when the referenced object (e.g., a Language) is deleted. `SET_NULL` keeps the Movie record but sets its `language` field to `NULL`. This is safer than `CASCADE` (which would delete the movie) because we don't want to wipe out our movie database just because we removed a language from the system.

25. **Why do we need `Pillow` for `ImageField`?**

    - **Answer:** `ImageField` in Django is a wrapper around `FileField` that adds validation to ensure the uploaded file is a valid image. It relies on the **Pillow** library (Python Imaging Library fork) to open, verify, and process image files. Without Pillow installed, `ImageField` will throw an error.

26. **What is the purpose of `related_name` in model relationships?**
    - **Answer:** `related_name` allows you to define the name of the reverse relation from the related object back to this one. For example, `language = ForeignKey(Language, related_name='movies')` allows us to access `english_language_obj.movies.all()` to get all movies in English. If not set, Django defaults to `movie_set`.

## Theater & Booking Logic (Advanced Models)

27. **Why do we define `verbose_name_plural` in the `City` model's Meta class?**

    - **Answer:** Django automatically pluralizes model names by adding an "s" (e.g., "Movie" -> "Movies"). For words like "City", the default would contain a spelling error ("Citys"). Setting `verbose_name_plural = 'cities'` tells Django explicitly what the correct plural form is for the Admin panel.

28. **Explain the implication of `on_delete=models.CASCADE` in the `Showtime` model.**

    - **Answer:** It maintains data integrity. Since a `Showtime` cannot strictly exist without a `Movie` or a `Screen`, `CASCADE` ensures that if a Movie is deleted from the database, all its scheduled showtimes are automatically deleted too. This prevents "orphan" records.

29. **Why use `DecimalField` for `price` instead of `FloatField`?**

    - **Answer:** `FloatField` uses binary floating-point representation which can introduce tiny precision errors (e.g., `0.1 + 0.2` might equal `0.30000000000000004`). In financial calculations, even small errors are unacceptable. `DecimalField` stores numbers as Python `Decimal` objects, guaranteeing exact precision for currency.

30. **(Scenario) Two users try to book the last seat at the exact same millisecond. How do you prevent double-booking?**

    - **Answer:** This is a classic concurrency race condition. You cannot just read `available_seats`, check if `> 0`, and then decrement.
    - **Solution:** Use **Database Transactions** with **Row Locking**.

    ```python
    from django.db import transaction

    with transaction.atomic():
        # select_for_update() locks this specific row until the transaction finishes
        show = Showtime.objects.select_for_update().get(id=show_id)
        if show.available_seats > 0:
            show.available_seats -= 1
            show.save()
            # ... process booking ...
        else:
            raise Exception("Housefull!")
    ```

## Views & Query Logic

31. **What is the difference between `filter()` and `get()` in Django ORM?**

    - **Answer:**
      - `filter(**kwargs)`: Returns a **QuerySet** (a list of objects). returns an empty list `[]` if no matches found. Used when you expect multiple or zero items.
      - `get(**kwargs)`: Returns a **single object** instance. Raises `DoesNotExist` error if 0 items found, and `MultipleObjectsReturned` error if >1 items found. Used when you need exactly one item (like a specific movie profile).

32. **Why do we use `get_object_or_404()` instead of just `Movie.objects.get()`?**

    - **Answer:** If `Movie.objects.get()` fails to find an object, it raises a `DoesNotExist` exception, which causes a "500 Internal Server Error" (a crash). `get_object_or_404()` catches this and handles it gracefully by returning a standard "404 Not Found" response, which is the correct HTTP behavior for missing pages.

33. **What are `Q` objects used for?**

    - **Answer:** By default, chaining arguments in `.filter(name="A", age=20)` works like an **AND** operator (name is A AND age is 20). `Q` objects allow complex lookups like **OR** logic.

    ```python
    from django.db.models import Q
    # Find movies with title "Love" OR description containing "Romance"
    Movie.objects.filter(Q(title="Love") | Q(description__icontains="Romance"))
    ```

34. **What is the `context` dictionary in a View function?**
    - **Answer:** It's the mechanism to pass data from Python (the backend) to HTML (the frontend). The keys in the dictionary become the variable names available in the Django Template. For example, `context = {'user_name': 'Alice'}` allows you to use `{{ user_name }}` in the HTML file.

## System Design & Bookings

35. **The "Double Booking" Problem (Race Condition):**

    - **Scenario:** Two users try to book Seat A1 at the exact same millisecond. Both see it as "Available".
    - **Question:** How do you prevent both from booking it?
    - **Answer:**
      1. **Database Transactions:** Use `transaction.atomic()` and `select_for_update()` to lock the row in the DB until the booking is done.
      2. **Optimistic Locking:** Add a `version` field. If the version changes before you save, fail the request.
      3. **Redis Locks (Our Approach):** Use an in-memory lock (Redis) to "hold" the seat for 10 minutes while payment is pending. If User A holds the lock, User B instantly sees "Unavailable".

36. **Why use `JSONField` for storing seats `['A1', 'B2']` instead of a separate Table?**

    - **Answer:**
      - **Pros:** Faster reads (no complex JOINs needed to get just seat numbers), simpler schema for non-queryable data.
      - **Cons:** Harder to query (e.g. "Find all bookings with seat A1" is slow in SQL).
      - **Verdict:** For a booking history where we just need to _show_ the seats (read-only), JSON is perfect. For checking availability, we use a more robust system (Redis/Showtime model).

37. **Why do we calculate Price/Tax on the Backend vs Frontend?**

    - **Answer:** **Security.** Never trust data sent from the client. A malicious user could use Postman/Curl to send `{"total_amount": 1.00}` for a 500 rupee ticket. Always recalculate the final price on the server before talking to the Payment Gateway.

38. **Source of Truth: Is seat info stored in Redis or the Database?**
    - **Answer:** Both, but for different purposes:
      - **Redis (Transient State):** Stores the "Live Status". It's the source of truth for **Availability** and **Temporary Locks**. If Redis clears, we just re-generate the map from the DB.
      - **Database (Persistent Records):** Stores the "Final Truth". It's the source of truth for **Successful Bookings**. You cannot "lose" a ticket if Redis crashes because it's safely in the SQL Database.

## Booking Workflow & Security

39. **What is the lifecycle of a `Booking` status?**

    - **Answer:**
      - **PENDING**: Record created, waiting for payment. Seats are "Temporarily Locked" in Redis.
      - **CONFIRMED**: Payment successful. Record updated. Seats marked "Booked" permanently.
      - **EXPIRED**: User didn't pay in time (e.g., 10 mins). Record updated, seats released for others.
      - **FAILED**: Payment failed. Seats released.

40. **Why do we use `@login_required` on almost every booking view?**

    - **Answer:**
      - **Identity**: We need to know _who_ is buying the ticket to link the `user_id` to the `Booking` record.
      - **Security**: Prevents bots or unauthenticated users from bulk-locking seats in Redis and "denying service" to real customers.

41. **How do we prevent a user from booking seats they never actually selected?**
    - **Answer:** **Double Verification.**
      1. When seats are selected, we store them in the user's **Session** (server-side).
      2. In the `create_booking` view, we check if the requested `seat_ids` match what is in the session _and_ what is currently locked in Redis. We never trust the IDs sent directly from the browser without checking our own server records first.

---

_Feel free to ask for deeper explanations on any of these topics!_
