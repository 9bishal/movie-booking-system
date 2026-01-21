#!/bin/bash

# Make user admin in Railway via management command
# Usage: ./add_admin.sh username

USERNAME=${1:-biku23sdcxsaiml}

echo "=================================================="
echo "  Adding admin to Railway: $USERNAME"
echo "=================================================="
echo ""

# Run the management command in Railway environment
railway run python manage.py make_user_admin "$USERNAME"

echo ""
echo "✅ Logout and login again to access admin panels"
