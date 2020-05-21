from django.conf import settings
from openwisp_notifications.types import register_notification_type

AUTO_GRAPHS = getattr(
    settings,
    'OPENWISP_MONITORING_AUTO_GRAPHS',
    ('traffic', 'wifi_clients', 'uptime', 'packet_loss', 'rtt',),
)

register_notification_type(
    'threshold crossed',
    {
        'name': 'Monitoring Alert',
        'verb': 'crossed threshold limit',
        'level': 'warning',
        'email_subject': '[{site}] {notification.level} - {notification.target} has {notification.verb}',
        'message': 'Metric {notification.data[metric]} {notification.verb} {notification.data[info]}',
    },
)

register_notification_type(
    'under threshold',
    {
        'name': 'Monitoring Alert',
        'verb': 'returned within threshold limit',
        'level': 'info',
        'email_subject': '[{site}] {notification.level} - {notification.target} has {notification.verb}',
        'message': 'Metric {notification.data[metric]} {notification.verb}',
    },
)
