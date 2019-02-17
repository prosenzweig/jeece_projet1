from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture,Lesson,Stats,Eleve
from datetime import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["janvier", u"février", "mars", "avril", "mai", "juin", "juillet", u"août", "septembre", "octobre","novembre","décembre"]

### CRONTAB ###
# 50 23 28-31 * * [ $(date -d +1day +%d) -eq 1 ] && cd /home/ecole01/intranet && /home/ecole01/venv/bin/python manage.py auto_val_prof > /home/ecole01/logs/cron.log

def conv_mois(value):
    try:
        m =value.split('_')
        return '%s %s' % (mois[int(m[0])-1], m[1])
    except ValueError:
        return None

def auto_val_prof():
    m_y = "%s_%s" % (datetime.now().month-1, datetime.now().year)
    relation_all = Relation.objects.all()
    print("Fonction Last Month Val Prof : Mois %s" % m_y)
    for relation in relation_all:
        # Validation des cours non validé
        lessons_of_the_month_by_relation_unvalid = Lesson.objects.filter(relation=relation,mois=m_y,is_valid_t=False)
        print("Relation %s : Il y a %s leçons non validées" % (relation, lessons_of_the_month_by_relation_unvalid.count()))
        for lesson_unvalid in lessons_of_the_month_by_relation_unvalid:
            lesson_unvalid.is_valid_t = True
            lesson_unvalid.save()

        lessons_of_the_month_by_relation = Lesson.objects.filter(relation=relation, mois=m_y).exclude(is_unvalid=True)
        if lessons_of_the_month_by_relation:
            context = {'mois': conv_mois(m_y), 'lessons': lessons_of_the_month_by_relation}
            msg_plain = render_to_string('email/email_valid_prof.txt', context=context)
            send_mail("Liste de vos cours de piano %s" % conv_mois(m_y),
                      msg_plain, settings.DEFAULT_FROM_EMAIL, [relation.student.email])

def stats():
    prof = User.objects.filter(is_staff=True, is_active=True).count()
    eleve = Eleve.objects.filter().count()
    user = User.objects.filter(is_staff=False, is_active=True).count()
    Stats.objects.create(nb_prof=prof,nb_user=user,nb_eleve=eleve)


class Command(BaseCommand):
    def handle(self, **options):
        print("!!! Lancement Manuel %s !!!" % datetime.now())
        auto_val_prof()
        stats()
        print("!!! Fin du patch %s !!!" % datetime.now())