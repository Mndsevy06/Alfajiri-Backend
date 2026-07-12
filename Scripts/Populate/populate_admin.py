import os
import sys
import django

# Add the backend directory to sys.path so we can import 'core'
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def populate():
    email = "agmail.com"
    password = "12345678"
    
    if User.objects.filter(email=email).exists():
        print(f"User {email} already exists.")
        return

    # Create Super Admin
    user = User.objects.create_superuser(
        email=email,
        password=password
    )
    
    print(f"Successfully created Super Admin user with email: {email}")

if __name__ == "__main__":
    populate()
