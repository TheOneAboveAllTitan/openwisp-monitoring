{% extends 'openwisp_notifications/default_message.md' %}
{% block body %}
Metric {{notification.data.metric}} {{notification.verb}} {{notification.data.info}}
{% if notification.target %}
Related : 
{% if notification.target_link %} [{{notification.target}}]({{notification.target_link}}) {% else %} {{notification.target}} {% endif %}
{% endif %}
{% endblock body %}
