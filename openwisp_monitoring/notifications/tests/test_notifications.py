from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from swapper import load_model

from openwisp_controller.config.models import Config, Device
from openwisp_controller.config.tests import CreateConfigTemplateMixin
from openwisp_users.models import OrganizationUser

from ...monitoring.tests import TestMonitoringMixin

Notification = load_model('openwisp_notifications', 'Notification')
notification_queryset = Notification.objects.order_by('timestamp')
start_time = timezone.now()
ten_minutes_ago = start_time - timedelta(minutes=10)


class TestNotifications(CreateConfigTemplateMixin, TestMonitoringMixin, TestCase):
    device_model = Device
    config_model = Config

    def test_general_check_threshold_crossed_immediate(self):
        admin = self._create_admin()
        m = self._create_general_metric(name='load')
        self._create_threshold(metric=m, operator='>', value=90, seconds=0)

        with self.subTest("Test notification for metric exceeding threshold"):
            m.write(99)
            self.assertFalse(m.is_healthy)
            self.assertEqual(Notification.objects.count(), 1)
            n = notification_queryset.first()
            self.assertEqual(n.recipient, admin)
            self.assertEqual(n.actor, m)
            self.assertEqual(n.action_object, m.threshold)
            self.assertEqual(n.level, 'warning')

        with self.subTest("Test no double alarm for metric exceeding threshold"):
            m.write(95)
            self.assertFalse(m.is_healthy)
            self.assertEqual(Notification.objects.count(), 1)

        with self.subTest("Test notification for metric falling behind threshold"):
            m.write(60)
            self.assertTrue(m.is_healthy)
            self.assertEqual(Notification.objects.count(), 2)
            n = notification_queryset.last()
            self.assertEqual(n.recipient, admin)
            self.assertEqual(n.actor, m)
            self.assertEqual(n.action_object, m.threshold)
            self.assertEqual(n.level, 'info')

        with self.subTest("Test no double alarm for metric falling behind threshold"):
            m.write(40)
            self.assertTrue(m.is_healthy)
            self.assertEqual(Notification.objects.count(), 2)

    def test_general_check_threshold_crossed_deferred(self):
        admin = self._create_admin()
        m = self._create_general_metric(name='load')
        self._create_threshold(metric=m, operator='>', value=90, seconds=60)
        m.write(99, time=ten_minutes_ago)
        self.assertFalse(m.is_healthy)
        self.assertEqual(Notification.objects.count(), 1)
        n = notification_queryset.first()
        self.assertEqual(n.recipient, admin)
        self.assertEqual(n.actor, m)
        self.assertEqual(n.action_object, m.threshold)
        self.assertEqual(n.level, 'warning')

    def test_general_check_threshold_deferred_not_crossed(self):
        self._create_admin()
        m = self._create_general_metric(name='load')
        self._create_threshold(metric=m, operator='>', value=90, seconds=60)
        m.write(99)
        self.assertTrue(m.is_healthy)
        self.assertEqual(Notification.objects.count(), 0)

    def test_general_check_threshold_crossed_for_long_time(self):
        """
        this is going to be the most realistic scenario:
        incoming metrics will always be stored with the current
        timestamp, which means the system must be able to look
        back in previous measurements to see if the threshold
        has been crossed for long enough
        """
        admin = self._create_admin()
        m = self._create_general_metric(name='load')
        self._create_threshold(metric=m, operator='>', value=90, seconds=61)

        with self.subTest("Test no notification is generated for healthy status"):
            m.write(89, time=ten_minutes_ago)
            self.assertTrue(m.is_healthy)
            self.assertEqual(Notification.objects.count(), 0)

        with self.subTest("Test no notification is generated when check=False"):
            m.write(91, time=ten_minutes_ago, check=False)
            self.assertEqual(Notification.objects.count(), 0)

        with self.subTest("Test notification for metric with current timestamp"):
            m.write(92)
            self.assertFalse(m.is_healthy)
            self.assertEqual(Notification.objects.count(), 1)
            n = notification_queryset.first()
            self.assertEqual(n.recipient, admin)
            self.assertEqual(n.actor, m)
            self.assertEqual(n.action_object, m.threshold)
            self.assertEqual(n.level, 'warning')

    def test_object_check_threshold_crossed_immediate(self):
        admin = self._create_admin()
        om = self._create_object_metric(name='load')
        t = self._create_threshold(metric=om, operator='>', value=90, seconds=0)

        with self.subTest("Test notification for object metric exceeding threshold"):
            om.write(99)
            self.assertFalse(om.is_healthy)
            self.assertEqual(Notification.objects.count(), 1)
            n = notification_queryset.first()
            self.assertEqual(n.recipient, admin)
            self.assertEqual(n.actor, om)
            self.assertEqual(n.action_object, t)
            self.assertEqual(n.target, om.content_object)
            self.assertEqual(n.level, 'warning')

        with self.subTest("Test no double alarm for object metric exceeding threshold"):
            om.write(95)
            self.assertFalse(om.is_healthy)
            self.assertEqual(Notification.objects.count(), 1)

        with self.subTest(
            "Test notification for object metric falling behind threshold"
        ):
            om.write(60)
            self.assertTrue(om.is_healthy)
            self.assertEqual(Notification.objects.count(), 2)
            n = notification_queryset.last()
            self.assertEqual(n.recipient, admin)
            self.assertEqual(n.actor, om)
            self.assertEqual(n.action_object, t)
            self.assertEqual(n.target, om.content_object)
            self.assertEqual(n.level, 'info')

        with self.subTest(
            "Test no double alarm for object metric falling behind threshold"
        ):
            om.write(40)
            self.assertTrue(om.is_healthy)
            self.assertEqual(Notification.objects.count(), 2)

    def test_object_check_threshold_crossed_deferred(self):
        admin = self._create_admin()
        om = self._create_object_metric(name='load')
        t = self._create_threshold(metric=om, operator='>', value=90, seconds=60)
        om.write(99, time=ten_minutes_ago)
        self.assertFalse(om.is_healthy)
        self.assertEqual(Notification.objects.count(), 1)
        n = notification_queryset.first()
        self.assertEqual(n.recipient, admin)
        self.assertEqual(n.actor, om)
        self.assertEqual(n.action_object, t)
        self.assertEqual(n.target, om.content_object)
        self.assertEqual(n.level, 'warning')

    def test_object_check_threshold_deferred_not_crossed(self):
        self._create_admin()
        om = self._create_object_metric(name='load')
        self._create_threshold(metric=om, operator='>', value=90, seconds=60)
        om.write(99)
        self.assertTrue(om.is_healthy)
        self.assertEqual(Notification.objects.count(), 0)

    def test_object_check_threshold_crossed_for_long_time(self):
        admin = self._create_admin()
        om = self._create_object_metric(name='load')
        t = self._create_threshold(metric=om, operator='>', value=90, seconds=61)
        om.write(89, time=ten_minutes_ago)
        self.assertEqual(Notification.objects.count(), 0)
        om.write(91, time=ten_minutes_ago, check=False)
        self.assertEqual(Notification.objects.count(), 0)
        om.write(92)
        self.assertFalse(om.is_healthy)
        self.assertEqual(Notification.objects.count(), 1)
        n = notification_queryset.first()
        self.assertEqual(n.recipient, admin)
        self.assertEqual(n.actor, om)
        self.assertEqual(n.action_object, t)
        self.assertEqual(n.target, om.content_object)
        self.assertEqual(n.level, 'warning')
        # ensure double alarm not sent
        om.write(95)
        self.assertFalse(om.is_healthy)
        self.assertEqual(Notification.objects.count(), 1)
        # threshold back to normal
        om.write(60)
        self.assertTrue(om.is_healthy)
        self.assertEqual(Notification.objects.count(), 2)
        n = notification_queryset.last()
        self.assertEqual(n.recipient, admin)
        self.assertEqual(n.actor, om)
        self.assertEqual(n.action_object, t)
        self.assertEqual(n.target, om.content_object)
        self.assertEqual(n.level, 'info')
        # ensure double alarm not sent
        om.write(40)
        self.assertTrue(om.is_healthy)
        self.assertEqual(Notification.objects.count(), 2)

    def test_general_metric_multiple_notifications(self):
        testorg = self._create_org()
        admin = self._create_admin()
        staff = self._create_user(
            username='staff', email='staff@staff.com', password='staff', is_staff=True
        )
        self._create_user(
            username='staff-lone',
            email='staff-lone@staff.com',
            password='staff',
            is_staff=True,
        )
        user = self._create_user(is_staff=False)
        OrganizationUser.objects.create(user=user, organization=testorg)
        OrganizationUser.objects.create(user=staff, organization=testorg)
        self.assertIsNotNone(staff.notificationuser)
        m = self._create_general_metric(name='load')
        t = self._create_threshold(metric=m, operator='>', value=90, seconds=61)
        m._notify_users(notification_type='default', threshold=t)
        self.assertEqual(Notification.objects.count(), 1)
        n = notification_queryset.first()
        self.assertEqual(n.recipient, admin)
        self.assertEqual(n.actor, m)
        self.assertEqual(n.target, None)
        self.assertEqual(n.action_object, m.threshold)
        self.assertEqual(n.level, 'info')
        self.assertEqual(n.verb, 'default verb')
        self.assertIn(
            'Default notification with default verb and level info', n.message
        )

    def test_object_metric_multiple_notifications(self):
        testorg = self._create_org()
        admin = self._create_admin()
        staff = self._create_user(
            username='staff', email='staff@staff.com', password='staff', is_staff=True
        )
        self._create_user(
            username='staff-lone',
            email='staff-lone@staff.com',
            password='staff',
            is_staff=True,
        )
        user = self._create_user(is_staff=False)
        OrganizationUser.objects.create(user=user, organization=testorg)
        OrganizationUser.objects.create(user=staff, organization=testorg)
        self.assertIsNotNone(staff.notificationuser)
        d = self._create_device(organization=testorg)
        om = self._create_object_metric(name='load', content_object=d)
        t = self._create_threshold(metric=om, operator='>', value=90, seconds=61)
        om._notify_users(notification_type='default', threshold=t)
        self.assertEqual(Notification.objects.count(), 2)
        n = notification_queryset.first()
        self.assertEqual(n.recipient, admin)
        self.assertEqual(n.actor, om)
        self.assertEqual(n.target, d)
        self.assertEqual(n.action_object, om.threshold)
        self.assertEqual(n.level, 'info')
        self.assertEqual(n.verb, 'default verb')
        self.assertIn(
            'Default notification with default verb and level info', n.message,
        )
        n = notification_queryset.last()
        self.assertEqual(n.recipient, staff)
        self.assertEqual(n.actor, om)
        self.assertEqual(n.target, d)
        self.assertEqual(n.action_object, om.threshold)
        self.assertEqual(n.level, 'info')
        self.assertEqual(n.verb, 'default verb')

    def test_object_metric_multiple_notifications_no_org(self):
        testorg = self._create_org()
        admin = self._create_admin()
        staff = self._create_user(
            username='staff', email='staff@staff.com', password='staff', is_staff=True
        )
        self._create_user(
            username='staff-lone',
            email='staff-lone@staff.com',
            password='staff',
            is_staff=True,
            first_name="'staff-lone'",
        )
        user = self._create_user(is_staff=False)
        OrganizationUser.objects.create(user=user, organization=testorg)
        OrganizationUser.objects.create(user=staff, organization=testorg)
        self.assertIsNotNone(staff.notificationuser)
        om = self._create_object_metric(name='logins', content_object=user)
        t = self._create_threshold(metric=om, operator='>', value=90, seconds=0)
        om._notify_users(notification_type='default', threshold=t)
        self.assertEqual(Notification.objects.count(), 1)
        n = notification_queryset.first()
        self.assertEqual(n.recipient, admin)
        self.assertEqual(n.actor, om)
        self.assertEqual(n.target, user)
        self.assertEqual(n.action_object, om.threshold)
        self.assertEqual(n.level, 'info')
        self.assertEqual(n.verb, 'default verb')

    def test_notification_types(self):
        self._create_admin()
        m = self._create_general_metric(name='load')
        self._create_threshold(metric=m, operator='>', value=90, seconds=0)

        with self.subTest("Test notification for 'threshold crossed'"):
            m.write(99)
            n = notification_queryset.first()
            self.assertEqual(n.level, 'warning')
            self.assertEqual(n.verb, 'crossed threshold limit')
            self.assertEqual(
                n.email_subject,
                '[example.com] warning - None has crossed threshold limit',
            )
            self.assertIn(
                'Metric Load crossed threshold limit (greater than 90.0)', n.message
            )

        with self.subTest("Test notification for 'under threshold'"):
            m.write(80)
            n = notification_queryset.last()
            self.assertEqual(n.level, 'info')
            self.assertEqual(n.verb, 'returned within threshold limit')
            self.assertEqual(
                n.email_subject,
                '[example.com] info - None has returned within threshold limit',
            )
            self.assertIn('Metric Load returned within threshold limit', n.message)

    def test_notification_message(self):
        self._create_admin()
        om = self._create_object_metric(name='load')
        self._create_threshold(metric=om, operator='>', value=90)
        target = self._get_user()

        with self.subTest("Test for metric exceeding threshold"):
            om.write(99)
            n = notification_queryset.first()
            exp_message = (
                '<p>warning : tester crossed threshold limit </p>\n'
                '<p>Metric Load (user: tester) crossed threshold limit (greater than 90.0)\n'
                f' Related : \n <a href="/admin/openwisp_users/user/{target.id}/change/">tester</a></p>'
            )
            self.assertEqual(n.message, exp_message)

        with self.subTest("Test for metric falling behind threshold"):
            om.write(70)
            n = notification_queryset.last()
            exp_message = (
                '<p>info : tester returned within threshold limit </p>\n'
                '<p>Metric Load (user: tester) returned within threshold limit \n'
                f' Related : \n <a href="/admin/openwisp_users/user/{target.id}/change/">tester</a></p>'
            )
            self.assertEqual(n.message, exp_message)
