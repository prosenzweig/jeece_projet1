from django.http import *
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.urls import reverse
from datetime import datetime,timedelta,date

import uuid
from django.contrib.sites.shortcuts import get_current_site

from django.core.mail import send_mail
from django.template.loader import render_to_string

from django.contrib.auth.models import User
from intranet.models import Article,UserProfile,Invitation,Relation,Cour,Notification,Prix,Facture,Eleve
from django.db.models import Q, Sum

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import static
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

import requests
import numpy as np

from pinax.stripe.actions import customers

import tempfile
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
    EleveFormset, PriceForm

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["Janvier", u"Février", "Mars", "Avril", "Mai", "Juin", "Juillet", u"Août", "Septembtre", "Octobre"]

def conv_mois(value):
    try:
        m =value.split('_')
        return '%s %s' % (mois[int(m[0])-1], m[1])
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
        return float(value) + float(value)*float(arg)/100
    except (ValueError, ZeroDivisionError):
        return None

# Frais de Gestion PDF
def gen_pdf(request,fac_id):
    # Create the HttpResponse object with the appropriate PDF headers.
    facture = get_object_or_404(Facture,pk=fac_id)
    if not request.user.is_superuser:
        if facture.to_user != request.user:
            messages.warning(request,"Impossible d'accéder à la facture !")
            return redirect('intranet:documents')


    response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = 'attachment;filename=facture_%s.pdf' % facture.pk
    response['Content-Disposition'] = 'filename=facture_%s.pdf' % facture.pk
    buffer = BytesIO()

    p = canvas.Canvas(buffer)
    logo = ImageReader("https://scontent-cdt1-1.xx.fbcdn.net/v/t1.0-9/10435640_175219366143139_807238508633238110_n.png?_nc_cat=0&oh=f71fd724af3b36a77c5e2369a880beff&oe=5BEF1DBB")
    # logo = ImageReader("https://static.wixstatic.com/media/ac3cde_87eef0b3e8904e2eb87cf9c4b69c6baa.png/v1/fill/w_61,h_61,al_c,q_80,usm_0.66_1.00_0.01/ac3cde_87eef0b3e8904e2eb87cf9c4b69c6baa.webp")

    p.drawImage(logo, 50, 600, mask='auto')
    p.setLineWidth(.3)
    H, L = 830, 587
    p.setFont('Helvetica-Bold', 16)
    p.drawString(350, 720, "Factures #%s" % facture.pk)
    p.setFont('Helvetica', 12)
    p.drawString(350, 705, "Date de Facturation: %s" % facture.created.strftime("%d/%m/%Y"))
    p.drawString(350, 690, "Date d'échéance: %s" % facture.last.strftime("%d/%m/%Y"))

    # Emetteur
    if facture.type in ['Frais de Gestion', 'Frais de Commission']:
        p.setFont('Helvetica-Bold', 12)
        p.drawString(50, 580, "Ecole Française de Piano")
        p.setFont('Helvetica', 12)
        p.drawString(50, 565, "Emmanuel BIRNBAUM")
        p.drawString(50, 550, "4 Rue du Champ de l'Alouette")
        p.drawString(50, 535, "75013 Paris")
        p.drawString(50, 520, "01 85 09 93 87")
        p.drawString(50, 505, "info@ecolefrancaisedepiano.fr")
        p.drawString(50, 490, "https://www.ecolefrancaisedepiano.fr")

    else:
        p.setFont('Helvetica-Bold', 12)
        p.drawString(50, 580, "%s %s" % (facture.from_user.last_name, facture.from_user.first_name))
        p.setFont('Helvetica', 12)
        p.drawString(50, 565, "%s"  % facture.from_user.userprofile.address)
        p.drawString(50, 550, "%s %s" % (facture.from_user.userprofile.zip_code, facture.from_user.userprofile.city))
        p.drawString(50, 535, "France")

    # Destinataire
    p.setFont('Helvetica-Bold', 12)
    p.drawString(350, 580, "%s %s" % (facture.to_user.last_name, facture.to_user.first_name))
    p.setFont('Helvetica', 12)
    p.drawString(350, 565, "%s" % facture.to_user.userprofile.address)
    p.drawString(350, 550, "%s %s" % (facture.to_user.userprofile.zip_code, facture.to_user.userprofile.city))
    p.drawString(350, 535, "France")

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
    p.drawString(350, 340, "%s€" % str(facture.price_ht/facture.object_qt))
    p.drawString(450, 340, "{0}%".format(facture.tva))
    p.drawString(510, 340, "%s€" % facture.price_ttc)
    p.line(50,330,551,330)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(440, 315, "Total (HT)")
    p.drawString(440, 300, "TVA {0}%".format(facture.tva))
    p.drawString(510, 315, "%s €" % facture.price_ht)
    p.drawString(510, 300, "%s €" % round(facture.price_ttc-facture.price_ht,2))
    p.line(440, 290, 551, 290)
    p.setFont('Helvetica-Bold', 12)
    p.drawString(440, 270, "Total (TTC)")
    p.drawString(510, 270, "%s €" % facture.price_ttc)

    p.setFont('Helvetica-Bold', 11)
    p.drawString(50, 220, "Echéance:")
    p.setFont('Helvetica', 11)
    p.drawString(200, 220, "%s" % facture.last.strftime("%d/%m/%Y"))


    p.setFont('Helvetica-Bold', 10)
    p.drawCentredString(300,60,'Ecole Française de Piano - SASU EFP')
    p.setFont('Helvetica-Oblique', 8)
    p.drawCentredString(300,45,'4 Rue du Champ de l\'Alouette 75013 Paris')
    p.drawCentredString(300,30,'Numéro de SIRET: 811 905 934 00014 - Numéro de TVA: FR 90 811905934 - 811 905 934 R.C.S.Paris')

    p.showPage()
    p.save()
    # Get the value of the BytesIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

