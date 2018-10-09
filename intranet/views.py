from django.http import *
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.urls import reverse
from datetime import datetime,timedelta,date

import uuid
from django.contrib.sites.shortcuts import get_current_site

from django.core.mail import send_mail
from django.template.loader import render_to_string

from django.contrib.auth.models import User
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture,Eleve,\
    Lesson,Attestation,Condition,Adhesion,Stats,InscriptionExamen,Examen

from django.db.models import Q, Sum

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import static
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from .filters import FactureFilter
import stripe
import requests
import numpy as np

from pinax.stripe.actions import customers

import tempfile
import re
import os
import json
os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()
# do this before importing pylab or pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.figure as mtf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg


from intranet.forms import LoginForm, RegistrationForm, RelationForm, InvitationForm, EditProfileForm, EditUserForm,\
    CoursFrom, PrixForm, FactureIdForm, ArticleForm, EditStaffProfileForm, ConditionForm, MailForm, ToMailFormset,\
    EleveFormset, PriceForm, LessonFrom, CondiForm, FactureForm, EditEleveForm, AddEleveForm,EditEleveFormset,\
    InscriptionExamenForm, ExamenForm

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", u"février", "mars", "avril", "mai", "juin", "juillet", u"août", "septembre", "octobre","novembre","décembre"]

def from_date_to_m_y(date):
    d = date.split('-')
    f = '%s_%s' % (d[1],d[0])
    return re.sub(r'^0', '', f)

def nb_new_notifs(user):
    # print(user.last_login.date())
    if user.is_superuser:
        nots = Notification.objects.filter(date__gte=user.userprofile.nots_view).count()
    else:
        nots = Notification.objects.filter(to_user=user, date__gte=user.userprofile.nots_view).count()
    # print(nots)
    return nots

def conv_date(date):
    return datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')

def conv_mois(value):
    try:
        m =value.split('_')
        return '%s %s' % (MOIS[int(m[0])-1], m[1])
    except ValueError:
        return None

def last_3_mois():
    mn = datetime.now().month
    my = datetime.now().year
    myl = my - 1
    if mn > 3:
        t3 = "%s_%s" % (int(mn)-2, my)
        t2 = "%s_%s" % (int(mn)-1, my)
        t1 = "%s_%s" % (mn,my)
        return (t3,t2,t1)
    if mn ==2:
        t3 = "%s_%s" % (12, my-1)
        t2 = "%s_%s" % (int(mn) - 1, my)
        t1 = "%s_%s" % (mn, my)
        return (t3, t2, t1)
    if mn ==1:
        t3 = "%s_%s" % (11, my-1)
        t2 = "%s_%s" % (12, my-1)
        t1 = "%s_%s" % (mn, my)
        return (t3, t2, t1)


def add_tva(value,arg):
    try:
        return round(float(value) + float(value)*float(arg)/100,2)
    except (ValueError, ZeroDivisionError):
        return None

# Frais de Gestion PDF
@user_passes_test(lambda u: u.userprofile.is_adherent)
def gen_pdf(request,fac_id):
    import unicodedata
    # Create the HttpResponse object with the appropriate PDF headers.
    facture = get_object_or_404(Facture,pk=fac_id)
    admin = User.objects.get(is_superuser=True)
    if not request.user.is_superuser:
        if facture.to_user != request.user and facture.from_user != request.user:
            messages.warning(request,"Impossible d'accéder à la facture !")
            return redirect('intranet:documents')


    response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = 'attachment;filename=facture_%s.pdf' % facture.pk
    fname = facture.facture_name
    chaine = unicodedata.normalize('NFKD', fname).encode('ASCII', 'ignore')
    response['Content-Disposition'] = 'filename=A_%s.pdf' % chaine.decode('UTF-8')
    buffer = BytesIO()

    p = canvas.Canvas(buffer)
    logo = ImageReader("https://scontent-cdt1-1.xx.fbcdn.net/v/t1.0-9/10435640_175219366143139_807238508633238110_n.png?_nc_cat=0&oh=f71fd724af3b36a77c5e2369a880beff&oe=5BEF1DBB")
    # logo = ImageReader("https://static.wixstatic.com/media/ac3cde_87eef0b3e8904e2eb87cf9c4b69c6baa.png/v1/fill/w_61,h_61,al_c,q_80,usm_0.66_1.00_0.01/ac3cde_87eef0b3e8904e2eb87cf9c4b69c6baa.webp")

    p.drawImage(logo, 50, 600, mask='auto')
    p.setLineWidth(.3)
    H, L = 830, 587
    p.setFont('Helvetica-Bold', 16)
    p.drawString(350, 720, "Facture N°A%s" % facture.nb_facture)
    p.setFont('Helvetica', 12)
    p.drawString(350, 705, "Date de facturation: %s" % facture.created.strftime("%d/%m/%Y"))
    p.drawString(350, 690, "Date d'échéance: %s" % facture.last.strftime("%d/%m/%Y"))

    # Emetteur
    # if facture.type in ['Frais de gestion', 'Frais de commission', 'Adhésion élève', 'Adhésion élèves', 'Adhésion professeur',
    #                     'Frais de Gestion', 'Frais de Commission', 'Adhésion Eleve', 'Adhésion Elèves',
    #                     'Adhésion Professeur','Adhésion Éleve', 'Adhésion Élèves']:
    if facture.from_user.is_superuser:
        p.setFont('Helvetica-Bold', 12)
        p.drawString(50, 580, "École Française de Piano")
        p.setFont('Helvetica', 12)
        # p.drawString(50, 565, "Emmanuel BIRNBAUM")
        p.drawString(50, 565, "%s"  % facture.from_user_address)
        p.drawString(50, 550, "%s %s" % (facture.from_user_zipcode, facture.from_user_city))
        p.drawString(50, 535, "01 85 09 93 87")
        p.drawString(50, 520, "info@ecolefrancaisedepiano.fr")
        p.drawString(50, 505, "https://www.ecolefrancaisedepiano.fr")

    else:
        p.setFont('Helvetica-Bold', 12)
        if facture.from_user.is_superuser:
            p.drawString(50, 580, "École Française de Piano")
        else:
            p.drawString(50, 580, "%s %s" % (facture.from_user_lastname, facture.from_user_firstname))
        p.setFont('Helvetica', 12)
        p.drawString(50, 565, "%s"  % facture.from_user_address)
        p.drawString(50, 550, "%s %s" % (facture.from_user_zipcode, facture.from_user_city))
        p.drawString(50, 535, "France")

    # Destinataire
    p.setFont('Helvetica-Bold', 12)
    p.drawString(350, 580, "%s %s" % (facture.to_user_lastname, facture.to_user_firstname))
    p.setFont('Helvetica', 12)
    p.drawString(350, 565, "%s" % facture.to_user_address)
    p.drawString(350, 550, "%s %s" % (facture.to_user_zipcode, facture.to_user_city))
    p.drawString(350, 535, "France")

    if facture.type in ['Adhésion Elève', 'Adhésion Elèves', 'Adhésion Professeur','Adhésion élève', 'Adhésion élèves', 'Adhésion professeur']:
        p.drawString(50, 400, "%s %s-%s" % (facture.type,facture.created.year,facture.created.year+1))
    else:
        p.drawString(50, 400, "%s" % facture.type)
    p.setFont('Helvetica-Bold', 12)
    p.setStrokeColorRGB(0.7, 0.7, 0.7)
    p.setFillColorRGB(0.7, 0.7, 0.7)
    p.rect(50, 355, 501, 20, fill=1)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(55, 360, "Description")
    p.drawString(250, 360, "Date")
    p.drawString(300, 360, "Qté")
    p.drawString(350, 360, "Prix unitaire")
    p.drawString(450, 360, "TVA")
    p.drawString(500, 360, "Montant")
    p.setFont('Helvetica', 12)
    p.drawString(55, 340, "%s" % facture.object)
    p.drawString(220, 340, "%s" % facture.created.strftime("%d/%m/%Y"))
    p.drawString(300, 340, "%s" % facture.object_qt)
    if facture.type not in ['Adhésion Elève', 'Adhésion Elèves', 'Adhésion Professeur','Adhésion élève', 'Adhésion élèves', 'Adhésion professeur']:
        p.drawString(350, 340, "%s€" % str(round(facture.price_ht / facture.h_qt,2)))
    else:
        p.drawString(350, 340, "%s€" % str(facture.price_ht/facture.object_qt))
    p.drawString(450, 340, "{0}%".format(facture.tva))
    p.drawString(510, 340, "%s€" % facture.price_ttc)
    p.line(50,330,551,330)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(440, 315, "Total (HT)")
    p.drawString(440, 300, "TVA {0}%".format(facture.tva))
    p.drawString(510, 315, "%s €" % round(facture.price_ht,2))
    p.drawString(510, 300, "%s €" % round(facture.price_ttc-facture.price_ht,2))
    p.line(440, 290, 551, 290)
    p.setFont('Helvetica-Bold', 12)
    p.drawString(440, 270, "Total (TTC)")
    p.drawString(510, 270, "%s €" % facture.price_ttc)

    p.setFont('Helvetica-Bold', 11)
    p.drawString(50, 220, "Echéance:")
    p.setFont('Helvetica', 11)
    p.drawString(200, 220, "%s" % facture.last.strftime("%d/%m/%Y"))

    if facture.from_user.is_superuser:
        p.setFont('Helvetica-Bold', 10)
        p.drawCentredString(300,60,'Ecole Française de Piano - SASU EFP')
        p.setFont('Helvetica-Oblique', 8)
        # p.drawCentredString(300,45,'4 Rue du Champ de l\'Alouette 75013 Paris')
        p.drawCentredString(300,45,'%s %s %s' % (facture.admin_address,facture.admin_zipcode,facture.admin_city))
        p.drawCentredString(300,30,'Numéro de SIRET: 811 905 934 00014 - Numéro de TVA: FR 90 811905934 - 811 905 934 R.C.S.Paris')
    else:
        p.setFont('Helvetica-Oblique', 9)
        p.drawCentredString(300, 85, 'TVA non applicable, art. 293 B du CGI - Facture établie au nom et pour le compte de %s %s par la société : SASU EFP -' % (facture.from_user_firstname,facture.from_user_lastname))
        p.drawCentredString(300, 75, 'Siret n°811 905 934 00014 - 811 905 934 R.C.S.Paris - %s %s %s' % (facture.admin_address,facture.admin_zipcode,facture.admin_city))
        p.setFont('Helvetica-Bold', 9)
        p.drawCentredString(300, 60, '%s %s' % (facture.from_user_firstname,facture.from_user_lastname))
        p.setFont('Helvetica-Oblique', 8)
        p.drawCentredString(300, 45, '%s %s %s' % (facture.from_user_address,facture.from_user_zipcode,facture.from_user_city))
        p.drawCentredString(300, 35, 'Numéro de SIRET: %s' % (facture.from_user_siret))

    p.showPage()
    p.save()
    # Get the value of the BytesIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

