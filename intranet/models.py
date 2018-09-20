from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from datetime import datetime, timedelta, date
from django.contrib.auth.models import User

class Article(models.Model):
    titre = models.CharField(max_length=100)
    auteur = models.CharField(max_length=50, default="admin")
    contenu = models.TextField(null=True)
    lien = models.CharField(max_length=150,null=True, blank=True)
    photo = models.FileField(upload_to="photos/", default=None, blank=True, null=True)
    date = models.DateTimeField(default=timezone.now,verbose_name="Date de parution")

    class Meta:
        verbose_name = "article"
        ordering = ['date']

    def __str__(self):
        return self.titre

    @property
    def photo_url(self):
        if self.photo and hasattr(self.photo, 'url'):
            return self.photo.url

class UserProfile(models.Model):
    STATS_CHOICES = (
        ('A', 'Moteur de rechercheGoogle'),
        ('B', 'Facebook'),
        ('C', 'Autre source internet'),
        ('D', 'Annuaire(pages jaunes...)'),
        ('E', 'Nebout & Hamm'),
        ('F', 'Falado'),
        ('G', 'Connaissance(famille, amis...)'),
    )

    user = models.OneToOneField(User,  on_delete=models.CASCADE)  # La liaison OneToOne vers le modèle User
    avatar = models.ImageField(null=True, blank=True, upload_to="avatars/")
    phone_regex = RegexValidator(regex=r'^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$',
                                 message="Le numéro de téléphone doit suivre le format XX.XX.XX.XX.XX")
    phone_number = models.CharField(validators=[phone_regex], max_length=19, blank=True)  # validators should be a list
    address = models.CharField(max_length=60, default='')
    city = models.CharField(max_length=50, default='')
    country = models.CharField(max_length=50, default='France')
    # Use to geolocation
    lat = models.CharField(null=True,blank=True,default='None',max_length=50)
    lgn = models.CharField(null=True,blank=True,default='None',max_length=50)
    zip_code_regex = RegexValidator(regex=r'^(([0-8][0-9])|(9[0-5])|(2[ab]))[0-9]{3}$',
                                    message="Le Code Postal doit suivre le format DDDDD")
    zip_code = models.CharField(validators=[zip_code_regex], max_length=6, blank=True)
    # iban_regex = RegexValidator(regex='^([A-Za-z]{2}[ \-]?[0-9]{2})(?=(?:[ \-]?[A-Za-z0-9]){9,30}$)((?:[ \-]?[A-Za-z0-9]{3,5}){2,6})([ \-]?[A-Za-z0-9]{1,3})?$')
    # iban = models.CharField(validators=[iban_regex], max_length=27, blank=True)
    is_adherent = models.BooleanField(default=False)

    # Use to generate attestation
    siret = models.CharField(max_length=21,default='SIRET',blank=True)
    sap = models.CharField(max_length=11,default='SAP',blank=True)
    nb_facture = models.IntegerField(default=1)
    stats = models.CharField(max_length=1, choices=STATS_CHOICES,null=True,blank=True)
    is_premium = models.BooleanField(default=False,help_text="Permet d'annuler un cours à la dernière minute, les cours sont majorés de 10€")
    stripe_account_id = models.CharField(max_length=40,default="StripeAccId",blank=True,help_text='ex: acct_1D5xIp...')

    def __str__(self):
        return "Profil de {0}".format(self.user.username)

    def create_profile(sender, **kwargs):
        if kwargs['created']:
            user_profile = UserProfile.objects.create(user=kwargs['instance'])
    post_save.connect(create_profile, sender=User)


class Invitation(models.Model):
    uuid_regex = RegexValidator(regex='^[0-9a-f-]+$')
    uuid = models.UUIDField(validators=[uuid_regex], max_length=36)
    is_staff = models.BooleanField(default=False)
    is_free = models.BooleanField(default=False)
    email = models.EmailField()
    valid = models.BooleanField(default=False)


class Relation(models.Model):
    teacher = models.ForeignKey(User, related_name='teacher_in_relation_model', on_delete=models.CASCADE)
    student = models.ForeignKey(User, related_name='student_in_relation_model', on_delete=models.CASCADE)

    def __str__(self):
        return '{0} & {1}'.format(self.teacher, self.student)


