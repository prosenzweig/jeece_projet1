from django.core.management.base import BaseCommand
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture,Lesson,Attestation
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from datetime import datetime,date
from decimal import Decimal


### CRONTAB ###
# 0 0 1 1 * cd /home/ecole01/intranet && /home/ecole01/venv/bin/python manage.py auto_attest > /home/ecole01/logs/cron.log

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["janvier", u"février", "mars", "avril", "mai", "juin", "juillet", u"août", "septembre", "octobre","novembre","décembre"]


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

def auto_attest():
    prix = Prix.objects.get(end=None)
    admin = User.objects.get(is_superuser=True)
    last_year = datetime.now().year-1
    # last_year = datetime.now().year # TODO ROSEN

    print("")
    print("Création des Attestattions :")

    referent = User.objects.exclude(is_staff=True,is_active=True)
    # print("ref", referent)
    profs = User.objects.filter(is_staff=True,is_active=True).exclude(is_superuser=True)
    # print("profs", profs)
    start = date(last_year, 1, 1)
    end = date(last_year, 12, 31)
    print("%s - %s" % (start,end))

    for user in referent:
        for prof in profs:
            facs = Facture.objects.filter(from_user=prof,to_user=user,created__gte=start,created__lte=end,is_paid=True)
            if facs.count() > 0:
                print("")
                print("%s - %s nbr: %s" % (prof, user, facs.count()))
                sums_tt = sum(f.price_ht for f in facs)
                sums_h = sum(f.h_qt for f in facs)
                print("sums_tt %s sums_h %s" % (sums_tt,sums_h))
                Attestation.objects.create(
                    to_user=user, from_user=prof,price=sums_tt, nb_cours=sums_h, h_qt=sums_h, nb_adh=prof.userprofile.nb_adh,
                    to_user_firstname=user.first_name, to_user_lastname=user.last_name,
                    to_user_address=user.userprofile.address,
                    to_user_city=user.userprofile.city, to_user_zipcode=user.userprofile.zip_code,
                    to_user_siret=user.userprofile.siret, to_user_sap=user.userprofile.sap,
                    from_user_firstname=prof.first_name, from_user_lastname=prof.last_name,
                    from_user_address=prof.userprofile.address, from_user_city=prof.userprofile.city,
                    from_user_zipcode=prof.userprofile.zip_code, from_user_siret=prof.userprofile.siret,
                    from_user_sap=prof.userprofile.sap,admin_address=admin.userprofile.address,
                    admin_zipcode=admin.userprofile.zip_code, admin_city=admin.userprofile.city)
                prof.userprofile.nb_adh += 1
                prof.userprofile.save()



class Command(BaseCommand):
    def handle(self, **options):
        auto_attest()