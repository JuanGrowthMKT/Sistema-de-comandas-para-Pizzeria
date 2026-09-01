from django import template

register = template.Library()


@register.filter
def guarani(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = 0
    return "{:,}".format(n).replace(",", ".")