
from django import template

register = template.Library()


@register.filter(name="lines")
def lines(value):
    """
    Split a text into non-empty lines for templating bullets.
    Usage: {% for l in text|lines %}
    """
    if not value:
        return []
    if not isinstance(value, str):
        value = str(value)
    return [l for l in value.splitlines() if l.strip()]

