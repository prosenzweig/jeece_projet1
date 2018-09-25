from django.core.management.base import BaseCommand
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture,Lesson
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from datetime import datetime
from decimal import Decimal

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["Janvier", u"Février", "Mars", "Avril", "Mai", "Juin", "Juillet", u"Août", "Septembtre", "Octobre"]

### CRONTAB ###
# 50 23 5 * * cd /home/ecole01/intranet && /home/ecole01/venv/bin/python manage.py auto_val_eleve > /home/ecole01/logs/cron.log


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
        return round(float(value)+float(value)*float(arg)/100,2)
    except (ValueError, ZeroDivisionError):
        return None


def auto_val_eleve():
    last_m_y = give_past_month()
    relation_all = Relation.objects.all()
    prix = Prix.objects.get(end=None)
    admin = User.objects.get(is_superuser=True)

    for relation in relation_all:
        # MAJ des validation Eleve
        # print(relation)
        cours_du_mois_unvalid = Lesson.objects.filter(relation=relation,mois=last_m_y,is_valid_t=True,is_valid_s=False).exclude(is_unvalid=True)
        # print("Cours non validé", cours_du_mois_unvalid)
        for cour in cours_du_mois_unvalid:
            print('id:', cour.id)
            cour.is_valid_s = True
            cour.save()

        # Generation des factures
        cours_list = Lesson.objects.filter(relation=relation,mois=last_m_y,is_valid_t=True,is_valid_s=True,is_unvalid=False)

        if cours_list:
            nb_cours = len(cours_list)
            nbr_h = sum(cour.nb_h for cour in cours_list)
            nbr_m = sum(cour.nb_m for cour in cours_list)
            nbr_tt = round((nbr_h*60+nbr_m)/60, 2)
            print("tth: %s, ttm: %s, TT %s" % (nbr_h,nbr_m,nbr_tt))

            student = relation.student
            teacher = relation.teacher

            # Cours de piano Ecole
            if teacher == admin:
                price = prix.cours_ecole
                fac_name = "EFP_%s_%s" % (student.last_name, teacher.userprofile.nb_facture)
                print(fac_name, price, nb_cours, nbr_tt)
                Facture.objects.create(
                    to_user=student, from_user=teacher, object="Cours de Piano - 60min", is_paid=False,
                    object_qt=nb_cours, h_qt=nbr_tt, tva=prix.tva, price_ht=price * nbr_tt, price_ttc=add_tva(price*nbr_tt,prix.tva), type="Cours de Piano Ecole",
                    facture_name=fac_name, nb_facture=teacher.userprofile.nb_facture,
                    to_user_firstname=student.first_name, to_user_lastname=student.last_name,
                    to_user_address=student.userprofile.address,
                    to_user_city=student.userprofile.city, to_user_zipcode=student.userprofile.zip_code,
                    to_user_siret=student.userprofile.siret, to_user_sap=student.userprofile.sap,
                    from_user_firstname=teacher.first_name, from_user_lastname=teacher.last_name,
                    from_user_address=teacher.userprofile.address, from_user_city=teacher.userprofile.city,
                    from_user_zipcode=teacher.userprofile.zip_code, from_user_siret=teacher.userprofile.siret,
                    from_user_sap=teacher.userprofile.sap)
            # Cours de Piano Classique
            else:
                price = prix.cours_premium if student.userprofile.is_premium else prix.cours
                fac_name = "%s_%s_%s" % (teacher.last_name, student.last_name, teacher.userprofile.nb_facture)
                print(fac_name, price, nb_cours, nbr_tt)
                Facture.objects.create(
                    to_user=student, from_user=teacher, object="Cours de Piano - 60min", is_paid=False,
                    object_qt=nb_cours, h_qt=nbr_tt, tva=0, price_ht=price*nbr_tt, price_ttc=price*nbr_tt, type="Cours de Piano",
                    facture_name=fac_name, nb_facture=teacher.userprofile.nb_facture,
                    to_user_firstname=student.first_name, to_user_lastname=student.last_name,
                    to_user_address=student.userprofile.address,
                    to_user_city=student.userprofile.city, to_user_zipcode=student.userprofile.zip_code,
                    to_user_siret=student.userprofile.siret, to_user_sap=student.userprofile.sap,
                    from_user_firstname=teacher.first_name, from_user_lastname=teacher.last_name,
                    from_user_address=teacher.userprofile.address, from_user_city=teacher.userprofile.city,
                    from_user_zipcode=teacher.userprofile.zip_code, from_user_siret=teacher.userprofile.siret,
                    from_user_sap=teacher.userprofile.sap)

            teacher.userprofile.nb_facture += 1
            teacher.userprofile.save()

            Notification.objects.create(to_user=student, from_user=teacher,
                                            object="Factures Cours de Piano %s" % conv_mois(last_m_y),
                                            text="Votre facture est téléchargeable dans la section \"Mes documents\".")
            if teacher != admin:
                # Frais de Gestion (de l'admin vers les élèves)
                Facture.objects.create(
                    to_user=student, from_user=admin, object="Frais de gestion - 60 min", is_paid=False,
                    object_qt=nb_cours, h_qt=nbr_tt, tva=prix.tva, price_ht=prix.frais_gestion, price_ttc=add_tva(prix.frais_gestion*nbr_tt,prix.tva), type="Frais de Gestion",
                    facture_name=fac_name, nb_facture=teacher.userprofile.nb_facture,
                    to_user_firstname=student.first_name, to_user_lastname=student.last_name,
                    to_user_address=student.userprofile.address,
                    to_user_city=student.userprofile.city, to_user_zipcode=student.userprofile.zip_code,
                    to_user_siret=student.userprofile.siret, to_user_sap=student.userprofile.sap,
                    from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
                    from_user_address=admin.userprofile.address, from_user_city=admin.userprofile.city,
                    from_user_zipcode=admin.userprofile.zip_code, from_user_siret=admin.userprofile.siret,
                    from_user_sap=admin.userprofile.sap)

                admin.userprofile.nb_facture += 1
                admin.userprofile.save()

                Notification.objects.create(to_user=student, from_user=admin,
                                            object="Factures Frais de Gestion %s" % conv_mois(last_m_y),
                                            text="Votre facture est téléchargeable dans la section \"Mes documents\".")

