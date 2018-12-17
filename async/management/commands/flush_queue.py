"""
    Django Async management commands.
"""
from django.core.management.base import BaseCommand
try:
    # No name 'timezone' in module 'django.utils'
    # pylint: disable=E0611
    from django.utils import timezone
except ImportError: # pragma: no cover
    from datetime import datetime as timezone
from optparse import make_option
from lockfile import FileLock, AlreadyLocked
import os

from async.models import Job


def acquire_lock(lockname):
    """Return a decorator for the given lock name
    """
    def decorator(handler):
        """Decorator for lock acquisition
        """
        def handle(*args):
            """Acquire the lock before running the method.
            """
            lock = FileLock(lockname)
            try:
                lock.acquire(timeout=-1)
            except AlreadyLocked: # pragma: no cover
                print 'Lock is already set, aborting.'
                return
            try:
                handler(*args)
            finally:
                lock.release()
        return handle
    return decorator

def get_fairness_items(location):
    if not os.path.isfile(location):
        return []

    f = file(location, 'r+')
    lines = f.read()
    f.close()
    return filter(bool, lines.split(","))

def add_fairness_items(location, item):
    if item is None:
        return
    f = file(location, 'a')
    lines = f.write(",%s" % item)
    f.close()

def clear_fairness_items(location):
    f = file(location, 'w')
    f.close()

def run_queue(which, outof, limit, name_filter):
    """
        Code that actually executes the jobs in the queue.

        This implementation is pretty ugly, but does behave in the
        right way.
    """
    location = 'last_processed_items_%s_%s_%s.dat' % (which, outof, name_filter)
    for _ in xrange(limit):
        now = timezone.now()
        def run(jobs):
            """Run the jobs handed to it
            """
            for job in jobs.iterator():
                if job.id % outof == which % outof:
                    if (job.group and job.group.final and
                            job.group.final.pk == job.pk):
                        if not job.group.has_completed(job):
                            continue
                    print "%s: %s: %s" % (job.id, unicode(job), job.fairness)
                    add_fairness_items(location, job.fairness)
                    job.execute()
                    return False
            return True
        fairness_items = get_fairness_items(location)
        by_priority = by_priority_filter = (Job.objects
            .filter(executed=None, cancelled=None,
                name__startswith=name_filter)
            .exclude(scheduled__gt=now)
            .exclude(priority__lt=-20)
            .exclude(fairness__in=fairness_items)
            .order_by('-priority'))
        while True:
            try:
                priority = by_priority[0].priority
            except IndexError:
                clear_fairness_items(location)
                #If we had some fairness filter, try again after clearing the filter.
                if fairness_items:
                    break
                print "No jobs to execute"
                return
            if run(Job.objects
                    .filter(executed=None, cancelled=None,
                        scheduled__lte=now, priority=priority,
                        name__startswith=name_filter)
                    .exclude(fairness__in=fairness_items)
                    .order_by('scheduled', 'id')):
                if run(Job.objects
                        .filter(executed=None, cancelled=None,
                            scheduled=None, priority=priority,
                            name__startswith=name_filter)
                        .exclude(fairness__in=fairness_items)
                        .order_by('id')):
                    by_priority = by_priority_filter.filter(
                        priority__lt=priority)
                else:
                    break
            else:
                break


class Command(BaseCommand):
    """
        Invoke using:
            python manage.py flush_queue
    """
    option_list = BaseCommand.option_list + (
        make_option('--jobs', '-j', dest='jobs',
            help='The maximum number of jobs to run'),
        make_option('--which', '-w', dest='which',
            help='The worker ID number'),
        make_option('--outof', '-o', dest='outof',
            help='How many workers there are'),
        make_option('--filter', '-f', dest='filter',
            help='Filter jobs by fully qualified name'),
    )
    help = 'Does a single pass over the asynchronous queue'

    def handle(self, **options):
        """
            Command implementation.
        """
        jobs_limit = int(options.get('jobs') or 300)
        which = int(options.get('which') or 0)
        outof = int(options.get('outof') or 1)
        name_filter = str(options.get('filter') or '')

        acquire_lock('async_flush_queue%s_%s' % (which, name_filter))(
            run_queue)(which, outof, jobs_limit, name_filter)
