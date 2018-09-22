from django.urls import path
from django.conf.urls import url
from django.contrib.auth.views import (
    password_reset, password_reset_done, password_reset_confirm,
    password_reset_complete )
from . import views

app_name = 'intranet'

urlpatterns = [
    path('', views.accueil, name='base'),
    path('accueil', views.accueil, name='accueil'),
    path('creation_inscription', views.creation_inscription, name='creation_inscription'),
    path('creation_adhesion', views.creation_adhesion, name='creation_adhesion'),
    path('creation_condition', views.creation_condition, name='creation_condition'),
    path('gestion_mail', views.gestion_mail, name='gestion_mail'),
    path('cours_prof', views.cours_prof, name='cours_prof'),
    path('cours_eleve', views.cours_eleve, name='cours_eleve'),
    path('validation_prof/<int:id>/', views.validation_prof, name='validation_prof'),
    path('suppression_prof/<int:id>/', views.suppression_prof, name='suppression_prof'),
    url(r'^validation_eleve/(?P<id>\d+)/(?P<result>\w+)/$', views.validation_eleve, name='validation_eleve'),
    path('documents', views.documents, name='documents'),
    path('gen_pdf/<int:fac_id>/', views.gen_pdf, name='gen_pdf'),
    path('gen_attest_pdf/<int:fac_id>/', views.gen_attest_pdf, name='gen_attest_pdf'),
    path('checkout', views.checkout, name='checkout'),
    # path('out', views.out, name='out'),
    path('checkout_inscription', views.checkout_inscription, name='checkout_inscription'),
    path('notifications', views.notifications, name='notifications'),
    path('statistiques', views.statistiques, name='statistiques'),
    url(r'^graphs/membres.png$', views.graphs_membres,  name='graphs_membres'),
    url(r'^graphs/nbr_cours.png$', views.graphs_nb_cours,  name='graphs_nb_cours'),
    url(r'^graphs/evol.png$', views.graphs_evol,  name='graphs_evol'),
    path('gestion_membres', views.gestion_membres, name='gestion_membres'),
    path('gestion_invitations', views.gestion_invitations, name='gestion_invitations'),
    path('gestion_relations', views.gestion_relations, name='gestion_relations'),
    path('gestion_prix', views.gestion_prix, name='gestion_prix'),
    path('gestion_articles', views.gestion_articles, name='gestion_articles'),
    path('gestion_condition', views.gestion_condition, name='gestion_condition'),
    path('gestion_factures', views.gestion_factures, name='gestion_factures'),
    url(r'^invitation$', views.invitation, name='invitation'),
    url(r'^article', views.article, name='article'),
    url(r'^relation/$', views.relation, name='relation'),
    url(r'^prix/$', views.prix, name='prix'),
    url(r'^mail/$', views.mail, name='mail'),
    path('mon_compte', views.mon_compte, name='mon_compte'),
    path('edit_compte', views.edit_compte, name='edit_compte'),
    path('edit_pass', views.edit_pass, name='edit_pass'),
    url(r'^creation/(?P<uuid>[0-9a-f-]+)/$', views.creation, name='creation'),
    path('connexion', views.connexion, name='connexion'),
    path('deconnexion', views.deconnexion, name='deconnexion'),
    url(r'^reset-password/$', password_reset,
        {'template_name': 'intranet/reset_password.html', 'post_reset_redirect': 'intranet:password_reset_done',
         'email_template_name': 'intranet/reset_password_email.html'}, name='reset_password'),

    url(r'^reset-password/done/$', password_reset_done, {'template_name': 'intranet/reset_password_done.html'},
        name='password_reset_done'),

    url(r'^reset-password/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm,
        {'template_name': 'intranet/reset_password_confirm.html',
         'post_reset_redirect': 'intranet:password_reset_complete'}, name='password_reset_confirm'),

    url(r'^reset-password/complete/$', password_reset_complete,
        {'template_name': 'intranet/reset_password_complete.html'}, name='password_reset_complete')

]