def gen_attest_pdf(request):
    # fac_id
    # Create the HttpResponse object with the appropriate PDF headers.
    facture = get_object_or_404(Facture,pk=1)
    if not request.user.is_superuser:
        if facture.to_user != request.user:
            messages.warning(request,"Impossible d'accéder à la facture !")
            return redirect('intranet:documents')


    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename=attestation_%s.pdf' % facture.pk
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    p.setLineWidth(.3)
    H, L = 830, 587

    # Emetteur
    p.setFont('Helvetica', 12)
    p.drawString(75, 780, "%s %s" % (facture.from_user.last_name, facture.from_user.first_name))
    p.drawString(75, 765, "%s" % facture.from_user.userprofile.address)
    p.drawString(75, 750, "%s %s" % (facture.from_user.userprofile.zip_code, facture.from_user.userprofile.city))
    p.drawString(75, 735, "France")
    p.drawString(75, 720, "N° SIRET : %s" % facture.from_user.userprofile.siret)
    p.drawString(75, 705, "N° SAP : %s" % facture.from_user.userprofile.sap)


    p.drawString(350, 682, "Déclaration N°EFP%s - %s" % (facture.pk,facture.created.strftime("%d/%m/%Y")))

    # Destinataire
    p.drawString(75, 660, "%s %s" % (facture.to_user.last_name, facture.to_user.first_name))
    p.drawString(75, 645, "%s" % facture.to_user.userprofile.address)
    p.drawString(75, 630, "%s %s" % (facture.to_user.userprofile.zip_code, facture.to_user.userprofile.city))
    p.drawString(75, 615, "France")

    p.setFont('Helvetica-Bold', 14)
    p.drawString(150, 550, "ATTESTATION FISCALE ANNUELLE - %s" % facture.pk)
    p.setFont('Helvetica', 12)
    p.drawString(75, 520, "Je soussigné, %s %s, professeur indépendant de piano, certifie que M et Mme %s," % (facture.from_user.first_name, facture.from_user.last_name ,facture.to_user.last_name))
    p.drawString(75, 505, "domiciliés au %s, %s %s, ont bénéficié de services à la personne :" % (facture.to_user.userprofile.address, facture.to_user.userprofile.zip_code ,facture.to_user.userprofile.city))
    p.drawString(75, 490, "cours de piano")
    p.drawString(75, 460, "En %s, le montant des factures effectivement acquittées représente" % (datetime.now().year-1))
    p.drawString(75, 445, "une somme totale de : %s€." % facture.price_ttc)

    p.setFont('Helvetica-Bold', 12)
    p.drawString(75,400, "Intervenant :")
    p.setFont('Helvetica', 12)
    p.drawString(75, 380, "Julie ALCARAZ - 3 heures pour l’année 2017")
    p.drawString(75, 365, "Prix horaire de la prestation : 41€/heure")

    p.drawString(75, 330, "Fait pour valoir ce que de droit,")
    p.drawString(75, 300, "Le 15/04/2018")
    p.drawString(75, 270, "Julie ALCARAZ")
    p.setFont('Helvetica', 11)
    p.drawString(75, 230, "Afin de bénéficier de l'avantage fiscal au titre du Service à la Personne, veuillez")
    p.drawString(75, 215, "remplir la case de votre déclaration d'impôts correspondant au crédit et")
    p.drawString(75, 200, "réduction d'impôt pour l'emploi à domicile en page 4, partie 7, rubrique \"Sommes")
    p.drawString(75, 185, "versées pour l'emploi à domicile\". Case 7DB, 7DF ou 7DD en fonction de votre")
    p.drawString(75, 170, "situation sur l'année écoulée.")

    p.setFont('Helvetica-Oblique', 8)
    p.drawCentredString(300, 45, 'Attestation fiscale établie au nom et pour le compte de %s %s par la société :' % (facture.from_user.first_name, facture.from_user.last_name.upper()))
    p.drawCentredString(300, 30, 'SASU EFP - Siret n°811 905 934 00014 - 811 905 934 R.C.S.Paris - 4 rue du Champ de l\'Alouette Paris 13ème - info@ecolefrancaisedepiano.fr')





    p.showPage()
    p.save()
    # Get the value of the BytesIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

