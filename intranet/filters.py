from django.contrib.auth.models import User
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture,Eleve,\
    Lesson,Attestation,Condition,Adhesion
import django_filters
from django_filters.filters import ChoiceFilter

class FactureFilter(django_filters.FilterSet):
    # to_user = ChoiceFilter(choices=Facture.to_user,label='Destinataire')
    # from_user = ChoiceFilter(label='Emetteur')
    class Meta:
        model = Facture
        fields = ['to_user', 'from_user', 'type', 'last', 'is_paid']
        labels = {
            'to_user': 'Émetteur',
            'from_user': 'Destinataire',
            'type': 'Type',
            'last': 'Echéance',
            'is_paid': 'Payé'
        }