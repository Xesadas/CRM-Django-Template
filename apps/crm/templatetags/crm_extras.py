from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Retorna um valor de um dicionário pela chave"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def next(list_obj, index):
    """Retorna o próximo item de uma lista"""
    try:
        index = int(index)
        if index + 1 < len(list_obj):
            return list_obj[index + 1]
        return ''
    except (ValueError, IndexError, TypeError):
        return ''

@register.filter
def mul(value, arg):
    """Multiplica o valor pelo argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide o valor pelo argumento"""
    try:
        if float(arg) != 0:
            return float(value) / float(arg)
        return 0
    except (ValueError, TypeError):
        return 0

@register.filter
def filter_by_etapa(queryset, etapa):
    """Filtra um queryset pela etapa"""
    if hasattr(queryset, 'filter'):
        return queryset.filter(etapa=etapa)
    return [item for item in queryset if getattr(item, 'etapa', None) == etapa]

@register.filter
def stringformat(value, format_spec):
    """Formata um valor como string"""
    try:
        if format_spec == "i":
            return str(int(value))
        return str(value)
    except (ValueError, TypeError):
        return str(value)