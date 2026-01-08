# 📚 API Documentation

## Overview

This document describes all API endpoints available in the Movie Booking System.

---

## Base URL

**Development**: `http://localhost:8000`
**Production**: `https://your-app-name.herokuapp.com`

---

## Authentication

Most endpoints require authentication. Include the session cookie or authentication token.

### Login
```
POST /accounts/login/
Content-Type: application/x-www-form-urlencoded

username=user@example.com
password=password123
```

**Response** (302 redirect to dashboard on success)

---

## Endpoints

### Movies

#### List All Movies
```
GET /movies/
```

**Response** (200 OK):
```json
{
  "movies": [
    {
      "id": 1,
      "title": "Avatar 3",
      "slug": "avatar-3",
      "description": "...",
      "poster": "/media/posters/avatar3.jpg",
      "duration": 192,
      "rating": 8.5,
      "status": "NOW_SHOWING"
    }
  ]
}
```

#### Get Movie Details
```
GET /movies/<slug>/
```

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Avatar 3",
  "description": "...",
  "release_date": "2024-12-20",
  "duration": 192,
  "rating": 8.5,
  "poster": "/media/posters/avatar3.jpg",
  "showtimes": [
    {
      "id": 1,
      "date": "2024-12-21",
      "start_time": "10:00",
      "end_time": "12:32",
      "price": 250,
      "available_seats": 45
    }
  ]
}
```

---

### Bookings

#### Get My Bookings
```
GET /bookings/my-bookings/
```

**Authentication**: Required

**Response** (200 OK):
```json
{
  "bookings": [
    {
      "id": 1,
      "booking_number": "BOOK-20240121-12345",
      "movie_title": "Avatar 3",
      "showtime_date": "2024-12-21",
      "showtime_time": "10:00",
      "seats": ["A1", "A2"],
      "total_seats": 2,
      "total_amount": 605.00,
      "status": "CONFIRMED",
      "created_at": "2024-01-21T10:30:00Z"
    }
  ]
}
```

#### Get Booking Details
```
GET /bookings/detail/<booking_id>/
```

**Authentication**: Required

**Response** (200 OK):
```json
{
  "id": 1,
  "booking_number": "BOOK-20240121-12345",
  "movie": {
    "title": "Avatar 3",
    "duration": 192
  },
  "showtime": {
    "date": "2024-12-21",
    "start_time": "10:00",
    "end_time": "12:32",
    "theater": {
      "name": "PVR Cinemas",
      "address": "Mall, City"
    },
    "screen": {
      "name": "Screen 1"
    }
  },
  "seats": ["A1", "A2"],
  "total_seats": 2,
  "base_price": 500.00,
  "convenience_fee": 50.00,
  "tax_amount": 55.00,
  "total_amount": 605.00,
  "status": "CONFIRMED",
  "payment_id": "pay_1234567890",
  "created_at": "2024-01-21T10:30:00Z",
  "payment_received_at": "2024-01-21T10:35:00Z"
}
```

---

### Seat Management

#### Get Seat Status for Showtime
```
GET /bookings/api/seat-status/<showtime_id>/
```

**Authentication**: Required

**Response** (200 OK):
```json
{
  "available_seats": [
    "A1", "A2", "A3", "B1", "B2", ...
  ],
  "reserved_seats": [
    "C1", "C2"
  ],
  "booked_seats": [
    "A10", "B10"
  ],
  "available_count": 87,
  "reserved_count": 2,
  "booked_count": 2,
  "total_seats": 100
}
```

#### Reserve Seats
```
POST /bookings/api/reserve-seats/<showtime_id>/ 
Content-Type: application/json
Authorization: Bearer <token>

{
  "seats": ["A1", "A2"]
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Seats reserved for 12 minutes",
  "reservation_id": "res_1234",
  "expires_at": "2024-01-21T10:42:00Z"
}
```

**Response** (409 Conflict - seats taken):
```json
{
  "success": false,
  "message": "Seat A1 is no longer available",
  "available_seats": ["A2", "A3", ...]
}
```

#### Release Reserved Seats
```
POST /bookings/api/release-seats/<showtime_id>/
Content-Type: application/json
Authorization: Bearer <token>