def deconnexion(request):
    logout(request)
    return redirect(reverse('intranet:connexion'))

def connexion(request):
    error = False
    print (request.user)
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
    print(inv)
    if inv.valid:
        messages.error(request, 'Votre invitation n\'est plus valide!')
    else:
        if request.method == "POST":
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_staff = inv.is_staff
                user.save()
                inv.valid = True
                inv.save()

                #Test Create new customer for each new accoutns
                customers.create(user=user)

                # test.backend = 'django.contrib.auth.backends.ModelBackend'
                # login(request, test)
                #TODO change this
                # messages.success(request, 'Bienvenue l\'intranet, modifiez vos informations dans "Mon Compte".')
                return redirect('intranet:accueil') # nous le renvoyons vers la page accueil.html
            else:  # sinon une erreur sera affichée
                messages.warning(request,'Impossible de vous inscrire.')
        else:
            form = RegistrationForm()

    return render(request, 'intranet/creation.html', locals())


@login_required
def accueil(request):
    if not request.user.userprofile.is_adherent:
        return redirect('intranet:creation_adhesion')

    """ Redirection apres connexion, ici seront afficher les articles du blog"""
    articles_list = reversed(Article.objects.all()) # Nous sélectionnons tous nos articles
    return render(request, 'intranet/accueil.html', locals())

