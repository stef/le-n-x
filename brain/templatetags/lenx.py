from django.template import Library, Variable
from django.conf import settings
from django import template
import random

register = Library()

@register.simple_tag
def root_url():
    return settings.ROOT_URL

