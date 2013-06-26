from django import template
from forums.models import *

register = template.Library()

@register.filter
def cut(value, arg):
    """Removes all values of arg from the given string"""
    return value.replace(arg, '')

@register.filter
def lookup_user(value):
    """given a user ID, returns username"""
    user = Users.objects.filter(user_id = value)[0]
    if user: return user.username
    else: return ""
    
