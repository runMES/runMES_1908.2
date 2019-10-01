from django import template
from django.contrib.auth.models import Group, User

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
  try:
    g_set=user.groups.all().values_list('name',flat=True)
    if group_name in g_set:
      return True
    else:
      return False
  except Group.DoesNotExist:
    return False

@register.filter(name='group_list')
def group_list(user):
  try:
    g_set=user.groups.all().values_list('name',flat=True)
    groups=[]
    for g in g_set:
      groups.append(g)

    return groups
  except Group.DoesNotExist:
    return None