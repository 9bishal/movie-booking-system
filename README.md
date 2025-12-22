# Movie Booking System

![Django](https://img.shields.io/badge/Django-5.x-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Planned-blue)
![Celery](https://img.shields.io/badge/Celery-Planned-orange)

A BookMyShow clone built with Django.

## 🛠️ Tech Stack

### **Backend**

- **Framework**: Django 5.x
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Cache**: Redis (Planned)
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

### **DevOps**

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
