from django.db import models
from django.contrib.localflavor.us.models import PhoneNumberField, USStateField
from django.contrib.auth.models import User
import stripe

ORDER_OPTIONS = (('b','bulk'), ('s','sub'))
SUBSCRIPTION_QUANTITY = 20
COST_PER_COOKIE = 1.99

class Customer(models.Model):
    user = models.ForeignKey(User)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    orders = models.ManyToManyField('regalness.Order', symmetrical=False, null=True, blank=True)
    addresses = models.ManyToManyField('regalness.Address', symmetrical=False, null=True, blank=True)
    contacts = models.ManyToManyField('regalness.Contact', symmetrical=False, null=True, blank=True)
    created_date = models.DateTimeField(auto_now=True)

    def add_contact(self, contact):
        contactos = self.contacts.all()
        if contact not in contactos:
            self.contacts.add(contact)
        self.set_default_contact(contact)

    def add_address(self, address):
        addressi = self.addresses.all()
        if address not in addressi:
            self.addresses.add(address)
        self.set_default_address(address)

    def get_default_address(self):
        try:
            return self.addresses.filter(is_default=True).order_by('-created_date')[0]
        except Exception as e:
            return None

    def get_default_contact(self):
        try:
            return self.contacts.filter(is_default=True).order_by('-created_date')[0]
        except Exception as e:
            return None

    def set_default_address(self, address):
        if not address.is_default:
            addresses = self.addresses.filter(is_default=True)
            for addr in addresses:
                addr.is_default = False
                addr.save()
            address.is_default = True
            address.save()
            if address not in addresses:
                self.addresses.add(address)
            self.save()

    def set_default_contact(self, contact):
        if not contact.is_default:
            contacts = self.contacts.filter(is_default=True)
            for c in contacts:
                c.is_default = False
                c.save()
            contact.is_default = True
            contact.save()
            if contact not in contacts:
                self.contacts.add(contact)
            self.save()

class Address(models.Model):
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = USStateField()
    zip = models.CharField(max_length=10)
    created_date = models.DateTimeField(auto_now=True) 
    is_default = models.BooleanField(default=False)

class Contact(models.Model):
    email = models.EmailField(max_length=255)    
    phone_number = PhoneNumberField(max_length=12)
    is_default = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True) 


class Order(models.Model):
    order_type = models.CharField(max_length=10, choices=ORDER_OPTIONS)
    quantity = models.PositiveIntegerField()
    delivery_address = models.ForeignKey('regalness.Address')
    contact = models.ForeignKey('regalness.Contact')
    total_cost = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    active = models.BooleanField(default=False)
    stripe_plan_id = models.CharField(blank=True, null=True, max_length=255)
    created_date = models.DateTimeField(auto_now=True) 

    def set_cost(self):
        if self.order_type == 'b':
            self.total_cost = COST_PER_COOKIE * SUBSCRIPTION_QUANTITY * self.quantity
        else:
            self.total_cost = COST_PER_COOKIE * self.quantity
        self.save()

    def cancel_plan(self):
        self.active = False
        self.save()
