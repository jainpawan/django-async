"""
    Testing that models work properly.
"""
import datetime

from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
try:
    # No name 'timezone' in module 'django.utils'
    # pylint: disable=E0611
    from django.utils import timezone
except ImportError:
    from datetime import datetime as timezone

from async import schedule
from async.models import Error, Job, Group

def _fn(*_a, **_kw):
    """Test function.
    """
    pass


class TestJob(TransactionTestCase):
    """Make sure the basic model features work properly.
    """
    def test_model_creation(self):
        """Make sure schedule API works.
        """
        job = schedule('async.tests.test_models._fn')
        self.assertEqual(Job.objects.all().count(), 1)
        self.assertEqual(unicode(job), "async.tests.test_models._fn()")
        self.assertEqual(job.identity,
            '289dbff9c1bd746fc444a20d396986857a6e8f04')

    def test_model_creation_with_no_group(self):
        """Make sure schedule API works with no group.
        """
        job = schedule('async.tests.test_models._fn')
        self.assertEqual(Job.objects.all().count(), 1)
        self.assertEqual(job.group, None)

    def test_model_creattion_with_group(self):
        """make sure schedule API works with group.
        """
        group = Group.objects.create(
            reference='test-group',
            description='for testing'
        )
        job = schedule('async.tests.test_models._fn')
        job.group = group
        job.save()

        self.assertEqual(Job.objects.all().count(), 1)
        self.assertEqual(job.group, group)

    def test_identity(self):
        """Make sure that the identity we get is the same as in another
        test when given the same arguments.
        """
        job = schedule('async.tests.test_models._fn')
        self.assertEqual(job.identity,
            '289dbff9c1bd746fc444a20d396986857a6e8f04')

    def test_unicode_with_args(self):
        """Make sure unicode handling deals with args properly.
        """
        self.assertEqual(unicode(schedule(
                'async.tests.test_models._fn', args=['argument'])),
            "async.tests.test_models._fn('argument')")
        self.assertEqual(unicode(schedule(
                'async.tests.test_models._fn', args=['a1', 'a2'])),
            "async.tests.test_models._fn('a1', 'a2')")
        self.assertEqual(unicode(schedule(
                'async.tests.test_models._fn', args=[1, 2])),
            'async.tests.test_models._fn(1, 2)')
        self.assertEqual(unicode(schedule(
                'async.tests.test_models._fn', args=[dict(k='v', x=None)])),
            "async.tests.test_models._fn({'x': None, 'k': 'v'})")

    def test_unicode_with_kwargs(self):
        """Make sure unicode handling deals with kwargs properly.
        """
        job = schedule('async.tests.test_models._fn',
            kwargs=dict(k='v', x=None))
        self.assertEqual(unicode(job),
            "async.tests.test_models._fn(x=None, k='v')")
        self.assertEqual(job.identity,
            '60941ebcc096c0223ba1db02b3d256f19ba553a3')

    def test_unicode_with_args_and_kwargs(self):
        """Make sure unicode handling deals with kwargs properly.
        """
        job = schedule('async.tests.test_models._fn',
            args=['argument'], kwargs=dict(k='v', x=None))
        self.assertEqual(unicode(job),
            "async.tests.test_models._fn('argument', x=None, k='v')")
        self.assertEqual(job.identity,
            '2ce2bb7935439a6ab3f111882f359a06b36bf995')


class TestError(TestCase):
    """Test the Error model.
    """

    def test_unicode(self):
        """Make sure the that the Unicode form of the Error works.
        """
        job = schedule('async.tests.test_models._fn')
        error = Error.objects.create(job=job, exception="Exception text")
        self.assertTrue(
            unicode(error).endswith(u' : Exception text'), unicode(error))


class TestGroup(TestCase):
    """Test the Group model.
    """
    def setUp(self):
        self.g1 = Group.objects.create(
                reference='group1',
                description='test group1'
            )
        self.j1 = Job.objects.create(
                name='job1',
                args='[]',
                kwargs='{}',
                meta='{}',
                priority=3,
            )

        self.j2 = Job.objects.create(
                name='job2',
                args='[]',
                kwargs='{}',
                meta='{}',
                priority=3,
            )

        self.j3 = Job.objects.create(
                name='job3',
                args='[]',
                kwargs='{}',
                meta='{}',
                priority=3,
            )

    def test_model_creation(self):
        """ Test if can create model. Get new instance.
        """
        group = Group.objects.create(
            reference='test-group',
            description='for testing'
        )

        self.assertTrue(Group.objects.all().count(), 1)
        self.assertEqual(unicode(group), u'test-group')
        self.assertEqual(group.description, 'for testing')

    def test_creating_group_with_duplicate_reference_and_executed_job(self):
        """ Create new group with reference same as old group which has
            one job and already executed. Creating should success.
        """
        self.j1.group = self.g1
        self.j1.executed = timezone.now()
        self.j1.save()

        g2 = Group.objects.create(reference=self.g1.reference)
        self.assertEqual(Group.objects.filter(reference=self.g1.reference).count(), 2)

    def test_creating_group_with_duplicate_reference_and_has_one_unexecuted_job(self):
        """ Create new group with reference same as old group which has
            unexecuted job. Creating should not success.
        """

        # Assiging j1, j2, j3 to group1
        self.j1.group = self.g1
        self.j1.save()

        self.j2.group = self.g1
        self.j2.save()

        self.j3.group = self.g1
        self.j3.save()

        # Mark executed for j1, j2
        self.j1.executed = timezone.now()
        self.j1.save()

        self.j2.executed = timezone.now()
        self.j2.save()

        with self.assertRaises(ValidationError) as e:
            Group.objects.create(reference=self.g1.reference)
        self.assertTrue(isinstance(e.exception, ValidationError))
        self.assertEqual(Group.objects.filter(reference=self.g1.reference).count(), 1)

    def test_adding_job_to_group_that_has_executed_job(self):
        """ Add job to group which have one executed job.
        """
        self.j1.group = self.g1
        self.j1.executed = timezone.now()
        self.j1.save()

        with self.assertRaises(ValidationError) as e:
            self.j2.group = self.g1
            self.j2.save()
        self.assertTrue(isinstance(e.exception, ValidationError))
        self.assertEqual(Job.objects.filter(group=self.g1).count(), 1)

    def test_adding_job_to_group_that_has_unexecuted_job(self):
        """ Add jobs to group which has unexecuted job.
        """
        self.j1.group = self.g1
        self.j1.save()

        self.j2.group = self.g1
        self.j2.save()

        self.assertEqual(Group.objects.get(reference=self.g1.reference).jobs.count(), 2)
