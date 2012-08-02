from django import forms
from django.contrib.localflavor.us.forms import USPhoneNumberField, USZipCodeField
from regal.orders.models import Address, Contact


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address