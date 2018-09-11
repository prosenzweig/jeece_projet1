from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import UserProfile, Relation, Prix, Article, Eleve


class LoginForm(forms.Form):
    # email = forms.EmailField(required=True, label='', max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Email address', 'class':'form-control'}))
    username = forms.CharField(required=True, label='', max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Pseudo', 'class':'form-control'}))
    password = forms.CharField(required=True, label='', widget=forms.PasswordInput(attrs={'placeholder': 'mot de passe', 'class':'form-control'}))


class InvitationForm(forms.Form):
    email = forms.EmailField(required=True, label='', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Email', 'class': 'form-control'}))
    is_staff = forms.BooleanField(required=False, label='Professeur:', help_text="(Cocher la case si l'invitation est destinée à un professeur)")


class ConditionForm(forms.Form):
    condition = forms.BooleanField(label='J\'ai lu & J\'accepte les conditions d\'utilisation')

class RelationForm(forms.Form):
    eleve = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=False), required=True, help_text=" (pseudo de l'éleve)", to_field_name="username")
    professeur = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=True), required=True, help_text=" (pseudo du professeur)", to_field_name="username")

class FactureIdForm(forms.Form):
    fac_id =forms.IntegerField(min_value=1,max_value=999999)

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
                               widget=forms.PasswordInput(attrs={'placeholder': 'Répété Mot de passe', 'class': 'form-control'}))

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

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            'phone_number',
            'address',
            'city',
            'zip_code',
            'country',
            'stats'
        )
        labels = {
            'phone_number': 'Numéro de téléphone',
            'address': 'Adresse',
            'city': 'Ville',
            'zip_code': 'Code Postale',
            'country': 'Pays',
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
            'zip_code': 'Code Postale',
            'country': 'Pays',
            'siret': 'SIRET',
            'sap': 'SAP',
            'stats': 'Comment avez-vous connu l\'EFP ?'
        }


class PrixForm(forms.ModelForm):
    class Meta:
        model = Prix
        fields = (
            'tva',
            'adhesion',
            'cours',
            'commission',
            'frais_gestion'
        )

class EleveForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = (
            'referent',
            'nom',
            'prenom'
        )


class ArticleForm(forms.Form):
    titre = forms.CharField()
    contenu = forms.CharField(widget=forms.Textarea)
    lien = forms.CharField(required=False)
    photo = forms.ImageField(required=False)