def creation_inscription(request):
    if request.method == 'POST':
        form_user = EditUserForm(request.POST, instance=request.user)
        form_profile = EditStaffProfileForm(request.POST, instance=request.user.userprofile) if request.user.is_staff else EditProfileForm(request.POST, instance=request.user.userprofile)
        formset = EleveFormset(request.POST)
        if request.user.is_staff:
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
                Notification.objects.create(to_user=admin, from_user=request.user,
                                            object="Creation du compte %s %s (%s)" % (
                                            request.user.first_name, request.user.last_name, request.user),
                                            text="Je viens de créer mon compte professeur!")
                return redirect('intranet:creation_condition')
        else:
            if form_profile.is_valid() and form_user.is_valid() and formset.is_valid():
                form_user.save()
                form_profile.save()
                messages.success(request, 'Vos informations personnelles ont bien été enregistrées.')
                address = form_profile.cleaned_data["address"]
                city = form_profile.cleaned_data["city"]
                zip_code = form_profile.cleaned_data["zip_code"]
                country = form_profile.cleaned_data["country"]
                # print(address, city, zip_code, country)
                location = "%s %s %s %s" % (address, city, zip_code, country)
                r = requests.get(
                    'http://www.mapquestapi.com/geocoding/v1/address?key=7MspWFOeqU2eH72DNDg8LM6sTXKcaQmz&location=%s' % location)
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
                for f in formset:
                    name = f.cleaned_data.get('name')
                    if name:
                        Eleve.objects.create(referent=request.user,nom_prenom=name)

                admin = User.objects.get(is_superuser=True)
                Notification.objects.create(to_user=admin, from_user=request.user,
                                            object="Creation du compte %s %s (%s)" % (
                                                request.user.first_name, request.user.last_name, request.user),
                                            text="Je viens de créer mon compte!")
                return redirect('intranet:creation_condition')
    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = EditStaffProfileForm(instance=request.user.userprofile) if request.user.is_staff else EditProfileForm(instance=request.user.userprofile)
        formset = EleveFormset()

    return render(request, 'intranet/creation_inscription.html', locals())

def creation_adhesion(request):
    key = settings.STRIPE_PUBLISHABLE_KEY
    if request.user.is_staff:
        price = 19
    else:
        nb_eleve = Eleve.objects.filter(referent=request.user).count()
        price = 72 * nb_eleve
    return render(request, 'intranet/creation_adhesion.html', locals())

def creation_condition(request):
    if request.method == "POST":
        form = ConditionForm(request.POST)
        if form.is_valid():
            return redirect('intranet:creation_adhesion')
        else:
            messages.warning(request, 'Vous devez valider les conditions d\'utilisations.')
            return redirect('intranet:creation_condition')
    form = ConditionForm()
    return render(request, 'intranet/creation_condition.html', locals())

