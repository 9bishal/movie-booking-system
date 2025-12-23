# Movie Booking System

![Django](https://img.shields.io/badge/Django-5.x-092e20?style=for-the-badge&logo=django)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952b3?style=for-the-badge&logo=bootstrap)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-dc382d?style=for-the-badge&logo=redis)
![Celery](https://img.shields.io/badge/Celery-373737?style=for-the-badge&logo=celery)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx)
![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn)

A BookMyShow clone built with Django.

## 🛠️ Tech Stack

### **Backend**

- **Framework**: Django 5.x
- **Database**: SQLite (Dev) / PostgreSQL (Prod)
- **Cache**: Redis (Active - Seat Locking & Layout)
- **Task Queue**: Celery (Planned)

### **Frontend**

- **Templates**: Django Templates
- **Styling**: Bootstrap 5
- **Icons**: Font Awesome
- **JavaScript**: Vanilla JS

### **Integrations (Planned)**

- **Payment**: Razorpay
- **Email**: SendGrid
- **Trailers**: YouTube API

### **DevOps & Deployment**

- **Web Server**: Nginx
- **WSGI Server**: Gunicorn
- **Container**: Docker (Planned)
- **Hosting**: Heroku/AWS (Planned)

## 🚀 Getting Started

```bash
# Clone repo
git clone https://github.com/9bishal/movie-booking-system.git
cd movie-booking-system

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django

# Run migrations
python manage.py migrate

# Run server
python manage.py runserver
```

## 🚀 Production Deployment

For a production environment, it is highly recommended to use a robust web server stack:

1. **Nginx**: As a reverse proxy to handle SSL, static files, and security.
2. **Gunicorn**: As a WSGI HTTP Server to manage multiple Django worker processes.
3. **Whitenoise**: For efficient static file serving within Django (optional if using Nginx for statics).
