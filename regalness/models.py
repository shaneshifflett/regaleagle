from django.db import models
from django.contrib.auth.models import User
import stripe

class Customer(models.Model):
    user = models.ForeignKey(User)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    street_address = models.TextField(blank=True)
    city = models.TextField(blank=True)
    state = models.CharField(blank=True, max_length=2)
    zip = models.CharField(blank=True, max_length=10)
    phone_number = models.CharField(blank=True, max_length=12)
    active = models.BooleanField(default=True)
