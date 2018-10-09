from django.contrib import admin
from .models import (Article, Relation, UserProfile, Cour, Facture, Invitation, Notification, Prix, Attestation,Lesson,
                     Condition,Adhesion,Eleve,Stats,Examen,InscriptionExamen)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

class MyUserAdmin(UserAdmin):
    # override the default sort column
    ordering = ('last_name', 'first_name', )
    # if you want the date they joined or other columns displayed in the list,
    # override list_display too
    list_display = ('username', 'email', 'date_joined', 'first_name', 'last_name', 'is_staff')


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('titre', 'contenu', 'lien', 'date', 'photo')
    date_hierarchy = 'date'
    ordering = ('date',)
    search_fields = ('titre', 'contenu')


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address', 'city', 'zip_code', 'country', 'siret', 'sap', 'stripe_account_id', 'nots_view', 'lat', 'lgn')
    search_fields = ('user', 'city', 'zip_code', 'iban')
    ordering = ('user',)

class ConditionAdmin(admin.ModelAdmin):
    list_display = ('start','end','file')

class ExamenAdmin(admin.ModelAdmin):
    list_display = ('name','description','last','price')

class InscriptionExamenAdmin(admin.ModelAdmin):
    list_display = ('examen','eleve')

class RelationAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'student')
    ordering = ('teacher',)
    search_fields = ('teacher', 'student')


class CourAdmin(admin.ModelAdmin):
    list_display = ('relation', 'duree_cours', 'mois', 'is_valid_t', 'is_valid_s', 'is_unvalid', 'apercu_nbrcours')
    ordering = ('-mois',)
    search_fields = ('relation', 'mois')
    def apercu_nbrcours(self, cour):
        """"""
        return round(cour.duree_cours/60,2)
    # En-tête de notre colonne
    apercu_nbrcours.short_description = 'Nombre de cours'

class LessonAdmin(admin.ModelAdmin):
    list_display = ('relation', 'date', 'nb_h', 'nb_m', 'is_valid_t', 'is_valid_s', 'is_unvalid')
    ordering = ('-date',)
    search_fields = ('relation', 'date')

class EleveAdmin(admin.ModelAdmin):
    list_display=('referent','nom_prenom')

class FactureAdmin(admin.ModelAdmin):
    list_display = ('to_user','from_user', 'facture_name', 'nb_facture', 'type', 'object', 'object_qt', 'tva', 'price_ht', 'price_ttc', 'created', 'last', 'is_paid')

class InvitationAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'email', 'is_staff', 'is_free', 'valid')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('to_user', 'from_user', 'date', 'object', 'text')
    ordering = ('-date', )

class PrixAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'tva', 'adhesion', 'adhesion_reduc', 'adhesion_prof', 'cours', 'cours_premium', 'cours_ecole', 'commission', 'frais_gestion')
    ordering = ('-start', )

class AttestationnAdmin(admin.ModelAdmin):
    list_display = ('to_user', 'from_user', 'price', 'created', 'last')
    search_fields = ('to_user', 'from_user', 'created', 'last')

class AdhesionAdmin(admin.ModelAdmin):
    list_display = ('to_user','created','end')

class StatsAdmin(admin.ModelAdmin):
    list_display = ('date','nb_prof','nb_eleve', 'nb_user')

# Register your models here.
admin.site.register(Article, ArticleAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Relation, RelationAdmin)
# admin.site.register(Cour, CourAdmin)
admin.site.register(Facture, FactureAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Prix, PrixAdmin)
admin.site.register(Attestation, AttestationnAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(Adhesion, AdhesionAdmin)
admin.site.register(Eleve, EleveAdmin)
admin.site.register(Stats, StatsAdmin)
admin.site.register(Examen, ExamenAdmin)
admin.site.register(InscriptionExamen, InscriptionExamenAdmin)
# finally replace the default UserAdmin with yours
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)