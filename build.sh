#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Create superuser if it doesn't exist (optional)
# python manage.py shell -c "from accounts.models import User; User.objects.filter(email='admin@example.com').exists() or User.objects.create_superuser('admin@example.com', 'admin', 'password')"
