# Beginner Interview Questions – MovieBooking System

This guide is designed for developers just starting with Django, Celery, and Payment Gateways.

---

## 🏗️ Project Architecture & File Structure

### 1. Why do we create separate "apps" like `accounts`, `movies`, and `bookings`?

**Answer:** This is called **Modularity**.

- **WHY:** It makes the code easier to manage. If you have a bug in "login", you know exactly which folder to look in (`accounts`).
- **HOW:** Each app has its own `models.py` (data), `views.py` (logic), and `urls.py` (paths).

### 2. Why is there a `__init__.py` file in almost every folder?

**Answer:**

- **WHY:** It tells Python that this folder should be treated as a "Package".
- **HOW:** Without it, you wouldn't be able to do `from bookings import views`. In our project, we also use the main `moviebooking/__init__.py` to make sure Celery starts when the website starts.

### 3. Why do we use a `.env` file?

**Answer:**

- **WHY:** To store "Secrets" like your Razorpay API Key or Database password.
- **HOW:** You never want to upload these secrets to GitHub (public). We store them in `.env` and tell Git to ignore that file using `.gitignore`.

---

## ⚡ Celery & Background Tasks

### 4. What is Celery in simple terms?

**Answer:** Imagine you are at a restaurant (the website).

- The **Waiter** (Django) takes your order.
- If the waiter also had to cook the food, wash the dishes, and clean the floor (tasks like sending emails), he would be very slow.
- Instead, the waiter gives these tasks to the **Chef** (Celery Worker) in the kitchen.
- The waiter is now free to help the next customer immediately.

### 5. What is a "Message Broker" (like Redis)?

**Answer:** It's the **Clipboard** or **Buffer** where the Waiter writes down the order for the Chef. Celery can't talk to Django directly; they use Redis to pass messages back and forth.

### 6. What is "Celery Beat"?

**Answer:** It's an **Alarm Clock**. It tells Celery to run tasks at a specific time (e.g., "Clean the floor every night at 12 AM" or "Check for expired bookings every 60 seconds").

---

## 💳 Razorpay & Payments

### 7. Why can't we just have a "Success" button on the frontend?

**Answer:** **SECURITY.**

- **WHY:** A user could just look at the code, find the "Success" URL, and type it into their browser to get a free ticket.
- **HOW:** We use **Signature Verification**. Razorpay gives us a secret code (signature) that only our server can verify. This proves the user actually paid.

### 8. Why do we multiply the price by 100?

**Answer:** Computer programs sometimes make mistakes with decimals (like `0.1 + 0.2` not being exactly `0.3`).

- **HOW:** Razorpay avoids this by asking for the amount in the smallest unit (Paise). So, ₹10.00 becomes `1000` paise.

---

## 🛡️ Database & Security

### 9. What is `@login_required`?

**Answer:** It's a **Bouncer** for your views. It checks if the user is logged in. If not, it kicks them back to the login page.

### 10. What does `on_delete=models.CASCADE` mean?

**Answer:** It's a "Chain Reaction".

- **EXAMPLE:** If you delete a **Movie**, it doesn't make sense to keep its **Showtimes**. `CASCADE` tells Django: "If the parent (Movie) is deleted, delete all its children (Showtimes) too."

### 11. What is the difference between a `ForeignKey` and a `ManyToManyField`?

**Answer:**

- **ForeignKey:** One-to-Many. (One Movie belongs to one Language, but a Language has many Movies).
- **ManyToManyField:** Many-to-Many. (One Movie has many Genres, and one Genre has many Movies).

---

## 📝 Coding Best Practices

### 12. Why do we add "Docstrings" (the text in `""" """)` at the top of functions?

**Answer:** It's a **Note to your future self**. It explains what the function does and _why_ it exists, making it easier for other developers to understand your code.

### 13. Why do we use `try...except` blocks?

**Answer:** **Crash Prevention.** If something goes wrong (like the internet being down), the `try` block catches the error and the `except` block handles it gracefully instead of showing a scary error screen to the user.
