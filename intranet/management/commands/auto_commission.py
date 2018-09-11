from django.core.management.base import BaseCommand
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from datetime import datetime

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["Janvier", u"Février", "Mars", "Avril", "Mai", "Juin", "Juillet", u"Août", "Septembtre", "Octobre"]

def give_past_month():
    m, y = datetime.now().month, datetime.now().year
    if m == 1:
        return "12_%s" % (y-1)
    else:
        return "%s_%s" % (m-1,y)

def conv_mois(value):
    try:
        m =value.split('_')
        return '%s %s' % (mois[int(m[0])-1], m[1])
    except ValueError:
        return None

def add_tva(value,arg):
    try:
        return float(value) + float(value)*float(arg)/100
    except (ValueError, ZeroDivisionError):
        return None


def auto_commission():
    mois = give_past_month()
    admin = User.objects.get(is_superuser=True)
    prix = Prix.objects.get(end=None)
    prof_list = User.objects.filter(is_staff=True).exclude(is_superuser=True)
    for prof in prof_list:
        nb_cours = 0 if not Cour.objects.filter(mois=mois, relation__teacher=prof) else Cour.objects.filter(mois=mois, relation__teacher=prof).aggregate(Sum('duree_cours'))['duree_cours__sum']/60
        print(prof, nb_cours)
        if nb_cours > 0:
            # Frais de Commissions
            Facture.objects.create(to_user=prof, from_user=admin,
                                   object="Frais de commission - 60 min",
                                   object_qt=nb_cours, tva=prix.tva, price_ht=nb_cours * prix.frais_gestion,
                                   price_ttc=add_tva(nb_cours * prix.frais_gestion, prix.tva),
                                   type="Frais de Commission")

            Notification.objects.create(to_user=prof, from_user=admin,
                                        object="Factures Frais de Commission %s" % conv_mois(mois),
                                        text="Votre facture est téléchargeable dans la section \"Mes documents\".")


class Command(BaseCommand):
    def handle(self, **options):
        auto_commission()