from django import forms
from django.utils import timezone
from django.forms import formset_factory, inlineformset_factory, modelformset_factory
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import UserProfile, Relation, Prix, Article, Eleve,Condition, InscriptionExamen, Examen
import datetime


class LoginForm(forms.Form):
    # email = forms.EmailField(required=True, label='', max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Email address', 'class':'form-control'}))
    username = forms.CharField(required=True, label='', max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Pseudo', 'class':'form-control'}))
    password = forms.CharField(required=True, label='', widget=forms.PasswordInput(attrs={'placeholder': 'mot de passe', 'class':'form-control'}))


class InvitationForm(forms.Form):
    email = forms.EmailField(required=True, label='', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Email', 'class': 'form-control'}))
    is_staff = forms.BooleanField(required=False, label='Professeur:', help_text="(Cochez la case si l'invitation est destinée à un professeur)")
    is_free = forms.BooleanField(required=False, label='Adhésion gratuite:', help_text="(Cochez la case si vous voulez offrir l'adhésion à l'utilisateur)")


class ConditionForm(forms.Form):
    condition = forms.BooleanField(label='J\'ai lu & j\'accepte les conditions générales d\'utilisation')

class RelationForm(forms.Form):
    eleve = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=False, is_active=True), required=True, label='Elève', help_text=" (pseudo de l'élève)", to_field_name="username")
    professeur = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=True, is_active=True), required=True, help_text=" (pseudo du professeur)", to_field_name="username")

class FactureIdForm(forms.Form):
    fac_id =forms.IntegerField(min_value=1,max_value=999999)

class PriceForm(forms.Form):
    fac_id =forms.CharField(max_length=8)

class CoursFrom(forms.Form):
    def __init__(self, *args, **kwargs):
        prof = kwargs.pop('prof')
        super(CoursFrom, self).__init__(*args, **kwargs)
        self.fields['eleve'] = forms.ChoiceField(widget=forms.Select(),choices=[(x.student,x.student) for i,x in enumerate(Relation.objects.filter(teacher=prof))], required=True,help_text="(pseudo de l'éleve)", label="Elève")
        self.fields['duree'] = forms.IntegerField(required=True,min_value=60,max_value=2100,help_text="(Temps de cours en minutes)")
        self.fields['action'] = forms.ChoiceField(widget=forms.Select(),choices=[('Ajouter','Ajouter'),('Modifier','Modifier'),('Supprimer','Supprimer')],help_text="(Ajouter du temps de cours ou modifier/réduiser celui-ci)")

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='', max_length=50, widget=forms.TextInput(
        attrs={'placeholder': 'Email', 'class':'form-control'}))
    username = forms.CharField(required=True, label='', max_length=20, widget=forms.TextInput(
        attrs={'placeholder': 'Pseudo', 'class':'form-control'}))
    first_name = forms.CharField(required=False, label='', max_length=30, widget=forms.TextInput(
        attrs={'placeholder': 'Prénom', 'class': 'form-control'}))
    last_name = forms.CharField(required=False, label='', max_length=30, widget=forms.TextInput(
        attrs={'placeholder': 'Nom', 'class': 'form-control'}))
    password1 = forms.CharField(required=True, label='',
                               widget=forms.PasswordInput(attrs={'placeholder': 'Mot de passe', 'class': 'form-control'}))
    password2= forms.CharField(required=True, label='',
                               widget=forms.PasswordInput(attrs={'placeholder': 'Répéter mot de passe', 'class': 'form-control'}))

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        )

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name'
        )

class EditEleveForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = (
            'nom_prenom',
        )
        labels = {
            'nom_prenom': 'Nom/prénom de l\'élève 00.00.00'
        }
EditEleveFormset = modelformset_factory(Eleve, fields=('nom_prenom',), extra=1, max_num=10,min_num=0)

class AddEleveForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = (
            'nom_prenom',
        )
        labels = {
            'nom_prenom': 'Nom/prénom de l\'élève 00.00.00'
        }

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            'phone_number',
            'address',
            'city',
            'zip_code',
            'country',
            'is_premium',
            'stats'
        )
        labels = {
            'phone_number': 'Numéro de téléphone',
            'address': 'Adresse',
            'city': 'Ville',
            'zip_code': 'Code postal',
            'country': 'Pays',
            'is_premium': 'Assurance cours',
            'stats': 'Comment avez-vous connu l\'EFP ?'
        }

class EditStaffProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            'phone_number',
            'address',
            'city',
            'zip_code',
            'country',
            'siret',
            'sap',
            'stats'
        )
        labels = {
            'phone_number': 'Numéro de téléphone',
            'address': 'Adresse',
            'city': 'Ville',
            'zip_code': 'Code postal',
            'country': 'Pays',
            'siret': 'SIRET',
            'sap': 'SAP',
            'stats': 'Comment avez-vous connu l\'EFP ?'
        }


