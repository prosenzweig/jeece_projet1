from django.core.management.base import BaseCommand
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture,Lesson
from datetime import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["Janvier", u"Février", "Mars", "Avril", "Mai", "Juin", "Juillet", u"Août", "Septembtre", "Octobre"]

# Lancement Automatique de auto_val_prof

def conv_mois(value):
    try:
        m =value.split('_')
        return '%s %s' % (mois[int(m[0])-1], m[1])
    except ValueError:
        return None

def auto_val_prof():
    m_y = "%s_%s" % (datetime.now().month, datetime.now().year)
    relation_all = Relation.objects.all()

    for relation in relation_all:
        # Validation des cours non validé
        lessons_of_the_month_by_relation_unvalid = Lesson.objects.filter(relation=relation,mois=m_y,is_valid_t=False)
        for lesson_unvalid in lessons_of_the_month_by_relation_unvalid:
            lesson_unvalid.is_valid_t = True
            lesson_unvalid.save()

        lessons_of_the_month_by_relation = Lesson.objects.filter(relation=relation, mois=m_y).exclude(is_unvalid=True)
        context = {'mois': conv_mois(m_y), 'lessons': lessons_of_the_month_by_relation}
        msg_plain = render_to_string('email/email_valid_prof.txt', context=context)
        send_mail("Liste de vos cours de Piano %s" % conv_mois(m_y),
                  msg_plain, 'admin@ecole01.fr', [relation.student.email])

class Command(BaseCommand):
    def handle(self, **options):
        auto_val_prof()