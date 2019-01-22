"""
    Django manage.py command to archive old jobs
"""
from async.command_stats import StatBaseCommand

from async.api import archive_old_jobs


class Command(StatBaseCommand):
    option_list = StatBaseCommand.option_list + (
        optparse.make_option(
            '--before_days',
            action='store',
            dest='before_days',
            help='before_days'
        ),
    )
    help = 'Does a single pass over the asynchronous queue'

    """
        Invoke using:
            python manage.py queue_health
    """
    help = 'Prints information about the queue in JSON format.'

    def handle(self, **options):
        """Command implementation.
        """
        before_days = options.get('before_days')
        print archive_old_jobs(int(before_days))