@user_passes_test(lambda u: u.userprofile.is_adherent)
def gen_attest_pdf(request,fac_id):
    import unicodedata
    # fac_id
    # Create the HttpResponse object with the appropriate PDF headers.
    att = get_object_or_404(Attestation,pk=fac_id)
    if not request.user.is_superuser:
        if att.to_user != request.user and att.from_user != request.user:
            messages.warning(request,"Impossible d'accéder au document !")
            return redirect('intranet:documents')


    response = HttpResponse(content_type='application/pdf')
    fname = 'attestation_%s_%s_%s.pdf' % (att.from_user_lastname,att.to_user_lastname,att.nb_adh)
    chaine = unicodedata.normalize('NFKD', fname).encode('ASCII', 'ignore')
    response['Content-Disposition'] = 'filename=%s' % chaine.decode('UTF-8')
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    p.setLineWidth(.3)
    H, L = 830, 587

    # Emetteur
    p.setFont('Helvetica', 12)
    p.drawString(75, 780, "%s %s" % (att.from_user_lastname.upper(), att.from_user_firstname))
    p.drawString(75, 765, "%s" % att.from_user_address)
    p.drawString(75, 750, "%s %s" % (att.from_user_zipcode, att.from_user_city))
    p.drawString(75, 735, "France")
    p.drawString(75, 720, "N° SIRET : %s" % att.from_user_siret)
    p.drawString(75, 705, "N° SAP : %s" % att.from_user_sap)


    p.drawString(350, 682, "Déclaration N°EFP%s - %s" % (att.pk,att.created.strftime("%d/%m/%Y")))

    # Destinataire
    p.drawString(75, 660, "%s %s" % (att.to_user_lastname.upper(), att.to_user_firstname))
    p.drawString(75, 645, "%s" % att.to_user_address)
    p.drawString(75, 630, "%s %s" % (att.to_user_zipcode, att.to_user_city))
    p.drawString(75, 615, "France")

    p.setFont('Helvetica-Bold', 14)
    p.drawString(150, 550, "ATTESTATION FISCALE ANNUELLE - %s" % att.pk)
    p.setFont('Helvetica', 10)
    p.drawString(75, 520, "Je soussigné, %s %s, professeur indépendant de piano, certifie que " % (att.from_user_firstname, att.from_user_lastname.upper() ))
    p.drawString(75, 505, "M et Mme %s, domiciliés au %s, %s %s, " % (att.to_user_lastname.upper(),att.to_user_address, att.to_user_zipcode ,att.to_user_city))
    p.drawString(75, 490, "ont bénéficié de services à la personne : cours de piano")
    p.drawString(75, 460, "En %s, le montant des attestations effectivement acquittées représente" % (datetime.now().year-1))
    p.drawString(75, 445, "une somme totale de : %s€." % att.price)

    p.setFont('Helvetica-Bold', 10)
    p.drawString(75,400, "Intervenant :")
    p.setFont('Helvetica', 10)
    p.drawString(75, 380, "%s %s - %s heures pour l’année %s" % (att.from_user_firstname, att.from_user_lastname.upper(), att.nb_cours,  (datetime.now().year-1)))
    p.drawString(75, 365, "Prix horaire de la prestation : %s€/heure" % (round(att.price/att.h_qt,2)))

    p.drawString(75, 330, "Fait pour valoir ce que de droit,")
    p.drawString(75, 300, "Le %s" % att.created)
    p.drawString(75, 270, "%s %s" % (att.from_user_firstname,att.from_user_lastname.upper()))
    p.setFont('Helvetica', 10)
    p.drawString(75, 230, "Afin de bénéficier de l'avantage fiscal au titre du Service à la Personne, veuillez")
    p.drawString(75, 215, "remplir la case de votre déclaration d'impôts correspondant au crédit et")
    p.drawString(75, 200, "réduction d'impôt pour l'emploi à domicile en page 4, partie 7, rubrique \"Sommes")
    p.drawString(75, 185, "versées pour l'emploi à domicile\". Case 7DB, 7DF ou 7DD en fonction de votre")
    p.drawString(75, 170, "situation sur l'année écoulée.")

    p.setFont('Helvetica-Oblique', 8)
    p.drawCentredString(300, 45, 'Attestation fiscale établie au nom et pour le compte de %s %s par la société :' % (att.from_user_firstname, att.from_user_lastname.upper()))
    p.drawCentredString(300, 30, 'SASU EFP - Siret n°811 905 934 00014 - 811 905 934 R.C.S.Paris - %s %s %s - info@ecolefrancaisedepiano.fr' % (att.admin_address,att.admin_city,att.admin_zipcode))





    p.showPage()
    p.save()
    # Get the value of the BytesIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

@user_passes_test(lambda u: u.userprofile.is_adherent)
def deconnexion(request):
    logout(request)
    return redirect(reverse('intranet:connexion'))

def connexion(request):
    error = False
    # print (request.user)
    if request.user.is_authenticated:
        return redirect('intranet:accueil')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)  # Nous vérifions si les données sont correctes
            if user:  # Si l'objet renvoyé n'est pas None
                login(request, user)  # nous connectons l'utilisateur
                return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL) # nous le renvoyons vers la page accueil.html
            else:  # sinon une erreur sera affichée
                error = True
    else:
        form = LoginForm()

    return render(request, 'intranet/login.html', locals())

# Registered
def creation(request, uuid):
    inv = get_object_or_404(Invitation, uuid=uuid)
    # print(inv)
    if inv.valid:
        messages.error(request, 'Votre invitation n\'est plus valide!')
        return redirect('intranet:creation')
    else:
        if request.method == "POST":
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_staff = inv.is_staff
                user.save()
                if inv.is_free:
                    # user.userprofile.is_adherent = True
                    # user.userprofile.save()
                    Adhesion.objects.create(to_user=user)
                inv.valid = True
                inv.save()

                #Test Create new customer for each new accoutns
                customers.create(user=user) # Strip stuff
                login(request, user)
                return redirect('intranet:creation_inscription') # nous le renvoyons vers la page accueil.html
            else:  # sinon une erreur sera affichée
                messages.warning(request,'Impossible de vous inscrire.')
        else:
            form = RegistrationForm()

    return render(request, 'intranet/creation.html', locals())


@login_required
def accueil(request):
    if not request.user.userprofile.is_adherent:
        return redirect('intranet:creation_inscription')

    nots = nb_new_notifs(request.user)

    """ Redirection apres connexion, ici seront afficher les articles du blog"""
    articles_list = reversed(Article.objects.all()) # Nous sélectionnons tous nos articles
    return render(request, 'intranet/accueil.html', locals())

def creation_inscription(request):
    if request.method == 'POST':
        # print("POST")
        form_user = EditUserForm(request.POST, instance=request.user)
        form_profile = EditStaffProfileForm(request.POST, instance=request.user.userprofile) if request.user.is_staff else EditProfileForm(request.POST, instance=request.user.userprofile)
        if form_profile.is_valid() and form_user.is_valid():
            form_user.save()
            form_profile.save()
            messages.success(request, 'Vos informations personnelles ont bien été enregistrées.')
            address = form_profile.cleaned_data["address"]
            city = form_profile.cleaned_data["city"]
            zip_code = form_profile.cleaned_data["zip_code"]
            country = form_profile.cleaned_data["country"]
            # print(address, city, zip_code, country)
            location = "%s %s %s %s" % (address, city, zip_code, country)
            r = requests.get('http://www.mapquestapi.com/geocoding/v1/address?key=7MspWFOeqU2eH72DNDg8LM6sTXKcaQmz&location=%s' % location)
            us = User.objects.get(pk=request.user.pk)
            if r.status_code == requests.codes.ok:
                data = json.loads(r.text)
                # print(json.dumps(data,indent=4))
                try:
                    # print(data["results"][0]['locations'][0]['latLng']['lat'], data["results"][0]['locations'][0]['latLng']['lng'])
                    us.userprofile.lat = data["results"][0]['locations'][0]['latLng']['lat']
                    us.userprofile.lgn = data["results"][0]['locations'][0]['latLng']['lng']
                    us.userprofile.save()
                except:
                    pass

            admin = User.objects.get(is_superuser=True)

            if request.user.is_staff:
                Notification.objects.create(to_user=admin, from_user=request.user,
                                        object="Creation du compte %s %s (%s)" % (
                                        request.user.first_name, request.user.last_name, request.user.username),
                                        text="Je viens de compléter mon compte professeur!")
            else:
                Notification.objects.create(to_user=admin, from_user=request.user,
                                            object="Creation du compte %s %s (%s)" % (
                                                request.user.first_name, request.user.last_name, request.user.username),
                                            text="Je viens de compléter mon compte!")


            if request.user.is_staff:
                adh = Adhesion.objects.filter(to_user=request.user)
                if adh:
                    request.user.userprofile.is_adherent = True
                    request.user.userprofile.save()
                    return redirect('intranet:accueil')
                else:
                    return redirect('intranet:creation_adhesion')
            else:
                return redirect('intranet:creation_eleves')
        else:
            messages.error(request,"Le formulaire n'est pas valide")
            return redirect('intranet:creation_inscription')

    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = EditStaffProfileForm(instance=request.user.userprofile) if request.user.is_staff else EditProfileForm(instance=request.user.userprofile)

    return render(request, 'intranet/creation_inscription.html', locals())

