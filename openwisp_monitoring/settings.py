from django.conf import settings
from openwisp_notifications.notification_types import register_notification_type

AUTO_GRAPHS = getattr(
    settings,
    'OPENWISP_MONITORING_AUTO_GRAPHS',
    ('traffic', 'wifi_clients', 'uptime', 'packet_loss', 'rtt',),
)

MONITORING_NOTIFICATION_TYPES = {
    'threshold crossed': {
        'name': 'Monitoring Alert',
        'verb': 'crossed threshold limit',
        'level': 'warning',
    },
    'under threshold': {
        'name': 'Monitoring Alert',
        'verb': 'returned within threshold limit',
        'level': 'info',
    },
}
register_notification_type(MONITORING_NOTIFICATION_TYPES)
setattr(
    settings,
    'OPENWISP_NOTIFICATION_MESSAGE_TEMPLATE',
    getattr(settings, 'OPENWISP_NOTIFICATION_MESSAGE_TEMPLATE', 'configurables/mes'),
)
