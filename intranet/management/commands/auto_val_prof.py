from django.core.management.base import BaseCommand
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture
from datetime import datetime

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["Janvier", u"Février", "Mars", "Avril", "Mai", "Juin", "Juillet", u"Août", "Septembtre", "Octobre"]

def conv_mois(value):
    try:
        m =value.split('_')
        return '%s %s' % (mois[int(m[0])-1], m[1])
    except ValueError:
        return None

def auto_val_prof():
    cours_unvalid = Cour.objects.filter(is_valid_t=False)
    for cour in cours_unvalid:
        cour.is_valid_t = True
        cour.save()
        Notification.objects.create(to_user=cour.relation.student, from_user=cour.relation.teacher,
                                    object="Validation Cours %s" % conv_mois(cour.mois),
                                    text="Vous pouvez désormais valider ou refuser vos cours dans la section 'Mes Cours'!")

class Command(BaseCommand):
    def handle(self, **options):
        auto_val_prof()