class Cour(models.Model):
    relation = models.ForeignKey(Relation, on_delete=models.CASCADE)
    duree_cours = models.SmallIntegerField(default=0, verbose_name="Durée des cours")
    mois = models.CharField(max_length=7)
    is_valid_t = models.BooleanField(default=False)
    is_valid_s = models.BooleanField(default=False)
    is_unvalid = models.BooleanField(default=False)

class Lesson(models.Model):
    relation = models.ForeignKey(Relation, on_delete=models.CASCADE)
    nb_h = models.SmallIntegerField(default=0, verbose_name="Heures")
    nb_m = models.SmallIntegerField(default=0, verbose_name="Minutes")
    date = models.DateField(default=timezone.now())
    mois = models.CharField(max_length=7)
    is_valid_t = models.BooleanField(default=False)
    is_valid_s = models.BooleanField(default=False)
    is_unvalid = models.BooleanField(default=False)

    def __str__(self):
        if self.is_unvalid:
            return "%s, Date: %s, Durée: %sh%smin, Status: Rejeté par l'élève" % (
                self.relation,self.date,self.nb_h,self.nb_m)
        elif self.is_valid_s:
            return "%s, Date: %s, Durée: %sh%smin, Status: Validé par l'élève" % (
            self.relation, self.date, self.nb_h, self.nb_m)
        elif self.is_valid_t:
            return "%s, Date: %s, Durée: %sh%smin, Status: En attente de validation par l'élève" % (
            self.relation, self.date, self.nb_h, self.nb_m)
        else:
            return "%s, Date: %s, Durée: %sh%smin, Status: En attente de validation par le professeur" % (
            self.relation, self.date, self.nb_h, self.nb_m)

class Attestation(models.Model):
    to_user = models.ForeignKey(User, related_name='User_student', on_delete=models.DO_NOTHING)
    from_user = models.ForeignKey(User, related_name='User_professor', on_delete=models.DO_NOTHING)
    price = models.SmallIntegerField()
    nb_cours = models.SmallIntegerField(default=None, null=True, blank=True)
    created = models.DateField(default=date.today(), verbose_name='date d\'émission')
    last = models.DateField(default=date.today() + timedelta(days=365), verbose_name='date d\'échéance')
    # TO USER
    to_user_firstname = models.CharField(max_length=60, default=None, null=True, blank=True)
    to_user_lastname = models.CharField(max_length=60, default=None, null=True, blank=True)
    to_user_address = models.CharField(max_length=60, default=None, null=True, blank=True)
    to_user_city = models.CharField(max_length=60, default=None, null=True, blank=True)
    to_user_zipcode = models.CharField(max_length=60, default=None, null=True, blank=True)
    to_user_siret = models.CharField(max_length=21, default='SIRET', null=True, blank=True)
    to_user_sap = models.CharField(max_length=11, default='SAP', null=True, blank=True)
    # FROM USER
    from_user_firstname = models.CharField(max_length=60, default=None, null=True, blank=True)
    from_user_lastname = models.CharField(max_length=60, default=None, null=True, blank=True)
    from_user_address = models.CharField(max_length=60, default=None, null=True, blank=True)
    from_user_city = models.CharField(max_length=60, default=None, null=True, blank=True)
    from_user_zipcode = models.CharField(max_length=60, default=None, null=True, blank=True)
    from_user_siret = models.CharField(max_length=21, default='SIRET', null=True, blank=True)
    from_user_sap = models.CharField(max_length=11, default='SAP', null=True, blank=True)

