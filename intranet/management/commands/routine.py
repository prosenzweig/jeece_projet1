from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture,Lesson,Stats,Eleve,Adhesion

from datetime import datetime,timedelta,date
from django.core.mail import send_mail
from django.template.loader import render_to_string

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["janvier", u"février", "mars", "avril", "mai", "juin", "juillet", u"août", "septembre", "octobre","novembre","décembre"]

# Lancement Automatique de auto_val_prof

def conv_mois(value):
    try:
        m =value.split('_')
        return '%s %s' % (mois[int(m[0])-1], m[1])
    except ValueError:
        return None


def check():
    adhesions = Adhesion.objects.all()
    for adhesion in adhesions:
        diff = adhesion.end - timezone.now()
        # print(diff.days)
        if diff.days < 1:
            adhesion.to_user.userprofile.is_adherent = False
            adhesion.to_user.userprofile.save()
            adhesion.delete()

class Command(BaseCommand):
    def handle(self, **options):
        check()