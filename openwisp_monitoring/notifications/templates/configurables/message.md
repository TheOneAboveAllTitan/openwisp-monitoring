{% extends 'openwisp_notifications:configurables/message.md' %}
{% block head %}Metric {{ metric }} {{ verb }}{{ info }}{% endblock head %}
{% block body %}
{{ actor }} {{ verb }} {% if target %} for {{ target }}.{% endif %}
{% if url %} For more info, see {{ url }}. {% endif %}
{% endblock body %}
