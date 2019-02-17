from django import template
from datetime import datetime
from datetime import timedelta

register = template.Library()

@register.filter
def qt_dec(facture):
    try:
        if facture.type not in ['Adhésion Elève', 'Adhésion Elèves', 'Adhésion Professeur', 'Adhésion élève',
                                'Adhésion élèves', 'Adhésion professeur'] and str(facture.created) > "2018-12-03":
            return facture.h_qt
        else:
            return facture.object_qt
    except (ValueError, ZeroDivisionError):
        return facture.h_qt

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
def live_time(value):
    return value + timedelta(hours=2)

@register.filter
def mois(value):
    liste_mois = ["janvier", u"février", "mars", "avril", "mai", "juin", "juillet", u"août", "septembre", "octobre","novembre","décembre"]
    try:
        m =value.split('_')
        return '%s %s' % (liste_mois[int(m[0])-1], m[1])
    except ValueError:
        return None

@register.filter
def stripe(value):
    try:
        return float(value)*100
    except (ValueError, ZeroDivisionError):
        return None

@register.filter(name='proper_paginate')
def proper_paginate(paginator, current_page, neighbors=10):
    if paginator.num_pages > 2*neighbors:
        start_index = max(1, current_page-neighbors)
        end_index = min(paginator.num_pages, current_page + neighbors)
        if end_index < start_index + 2*neighbors:
            end_index = start_index + 2*neighbors
        elif start_index > end_index - 2*neighbors:
            start_index = end_index - 2*neighbors
        if start_index < 1:
            end_index -= start_index
            start_index = 1
        elif end_index > paginator.num_pages:
            start_index -= (end_index-paginator.num_pages)
            end_index = paginator.num_pages
        page_list = [f for f in range(start_index, end_index+1)]
        return page_list[:(2*neighbors + 1)]
    return paginator.page_range


@register.simple_tag
def url_replace(request, field, value):
    query_string = request.GET.copy()
    query_string[field] = value

    return query_string.urlencode()