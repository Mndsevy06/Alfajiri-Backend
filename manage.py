#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Custom logic to use PORT from .env for runserver
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        import environ
        env = environ.Env()
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_file):
            environ.Env.read_env(env_file)
        port = env('PORT', default='8000')
        # If no port is specified in the arguments, append the port from .env
        if len(sys.argv) == 2:
            sys.argv.append(port)

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
