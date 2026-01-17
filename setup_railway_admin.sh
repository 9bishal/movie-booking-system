#!/bin/bash

# Railway Admin User Setup Script
# This script creates or resets the admin user in Railway production

echo "=================================================="
echo "  Railway Admin User Setup"
echo "=================================================="
echo ""
echo "This script will help you create/reset admin user in Railway."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "⚠️  Railway CLI not found. Installing Railway CLI..."
    echo ""
    echo "Run this command to install Railway CLI:"
    echo "  npm i -g @railway/cli"
    echo ""
    echo "Or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

echo "✅ Railway CLI is installed"
echo ""

# Get admin credentials
read -p "Enter admin username (default: admin): " USERNAME
USERNAME=${USERNAME:-admin}

read -p "Enter admin email (default: admin@moviebooking.com): " EMAIL
EMAIL=${EMAIL:-admin@moviebooking.com}

echo ""
read -s -p "Enter admin password (default: admin123): " PASSWORD
echo ""
PASSWORD=${PASSWORD:-admin123}

echo ""
echo "=================================================="
echo "  Creating admin user with:"
echo "  Username: $USERNAME"
echo "  Email:    $EMAIL"
echo "  Password: ********"
echo "=================================================="
echo ""

# Link to Railway project (if not already linked)
echo "🔗 Linking to Railway project..."
railway link

echo ""
echo "🚀 Running management command on Railway..."
railway run python manage.py create_admin --username "$USERNAME" --email "$EMAIL" --password "$PASSWORD" --reset

echo ""
echo "=================================================="
echo "✅ Admin user setup complete!"
echo "=================================================="
echo ""
echo "You can now login to:"
echo "  Django Admin:  https://your-app.railway.app/admin/"
echo "  Custom Admin:  https://your-app.railway.app/custom-admin/"
echo ""
