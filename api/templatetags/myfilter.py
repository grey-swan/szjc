from django import template

register = template.Library()


@register.filter
def get_time(value):
    if value:
        return value.replace('-', '.')
    else:
        return ''
