"""
    Schedule the execution of an async task.
"""
from datetime import timedelta
# No name 'sha1' in module 'hashlib'
# pylint: disable=E0611
from hashlib import sha1
from simplejson import dumps

from django.db.models import Q
try:
    # No name 'timezone' in module 'django.utils'
    # pylint: disable=E0611
    from django.utils import timezone
except ImportError: # pragma: no cover
    from datetime import datetime as timezone

from async.models import Error, Job, Group
from async.models import ErrorArchive, JobArchive
from async.utils import full_name
from time import sleep

def _get_now():
    """Get today datetime, testing purpose.
    """
    return timezone.now()


def schedule(function, args=None, kwargs=None,
        priority=5, run_after=None, group=None, meta=None, fairness=None):
    """Schedule a tast for execution.
    """
    # Too many arguments
    # pylint: disable=R0913
    if group:
        if type(group) == Group:
            expected_group = group
        else:
            expected_group = Group.latest_group_by_reference(group)
    else:
        expected_group = None
    job = Job(
        name=full_name(function),
            args=dumps(args or []), kwargs=dumps(kwargs or {}),
        meta=dumps(meta or {}), scheduled=run_after,
        priority=priority,
        group=expected_group,
        fairness=fairness)
    job.save()
    return job


def deschedule(function, args=None, kwargs=None):
    """Remove any instances of the job from the queue.
    """
    job = Job(
        name=full_name(function),
            args=dumps(args or []), kwargs=dumps(kwargs or {}))
    mark_cancelled = Job.objects.filter(executed=None,
        identity=sha1(unicode(job)).hexdigest())
    mark_cancelled.update(cancelled=_get_now())


def health():
    """Return information about the health of the queue in a format that
    can be turned into JSON.
    """
    output = {'queue': {}, 'errors': {}}
    output['queue']['all-jobs'] = Job.objects.all().count()
    output['queue']['not-executed'] = Job.objects.filter(executed=None).count()
    output['queue']['executed'] = Job.objects.exclude(executed=None).count()
    output['errors']['number'] = Error.objects.all().count()
    return output

def archive_old_jobs(archive_jobs_before_days=7):
    archive_jobs_before_dt = _get_now() - timedelta(
        days=archive_jobs_before_days)

    archive_job = (Q(executed__isnull=False) &
        Q(executed__lt=archive_jobs_before_dt)) | \
             (Q(cancelled__isnull=False) &
        Q(cancelled__lt=archive_jobs_before_dt))
    batch_size = 1000
    more_jobs_to_be_archived = True
    counter = 1
    max_counter = 20
    while more_jobs_to_be_archived and counter < max_counter:
        print 'archiving jobs...', counter*batch_size
        sleep(5)
        counter += 1
        to_be_archived_jobs = Job.objects.filter(Q(group__isnull=True), archive_job)
        if to_be_archived_jobs.count() > batch_size:
            to_be_archived_jobs = to_be_archived_jobs[:batch_size]
            more_jobs_to_be_archived = True
        else:
            more_jobs_to_be_archived = False

        for job in to_be_archived_jobs:
            print 'archiving job...', job.id
            #Copy finished jobs and errors here.
            archived_job = JobArchive(
                job_id=job.id, name=job.name,
                args=job.args, kwargs=job.kwargs,
                meta=job.meta, result=job.result,
                priority=job.priority, identity=job.identity,
                added=job.added,scheduled=job.scheduled,
                started=job.started, executed=job.executed,
                cancelled=job.cancelled, fairness=job.fairness)
            archived_job.save()
            errors = job.errors.all()
            if errors:
                for error in errors:
                    archived_error = ErrorArchive(
                        error_id = error.id,
                        job=archived_job,
                        executed=error.executed,
                        exception=error.exception,
                        traceback=error.traceback)
                    archived_error.save()
                #errors.delete()
        delete_ids = [_.id for _ in to_be_archived_jobs]
        print 'deleting...', delete_ids
        #Job.objects.filter(id__in=delete_ids).delete()


def remove_old_jobs(remove_jobs_before_days=30, resched_hours=8):
    """Remove old jobs start from these conditions

    Removal date for jobs is `remove_jobs_before_days` days earlier
    than when this is executed.

    It will delete jobs and groups that meet the following:
    - Jobs execute before the removal date and which are not in any group.
    - Groups (and their jobs) where all jobs have executed before the removal
        date.
    """
    start_remove_jobs_before_dt = _get_now() - timedelta(
        days=remove_jobs_before_days)

    # Jobs not in a group that are old enough to delete
    rm_job = (Q(executed__isnull=False) &
        Q(executed__lt=start_remove_jobs_before_dt)) | \
             (Q(cancelled__isnull=False) &
        Q(cancelled__lt=start_remove_jobs_before_dt))
    Job.objects.filter(Q(group__isnull=True), rm_job).delete()

    # Groups with all executed jobs -- look for groups that qualify
    groups = Group.objects.filter(Q(jobs__executed__isnull=False) |
                                  Q(jobs__cancelled__isnull=False))
    for group in groups.iterator():
        if group.jobs.filter(rm_job).count() == group.jobs.all().count():
            group.jobs.filter(rm_job).delete()
            group.delete()

    next_exec = _get_now() + timedelta(hours=resched_hours)

    schedule(remove_old_jobs,
        args=[remove_jobs_before_days, resched_hours],
        run_after=next_exec)