class Facture(models.Model):
    to_user = models.ForeignKey(User, related_name='User_who_received_the_bill', on_delete=models.DO_NOTHING, default=None,verbose_name='Destinataire')
    from_user = models.ForeignKey(User, related_name='User_who_send_the_bill', on_delete=models.DO_NOTHING,default=None,verbose_name='Emetteur')
    tva = models.FloatField(default=None)
    price_ht = models.FloatField(default=None)
    price_ttc = models.FloatField(default=None)
    object = models.CharField(max_length=60,default=None)
    object_qt = models.FloatField(default=None)
    type = models.CharField(max_length=60,default=None)
    created = models.DateField(default=date.today(), verbose_name='date d\'émission')
    last = models.DateField(default=date.today() + timedelta(days=7), verbose_name='date d\'échéance')
    is_paid = models.BooleanField(default=False,verbose_name='Payé')

    facture_name = models.CharField(max_length=60,default=None, null=True, blank=True) # NomEmmeteur_NomDest_ID
    nb_facture = models.IntegerField(default=1)
    # TO USER
    to_user_firstname = models.CharField(max_length=60,default=None, null=True,blank=True)
    to_user_lastname = models.CharField(max_length=60,default=None, null=True,blank=True)
    to_user_address = models.CharField(max_length=60,default=None, null=True,blank=True)
    to_user_city = models.CharField(max_length=60,default=None, null=True,blank=True)
    to_user_zipcode = models.CharField(max_length=60,default=None, null=True,blank=True)
    to_user_siret = models.CharField(max_length=21, default='SIRET', null=True,blank=True)
    to_user_sap = models.CharField(max_length=11, default='SAP', null=True,blank=True)
    # FROM USER
    from_user_firstname = models.CharField(max_length=60, default=None, null=True,blank=True)
    from_user_lastname = models.CharField(max_length=60, default=None, null=True,blank=True)
    from_user_address = models.CharField(max_length=60, default=None, null=True,blank=True)
    from_user_city = models.CharField(max_length=60, default=None, null=True,blank=True)
    from_user_zipcode = models.CharField(max_length=60, default=None, null=True,blank=True)
    from_user_siret = models.CharField(max_length=21, default='SIRET', null=True,blank=True)
    from_user_sap = models.CharField(max_length=11, default='SAP', null=True,blank=True)

class Eleve(models.Model):
    referent = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=None)
    nom_prenom = models.CharField(max_length=100, default=None)

    def __str__(self):
        return self.nom_prenom

class Notification(models.Model):
    to_user = models.ForeignKey(User, related_name='User_who_received_the_notification', on_delete=models.CASCADE, default=None)
    from_user = models.ForeignKey(User, related_name='User_who_send_the_notification', on_delete=models.CASCADE, default=None)
    date = models.DateTimeField(default=timezone.now)
    object = models.CharField(max_length=60)
    text = models.CharField(max_length=340)

class Prix(models.Model):
    start = models.DateField(default=date.today()+timedelta(days=1), verbose_name='Début')
    end = models.DateField(default=None, verbose_name='Fin',null=True, blank=True)
    tva = models.FloatField(max_length=5, default=20.00) # 20,00
    adhesion =  models.FloatField(max_length=5, default=66.67)
    adhesion_reduc =  models.FloatField(max_length=5, default=60)
    adhesion_prof =  models.FloatField(max_length=5, blank=True, default=15.83)
    cours =  models.FloatField(max_length=5, default=41.00)
    cours_premium =  models.FloatField(max_length=5, blank=True, default=51.00)
    cours_ecole =  models.FloatField(max_length=5, blank=True, default=40.00)
    commission =  models.FloatField(max_length=5, default=0.83)
    frais_gestion = models.FloatField(max_length=5, default=7.50)
    class Meta:
        verbose_name_plural = "Prix"

class Condition(models.Model):
    start = models.DateField(default=date.today() + timedelta(days=1), verbose_name='Début')
    end = models.BooleanField(default=False, blank=True)
    file = models.FileField(upload_to='documents/',blank=True,default=None,null=True)

class Stats(models.Model):
    date = models.DateField(default=date.today())
    nb_prof = models.IntegerField(default=0,blank=True,null=True)
    nb_user = models.IntegerField(default=0,blank=True,null=True)
    nb_eleve = models.IntegerField(default=0,blank=True,null=True)

class Adhesion(models.Model):
    to_user = models.ForeignKey(User, related_name='Adhérent', on_delete=models.DO_NOTHING)
    created = models.DateField(default=date.today(), verbose_name='date d\'émission')
    end = models.DateField(default=date.today() + timedelta(days=365), verbose_name='Fin')
    def __str__(self):
        return self.end.strftime("%d/%m/%Y")

def get_full_name(self):
    return "%s (%s %s)" % (self.username, self.first_name, self.last_name)

User.add_to_class("__str__", get_full_name)