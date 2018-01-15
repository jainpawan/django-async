"""
    Django manage.py command to archive old jobs
"""
from django.core.management.base import BaseCommand

from async.api import archive_old_jobs


class Command(BaseCommand):
    """
        Invoke using:
            python manage.py queue_health
    """
    help = 'Prints information about the queue in JSON format.'

    def handle(self, **options):
        """Command implementation.
        """
        print archive_old_jobs(7)

