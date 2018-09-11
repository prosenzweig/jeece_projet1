from django import template

register = template.Library()

@register.filter
def divide(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def tva(value, arg):
    try:
        return float(value) + float(value)*float(arg)/100
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def mois(value):
    liste_mois = ["Janvier", u"Février", "Mars", "Avril", "Mai", "Juin", "Juillet", u"Août", "Septembtre", "Octobre"]
    try:
        m =value.split('_')
        return '%s %s' % (liste_mois[int(m[0])-1], m[1])
    except ValueError:
        return None

@register.filter
def stripe(value):
    try:
        return int(value)*100
    except (ValueError, ZeroDivisionError):
        return None