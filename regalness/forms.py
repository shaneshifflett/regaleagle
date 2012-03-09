from django import forms


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(max_length=30)
    repassword = forms.CharField(max_length=30)