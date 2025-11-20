from django import template

register = template.Library()

@register.simple_tag
def increment(var):
    return var + 1