import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def update_comptes():
    with connection.cursor() as cursor:
        try:
            cursor.execute("""
                UPDATE plan_comptable_comptecomptable 
                SET numero = RPAD(numero, 6, '0') 
                WHERE LENGTH(numero) < 6;
            """)
            print(f"Update successful. Rows affected: {cursor.rowcount}")
        except Exception as e:
            print(f"Error during update: {e}")
            # If there's an FK error, we will see it here.

if __name__ == "__main__":
    update_comptes()