{
  "seats": ["A1", "A2"]
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Seats released successfully"
}
```

---

### Booking Creation

#### Create Booking
```
POST /bookings/api/create-booking/<showtime_id>/
Content-Type: application/json
Authorization: Bearer <token>

{
  "seats": ["A1", "A2"],
  "num_seats": 2
}
```

**Response** (201 Created):
```json
{
  "booking_id": 1,
  "booking_number": "BOOK-20240121-12345",
  "total_amount": 605.00,
  "breakdown": {
    "base_price": 500.00,
    "convenience_fee": 50.00,
    "tax_amount": 55.00
  },
  "razorpay_order_id": "order_1234567890",
  "status": "PENDING"
}
```

#### Cancel Booking
```
POST /bookings/api/cancel/<booking_id>/
Content-Type: application/json
Authorization: Bearer <token>

{}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Booking cancelled successfully",
  "refund_amount": 605.00
}
```

---

### Payment

#### Payment Success Callback
```
POST /bookings/razorpay-webhook/
Content-Type: application/json

{
  "payment_id": "pay_1234567890",
  "order_id": "order_1234567890",
  "signature": "signature_here"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Payment verified and booking confirmed"
}
```

#### Payment Failure Page
```
GET /bookings/<booking_id>/payment/failed/
```

**Response** (200 OK - HTML page showing failure message)

---

### User Management

#### Register
```
POST /accounts/register/
Content-Type: application/x-www-form-urlencoded

email=user@example.com
username=username
password=password123
password2=password123
```

**Response** (302 redirect to login on success)

#### Login
```
POST /accounts/login/
Content-Type: application/x-www-form-urlencoded

username=username
password=password123
```

**Response** (302 redirect to dashboard on success)

#### Logout
```
GET /accounts/logout/
```

**Response** (302 redirect to home page)

#### User Profile
```
GET /accounts/profile/
```

**Authentication**: Required

**Response** (200 OK):
```json
{
  "user": {
    "id": 1,
    "username": "username",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "joined_date": "2024-01-01"
  }
}
```

---

### Admin Panel

#### Django Admin
```
GET /admin/
```

**Authentication**: Required (Staff/Superuser)

**Available Models**:
- Users
- Movies
- Theaters
- Screens
- Showtimes
- Bookings
- Transactions

---

## Error Codes

### 400 Bad Request
Invalid request parameters

```json
{
  "error": "Bad Request",
  "message": "Invalid seat selection"
}
```

### 401 Unauthorized
Authentication required or invalid

```json
{
  "error": "Unauthorized",
  "message": "Please login to continue"
}
```

### 403 Forbidden
User doesn't have permission

```json
{
  "error": "Forbidden",
  "message": "You don't have permission to access this booking"
}
```

### 404 Not Found
Resource not found

```json
{
  "error": "Not Found",
  "message": "Booking not found"
}
```

### 409 Conflict
Resource conflict (seats taken, etc.)

```json
{
  "error": "Conflict",
  "message": "Seat A1 is no longer available"
}
```

### 429 Too Many Requests
Rate limit exceeded

```json
{
  "error": "Too Many Requests",
  "message": "Too many booking attempts. Please wait before trying again.",
  "retry_after": 60
}
```

### 500 Internal Server Error
Server error

```json
{
  "error": "Internal Server Error",
  "message": "Something went wrong. Please try again later."
}
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Booking creation**: 10 requests per 60 seconds per user
- **Seat reservation**: 20 requests per 60 seconds per user
- **Payment**: 5 requests per 60 seconds per user

**Rate limit headers**:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1705863720
```

When rate limit exceeded:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 42
```

---

## Pagination

List endpoints support pagination:

```
GET /movies/?page=1&limit=10
```

