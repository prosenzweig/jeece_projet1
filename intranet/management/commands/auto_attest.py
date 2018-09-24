from django.core.management.base import BaseCommand
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture,Lesson,Attestation
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from datetime import datetime
from decimal import Decimal


### CRONTAB ###
# 0 0 1 1 * cd /home/ecole01/intranet && /home/ecole01/venv/bin/python manage.py auto_attest > /home/ecole01/logs/cron.log

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
def auto_attest():
    prix = Prix.objects.get(end=None)
    admin = User.objects.get(is_superuser=True)
    # last_year = datetime.now().year-1
    last_year = datetime.now().year # ICI en TEST
    lst = [ '%s_%s' % (x,last_year) for x in range(1,13)]
    # print(lst)
    relation_all = Relation.objects.all().exclude(teacher=admin)

    for relation in relation_all:
        # print(relation)
        cours_list = Lesson.objects.filter(relation=relation, mois__in=lst, is_valid_t=True, is_valid_s=True, is_unvalid=False)
        # print(cours_list)
        if cours_list:
            nb_cours = len(cours_list)
            nbr_h = sum(cour.nb_h for cour in cours_list)
            nbr_m = sum(cour.nb_m for cour in cours_list)
            nbr_tt = round((nbr_h * 60 + nbr_m) / 60, 2)
            print("tth: %s, ttm: %s, TT %s" % (nbr_h, nbr_m, nbr_tt))

            student = relation.student
            teacher = relation.teacher
            price = prix.cours_premium if student.userprofile.is_premium else prix.cours

            Attestation.objects.create(
                to_user=student, from_user=teacher,price=price * nbr_tt, nb_cours=nbr_tt,
                to_user_firstname=student.first_name, to_user_lastname=student.last_name,
                to_user_address=student.userprofile.address,
                to_user_city=student.userprofile.city, to_user_zipcode=student.userprofile.zip_code,
                to_user_siret=student.userprofile.siret, to_user_sap=student.userprofile.sap,
                from_user_firstname=teacher.first_name, from_user_lastname=teacher.last_name,
                from_user_address=teacher.userprofile.address, from_user_city=teacher.userprofile.city,
                from_user_zipcode=teacher.userprofile.zip_code, from_user_siret=teacher.userprofile.siret,
                from_user_sap=teacher.userprofile.sap)


class Command(BaseCommand):
    def handle(self, **options):
        auto_attest()