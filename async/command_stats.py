import sys
import traceback
import time
import socket
from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import smart_str
from statsd.defaults.django import statsd


class StatBaseCommand(BaseCommand):

    def __init__(self):
        self.start_time = time.time()
        super(StatBaseCommand, self).__init__()

    def get_machine_host(self):
        try:
            return socket.getfqdn()
        except Exception:
            return socket.gethostbyname(socket.gethostname())

    def _schedule_deschedule_stats(self, transaction_type):
        self.end_time = time.time()
        metric = "django_async_scheduling_{},host={},transaction_type={}".format(
            self.command, self.get_machine_host(), transaction_type
        )
        ms = (self.end_time - self.start_time) * 1000
        statsd.timing(metric, ms)

    def _stats(self, success=True, stats_type="run"):
        self.end_time = time.time()
        metric = "django_async_{}.{},host={},success={}".format(
            stats_type, self.command, self.get_machine_host(), success)
        ms = (self.end_time - self.start_time) * 1000
        statsd.timing(metric, ms)

    def run_from_argv(self, argv):
        """
        Just getting command name
        """
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        self.command = options.filter
        super(StatBaseCommand, self).run_from_argv(argv)

    def execute(self, *args, **options):
        """
        Try to execute this command, performing model validation if
        needed (as controlled by the attribute
        ``self.requires_model_validation``). If the command raises a
        ``CommandError``, intercept it and print it sensibly to
        stderr.
        """
        try:
            super(StatBaseCommand, self).execute(*args, **options)
            self._stats()
        except Exception:
            self._stats(success=False)

def push_statsd(func):
    # This function is what we "replace" hello with
    def wrapper(function, *args, **kwargs):
        sbc = StatBaseCommand()
        sbc.command = function
        job = func(function, *args, **kwargs)
        sbc._schedule_deschedule_stats(func.func_name)
        return job
    return wrapper
