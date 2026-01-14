# 🛠️ Management Scripts

Simple utility scripts for managing the Movie Booking System.

## Usage

Run any script from the project root:

```bash
python scripts/<script_name>.py
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `clear_cache.py` | Clear all Redis/Django cache |
| `release_all_seats.py` | Delete all bookings (release all seats) |
| `delete_users.py` | Delete users (with options) |
| `delete_movies.py` | Delete all movies |
| `delete_theaters.py` | Delete theaters/screens/showtimes |
| `reset_database.py` | Reset entire database |
| `show_stats.py` | Show database statistics |
| `cancel_expired.py` | Cancel expired pending bookings |
| `create_sample_data.py` | Create sample movie/theater/showtime |

## Quick Commands

```bash
# Clear cache
python scripts/clear_cache.py

# Show stats
python scripts/show_stats.py

# Create sample data
python scripts/create_sample_data.py

# Reset everything
python scripts/reset_database.py
```

## ⚠️ Warning

Most scripts require confirmation before deleting data. Type exactly what is asked (usually `yes` or `RESET`).
