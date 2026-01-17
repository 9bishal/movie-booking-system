#!/bin/bash

# Fly.io Deployment Script for Django Movie Booking System
# This script handles complete deployment and admin user creation

echo "=================================================="
echo "  Django Movie Booking - Fly.io Deployment"
echo "=================================================="
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Fly CLI not found. Installing..."
    curl -L https://fly.io/install.sh | sh
    echo ""
    echo "⚠️  Please restart your terminal and run this script again."
    exit 1
fi

echo "✅ Fly CLI is installed"
echo ""

# Check if fly.toml exists
if [ ! -f "fly.toml" ]; then
    echo "📝 Creating new Fly.io app..."
    flyctl launch --no-deploy
    echo ""
fi

# Get admin credentials
echo "🔐 Admin User Setup"
read -p "Enter admin username (default: admin): " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}

read -p "Enter admin email (default: admin@example.com): " ADMIN_EMAIL
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}

read -s -p "Enter admin password (default: admin123): " ADMIN_PASS
echo ""
ADMIN_PASS=${ADMIN_PASS:-admin123}

echo ""
echo "=================================================="
echo "  Deploying to Fly.io..."
echo "=================================================="

# Deploy to Fly.io
flyctl deploy

echo ""
echo "=================================================="
echo "  Running migrations..."
echo "=================================================="

# Run migrations
flyctl ssh console -C "python manage.py migrate"

echo ""
echo "=================================================="
echo "  Creating admin user..."
echo "=================================================="

# Create admin user
flyctl ssh console -C "python manage.py create_admin --username $ADMIN_USER --email $ADMIN_EMAIL --password $ADMIN_PASS --reset"

echo ""
echo "=================================================="
echo "  Collecting static files..."
echo "=================================================="

flyctl ssh console -C "python manage.py collectstatic --noinput"

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "Admin Credentials:"
echo "  Username: $ADMIN_USER"
echo "  Password: ********"
echo ""
echo "Access your app at:"
flyctl status --json | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4 | head -1 | xargs -I {} echo "  https://{}"
echo ""
echo "Admin panels:"
echo "  Django Admin:  /admin/"
echo "  Custom Admin:  /custom-admin/"
echo ""