@login_required
@user_passes_test(lambda u: u.is_staff)
def cours_prof(request):
    """Minimal function rendering a template"""
    def last_day_of_month(any_day):
        next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
        last_day = next_month - timedelta(days=next_month.day)
        return last_day.replace(hour=0,minute=0,second=0) - datetime.now()

    m_y = "%s_%s" % (datetime.now().month, datetime.now().year)

    cours_list = Cour.objects.filter(relation__teacher=request.user, mois=m_y)
    ancien_cours_list = Cour.objects.filter(relation__teacher=request.user).exclude(mois=m_y)
    month = '%s %s' % (mois[datetime.now().month-1], datetime.now().year)
    delta = last_day_of_month(datetime.now())

    if delta.days < 7:
        messages.warning(request, 'Il vous reste %s jours, %s heures et %s minutes avant la fin du mois, n\'oubliez pas de valider vos cours !' % (delta.days, delta.seconds//3600, (delta.seconds//60)%60))

    if request.method == "POST":
        form = CoursFrom(request.POST, prof=request.user)
        if form.is_valid():
            eleve = form.cleaned_data["eleve"]
            time = form.cleaned_data["duree"]
            action = form.cleaned_data["action"]

            user_eleve = User.objects.get(username=eleve)
            relation = Relation.objects.get(teacher=request.user, student=user_eleve)
            cours = Cour.objects.filter(mois=m_y,relation=relation)

            if not cours:
                Cour.objects.create(mois=m_y, relation=relation, duree_cours=time)
                messages.success(request, 'Le cour pour l\'élève %s d\'une durée de %s minutes à bien été ajouté.' % (eleve,time))
            else:
                cour = cours.first()
                if cour.is_valid_t:
                    messages.warning(request, "Vous avez déjà validé ces cours !")
                    return redirect('intranet:cours')
                if action == 'Ajouter':
                    cour.duree_cours += time
                    cour.save()
                    messages.success(request, 'Le temps de cour pour l\'élève %s a bien été mis à jour.' % eleve)
                elif action == 'Modifier':
                    cour.duree_cours = time
                    cour.save()
                    messages.success(request, 'Le temps de cour pour l\'élève %s a bien été mis à jour.' % eleve)
                elif action == 'Supprimer':
                    cour.duree_cours = 0 if cour.duree_cours < time else cour.duree_cours - time
                    cour.save()
                    messages.success(request, 'Le temps de cour pour l\'élève %s a bien été mis à jour.' % eleve)
                else:
                    messages.error(request, 'L\'action demandée n\'a pas pu être éxécutée')
            return redirect('intranet:cours_prof')
        else:
            return redirect('intranet:cours_prof')
    else:
        form = CoursFrom(prof=request.user)
    return render(request, 'intranet/cours_prof.html', locals())

@login_required
@user_passes_test(lambda u: u.is_staff)
def validation_prof(request, id):
    cour = Cour.objects.filter(pk=id)
    if not cour:
        messages.error(request, 'Action Impossible.')
        return redirect('intranet:cours')
    else:
        cour = cour.first()

    if cour.relation.teacher == request.user:
        cour.is_valid_t = True
        cour.save()
        messages.success(request, 'Cours validé !')
        Notification.objects.create(to_user=cour.relation.student,from_user=cour.relation.teacher,
                                   object="Validation Cours %s" % conv_mois(cour.mois),
                                   text="Vous pouvez désormais valider ou refuser vos cours dans la section 'Mes Cours'!")
    else:
        messages.error(request,'Action Impossible.')
    return redirect('intranet:cours_prof')

@login_required
def cours_eleve(request):
    cours_list = Cour.objects.filter(relation__student=request.user, is_valid_t=True)
    return render(request, 'intranet/cours_eleve.html', locals())

@login_required
def validation_eleve(request, id, result):
    print(id,result)
    cour = Cour.objects.filter(pk=id)
    if not cour:
        messages.error(request, 'Action Impossible.')
        return redirect('intranet:cours_eleve')
    else:
        cour = cour.first()

    if cour.relation.student == request.user and cour.is_valid_s is False:
        if result == 'valid':
            cour.is_valid_s = True
            cour.save()
            messages.success(request, 'Vous venez de valider vos heures de cours.')
            messages.info(request, 'Factures en cours de création.')
            Notification.objects.create(to_user=cour.relation.teacher, from_user=cour.relation.student,
                                       object="Cours %s correctement validés" % conv_mois(cour.mois),
                                       text="J'ai bien confirmé mes cours pour ce mois-ci.")
            try:
                admin = User.objects.get(is_superuser=True)
                prix = Prix.objects.get(end=None)
                nb_cours = round(cour.duree_cours/60,2)
                #Cours de Piano
                Facture.objects.create(to_user=cour.relation.student, from_user=cour.relation.teacher, object="Cours de Piano - 60 min",
                                       object_qt=nb_cours, tva=0, price_ht= nb_cours*prix.cours, price_ttc= nb_cours*prix.cours,
                                       type="Cours de Piano")
                Notification.objects.create(to_user=cour.relation.student, from_user=cour.relation.teacher,
                                            object="Factures Cours de Piano %s" % conv_mois(cour.mois),
                                            text="Votre facture est téléchargeable dans la section \"Mes documents\".")
                # Frais de Gestion
                Facture.objects.create(to_user=cour.relation.student, from_user=admin,
                                       object="Frais de gestion - 60 min",
                                       object_qt=nb_cours, tva=prix.tva, price_ht=nb_cours * prix.frais_gestion,
                                       price_ttc=add_tva(nb_cours*prix.frais_gestion,prix.tva),
                                       type="Frais de Gestion")

                Notification.objects.create(to_user=cour.relation.student, from_user=admin,
                                            object="Factures Frais de Gestion %s" % conv_mois(cour.mois),
                                            text="Votre facture est téléchargeable dans la section \"Mes documents\".")

            except:
                messages.error(request, "Impossible de trouver les tarifs, un message a été evnoyé à l'administateur.")

        elif result == 'refus':
            cour.is_unvalid = True
            cour.save()
            messages.warning(request, 'Vous n\'avez pas validé vos heures de cours.')
            Notification.objects.create(to_user=cour.relation.teacher, from_user=cour.relation.student,
                                       object="Problème Validation Cours %s" % conv_mois(cour.mois),
                                       text="Il y a un problème dans les cours que vous m'avez demandé de valider.")
            # Notification.objects.create(to_user__username="admin", from_user=cour.relation.student,
            #                             object="Problème Validation Cours %s" % conv_mois(cour.mois),
            #                             text="Il y a un problème de validation de cours entre .")
    else:
        messages.error(request,'Action Impossible.')

    return redirect('intranet:cours_eleve')


@login_required
def documents(request):
    key = settings.STRIPE_PUBLISHABLE_KEY
    if request.user.is_superuser:
        factures_list_notpaid = Facture.objects.filter(is_paid=False)
        factures_list_paid = Facture.objects.filter(is_paid=True)
    else:
        factures_list = Facture.objects.filter(to_user=request.user)
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
        form = PriceForm(request.POST)
        print(form)
        if form.is_valid():
            print("VALIDDE!!!")
            price = form.cleaned_data["fac_id"]
            prix = Prix.objects.get(end=None)
            admin = User.objects.get(is_superuser=True)
            user = request.user
            if request.user.is_staff:
                fac = Facture.objects.create(
                    to_user=user, from_user=admin, object="Adhésion professeur", is_paid=True,
                    object_qt=1, tva=prix.tva, price_ht=1 * prix.adhesion_prof, price_ttc=price, type="Adhésion professeur",
                    to_user_firstname=user.first_name, to_user_lastname =user.last_name ,to_user_address =user.userprofile.address,
                    to_user_city=user.userprofile.city, to_user_zipcode =user.userprofile.zip_code,
                    to_user_siret=user.userprofile.siret, to_user_sap =user.userprofile.sap,
                    from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
                    from_user_address=admin.userprofile.address, from_user_city =admin.userprofile.city,
                    from_user_zipcode=admin.userprofile.zip_code, from_user_siret =admin.userprofile.siret ,
                    from_user_sap =admin.userprofile.sap )
            else:
                nb = 1 if price % 80 == 0 else price/72.00
                if nb == 1:
                    fac = Facture.objects.create(
                        to_user=user, from_user=admin, object="Adhésion élève", is_paid=True,
                        object_qt=1, tva=prix.tva, price_ht=nb * prix.adhesion, price_ttc=price, type="Adhésion Elève",
                        to_user_firstname=user.first_name, to_user_lastname=user.last_name,
                        to_user_address=user.userprofile.address,
                        to_user_city=user.userprofile.city, to_user_zipcode=user.userprofile.zip_code,
                        to_user_siret=user.userprofile.siret, to_user_sap=user.userprofile.sap,
                        from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
                        from_user_address=admin.userprofile.address, from_user_city=admin.userprofile.city,
                        from_user_zipcode=admin.userprofile.zip_code, from_user_siret=admin.userprofile.siret,
                        from_user_sap=admin.userprofile.sap)
                else:
                    fac = Facture.objects.create(
                        to_user=user, from_user=admin, object="Adhésion élèves", is_paid=True,
                        object_qt=1, tva=prix.tva, price_ht=nb * prix.adhesion_reduc, price_ttc=price, type="Adhésion Elèves",
                        to_user_firstname=user.first_name, to_user_lastname=user.last_name,
                        to_user_address=user.userprofile.address,
                        to_user_city=user.userprofile.city, to_user_zipcode=user.userprofile.zip_code,
                        to_user_siret=user.userprofile.siret, to_user_sap=user.userprofile.sap,
                        from_user_firstname=admin.first_name, from_user_lastname=admin.last_name,
                        from_user_address=admin.userprofile.address, from_user_city=admin.userprofile.city,
                        from_user_zipcode=admin.userprofile.zip_code, from_user_siret=admin.userprofile.siret,
                        from_user_sap=admin.userprofile.sap)

            fac.is_paid = True
            fac.save()
            user.userprofile.is_adherent=True
            user.userprofile.save()
            messages.success(request, "Votre adhésion a bien été payée.")
            return redirect('intranet:accueil')
    else:
        messages.warning(request,'Action non aurotisée.')

    return redirect('intranet:creation_adhesion')

@login_required
def notifications(request):
    """Minimal function rendering a template"""
    if request.user.is_superuser:
        notifications_list = reversed(Notification.objects.all())
    else:
        notifications_list = reversed(Notification.objects.filter(to_user=request.user))
    return render(request, 'intranet/notifications.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def statistiques(request):
    """Minimal function rendering a template"""
    geo_list = UserProfile.objects.exclude(lat="0.0").exclude(lat="None")
    print(geo_list)
    return render(request, 'intranet/statistiques.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def graphs_membres(request):
    f = mtf.Figure()
    labels = 'Admin', 'Professeurs', 'Eleves'
    a = User.objects.filter(is_superuser=True).count()
    p = User.objects.filter(is_staff=True).exclude(is_superuser=True).count()
    s = User.objects.exclude(is_staff=True).count()
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
def graphs_nb_cours(request):
    f = mtf.Figure()
    fig, ax = plt.subplots()
    list_prof = User.objects.filter(is_staff=True)
    label_prof = [u.username for u in list_prof]
    times = last_3_mois()
    # print(times)
    ind = np.arange(3)
    width = 0.35
    plts = []
    data = [[0 if not Cour.objects.filter(mois=t, relation__teacher=prof) else Cour.objects.filter(mois=t, relation__teacher=prof).aggregate(Sum('duree_cours'))['duree_cours__sum'] for t in times]for prof in list_prof]
    # data = [[Cour.objects.filter(mois=t, relation__teacher=prof) for t in times]for prof in list_prof]
    m = max(max(zip(*data)))
    for it,d in enumerate(data,1):
        bottom_counter=0
        # tmp = plt.bar(ind + width*it, d, width, label=label_prof[it-1], bottom=bottom_counter)
        tmp = plt.bar(ind, d, width, label=label_prof[it-1], bottom=bottom_counter)
        # bottom_counter+=it
        plts.append(tmp)

    plt.xticks(ind, [conv_mois(t) for t in times])
    plt.yticks(np.arange(0, m+120, 60))
    plt.ylabel('temps de cours (min)')
    plt.title('Temps de cours par professeurs et par mois')
    plt.legend(loc='best')

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
    form = ArticleForm()
    return render(request, 'intranet/gestion_articles.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_membres(request):
    """Members template to display all the members"""
    users_list = User.objects.all()
    return render(request, 'intranet/gestion_membres.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_relations(request):
    relations_list = Relation.objects.all()
    form2 = RelationForm()
    return render(request, 'intranet/gestion_relations.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_invitations(request):
    invitations_list = Invitation.objects.all()
    form = InvitationForm()
    return render(request, 'intranet/gestion_invitations.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_prix(request):
    prix_list = reversed(Prix.objects.all())
    form = PrixForm()
    return render(request, 'intranet/gestion_prix.html', locals())

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestion_mail(request):
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
            messages.success(request,'La relation a bien été crée.')
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
            cours = form.cleaned_data["cours"]
            commission = form.cleaned_data["commission"]
            frais_gestion = form.cleaned_data["frais_gestion"]
            if Prix.objects.all():
                last_price = Prix.objects.get(end=None)
                last_price.end = date.today()
                last_price.save()
            Prix.objects.get_or_create(tva=tva,adhesion=adhesion,cours=cours,commission=commission,frais_gestion=frais_gestion)
            messages.success(request,'Le changement de prix a bien été pris en compte. Il sera effectif à partir de minuit.')
            return redirect('intranet:gestion_prix')
        else:
            messages.warning(request, 'Impossible de modifier les prix.')
            return redirect('intranet:gestion_prix')

    return redirect('intranet:gestion_prix')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def invitation(request):
    mail = None
    if request.method == "POST":
        form = InvitationForm(request.POST)
        if form.is_valid():
            mail = form.cleaned_data["email"]
            is_staff = form.cleaned_data["is_staff"]
        else:
            messages.warning(request, 'Impossible d\'envoyer l\'invitation.')
            return redirect('intranet:gestion_invitations')

        current_site = get_current_site(request)
        my_uuid = str(uuid.uuid4())
        context = { 'protocol': 'http', 'domain': current_site.domain, 'site_name': current_site.name, 'uuid': my_uuid}
        msg_plain = render_to_string('email/email_invitation.txt', context=context)
        msg_html = render_to_string('email/email_invitation.html', context=context)
        send_mail(
            'Inscrivez-vous sur l\'intranet d\'Ecole01!',
            msg_plain,
            'some@sender.com',
            [mail],
            html_message=msg_html,
        )
        inv = Invitation.objects.create(uuid=my_uuid, email=mail, is_staff=is_staff)
        messages.success(request, 'L\'invitation a bien été envoyée.')
    return redirect('intranet:gestion_invitations')

@login_required
def mon_compte(request):
    user = User.objects.get(id=request.user.id)
    return render(request, 'intranet/mon_compte.html',locals())


@login_required
def edit_compte(request):
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
                                        text="Je viens de modifier mes informations, pour voire mon nouveau profile:")
            return redirect('intranet:mon_compte')
    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = EditStaffProfileForm(instance=request.user.userprofile) if request.user.is_staff else EditProfileForm(instance=request.user.userprofile)
        return render(request, 'intranet/edit_compte.html', locals())

def edit_pass(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect('intranet:mon_compte')
        else:
            return redirect('intranet:change_password')
    else:
        form = PasswordChangeForm(user=request.user)
        return render(request, 'intranet/edit_pass.html',  locals())

def article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST or None, request.FILES)
        if form.is_valid():
            contenu = form.cleaned_data["contenu"]
            titre = form.cleaned_data["titre"]
            lien = form.cleaned_data["lien"]
            photo = form.cleaned_data["photo"]
            Article.objects.create(titre=titre,contenu=contenu,lien=lien,photo=photo)
            messages.success(request,"Votre Article a bien été créé.")
            return redirect('intranet:accueil')

    messages.warning(request, "Impossible de rédiger votre article.")
    return redirect('intranet:gestion_articles')



def mail(request):
    if request.method == 'POST':
        form = MailForm(request.POST)
        formset = ToMailFormset(request.POST)
        print(request.POST)
        print(formset)
        if form.is_valid() and formset.is_valid():
            objet = form.cleaned_data["objet"]
            message = form.cleaned_data["message"]
            address = []
            for f in formset:
                # extract name from each form and save
                email = f.cleaned_data.get('name')
                if email:
                    address.append(email)
            send_mail(object,message,'admin@ecole01.fr',address)
            messages.success(request,"Votre email a bien été envoyée.")
            return redirect('intranet:gestion_mail')

    messages.warning(request, "Impossible d'envoyer votre email.")
    return redirect('intranet:gestion_mail')