def creation_eleves(request):
    if request.method == 'POST':
        formset = EleveFormset(request.POST)
        if formset.is_valid():
            for f in formset:
                name = f.cleaned_data.get('name')
                if name:
                    Eleve.objects.create(referent=request.user, nom_prenom=name)
                    admin = User.objects.get(is_superuser=True)
                    Notification.objects.create(to_user=admin, from_user=request.user,
                                                object="Ajout d'un élève %s %s (%s)" % (
                                                request.user.first_name, request.user.last_name, request.user.username),
                                                text="Je viens d'inscrire un élève: %s" % name)

            eleves_register = Eleve.objects.filter(referent=request.user)

            if not eleves_register:
                messages.warning(request,"Vous devez renseigner au moins un élève qui suivra les cours de piano.")
                return redirect('intranet:creation_eleves')

            return redirect('intranet:creation_condition')
    else:
        eleves = Eleve.objects.filter(referent=request.user)
        formset = EleveFormset()
    return render(request, 'intranet/creation_eleves.html', locals())

def creation_adhesion(request):
    prix = Prix.objects.get(end=None)
    key = settings.STRIPE_PUBLISHABLE_KEY
    tva = prix.tva
    ad_prof = add_tva(prix.adhesion_prof,tva)
    ad = add_tva(prix.adhesion,tva)
    ad_reduc = add_tva(prix.adhesion_reduc,tva)

    if request.user.is_staff:
        price = ad_prof
    else:
        nb_eleve = Eleve.objects.filter(referent=request.user).count()
        price = ad if nb_eleve == 1 else ad_reduc * nb_eleve
        eleves = Eleve.objects.filter(referent=request.user)
    return render(request, 'intranet/creation_adhesion.html', locals())

def creation_condition(request):
    if request.method == "POST":
        form = ConditionForm(request.POST)
        if form.is_valid():
            adh = Adhesion.objects.filter(to_user=request.user)
            if adh:
                request.user.userprofile.is_adherent = True
                request.user.userprofile.save()
                return redirect('intranet:accueil')
            else:
                return redirect('intranet:creation_adhesion')
        else:
            messages.warning(request, 'Vous devez valider les conditions d\'utilisations.')
            return redirect('intranet:creation_condition')
    form = ConditionForm()
    condition = Condition.objects.get(end=False)
    return render(request, 'intranet/creation_condition.html', locals())

