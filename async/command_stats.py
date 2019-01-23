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
        metric = "django_async.{},host={},transaction_type={}".format(
            self.command, self.get_machine_host(), transaction_type
        )
        ms = (self.end_time - self.start_time) * 1000
        statsd.timing(metric, ms)

    def _stats(self, success=True):
        self.end_time = time.time()
        metric = "django_async.{},host={},success={}".format(
            self.command, self.get_machine_host(), success)
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

        show_traceback = options.get('traceback', False)

        # Switch to English, because django-admin.py creates database content
        # like permissions, and those shouldn't contain any translations.
        # But only do this if we can assume we have a working settings file,
        # because django.utils.translation requires settings.
        saved_lang = None
        if self.can_import_settings:
            try:
                from django.utils import translation
                saved_lang = translation.get_language()
                translation.activate('en-us')
            except ImportError, e:
                # If settings should be available, but aren't,
                # raise the error and quit.
                if show_traceback:
                    traceback.print_exc()
                else:
                    sys.stderr.write(smart_str(
                        self.style.ERROR('Error: %s\n' % e)))
                sys.exit(1)

        try:
            self.stdout = options.get('stdout', sys.stdout)
            self.stderr = options.get('stderr', sys.stderr)
            if self.requires_model_validation:
                self.validate()
            output = self.handle(*args, **options)
            if output:
                if self.output_transaction:
                    # This needs to be imported here, because it relies on
                    # settings.
                    from django.db import connections, DEFAULT_DB_ALIAS
                    connection = connections[options.get(
                        'database', DEFAULT_DB_ALIAS)]
                    if connection.ops.start_transaction_sql():
                        self.stdout.write(
                            self.style.SQL_KEYWORD(
                                connection.ops.start_transaction_sql()
                            ) + '\n'
                        )
                self.stdout.write(output)
                if self.output_transaction:
                    self.stdout.write(
                        '\n' + self.style.SQL_KEYWORD("COMMIT;") + '\n')
            self._stats()
        except CommandError, e:
            if show_traceback:
                traceback.print_exc()
            else:
                self.stderr.write(
                    smart_str(self.style.ERROR('Error: %s\n' % e)))
            self._stats(success=False)
            sys.exit(1)
        if saved_lang is not None:
            translation.activate(saved_lang)

def push_statsd(func):
    # This function is what we "replace" hello with
    def wrapper(function, *args, **kwargs):
        sbc = StatBaseCommand()
        sbc.command = function
        job = func(function, *args, **kwargs)
        sbc._schedule_deschedule_stats(func.func_name)
        return job
    return wrapper
