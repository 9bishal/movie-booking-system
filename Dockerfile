FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
# it means all the commands will be run from /app directory
WORKDIR /app 

# Install system dependencies
#-y means “yes automatically” to prompts
RUN apt-get update && apt-get install -y --no-install-recommends \ 
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* 



# Why install postgresql-client?
# postgresql-client is needed to run migrations against a remote PostgreSQL database
# It installs tools like:
## psql:Connect to PostgreSQL
# pg_dump:Backup database
# pg_restore which are essential for database management tasks during deployment.



# --no-install-recommends
# What it does
# Installs only essential packages
# Skips optional extras



# rm -rf /var/lib/apt/lists/*
# What it does
# Deletes temporary package lists
# Why needed
# Saves 20–40 MB
# Cleaner image
# 📌 Without cleanup, Docker images grow unnecessarily.



# 🏁 Final Beginner Summary
# postgresql-client is installed so the Django container can properly talk to PostgreSQL, 
# run migrations, perform admin/debug tasks, and support production-level database operations. 
# The cleanup keeps the image small.



# Copy requirements
COPY requirements-production.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements-production.txt

# Copy project
COPY . .

# Create logs directory
RUN mkdir -p logs

# Collect static files
RUN python manage.py collectstatic --noinput --settings=moviebooking.settings_production

# Expose port
EXPOSE 8000

# Run gunicorn
# Why Gunicorn?

# -> Production-grade WSGI server

# -> Handles multiple requests efficiently

# Why NOT runserver

# -> runserver is for development only
CMD ["gunicorn", "moviebooking.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]



# 🔁 How Dockerfile + Docker Compose Work Together
# Dockerfile	            | Docker Compose
# Builds image	            | Runs containers
# Installs dependencies	    | Connects services
# Defines CMD	            | Sets env variables
# Exposes ports	            | Maps ports


# 🧠 Real-World Flow: Dockerfile → Image → Container → Service
# 1. Dockerfile builds image
# 2. Image is a snapshot of app + dependencies
# 3. Container runs image as isolated instance
# 4. Service manages container lifecycle (start, stop, restart)
# 5. Docker Compose orchestrates multiple services together