@login_required
@user_passes_test(lambda u: u.is_staff)
@user_passes_test(lambda u: u.userprofile.is_adherent)
def cours_prof(request):
    """Minimal function rendering a template"""
    def last_day_of_month(any_day):
        next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
        last_day = next_month - timedelta(days=next_month.day)
        return last_day.replace(hour=0,minute=0,second=0) - datetime.now()

    m_y = "%s_%s" % (datetime.now().month, datetime.now().year)
    nots = nb_new_notifs(request.user)
    lesson_by_month = [{x.student: Lesson.objects.filter(relation__teacher=request.user,relation__student=x.student,mois=m_y).order_by('-date')} for i, x in enumerate(Relation.objects.filter(teacher=request.user)) if Lesson.objects.filter(relation__teacher=request.user,relation__student=x.student,mois=m_y).order_by('-date')]

    # for dict in lesson_by_month:
    #     for k,v in dict.items():
    #         print(k, v)

    lesson_last = Lesson.objects.filter(relation__teacher=request.user).exclude(mois=m_y).order_by('-date')

    page = request.GET.get('page', 1)
    paginator = Paginator(lesson_last, 10, 3)
    try:
        lesson_last_page = paginator.page(page)
    except PageNotAnInteger:
        lesson_last_page = paginator.page(1)
    except EmptyPage:
        lesson_last_page = paginator.page(paginator.num_pages)

    month = '%s %s' % (MOIS[datetime.now().month-1], datetime.now().year)
    delta = last_day_of_month(datetime.now())

    if request.method == "GET":
        if delta.days < 7:
            if delta.days < 1:
                messages.warning(request,
                                 'Il vous reste %s heures et %s minutes avant la fin du mois, n\'oubliez pas de valider vos cours !' % (
                                  delta.seconds // 3600, (delta.seconds // 60) % 60))
            else:
                messages.warning(request, 'Il vous reste %s jours, %s heures et %s minutes avant la fin du mois, n\'oubliez pas de valider vos cours !' % (delta.days, delta.seconds//3600, (delta.seconds//60)%60))

    if request.method == "POST":
        form = LessonFrom(request.POST, prof=request.user)
        if form.is_valid():
            eleve = form.cleaned_data["eleve"]
            nb_h = form.cleaned_data["nb_h"]
            nb_m = form.cleaned_data["nb_m"]
            date = form.cleaned_data["date"]

            mois = from_date_to_m_y(str(date))
            # print(str(date).split('-')[1])
            if str(date).split('-')[1] != str(datetime.now().month) and str(date).split('-')[1] != '0' + str(datetime.now().month):
                messages.warning(request,'Vous devez saisir les cours du mois de %s' % month)
                return redirect('intranet:cours_prof')

            user_eleve = User.objects.get(username=eleve)
            relation = Relation.objects.get(teacher=request.user, student=user_eleve)
            Lesson.objects.create(relation=relation,nb_h=nb_h,nb_m=nb_m,date=date,mois=mois)
            messages.success(request,"Le cours a bien été ajouté")
            return redirect('intranet:cours_prof')
        else:
            messages.warning(request, "Imposssible d'ajouter le cours.")
            return redirect('intranet:cours_prof')
    else:
        form = LessonFrom(prof=request.user)
    return render(request, 'intranet/cours_prof.html', locals())

@login_required
@user_passes_test(lambda u: u.is_staff)
@user_passes_test(lambda u: u.userprofile.is_adherent)
def validation_prof(request, id):
    nots = nb_new_notifs(request.user)
    lesson = Lesson.objects.filter(pk=id)
    if not lesson:
        messages.error(request, 'Action Impossible.')
        return redirect('intranet:cours_prof')
    else:
        cour = lesson.first()

    if cour.relation.teacher == request.user:
        cour.is_valid_t = True
        cour.save()
        messages.success(request, 'Cours validé !')
        Notification.objects.create(to_user=cour.relation.student,from_user=cour.relation.teacher,
                                   object="Validation cours %s" % conv_date(str(cour.date)),
                                   text="Vous pouvez valider ou refuser un cours dans la section 'Mes cours'.")
    else:
        messages.error(request,'Action Impossible.')
    return redirect('intranet:cours_prof')

@login_required
@user_passes_test(lambda u: u.is_staff)
@user_passes_test(lambda u: u.userprofile.is_adherent)
def suppression_prof(request,id):
    nots = nb_new_notifs(request.user)
    lesson = Lesson.objects.filter(pk=id)
    if not lesson:
        messages.error(request, 'Action Impossible.')
        return redirect('intranet:cours_prof')
    else:
        cour = lesson.first()

    if cour.relation.teacher == request.user:
        cour.delete()
        messages.success(request, 'Cours supprimé !')
    else:
        messages.error(request, 'Action Impossible.')
    return redirect('intranet:cours_prof')

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
@user_passes_test(lambda u: u.userprofile.is_adherent)
def cours_eleve(request):
    nots = nb_new_notifs(request.user)
    lessons_list = reversed(Lesson.objects.filter(relation__student=request.user, is_valid_t=True))
    return render(request, 'intranet/cours_eleve.html', locals())

@login_required
def validation_eleve(request, id, result):
    # print(id,result)
    cour = Lesson.objects.filter(pk=id)
    if not cour:
        messages.error(request, 'Action Impossible.')
        return redirect('intranet:cours_eleve')
    else:
        cour = cour.first()

    if cour.relation.student == request.user and cour.is_valid_s is False:
        if result == 'valid':
            cour.is_valid_s = True
            cour.save()
            messages.success(request, 'Le cours a bien été validé.')
            Notification.objects.create(to_user=cour.relation.teacher, from_user=cour.relation.student,
                                       object="Cours Validé !",
                                       text="J'ai bien validé le cours du %s" % conv_date(str(cour.date)))


        elif result == 'refus':
            admin = User.objects.get(is_superuser=True)
            cour.is_unvalid = True
            cour.save()
            messages.warning(request, 'Le cours a bien été refusé. L\'administrateur en sera informé.')
            Notification.objects.create(to_user=cour.relation.teacher, from_user=cour.relation.student,
                                        object="Problème Validation cours",
                                        text="Il y a un problème dans le cours du %s que vous m'avez demandé de valider." % conv_date(str(cour.date)))

            context = {'date': conv_date(str(cour.date)), 't': cour.relation.teacher, 's': cour.relation.student,
                       'tel_t': cour.relation.teacher.userprofile.phone_number, 'email_t': cour.relation.teacher.email,
                       'tel_s': cour.relation.student.userprofile.phone_number, 'email_s': cour.relation.student.email}
            msg_plain = render_to_string('email/email_refus.txt', context=context)
            send_mail("Problème de validation entre %s et %s" % (cour.relation.teacher,cour.relation.student),
                     msg_plain,settings.DEFAULT_FROM_EMAIL,[admin.email])
    else:
        messages.error(request,'Action Impossible.')

    return redirect('intranet:cours_eleve')



@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
def documents(request):
    nots = nb_new_notifs(request.user)
    # TO DO PROF
    # key = settings.STRIPE_PUBLISHABLE_KEY
    admin = User.objects.get(is_superuser=True)
    if request.method == "POST":
        print("JE VEUX PAYER!")
        token = request.POST['stripeToken']
        stripe_customer_id = request.user.customer.stripe_id
        # print(request.user, stripe_customer_id)
        # print("Token",token)

        fac_list = Facture.objects.filter(to_user=request.user, is_paid=False).exclude(
            from_user__userprofile__stripe_account_id="StripeAccId")


        description = ", ".join([f.facture_name for f in fac_list])
        dest = set([f.from_user for f in fac_list])

        if admin not in dest and len(dest) == 1:
            print("Que pour un Prof")
            tt_ad = sum([float(f.price_ttc) for f in fac_list])
            try:
                charge = stripe.Charge.create(
                    amount=int(round(tt_ad,2) * 100),
                    currency="eur",
                    source=token,
                    description=description,
                    destination={'account': fac_list[0].from_user.userprofile.stripe_account_id}
                )
                for fac in fac_list:
                    fac.is_paid = True
                    fac.save()
                messages.success(request, "La facture a bien été payée.")
                return redirect('intranet:documents')
            except stripe.error.CardError as e:
                messages.error(request, "Votre carte a été refusée")
                body = e.json_body
                err = body.get('error', {})
                print("Status is: %s" % e.http_status)
                print("Type is: %s" % err.get('type'))
                print("Code is: %s" % err.get('code'))
                print("Param is: %s" % err.get('param'))
                print("Message is: %s" % err.get('message'))
                return redirect('intranet:documents')
            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.error(request, "Erreur de connexion avec l'API Stripe.")
                return redirect('intranet:documents')
            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.error(request, "Les paramètres transmis ne sont pas correctes.")
                return redirect('intranet:documents')
            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.error(request, "Les clefs de l'API ne sont pas bonnes.")
                return redirect('intranet:documents')
            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                return redirect('intranet:documents')
            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                return redirect('intranet:documents')
            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                messages.error(request, "Quelque chose d'anormal est survenu.")
                return redirect('intranet:documents')
        elif admin in dest and len(dest) == 1:
            print("Que pour l'admin")
            tt_ad = sum([float(f.price_ttc) for f in fac_list])
            try:
                charge = stripe.Charge.create(
                    amount=int(round(tt_ad,2) * 100),
                    currency="eur",
                    description=description,
                    source=token
                )
                for fac in fac_list:
                    fac.is_paid = True
                    fac.save()
                messages.success(request, "La facture a bien été payée.")
                return redirect('intranet:documents')
            except stripe.error.CardError as e:
                messages.error(request, "Votre carte a été refusée")
                body = e.json_body
                err = body.get('error', {})
                print("Status is: %s" % e.http_status)
                print("Type is: %s" % err.get('type'))
                print("Code is: %s" % err.get('code'))
                print("Param is: %s" % err.get('param'))
                print("Message is: %s" % err.get('message'))
                return redirect('intranet:documents')
            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.error(request, "Erreur de connexion avec l'API Stripe.")
                return redirect('intranet:documents')
            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.error(request, "Les paramètres transmis ne sont pas correctes.")
                return redirect('intranet:documents')
            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.error(request, "Les clefs de l'API ne sont pas bonnes.")
                return redirect('intranet:documents')
            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.error(request, "Quelque chose d'anormal est survene.")
                return redirect('intranet:documents')
            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.error(request, "Quelque chose d'anormal est survenu.")
                return redirect('intranet:documents')
            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                messages.error(request, "Quelque chose d'anormal est survenu.")
                return redirect('intranet:documents')
        elif admin in dest and len(dest) == 2:
            print("Cas Classique de Facturation")
            fac_ad = [f for f in fac_list if f.from_user == admin]
            fac_prof = [f for f in fac_list if f.from_user != admin]
            tt_ad = sum([float(f.price_ttc) for f in fac_list if f.from_user == admin])
            tt_prof = sum([float(f.price_ttc) for f in fac_list if f.from_user != admin])
            des_pr = ','.join([f.facture_name for f in fac_list if f.from_user != admin])
            try:
                charge = stripe.Charge.create(
                    amount= int(round(tt_ad+tt_prof,2)*100),
                    currency="eur",
                    source=token,
                    description=description,
                    destination={
                        "amount":int(round(tt_prof,2)*100),
                        "account": fac_prof[0].from_user.userprofile.stripe_account_id,
                    }
                )
                for fac in fac_list:
                    fac.is_paid = True
                    fac.save()
                messages.success(request, "Les factures ont bien été payées.")
                return redirect('intranet:documents')
            except stripe.error.CardError as e:
                messages.error(request, "Votre carte a été refusée")
                body = e.json_body
                err = body.get('error', {})
                print("Status is: %s" % e.http_status)
                print("Type is: %s" % err.get('type'))
                print("Code is: %s" % err.get('code'))
                print("Param is: %s" % err.get('param'))
                print("Message is: %s" % err.get('message'))
                return redirect('intranet:documents')
            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.error(request, "Erreur de connexion avec l'API Stripe.")
                return redirect('intranet:documents')
            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.error(request, "Les paramètres transmis ne sont pas correctes.")
                return redirect('intranet:documents')
            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.error(request, "Les clefs de l'API ne sont pas bonnes.")
                return redirect('intranet:documents')
            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.error(request, "Problème de connexion..")
                return redirect('intranet:documents')
            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.error(request, "Quelque chose d'anormal est survenu.")
                return redirect('intranet:documents')
            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                messages.error(request, "Quelque chose d'anormal est survenu.")
                return redirect('intranet:documents')
        else:
            dest_na = [d for d in dest if d != admin]
            fac_dest = Facture.objects.filter(to_user=request.user, from_user=dest_na[0], is_paid=False).exclude(
            from_user__userprofile__stripe_account_id="StripeAccId")
            tt_dest_na = sum([float(f.price_ttc) for f in fac_dest])
            description = ", ".join([f.facture_name for f in fac_dest])
            try:
                charge = stripe.Charge.create(
                    amount=int(round(tt_dest_na,2) * 100),
                    currency="eur",
                    source=token,
                    description=description,
                    destination={'account': fac_dest[0].from_user.userprofile.stripe_account_id}
                )
                for fac in fac_dest:
                    fac.is_paid = True
                    fac.save()
                messages.success(request, "Une partie des factures ont bien été payées.")
                messages.warning(request, "Impossible de payer l'ensemble des factures d'un coup.")
                return redirect('intranet:documents')
            except stripe.error.CardError as e:
                messages.error(request, "Votre carte a été refusée")
                body = e.json_body
                err = body.get('error', {})
                print("Status is: %s" % e.http_status)
                print("Type is: %s" % err.get('type'))
                print("Code is: %s" % err.get('code'))
                print("Param is: %s" % err.get('param'))
                print("Message is: %s" % err.get('message'))
                return redirect('intranet:documents')
            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.error(request, "Erreur de connexion avec l'API Stripe.")
                return redirect('intranet:documents')
            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.error(request, "Les paramètres transmis ne sont pas correctes.")
                return redirect('intranet:documents')
            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.error(request, "Les clefs de l'API ne sont pas bonnes.")
                return redirect('intranet:documents')
            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                return redirect('intranet:documents')
            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                return redirect('intranet:documents')
            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                messages.error(request, "Quelque chose d'anormal est survenu.")
                return redirect('intranet:documents')

        return redirect('intranet:documents')

    if request.user.is_superuser:
        factures_all = Facture.objects.all().order_by('-pk')
        attestation_list = Attestation.objects.all().order_by('-pk')
        filter = FactureFilter(request.GET, queryset=factures_all)
        page = request.GET.get('page', 1)
        paginator = Paginator(filter.qs, 10)
        current_path = request.get_full_path()
        new_current_path = re.sub(r'&page=\d+', '', current_path)
        # print(new_current_path)
        try:
            filter_page = paginator.page(page)
        except PageNotAnInteger:
            filter_page = paginator.page(1)
        except EmptyPage:
            filter_page = paginator.page(paginator.num_pages)

    else:
        if request.user.is_staff:
            attestation_list = Attestation.objects.filter(from_user=request.user).order_by('-pk')
            factures_emises = Facture.objects.filter(from_user=request.user).order_by('-pk')
            page = request.GET.get('page', 1)
            paginator = Paginator(factures_emises, 10, 3)
            try:
                factures_emises_page = paginator.page(page)
            except PageNotAnInteger:
                factures_emises_page = paginator.page(1)
            except EmptyPage:
                factures_emises_page = paginator.page(paginator.num_pages)
        else:
            attestation_list = Attestation.objects.filter(to_user=request.user).order_by('-pk')

        factures_list_paid = Facture.objects.filter(to_user=request.user,is_paid=True).order_by('-pk')
        factures_list_not_paid = Facture.objects.filter(to_user=request.user,is_paid=False).order_by('-pk')
        price = Facture.objects.filter(to_user=request.user,is_paid=False).exclude(from_user__userprofile__stripe_account_id="StripeAccId").aggregate(Sum('price_ttc'))['price_ttc__sum']
        if price:
            price = round(price,2)

        page = request.GET.get('page', 1)
        paginator = Paginator(factures_list_paid, 10, 3)
        try:
            factures_list_paid_page = paginator.page(page)
        except PageNotAnInteger:
            factures_list_paid_page = paginator.page(1)
        except EmptyPage:
            factures_list_paid_page = paginator.page(paginator.num_pages)

    user = User.objects.get(id=request.user.id)
    return render(request, 'intranet/documents.html', locals())

@login_required
def checkout(request):
    if request.method == "POST":
        form = FactureIdForm(request.POST)
        if form.is_valid():
            fac_id = form.cleaned_data["fac_id"]
            fac = get_object_or_404(Facture,pk=fac_id)
            fac.is_paid = True
            fac.save()
            messages.success(request, "Votre facture a bien été payée.")
            Notification.objects.create(to_user=fac.from_user, from_user=request.user,
                                        object="Validation Facture",
                                        text="La facture %s de %s€ a bien été payée!" % (fac.type,fac.price_ttc))
            return redirect('intranet:documents')
    else:
        messages.warning(request,'Action non aurotisée.')
    return redirect('intranet:documents')

@login_required
def checkout_inscription(request):
    if request.method == "POST":
        # print("VALIDDE!!!")
        token = request.POST['stripeToken']

        prix = Prix.objects.get(end=None)
        if not request.user.is_staff:
            nb_eleve = Eleve.objects.filter(referent=request.user).count()
            p = add_tva(prix.adhesion_reduc*nb_eleve,prix.tva) if nb_eleve > 1 else add_tva(prix.adhesion,prix.tva)

        price = prix.adhesion_prof if request.user.is_staff else p
        description = "EFP_%s_%s_ADH" % (request.user.last_name,admin.userprofile.nb_facture)

        try:
            charge = stripe.Charge.create(
                amount=int(round(price,2) * 100),
                currency="eur",
                description=description,
                source=token
            )
        except stripe.error.CardError as e:
            messages.error(request, "Votre carte a été refusée")
            body = e.json_body
            err = body.get('error', {})
            print("Status is: %s" % e.http_status)
            print("Type is: %s" % err.get('type'))
            print("Code is: %s" % err.get('code'))
            print("Param is: %s" % err.get('param'))
            print("Message is: %s" % err.get('message'))
            return redirect('intranet:creation_adhesion')
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(request, "Erreur de connexion avec l'API Stripe.")
            return redirect('intranet:creation_adhesion')
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(request, "Les paramètres transmis ne sont pas correctes.")
            return redirect('intranet:creation_adhesion')
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(request, "Les clefs de l'API ne sont pas bonnes.")
            return redirect('intranet:creation_adhesion')
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(request, "Problème de connection, réessayez svp.")
            return redirect('intranet:creation_adhesion')
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(request, "Quelque chose d'anormal est survenu.")
            return redirect('intranet:creation_adhesion')
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.error(request, "Quelque chose d'anormal est survenu.")
            return redirect('intranet:creation_adhesion')

        admin = User.objects.get(is_superuser=True)
        user = request.user

        fac_name = "EFP_%s_%s" % (user.last_name, admin.userprofile.nb_facture)

        if request.user.is_staff:
            fac = Facture.objects.create(
                to_user=user, from_user=admin, object="Adhésion professeur", is_paid=True,
                object_qt=1, h_qt=1, tva=prix.tva, price_ht=1 * prix.adhesion_prof, price_ttc=price, type="Adhésion Professeur",
                facture_name=fac_name, nb_facture=admin.userprofile.nb_facture,
                to_user_firstname=user.first_name, to_user_lastname =user.last_name ,to_user_address =user.userprofile.address,
                to_user_city=user.userprofile.city, to_user_zipcode =user.userprofile.zip_code,
                to_user_siret=user.userprofile.siret, to_user_sap =user.userprofile.sap,
                from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
                from_user_address=admin.userprofile.address, from_user_city =admin.userprofile.city,
                from_user_zipcode=admin.userprofile.zip_code, from_user_siret =admin.userprofile.siret ,
                from_user_sap =admin.userprofile.sap,admin_address=admin.userprofile.address,
                admin_zipcode=admin.userprofile.zip_code, admin_city=admin.userprofile.city)
        else:
            nb = 1 if price == add_tva(prix.adhesion,prix.tva) else price/add_tva(prix.adhesion_reduc,prix.tva)
            # print("nb eleves:",nb)
            if nb == 1:
                fac = Facture.objects.create(
                    to_user=user, from_user=admin, object="Adhésion élève", is_paid=True,
                    object_qt=nb, h_qt=nb, tva=prix.tva, price_ht=nb * prix.adhesion, price_ttc=price, type="Adhésion Élève",
                    facture_name=fac_name, nb_facture=admin.userprofile.nb_facture,
                    to_user_firstname=user.first_name, to_user_lastname=user.last_name,
                    to_user_address=user.userprofile.address,
                    to_user_city=user.userprofile.city, to_user_zipcode=user.userprofile.zip_code,
                    to_user_siret=user.userprofile.siret, to_user_sap=user.userprofile.sap,
                    from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
                    from_user_address=admin.userprofile.address, from_user_city=admin.userprofile.city,
                    from_user_zipcode=admin.userprofile.zip_code, from_user_siret=admin.userprofile.siret,
                    from_user_sap=admin.userprofile.sap,admin_address=admin.userprofile.address,
                    admin_zipcode=admin.userprofile.zip_code, admin_city=admin.userprofile.city)
            else:
                fac = Facture.objects.create(
                    to_user=user, from_user=admin, object="Adhésion élèves", is_paid=True,
                    object_qt=nb, h_qt=nb,tva=prix.tva, price_ht=nb * prix.adhesion_reduc, price_ttc=price, type="Adhésion Élèves",
                    facture_name=fac_name, nb_facture=admin.userprofile.nb_facture,
                    to_user_firstname=user.first_name, to_user_lastname=user.last_name,
                    to_user_address=user.userprofile.address,
                    to_user_city=user.userprofile.city, to_user_zipcode=user.userprofile.zip_code,
                    to_user_siret=user.userprofile.siret, to_user_sap=user.userprofile.sap,
                    from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
                    from_user_address=admin.userprofile.address, from_user_city=admin.userprofile.city,
                    from_user_zipcode=admin.userprofile.zip_code, from_user_siret=admin.userprofile.siret,
                    from_user_sap=admin.userprofile.sap,admin_address=admin.userprofile.address,
                    admin_zipcode=admin.userprofile.zip_code, admin_city=admin.userprofile.city)

        fac.is_paid = True
        fac.save()
        user.userprofile.is_adherent=True
        user.userprofile.save()
        admin.userprofile.nb_facture += 1
        admin.userprofile.save()
        Adhesion.objects.create(to_user=user)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        messages.success(request, "Votre adhésion a bien été payée.")
        return redirect('intranet:accueil')
    else:
        messages.warning(request, 'Action non aurotisée.')
        return redirect('intranet:creation_adhesion')


    return redirect('intranet:creation_adhesion')

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
@user_passes_test(lambda u: u.userprofile.is_adherent)
def notifications(request):
    request.user.userprofile.nots_view = datetime.now()
    request.user.userprofile.save()
    nots = nb_new_notifs(request.user)
    """Minimal function rendering a template"""
    if request.user.is_superuser:
        notifications_list = list(reversed(Notification.objects.all()))
        page = request.GET.get('page', 1)
        paginator = Paginator(notifications_list, 10, 3)
        try:
            notifications_list_page = paginator.page(page)
        except PageNotAnInteger:
            notifications_list_page = paginator.page(1)
        except EmptyPage:
            notifications_list_page = paginator.page(paginator.num_pages)
    else:
        notifications_list = list(reversed(Notification.objects.filter(to_user=request.user)))
        page = request.GET.get('page', 1)
        paginator = Paginator(notifications_list, 10, 3)
        try:
            notifications_list_page = paginator.page(page)
        except PageNotAnInteger:
            notifications_list_page = paginator.page(1)
        except EmptyPage:
            notifications_list_page = paginator.page(paginator.num_pages)

    user = request.user
    return render(request, 'intranet/notifications.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def statistiques(request):
    """Minimal function rendering a template"""
    nots = nb_new_notifs(request.user)
    geo_list = UserProfile.objects.exclude(lat="0.0").exclude(lat="None")
    # print(geo_list)
    prof = User.objects.filter(is_staff=True, is_active=True).count()
    eleve = Eleve.objects.exclude(referent=None).count()
    compte = User.objects.exclude(is_staff=True, is_active=False).count()

    return render(request, 'intranet/statistiques.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def statistiques2(request):
    nots = nb_new_notifs(request.user)
    return render(request, 'intranet/statistiques2.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def graphs_membres(request):
    f = mtf.Figure()
    labels = 'Admin', 'Professeurs', 'Élèves'
    a = User.objects.filter(is_superuser=True).count()
    p = User.objects.filter(is_staff=True).exclude(is_superuser=True).count()
    s = User.objects.exclude(is_staff=True, is_active=False).count()
    sizes = [a,p,s]
    explode = (0, 0, 0.1)  # only "explode" the 2nd slice (i.e. 'Hogs')
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    canvas = FigureCanvasAgg(f)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(f)
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def graphs_stats(request):
    f = mtf.Figure()

    labels = ['Moteur de recherche Google', 'Facebook', 'Autre source internet',  'Annuaire(pages jaunes...)',
             'Nebout & Hamm', 'Falado', 'Connaissance(famille, amis...)']

    a = UserProfile.objects.filter(stats='A').count()
    b = UserProfile.objects.filter(stats='B').count()
    c = UserProfile.objects.filter(stats='C').count()
    d = UserProfile.objects.filter(stats='D').count()
    e = UserProfile.objects.filter(stats='E').count()
    f = UserProfile.objects.filter(stats='F').count()
    g = UserProfile.objects.filter(stats='G').count()
    sizes = [a,b,c,d,e,f,g]
    explode = (0, 0, 0, 0, 0, 0, 0)
    # print(sizes)
    fig2, ax2 = plt.subplots()
    ax2.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    # canvas = FigureCanvasAgg(f)
    # ax2.legend([a,b,c,d,e,f,g], labels)
    # ax2.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    # ax2.legend(loc='best')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(f)
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def graphs_nb_cours(request):
    f = mtf.Figure()
    fig, ax = plt.subplots()
    list_prof = User.objects.filter(is_staff=True, is_active=True)
    label_prof = [u.username for u in list_prof]
    times = last_3_mois()
    # print(times)
    ind = np.arange(3)
    width = 0.35
    plts = []
    data = [[0 if not Lesson.objects.filter(mois=t, relation__teacher=prof) else Lesson.objects.filter(mois=t, relation__teacher=prof).aggregate(Sum('nb_h'))['nb_h__sum'] for t in times]for prof in list_prof]
    # data = [[Cour.objects.filter(mois=t, relation__teacher=prof) for t in times]for prof in list_prof]
    m = max(max(zip(*data)))
    for it,d in enumerate(data,1):
        bottom_counter=0
        # tmp = plt.bar(ind + width*it, d, width, label=label_prof[it-1], bottom=bottom_counter)
        tmp = ax.bar(ind, d, width, label=label_prof[it-1], bottom=bottom_counter)
        # bottom_counter+=it
        plts.append(tmp)

    plt.xticks(ind, [conv_mois(t) for t in times])
    ax.set_yticks(np.arange(0, m+4, 2))
    ax.set_ylabel('temps de cours (H)')
    ax.set_title('Temps de cours par professeurs et par mois')
    ax.legend(loc='best')

    canvas = FigureCanvasAgg(f)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(f)
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def graphs_evol(request):
    f = mtf.Figure()
    stats = Stats.objects.all()
    labels = [ x.date for x in stats]
    nb_prof = [ x.nb_prof for x in stats]
    nb_user = [ x.nb_user for x in stats]
    nb_eleve = [ x.nb_eleve for x in stats]

    fig, ax1 = plt.subplots()
    l1, = ax1.plot(nb_prof, label="professeurs")
    l2, = ax1.plot(nb_user, label="utilisateurs")
    l3, = ax1.plot(nb_eleve, label="élèves")
    plt.xticks(np.arange(len(stats)),labels)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Nbr de personnes')
    ax1.set_title('Evolution du nombre d\'utilisateurs')
    ax1.legend([l1, l2,l3], ["professeurs","utilisateurs","élèves"])
    # ax1.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    canvas = FigureCanvasAgg(f)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(f)
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_articles(request):
    """Members template to display all the members"""
    nots = nb_new_notifs(request.user)
    form = ArticleForm()
    return render(request, 'intranet/gestion_articles.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_membres(request):
    nots = nb_new_notifs(request.user)
    """Members template to display all the members"""
    users_list = User.objects.filter(is_active=True)
    return render(request, 'intranet/gestion_membres.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_relations(request):
    nots = nb_new_notifs(request.user)
    relations_list = Relation.objects.all()
    form2 = RelationForm()
    return render(request, 'intranet/gestion_relations.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_invitations(request):
    nots = nb_new_notifs(request.user)
    invitations_list = list(reversed(Invitation.objects.all()))
    page = request.GET.get('page', 1)
    paginator = Paginator(invitations_list, 10)
    try:
        invit_page = paginator.page(page)
    except PageNotAnInteger:
        invit_page = paginator.page(1)
    except EmptyPage:
        invit_page = paginator.page(paginator.num_pages)
    form = InvitationForm()
    return render(request, 'intranet/gestion_invitations.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_prix(request):
    nots = nb_new_notifs(request.user)
    prix_list = reversed(Prix.objects.all())
    form = PrixForm()
    return render(request, 'intranet/gestion_prix.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_mail(request):
    nots = nb_new_notifs(request.user)
    mail_form = MailForm()
    formset = ToMailFormset()
    return render(request, 'intranet/gestion_mail.html', locals())


@login_required
@user_passes_test(lambda u: u.is_superuser)
def relation(request):
    if request.method == "POST":
        form = RelationForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data["eleve"]
            teacher = form.cleaned_data["professeur"]
            Relation.objects.get_or_create(student=student,teacher=teacher)
            messages.success(request,'La relation a bien été créée.')
            return redirect('intranet:gestion_relations')
        else:
            messages.warning(request, 'Impossible de créer la relation.')
            return redirect('intranet:gestion_relations')

    return redirect('intranet:gestion_relations')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def prix(request):
    if request.method == "POST":
        form = PrixForm(request.POST)
        if form.is_valid():
            tva = form.cleaned_data["tva"]
            adhesion = form.cleaned_data["adhesion"]
            adhesion_reduc = form.cleaned_data["adhesion_reduc"]
            adhesion_prof = form.cleaned_data["adhesion_prof"]
            cours = form.cleaned_data["cours"]
            cours_premium = form.cleaned_data["cours_premium"]
            cours_ecole = form.cleaned_data["cours_ecole"]
            commission = form.cleaned_data["commission"]
            frais_gestion = form.cleaned_data["frais_gestion"]
            if Prix.objects.all():
                last_price = Prix.objects.get(end=None)
                last_price.end = date.today()
                last_price.save()
            Prix.objects.get_or_create(tva=tva,adhesion=adhesion,cours=cours,commission=commission,frais_gestion=frais_gestion,
                                       adhesion_reduc=adhesion_reduc, adhesion_prof=adhesion_prof,cours_premium=cours_premium,
                                       cours_ecole=cours_ecole)
            messages.success(request,'Le changement de prix a bien été pris en compte. Il sera effectif à partir de minuit.')
            return redirect('intranet:gestion_prix')
        else:
            messages.warning(request, 'Impossible de modifier les prix.')
            return redirect('intranet:gestion_prix')

    return redirect('intranet:gestion_prix')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def invitation(request):
    if request.method == "POST":
        form = InvitationForm(request.POST)
        if form.is_valid():
            mail = form.cleaned_data["email"]
            is_staff = form.cleaned_data["is_staff"]
            is_free = form.cleaned_data["is_free"]
        else:
            messages.warning(request, 'Impossible d\'envoyer l\'invitation.')
            return redirect('intranet:gestion_invitations')

        current_site = get_current_site(request)
        my_uuid = str(uuid.uuid4())
        context = { 'protocol': 'https', 'domain': current_site.domain, 'site_name': current_site.name, 'uuid': my_uuid}
        msg_plain = render_to_string('email/email_invitation.txt', context=context)
        msg_html = render_to_string('email/email_invitation.html', context=context)
        send_mail(
            'Inscrivez-vous sur l\'intranet de l\'EFP !',
            msg_plain,
            settings.DEFAULT_FROM_EMAIL,
            [mail],
            html_message=msg_html,
        )
        inv = Invitation.objects.create(uuid=my_uuid, email=mail, is_staff=is_staff, is_free=is_free)
        messages.success(request, 'L\'invitation a bien été envoyée.')
    return redirect('intranet:gestion_invitations')

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
def mon_compte(request):
    nots = nb_new_notifs(request.user)
    user = User.objects.get(id=request.user.id)
    adh = Adhesion.objects.filter(to_user=user)[0]
    eleves = Eleve.objects.filter(referent=request.user)
    return render(request, 'intranet/mon_compte.html',locals())

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
@user_passes_test(lambda u: u.is_staff)
def stripe_connect(request):
    code = request.GET.get('code', '')
    # print(code)
    if code == '':
        messages.error(request,"Impossible de lier votre compte stripe.")
    else:
        #CRITICAL POINT HERE
        r = requests.post("https://connect.stripe.com/oauth/token", data={'client_secret': settings.STRIPE_SECRET_KEY, 'code': code, 'grant_type': 'authorization_code'})
        res = json.loads(r.text)
        secret = res['stripe_user_id']
        print(secret)
        request.user.userprofile.stripe_account_id = secret
        request.user.userprofile.save()
        messages.success(request, "Votre compte Stripe à bien été liéé.")
    return redirect('intranet:mon_compte')

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
def edit_compte(request):
    nots = nb_new_notifs(request.user)
    if request.method == 'POST':
        form_user = EditUserForm(request.POST, instance=request.user)
        form_profile = EditStaffProfileForm(request.POST, instance=request.user.userprofile) if request.user.is_staff else EditProfileForm(request.POST, instance=request.user.userprofile)
        if form_profile.is_valid() and form_user.is_valid():
            form_user.save()
            form_profile.save()
            messages.success(request,'Vos informations personnelles ont bien été modifiées.')
            address = form_profile.cleaned_data["address"]
            city = form_profile.cleaned_data["city"]
            zip_code = form_profile.cleaned_data["zip_code"]
            country = form_profile.cleaned_data["country"]
            # print(address, city, zip_code, country)
            location = "%s %s %s %s" % (address,city,zip_code,country)
            r = requests.get('http://www.mapquestapi.com/geocoding/v1/address?key=7MspWFOeqU2eH72DNDg8LM6sTXKcaQmz&location=%s' % location)
            us = User.objects.get(pk=request.user.pk)
            if r.status_code == requests.codes.ok:
                data = json.loads(r.text)
                # print(json.dumps(data,indent=4))
                try:
                    # print(data["results"][0]['locations'][0]['latLng']['lat'], data["results"][0]['locations'][0]['latLng']['lng'])
                    us.userprofile.lat = data["results"][0]['locations'][0]['latLng']['lat']
                    us.userprofile.lgn = data["results"][0]['locations'][0]['latLng']['lng']
                    us.userprofile.save()
                except:
                    pass

            admin = User.objects.get(is_superuser=True)
            Notification.objects.create(to_user=admin, from_user=request.user,
                                        object="Modifications des informations %s %s (%s)" % (request.user.first_name, request.user.last_name, request.user),
                                        text="Je viens de modifier mes informations, pour voir mon nouveau profil:")
            return redirect('intranet:mon_compte')
    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = EditStaffProfileForm(instance=request.user.userprofile) if request.user.is_staff else EditProfileForm(instance=request.user.userprofile)
        return render(request, 'intranet/edit_compte.html', locals())

def edit_pass(request):
    nots = nb_new_notifs(request.user)
    if request.method == 'POST':
        # form = PasswordChangeForm(data=request.POST, user=request.user)
        form = PasswordChangeForm(request.user,request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Votre mot de passe  a bien été modifié.")
            return redirect('intranet:mon_compte')
        else:
            messages.error(request, "Impossible de modifier votre mot de passe.")
            return redirect('intranet:edit_pass')
    else:
        form = PasswordChangeForm(request.user)
        return render(request, 'intranet/edit_pass.html',  locals())

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
def add_eleve(request):
    nots = nb_new_notifs(request.user)
    prix = Prix.objects.get(end=None)
    admin = User.objects.get(is_superuser=True)
    if request.method == 'POST':
        form = EditEleveForm(request.POST)
        if form.is_valid():
            np = form.cleaned_data["nom_prenom"]
            Eleve.objects.create(referent=request.user, nom_prenom=np)
            to_user = request.user
            fac_name = "EFP_%s_%s" % (to_user.last_name, admin.userprofile.nb_facture)
            fac = Facture.objects.create(
                to_user=to_user, from_user=admin, object="Adhésion élève supp.", is_paid=False,
                object_qt=1, h_qt=1, tva=prix.tva, price_ht=prix.adhesion_reduc,
                price_ttc=add_tva(prix.adhesion_reduc, prix.tva), type="Adhésion élève supplémentaire",
                facture_name=fac_name, nb_facture=admin.userprofile.nb_facture,
                to_user_firstname=to_user.first_name, to_user_lastname=to_user.last_name,
                to_user_address=to_user.userprofile.address,
                to_user_city=to_user.userprofile.city, to_user_zipcode=to_user.userprofile.zip_code,
                to_user_siret=to_user.userprofile.siret, to_user_sap=to_user.userprofile.sap,
                from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
                from_user_address=admin.userprofile.address, from_user_city=admin.userprofile.city,
                from_user_zipcode=admin.userprofile.zip_code, from_user_siret=admin.userprofile.siret,
                from_user_sap=admin.userprofile.sap,admin_address=admin.userprofile.address,
                admin_zipcode=admin.userprofile.zip_code, admin_city=admin.userprofile.city)
            admin.userprofile.nb_facture += 1
            admin.userprofile.save()
            messages.success(request, "Le nouvel élève a bien été ajouté.")
            return redirect('intranet:mon_compte')
        else:
            messages.warning(request,"Impossible d'ajouter un élève.")
            return redirect('intranet:mon_compte')

    else:
        form = EditEleveForm()
    return render(request, 'intranet/add_eleve.html', locals())

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
def remove_eleve(request, id):
    e = Eleve.objects.get(pk=id)
    if request.user != e.referent:
        messages.error(request, "Impossible d'effectuer cette action.")
        return redirect('intranet:mon_compte')

    eleves = Eleve.objects.filter(referent=request.user)
    if len(eleves) == 1:
        messages.warning(request,"Vous devez avoir au minimum un élève.")
        return redirect('intranet:mon_compte')
    else:
        e.referent = None
        e.save()
        messages.success(request, "Élève supprimé.")
    return redirect('intranet:mon_compte')

@login_required
def remove_eleve_adh(request, id):
    e = Eleve.objects.get(pk=id)
    if request.user != e.referent:
        messages.error(request, "Impossible d'effectuer cette action.")
        return redirect('intranet:creation_adhesion')

    eleves = Eleve.objects.filter(referent=request.user)
    if len(eleves) == 1:
        messages.warning(request,"Vous devez avoir au minimum un élève.")
        return redirect('intranet:creation_adhesion')
    else:
        e.referent = None
        e.save()
        messages.success(request, "Élève supprimé.")
    return redirect('intranet:creation_adhesion')

@login_required
def remove_eleve_cr(request, id):
    e = Eleve.objects.get(pk=id)
    if request.user != e.referent:
        messages.error(request, "Impossible d'effectuer cette action.")
        return redirect('intranet:creation_eleves')

    eleves = Eleve.objects.filter(referent=request.user)
    if len(eleves) == 1:
        messages.warning(request,"Vous devez avoir au minimum un élève.")
        return redirect('intranet:creation_eleves')
    else:
        e.referent = None
        e.save()
        messages.success(request, "Élève supprimé.")
    return redirect('intranet:creation_eleves')

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
def edit_eleve(request, id):
    nots = nb_new_notifs(request.user)
    e = Eleve.objects.get(pk=id)
    if request.user != e.referent:
        return redirect('intranet:mon_compte')

    if request.method == 'POST':
        form = EditEleveForm(request.POST)
        if form.is_valid():
            np = form.cleaned_data["nom_prenom"]
            e.nom_prenom = np
            e.save()
            messages.success(request, "Changements validés.")
            return redirect('intranet:mon_compte')
        else:
            messages.warning(request,"Impossible de valider les changements.")
            return redirect('intranet:mon_compte')

    else:
        form = EditEleveForm(instance=e)
    return render(request, 'intranet/edit_eleve.html', locals())

@login_required
# @user_passes_test(lambda u: u.userprofile.is_adherent)
def edit_eleve_adh(request, id):
    nots = nb_new_notifs(request.user)
    e = Eleve.objects.get(pk=id)
    if request.user != e.referent:
        messages.warning(request,"Action impossible")
        return redirect('intranet:creation_adhesion')

    if request.method == 'POST':
        form = EditEleveForm(request.POST)
        if form.is_valid():
            np = form.cleaned_data["nom_prenom"]
            e.nom_prenom = np
            e.save()
            messages.success(request, "Changements validés.")
            return redirect('intranet:creation_adhesion')
        else:
            messages.warning(request,"Impossible de valider les changements.")
            return redirect('intranet:creation_adhesion')

    else:
        form = EditEleveForm(instance=e)
    return render(request, 'intranet/edit_eleve.html', locals())

@login_required
# @user_passes_test(lambda u: u.userprofile.is_adherent)
def edit_eleve_cr(request, id):
    nots = nb_new_notifs(request.user)
    e = Eleve.objects.get(pk=id)
    if request.user != e.referent:
        messages.warning(request, "Action impossible")
        return redirect('intranet:creation_eleves')

    if request.method == 'POST':
        form = EditEleveForm(request.POST)
        if form.is_valid():
            np = form.cleaned_data["nom_prenom"]
            e.nom_prenom = np
            e.save()
            messages.success(request, "Changements validés.")
            return redirect('intranet:creation_eleves')
        else:
            messages.warning(request,"Impossible de valider les changements.")
            return redirect('intranet:creation_eleves')

    else:
        form = EditEleveForm(instance=e)
    return render(request, 'intranet/edit_eleve.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST or None, request.FILES)
        if form.is_valid():
            contenu = form.cleaned_data["contenu"]
            titre = form.cleaned_data["titre"]
            lien = form.cleaned_data["lien"]
            photo = form.cleaned_data["photo"]
            print(lien)
            if lien:
                if re.match(r'^https?:\/\/', lien):
                    pass
                else:
                    lien = 'https://' + lien

            Article.objects.create(titre=titre,contenu=contenu,lien=lien,photo=photo)
            messages.success(request,"Votre Article a bien été créé.")
            return redirect('intranet:accueil')

    messages.warning(request, "Impossible de rédiger votre article.")
    return redirect('intranet:gestion_articles')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def mail(request):
    if request.method == 'POST':
        form = MailForm(request.POST)
        formset = ToMailFormset(request.POST)
        # print(request.POST)
        # print(formset)
        if form.is_valid() and formset.is_valid():
            objet = form.cleaned_data["objet"]
            message = form.cleaned_data["message"]
            tlp = form.cleaned_data["tlp"]
            tle = form.cleaned_data["tle"]
            # print(tle,tlp)
            address = []
            if tle:
                address += [ x.email for x in User.objects.filter(is_staff=False, is_active=True)]
            if tlp:
                address += [ x.email for x in User.objects.filter(is_staff=True, is_active=True)]

            for f in formset:
                # extract name from each form and save
                email = f.cleaned_data.get('name')
                if email:
                    address.append(email)

            print(address)
            send_mail(objet,message,settings.DEFAULT_FROM_EMAIL,address)
            messages.success(request,"Votre email a bien été envoyée")
            return redirect('intranet:gestion_mail')

    messages.warning(request, "Impossible d'envoyer votre email")
    return redirect('intranet:gestion_mail')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_condition(request):
    nots = nb_new_notifs(request.user)
    if request.method == 'POST':
        form = CondiForm(request.POST, request.FILES)
        # print(form)
        if form.is_valid():
            if Condition.objects.all().count() > 0:
                last = Condition.objects.get(end=False)
                last.end = True
                last.save()
                form.save()
            else :
                form.save()
            messages.success(request,'Les Confitions générale d\'utilisation ont bien été modifiées')
            return redirect('intranet:gestion_condition')
        else:
            messages.error(request, 'Impossible de télécharger le fichier')
            return redirect('intranet:gestion_condition')
    else:
        form = CondiForm()
        return render(request, 'intranet/gestion_condition.html', locals())


def handle_uploaded_file(f):
    with open('some/file/name.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_factures(request):
    nots = nb_new_notifs(request.user)
    if request.method == 'POST':
        form = FactureForm(request.POST)
        print(form)
        if form.is_valid():
            f_user = form.cleaned_data["from_user"]
            t_user = form.cleaned_data["to_user"]
            object = form.cleaned_data["object"]
            nb_item = form.cleaned_data["nb_item"]
            tva = form.cleaned_data["tva"]
            prix_ht = form.cleaned_data["prix_ht"]

            #TODO
            to_user = User.objects.get(username=t_user)
            from_user = User.objects.get(username=f_user)
            if from_user == 'admin':
                fac_name = "EFP_%s_%s" % (to_user, from_user.userprofile.nb_facture)
            else:
                fac_name = "%s_%s_%s" % ( from_user.last_name, to_user.last_name, from_user.userprofile.nb_facture)

            choix = {
                'cp': 'Cours de piano',
                'fg': 'Frais de gestion',
                'fc': 'Frais de commission',
                'fa': 'Frais d\'adhésion',
                'fp': 'Frais de préavis'
            }

            obj = choix[object]
            admin = User.objects.get(is_superuser=True)
            fac = Facture.objects.create(
                to_user=to_user, from_user=from_user, object=obj, is_paid=False,
                object_qt=nb_item, h_qt=nb_item, tva=tva, price_ht=nb_item * prix_ht, price_ttc=add_tva(nb_item*prix_ht,tva), type=obj,
                facture_name=fac_name, nb_facture=from_user.userprofile.nb_facture,
                to_user_firstname=to_user.first_name, to_user_lastname=to_user.last_name,
                to_user_address=to_user.userprofile.address,
                to_user_city=to_user.userprofile.city, to_user_zipcode=to_user.userprofile.zip_code,
                to_user_siret=to_user.userprofile.siret, to_user_sap=to_user.userprofile.sap,
                from_user_firstname=from_user.first_name, from_user_lastname=from_user.last_name,
                from_user_address=from_user.userprofile.address, from_user_city=from_user.userprofile.city,
                from_user_zipcode=from_user.userprofile.zip_code, from_user_siret=from_user.userprofile.siret,
                from_user_sap=from_user.userprofile.sap,admin_address=admin.userprofile.address,
                admin_zipcode=admin.userprofile.zip_code, admin_city=admin.userprofile.city)

            from_user.userprofile.nb_facture += 1
            from_user.userprofile.save()

            Notification.objects.create(to_user=to_user, from_user=from_user,
                                        object="Ajout d'une nouvelle facture entre %s et %s" % (to_user, from_user),
                                        text="L'administrateur de l'EFP vient d'ajouter une nouvelle facture vous concernant!")

            messages.success(request, 'La nouvelle facture a bien été créée.')
            return redirect('intranet:gestion_factures')
        else:
            messages.error(request, 'Impossible de télécharger le fichier')
            return redirect('intranet:gestion_factures')
    else:
        form=FactureForm()
    return render(request, 'intranet/gestion_factures.html', locals())


@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_examens(request):
    nots = nb_new_notifs(request.user)
    if request.method == 'POST':
        form = ExamenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"L'examen a bien été créé.")
            return redirect('intranet:gestion_examens')
        else:
            messages.warning(request, "Impossible de créer l'examen.")
            return redirect('intranet:gestion_examens')
    else:
        examens = Examen.objects.all()
        if examens:
            exam = examens[0]
            eleves_inscrit = InscriptionExamen.objects.filter(examen=exam)
            nb = eleves_inscrit.count()
        else:
            form=ExamenForm()
    return render(request, 'intranet/gestion_examens.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def remove_examens(request,id):
    exam = get_object_or_404(Examen, pk=id)
    if exam:
        exam.delete()
        messages.success(request,"Examen correctement supprimé.")
    else:
        messages.warning(request, "Impossible de supprimé l'examen.")
    return redirect('intranet:gestion_examens')

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
def examens_eleve(request):
    nots = nb_new_notifs(request.user)
    key = settings.STRIPE_PUBLISHABLE_KEY
    ex_list = Examen.objects.all()
    prix = Prix.objects.get(end=None)
    if ex_list:
        ex = ex_list[0]
        diff = ex.last - date.today()
        if diff.days > 0:
            exam = ex
            exam_ttc = add_tva(exam.price,prix.tva)
            eleves = Eleve.objects.filter(referent=request.user)
            eleves_inscrit = InscriptionExamen.objects.filter(examen=exam,eleve__in=eleves)
            if eleves_inscrit:
                test = [e.eleve.id for e in eleves_inscrit]
                eleves_non_inscrit = Eleve.objects.filter(referent=request.user).exclude(id__in=test)
            else:
                eleves_non_inscrit = eleves
            print("E",eleves)
            print("EI",eleves_inscrit)
            print("EN",eleves_non_inscrit)

    return render(request, 'intranet/examens_eleve.html', locals())

@login_required
@user_passes_test(lambda u: u.userprofile.is_adherent)
def checkout_exam(request):
    admin = User.objects.get(is_superuser=True)
    prix = Prix.objects.get(end=None)
    if request.method == "POST":
        form = PriceForm(request.POST)
        if form.is_valid():
            eleve_id = form.cleaned_data["fac_id"]
            token = request.POST['stripeToken']
            eleve = get_object_or_404(Eleve,pk=eleve_id)
            ex_list = Examen.objects.all()
            if ex_list:
                exam = ex_list[0]
            else:
                messages.warning(request, 'Action non aurotisée.')
                return redirect('intranet:examens_eleve')

            description = "EFP_%s_%s_examen" % (request.user.last_name,admin.userprofile.nb_facture)
            price = add_tva(exam.price,prix.tva)
            try:
                charge = stripe.Charge.create(
                    amount=int(round(price, 2) * 100),
                    currency="eur",
                    description=description,
                    source=token
                )
            except stripe.error.CardError as e:
                messages.error(request, "Votre carte a été refusée")
                body = e.json_body
                err = body.get('error', {})
                print("Status is: %s" % e.http_status)
                print("Type is: %s" % err.get('type'))
                print("Code is: %s" % err.get('code'))
                print("Param is: %s" % err.get('param'))
                print("Message is: %s" % err.get('message'))
                return redirect('intranet:examens_eleve')
            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.error(request, "Erreur de connexion avec l'API Stripe.")
                return redirect('intranet:examens_eleve')
            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.error(request, "Les paramètres transmis ne sont pas correctes.")
                return redirect('intranet:examens_eleve')
            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.error(request, "Les clefs de l'API ne sont pas bonnes.")
                return redirect('intranet:examens_eleve')
            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.error(request, "Problème de connection réseaux.")
                return redirect('intranet:examens_eleve')
            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.error(request, "Quelque chose d'anormal est survenu.")
                return redirect('intranet:examens_eleve')
            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                messages.error(request, "Quelque chose d'anormal est survenu.")
                return redirect('intranet:examens_eleve')

            user = request.user
            fac_name = "EFP_%s_%s" % (user.last_name, admin.userprofile.nb_facture)

            fac = Facture.objects.create(
                to_user=user, from_user=admin, object="Inscription examen", is_paid=True,
                object_qt=1, h_qt=1, tva=prix.tva, price_ht=1 * exam.price, price_ttc=add_tva(exam.price,prix.tva), type="Inscription examen",
                facture_name=fac_name, nb_facture=admin.userprofile.nb_facture,
                to_user_firstname=user.first_name, to_user_lastname =user.last_name ,to_user_address =user.userprofile.address,
                to_user_city=user.userprofile.city, to_user_zipcode =user.userprofile.zip_code,
                to_user_siret=user.userprofile.siret, to_user_sap =user.userprofile.sap,
                from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
                from_user_address=admin.userprofile.address, from_user_city =admin.userprofile.city,
                from_user_zipcode=admin.userprofile.zip_code, from_user_siret =admin.userprofile.siret ,
                from_user_sap =admin.userprofile.sap,admin_address=admin.userprofile.address,
                admin_zipcode=admin.userprofile.zip_code, admin_city=admin.userprofile.city)

            fac.is_paid = True
            fac.save()
            admin.userprofile.nb_facture += 1
            admin.userprofile.save()
            InscriptionExamen.objects.create(eleve=eleve,examen=exam)
            messages.success(request, "Votre élève a bien été inscrit à l'examen.")
            return redirect('intranet:examens_eleve')
        else:
            messages.warning(request, 'Action non aurotisée.')
            return redirect('intranet:examens_eleve')
    else:
        messages.warning(request,'Action non aurotisée.')
    return redirect('intranet:examens_eleve')