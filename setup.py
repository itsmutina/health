#!/usr/bin/env python
"""
Setup script for Mental Health Journal Django application.
Run this script to set up the development environment.
"""

import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running {description}: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_environment():
    """Set up the development environment."""
    print("Setting up Mental Health Journal...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("Error: manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("Failed to install requirements. Please check your Python environment.")
        sys.exit(1)
    
    # Set up environment variables
    if not os.path.exists('.env'):
        print("Creating .env file from template...")
        with open('env.example', 'r') as f:
            env_content = f.read()
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✓ .env file created. Please edit it with your settings.")
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health_journal.settings')
    django.setup()
    
    # Create migrations
    if not run_command("python manage.py makemigrations", "Creating database migrations"):
        print("Failed to create migrations.")
        sys.exit(1)
    
    # Apply migrations
    if not run_command("python manage.py migrate", "Applying database migrations"):
        print("Failed to apply migrations.")
        sys.exit(1)
    
    # Set up default data
    if not run_command("python manage.py setup_default_data", "Setting up default data"):
        print("Failed to set up default data.")
        sys.exit(1)
    
    # Create superuser (optional)
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Create a superuser account:")
    print("   python manage.py createsuperuser")
    print("\n2. Start the development server:")
    print("   python manage.py runserver")
    print("\n3. Open your browser and go to:")
    print("   http://localhost:8000/")
    print("\n4. Admin panel:")
    print("   http://localhost:8000/admin/")
    
    # Ask if user wants to create superuser
    create_superuser = input("\nWould you like to create a superuser account now? (y/n): ").lower().strip()
    if create_superuser in ['y', 'yes']:
        run_command("python manage.py createsuperuser", "Creating superuser account")
    
    # Ask if user wants to start the server
    start_server = input("\nWould you like to start the development server now? (y/n): ").lower().strip()
    if start_server in ['y', 'yes']:
        print("\nStarting development server...")
        print("Press Ctrl+C to stop the server")
        run_command("python manage.py runserver", "Starting development server")

if __name__ == "__main__":
    setup_environment()