def factures_commissions():
    last_m_y = give_past_month()
    prof_all = User.objects.filter(is_active=True,is_staff=True,is_superuser=False)
    prix = Prix.objects.get(end=None)
    admin = User.objects.get(is_superuser=True)

    for prof in prof_all:
        lessons_by_prof = Lesson.objects.filter(relation__teacher=prof, mois=last_m_y, is_valid_t=True, is_valid_s=True, is_unvalid=False)
        nb_cours = len(lessons_by_prof)
        nbr_h = sum(cour.nb_h for cour in lessons_by_prof)
        nbr_m = sum(cour.nb_m for cour in lessons_by_prof)
        nbr_tt = round((nbr_h * 60 + nbr_m) / 60, 2)
        print("%s\ttth: %s, ttm: %s, TT %s" % (prof,nbr_h, nbr_m, nbr_tt))

        # Frais de Commission de l'admin vers les profs
        Facture.objects.create(
            to_user=prof, from_user=admin, object="Frais de Commission - 60min", is_paid=False,
            object_qt=nb_cours, h_qt=nbr_tt, tva=prix.tva, price_ht=prix.commission * nbr_tt,
            price_ttc=add_tva(prix.commission * nbr_tt, prix.tva), type="Frais de Commission",
            facture_name=admin, nb_facture=admin.userprofile.nb_facture,
            to_user_firstname=prof.first_name, to_user_lastname=prof.last_name,
            to_user_address=prof.userprofile.address,
            to_user_city=prof.userprofile.city, to_user_zipcode=prof.userprofile.zip_code,
            to_user_siret=prof.userprofile.siret, to_user_sap=prof.userprofile.sap,
            from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
            from_user_address=admin.userprofile.address, from_user_city=admin.userprofile.city,
            from_user_zipcode=admin.userprofile.zip_code, from_user_siret=admin.userprofile.siret,
            from_user_sap=admin.userprofile.sap)

        admin.userprofile.nb_facture += 1
        admin.userprofile.save()

        Notification.objects.create(to_user=prof, from_user=admin,
                                    object="Factures Frais de Commission %s" % conv_mois(last_m_y),
                                    text="Votre facture est téléchargeable dans la section \"Mes documents\".")

class Command(BaseCommand):
    def handle(self, **options):
        auto_val_eleve()
        factures_commissions()