**Response**:
```json
{
  "results": [...],
  "count": 100,
  "next": "/?page=2&limit=10",
  "previous": null,
  "total_pages": 10
}
```

---

## Filtering

List endpoints support filtering:

```
GET /movies/?status=NOW_SHOWING&rating_min=7.0
```

---

## Sorting

List endpoints support sorting:

```
GET /movies/?sort=-rating,title
```

---

## Webhooks

### Razorpay Payment Webhook

**URL**: `/bookings/razorpay-webhook/`

**Method**: POST

**Headers**:
```
Content-Type: application/json
X-Razorpay-Signature: <signature>
```

**Payload**:
```json
{
  "event": "payment.authorized",
  "contains": ["payment", "order"],
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_1234567890",
        "amount": 60500,
        "currency": "INR",
        "status": "captured"
      }
    },
    "order": {
      "entity": {
        "id": "order_1234567890",
        "amount": 60500,
        "status": "paid"
      }
    }
  }
}
```

---

## Rate Limiting

API implements rate limiting:

**Limits per user**:
- Booking creation: 10 requests/minute
- Seat reservation: 20 requests/minute  
- Payment: 5 requests/minute

**Response when limit exceeded**:
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705863780
Retry-After: 60
```

---

## Caching

Some endpoints are cached:

- Movie list: 1 hour
- Movie detail: 1 hour
- Showtime list: 15 minutes (expires when showtime starts)

**Cache headers**:
```
Cache-Control: max-age=3600, public
ETag: "12345"
Last-Modified: Mon, 21 Jan 2024 10:00:00 GMT
```

---

## Common Workflows 

### Complete Booking Workflow

```
1. GET /movies/                              # List movies
2. GET /movies/<slug>/                       # Get movie details
3. POST /bookings/api/reserve-seats/<id>/   # Reserve seats
4. POST /bookings/api/create-booking/<id>/  # Create booking
5. Redirect to Razorpay payment page
6. POST /bookings/razorpay-webhook/         # Webhook confirmation
7. GET /bookings/detail/<booking_id>/       # View ticket
```

### Check Seat Availability

```
1. GET /bookings/api/seat-status/<id>/      # Get seat status
2. Check available_seats array
3. Reserve if needed: POST /bookings/api/reserve-seats/<id>/
```

### Cancel Booking

```
1. GET /bookings/detail/<booking_id>/       # View booking
2. POST /bookings/api/cancel/<booking_id>/  # Cancel booking
3. Refund processed automatically
```

--- 

## Testing

### Using curl

```bash
# Get movies
curl http://localhost:8000/movies/

# Get seat status (requires authentication)
curl -b cookies.txt http://localhost:8000/bookings/api/seat-status/1/

# Create booking (requires authentication)
curl -X POST http://localhost:8000/bookings/api/create-booking/1/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "seats": ["A1", "A2"],
    "num_seats": 2
  }'
```

### Using Postman

1. Create collection "Movie Booking API"
2. Set base URL to `http://localhost:8000`
3. Import requests from documentation
4. Set up authentication (store cookies)
5. Run requests

---

## SDK & Libraries

### JavaScript/Node.js
```javascript
const movieBooking = require('movie-booking-api');
const client = new movieBooking.Client({
  baseURL: 'http://localhost:8000'
});

// Get movies
const movies = await client.movies.list();
```

### Python
```python
from movie_booking import Client

client = Client('http://localhost:8000')
movies = client.movies.list()
booking = client.bookings.create(showtime_id=1, seats=['A1', 'A2'])
```

---

## Changelog

### v1.0.0 (2024-01-21)
- Initial API release
- Movies, Bookings, Seats endpoints
- Razorpay payment integration
- Rate limiting implemented

---

## Support

For issues, questions, or suggestions:

- **GitHub Issues**: [Create issue](https://github.com/9bishal/movie-booking-system/issues)
- **Email**: support@moviebooking.com
- **Documentation**: [Full docs](./DOCUMENTATION_INDEX.md)

---

**Last Updated**: 8 January 2026
**Status**: ✅ Production Ready
