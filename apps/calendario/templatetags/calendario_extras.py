from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter para acessar itens de um dicionário"""
    if dictionary is None:
        return []
    return dictionary.get(key, [])