class PrixForm(forms.ModelForm):
    class Meta:
        model = Prix
        labels = {
            'tva': 'TVA',
            'adhesion': 'Adhésion simple',
            'adhesion_reduc': 'Adhésion tarif réduit',
            'adhesion_prof': 'Adhésion professeur',
            'cours': 'Cours classique',
            'cours_premium': 'Cours premium',
            'cours_ecole': 'Cours tarif ecole',
            'commission': 'Commission',
            'frais_gestion': 'Frais de gestion'
        }
        fields = (
            'tva',
            'adhesion',
            'adhesion_reduc',
            'adhesion_prof',
            'cours',
            'cours_premium',
            'cours_ecole',
            'commission',
            'frais_gestion'
        )

class ArticleForm(forms.Form):
    titre = forms.CharField()
    contenu = forms.CharField(widget=forms.Textarea)
    lien = forms.CharField(required=False)
    photo = forms.ImageField(required=False)


class MailForm(forms.Form):
    objet = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea,required=True)
    tlp = forms.BooleanField(required=False, label='Tous les professeurs:', help_text="(si le mail est destiné à tous les professeurs)")
    tle = forms.BooleanField(required=False, label='Tous les élèves:', help_text="(si le mail est destiné à tous les élèves)")



class CondiForm(forms.ModelForm):
    class Meta:
        model = Condition
        fields = ('file',)
        labels = { 'file': 'Conditions générales d\'utilisations'}

class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = ('name', 'description', 'last', 'price')
        labels = {
            'name': 'Nom',
            'description': 'Description',
            'last': 'Date de clôture d\'inscription',
            'price': 'Prix HT'
        }

class InscriptionExamenForm(forms.ModelForm):
    class Meta:
        model = InscriptionExamen
        fields = ('examen', 'eleve')
        labels = {'examen': 'Examen',
                  'eleve': 'Elève'
                 }

class ToMailForm(forms.Form):
    name = forms.EmailField(
            label='Destinataire',
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'adressemail@destinataire.fr'
            })
        )

ToMailFormset = formset_factory(ToMailForm, extra=1, max_num=100)

class EleveForm(forms.Form):
    name = forms.CharField(
        label='Nom/prénom de l\'élève 00.00.00',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Dupont 01.01.99'
        })
    )

EleveFormset = formset_factory(EleveForm, extra=1, max_num=10,min_num=0)

class LessonFrom(forms.Form):
    def __init__(self, *args, **kwargs):
        prof = kwargs.pop('prof')
        super(LessonFrom, self).__init__(*args, **kwargs)
        self.fields['eleve'] = forms.ChoiceField(
            widget=forms.Select(attrs={'class': 'form-control','style':'width:20em','id': 'select-id'}),
            choices=[(x.student.username,x.student) for i,x in enumerate(Relation.objects.filter(teacher=prof))],
            required=True,help_text="(pseudo de l'élève)", label="Elève")
        self.fields['nb_h'] = forms.IntegerField(
            widget=forms.NumberInput(attrs={'class': 'mr-2','placeholder':'01'}),
            required=True,min_value=1,max_value=23,label='H',initial=1)
        self.fields['nb_m'] = forms.IntegerField(
            widget=forms.NumberInput(attrs={'class': 'mx-2','placeholder':'00'}),
            required=True,min_value=0,max_value=59,label='min',initial=00)
        self.fields['date'] = forms.DateField(
            widget=forms.SelectDateWidget(years=range(datetime.date.today().year, datetime.date.today().year+1),attrs={'class': 'ml-2'}), required=True,label="Date du cours")
        # self.fields['date'] = forms.DateField(initial=datetime.date.today, required=True)

class FactureForm(forms.Form):
     OBJECTS = (
        ('cp','Cours de piano'),
        ('fg','Frais de gestion'),
        ('fc','Frais de commission'),
        ('fa','Frais d\'adhésion'),
        ('fp','Frais de préavis')
     )

     from_user = forms.ChoiceField(
            widget=forms.Select(attrs={'class': 'form-control','style':'width:20em','id': 'select-id'}),
            choices=[(x.username,x) for i,x in enumerate(User.objects.filter(is_staff=True, is_active=True))],
            required=True, label="Emeteur")
     to_user = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width:20em', 'id': 'select-id'}),
        choices=[(x.username, x) for i, x in enumerate(User.objects.filter(is_active=True))],
        required=True, label="Destinataire")

     object = forms.ChoiceField(choices=OBJECTS,label="Objet")

     nb_item = forms.IntegerField(
            widget=forms.NumberInput(attrs={'class': 'mr-2','placeholder':'01'}),
            required=True,min_value=1,max_value=1000,label='Unités',initial=1)

     tva = forms.FloatField(
         widget=forms.NumberInput(attrs={'class': 'mr-2', 'placeholder': '01'}),
         required=True, min_value=0, max_value=1000, label='TVA', initial=20.00)

     prix_ht = forms.FloatField(
         widget=forms.NumberInput(attrs={'class': 'mr-2', 'placeholder': '01'}),
         required=True, min_value=0, max_value=1000, label='Prix HT', initial=1.00)

