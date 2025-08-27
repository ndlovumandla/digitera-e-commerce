#!/usr/bin/env python
"""
Direct server startup script to bypass autoreloader issues
"""
import os
import sys
import django
from django.core.wsgi import get_wsgi_application
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitera_platform.settings_working')
    
    try:
        # Setup Django
        django.setup()
        
        # Start server manually
        from django.core.management.commands.runserver import Command as RunserverCommand
        command = RunserverCommand()
        command.execute(
            addrport='127.0.0.1:8003',
            use_reloader=False,
            use_threading=True,
            verbosity=2
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
