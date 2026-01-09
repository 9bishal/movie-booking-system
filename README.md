# 🎬 Movie Booking System

[![Django](https://img.shields.io/badge/Django-5.x-green)](https://www.djangoproject.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)](https://getbootstrap.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Planned-blue)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-Planned-orange)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-Planned-red)](https://redis.io/)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-WSGI-lightgrey)](https://gunicorn.org/)
[![Nginx](https://img.shields.io/badge/Nginx-Reverse%20Proxy-brightgreen)](https://nginx.org/)
[![Docker](https://img.shields.io/badge/Docker-Planned-blue)](https://www.docker.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Planned-black)](https://vercel.com/)

A **BookMyShow-like Movie Ticket Booking System** built using **Django**, focusing on **high-concurrency seat booking**, **seat locking**, **payments**, and **scalable production deployment**.

---

## 📚 Documentation

**🎓 New to the system? Start here!**

We've created comprehensive beginner-friendly guides to help you understand how everything works:

### Essential Guides (Read in Order)
1. **[DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)** - Start here! Complete guide index
2. **[Understanding Redis](./UNDERSTANDING_REDIS.md)** - How seat locking works ⭐
3. **[Understanding Celery](./UNDERSTANDING_CELERY.md)** - Background tasks explained ⚙️
4. **[Understanding Razorpay](./UNDERSTANDING_RAZORPAY.md)** - Payment integration 💳
5. **[How Everything Works Together](./HOW_EVERYTHING_WORKS_TOGETHER.md)** - Complete system flow 🎬

### Technical Documentation
- **[Complete Fix Summary](./COMPLETE_FIX_SUMMARY.md)** - All system fixes and improvements
- **[Rate Limiting Guide](./RATE_LIMITING_GUIDE.md)** - Complete rate limiting documentation ⚡
- **[Rate Limiting Fix](./RATE_LIMITING_FIX.md)** - 429 error fix details 🛠️
- **[Celery Expiry Fix](./CELERY_EXPIRY_REDIS_FIX_COMPLETE.md)** - Background expiry implementation
- **[Refresh & Cancel Fix](./REFRESH_AND_CANCEL_FIX.md)** - Page refresh handling
- **[Redis Fix Complete](./REDIS_FIX_COMPLETE.md)** - Redis key cleanup fix

**💡 Tip**: Each guide includes real-world examples, analogies, and step-by-step explanations perfect for beginners!

---

## 🚀 Features

- 🎥 **Movie & Show Listings** - Browse movies, showtimes, and theaters
- 🪑 **Real-time Seat Selection** - Interactive seat selection UI
- 🔒 **Concurrency Control** - Redis-based seat locking to prevent double booking
- 💳 **Payment Integration** - Secure payment processing (Planned)
- 📧 **Email Notifications** - Booking confirmations and tickets (Planned)
- 🎫 **Ticket Generation** - Digital tickets with QR codes (Planned)
- 📱 **Responsive Design** - Mobile-friendly Bootstrap interface
- ⚡ **Scalable Architecture** - Production-ready with Celery, Redis, and PostgreSQL

---

## 🛠️ Tech Stack

### 🔙 Backend
- **Framework**: Django 5.x
- **Database**: SQLite (Development) / PostgreSQL (Production – Planned)
- **Cache & Locking**: Redis (Seat locking & caching)
- **Async Tasks**: Celery (Emails, seat release, ticket generation)

### 🎨 Frontend
- **Templates**: Django Templates
- **Styling**: Bootstrap 5
- **Icons**: Font Awesome
- **JavaScript**: Vanilla JS

### 🔌 Integrations (Planned)
- **Payments**: Razorpay / Stripe
- **Emails**: SendGrid
- **Trailers**: YouTube Data API

### 🚢 DevOps & Deployment
- **Reverse Proxy**: Nginx
- **WSGI Server**: Gunicorn
- **Caching / Broker**: Redis
- **Containerization**: Docker (Planned)
- **Hosting**: AWS / Heroku (Planned)
- **Frontend Hosting**: Vercel (Optional)

---

## 📋 Prerequisites

- Python 3.9+
- Redis (for seat locking)
- PostgreSQL (for production)

---

## 🚀 Getting Started

### Development Setup

```bash
# 1. Clone repository
git clone https://github.com/9bishal/movie-booking-system.git
cd movie-booking-system

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install django redis celery

# 5. Apply migrations
python manage.py migrate

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver

# 8. Open in browser
# Visit: http://127.0.0.1:8000/
```

### Redis Setup (Required for seat locking)

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Start Redis service
sudo systemctl start redis

# Check Redis status
redis-cli ping
# Should respond with: PONG
```

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌──────────────────┐
│   User Browser   │
│ (Web / Mobile)   │
└─────────┬────────┘
          │ HTTP Request
          ▼
┌──────────────────┐
│      Nginx       │
│ Reverse Proxy    │
│ SSL + Static     │
└─────────┬────────┘
          │
          ▼
┌──────────────────┐
│    Gunicorn      │
│ WSGI Server      │
└─────────┬────────┘
          │
          ▼
┌────────────────────────────────────┐
│            Django App               │
│ ────────────────────────────────── │
│  • User Auth                       │
│  • Movie & Show Listing            │
│  • Seat Selection                  │
│  • Booking Logic                   │
└─────────┬───────────────┬──────────┘
          │               │
          │               │
          ▼               ▼
┌───────────────┐  ┌────────────────┐
│  PostgreSQL   │  │     Redis      │
│  Main DB      │  │ Seat Locks     │
│  Users        │  │ Cache + TTL    │
│  Movies       │  └────────────────┘
│  Bookings     │
└───────────────┘
          │
          │ Payment Initiated
          ▼
┌──────────────────┐
│ Payment Gateway  │
│ Razorpay/Stripe  │
└─────────┬────────┘
          │ Payment Success
          ▼
┌────────────────────────────────────┐
│        Booking Confirmation        │
│  • Seats marked CONFIRMED          │
│  • Ticket generated                │
└─────────┬───────────────┬──────────┘
          │               │
          │               │
          ▼               ▼
┌────────────────┐  ┌──────────────────┐
│   PostgreSQL   │  │     Celery       │
│ Save Ticket    │  │ Background Jobs  │
└────────────────┘  │ ──────────────── │
                     │ • Send Email     │
                     │ • Release Locks  │
                     │ • Notifications  │
                     └───────┬────────┘
                             │
                             ▼
                     ┌──────────────────┐
                     │   Email Service  │
                     │   (SendGrid)     │
                     │ Ticket + Receipt │
                     └──────────────────┘
```

---

## 🔐 Seat Booking & Concurrency Control

This system uses **Redis-based Optimistic Locking** to prevent double booking during high traffic.

### 🔄 Seat Booking Flow

1. **User selects seats** (no lock applied initially)
2. **User proceeds to payment** page
3. **Seats are temporarily locked** in Redis with a TTL
4. **Lock expires** after a fixed time (e.g., 5 minutes) if payment not completed
5. **Payment success** → booking confirmed, seats permanently reserved
6. **Payment failure/timeout** → seats automatically released

### 🪑 Redis Seat Locking Strategy

**Key Format:**
```makefile
seat_lock:{show_id}:{seat_id} = user_id
TTL = 300 seconds (5 minutes)
```

**Example:**
```makefile
seat_lock:101:B12 = user_45
```
If TTL expires → Redis auto-deletes → seat becomes available again.

---

## 📧 Email & Ticket Flow

### After Successful Payment:
- 🎟️ **Ticket generated** (PDF / HTML format)
- 📩 **Email sent** to user containing:
  - Booking confirmation
  - Movie & show details
  - Seat numbers
  - QR code / booking ID

### Background Tasks (Celery):
- Send confirmation email
- Release expired seat locks
- Retry failed emails
- Generate and store tickets

---

## 🗂️ Project Structure

```
movie-booking-system/
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── moviebooking/          # Main Django project
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── booking/              # Booking app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── migrations/
├── movies/               # Movies app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── users/                # User authentication app
│   ├── models.py
│   ├── views.py
│   └── forms.py
├── static/              # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── media/               # Uploaded files
├── templates/           # Base templates
└── tests/               # Test files
```

---

## 🚀 Production Deployment

### Deployment Checklist

1. **Database Migration:**
   ```bash
   python manage.py migrate
   ```

2. **Collect Static Files:**
   ```bash
   python manage.py collectstatic
   ```

3. **Environment Variables:**
   ```bash
   DEBUG=False
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://...
   REDIS_URL=redis://...
   EMAIL_HOST=...
   ```

4. **Start Services:**
   ```bash
   # Start Gunicorn
   gunicorn moviebooking.wsgi:application --bind 0.0.0.0:8000

   # Start Celery worker
   celery -A moviebooking worker --loglevel=info

   # Start Celery beat (for scheduled tasks)
   celery -A moviebooking beat --loglevel=info
   ```

5. **Configure Nginx:**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location /static/ {
           alias /path/to/static/;
       }
       
       location /media/ {
           alias /path/to/media/;
       }
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

## 📊 API Endpoints (Planned)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/movies/` | List all movies |
| GET | `/api/movies/{id}/` | Get movie details |
| GET | `/api/shows/{id}/seats/` | Get seat availability |
| POST | `/api/bookings/lock-seats/` | Lock selected seats |
| POST | `/api/bookings/create/` | Create booking |
| POST | `/api/payments/initiate/` | Initiate payment |
| GET | `/api/bookings/{id}/` | Get booking details |

---

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test booking

# Run with coverage
coverage run manage.py test
coverage report
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create a feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation accordingly
- Use meaningful commit messages

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Redis connection failed | Ensure Redis server is running: `redis-cli ping` |
| Migration errors | Try: `python manage.py makemigrations` then `python manage.py migrate` |
| Static files not loading | Run: `python manage.py collectstatic` |
| Celery not working | Check Redis connection and Celery worker status |
| 429 Too Many Requests | See [Rate Limiting Guide](./RATE_LIMITING_GUIDE.md) - Adjust limits in `utils/rate_limit.py` |
| Rate limiting not working | Test Redis: `python test_rate_limiting.py` |

---

## 📝 License

This project is for **educational purposes only**. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Django Documentation](https://docs.djangoproject.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Redis Documentation](https://redis.io/documentation)
- [Celery Documentation](https://docs.celeryq.dev/)

---

## 📞 Contact

Project Link: [https://github.com/9bishal/movie-booking-system](https://github.com/9bishal/movie-booking-system)

---

## 📊 Project Status

| Feature | Status |
|---------|--------|
| Movie & show listing | ✅ Completed |
| Seat selection logic | ✅ Completed |
| Redis seat locking | ✅ Completed |
| Payment gateway integration | 🚧 In Progress |
| Email & ticket generation | 🚧 In Progress |
| Docker & cloud deployment | 🚧 Planned |
| Mobile app (React Native) | 🚧 Future |

---

**Happy Coding! 🚀🎬**
