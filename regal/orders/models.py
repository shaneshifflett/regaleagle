from django.db import models
from django.contrib.localflavor.us.models import PhoneNumberField, USStateField
from django.contrib.auth.models import User
from django.conf import settings
import stripe
import logging


ORDER_OPTIONS = (('b','bulk'), ('s','sub'))
SUBSCRIPTION_QUANTITY = 20
SUBSCRIPTION_PRICE = 20.00
COST_PER_COOKIE = 1.99
SHIPPING_COST = 4.99

CUST_KEY = 'customer'    
ADDR_FORM_KEY = 'addr'
CONTACT_FORM_KEY = 'contact'

def calculate_amt(quantity):
    return int(((COST_PER_COOKIE * float(quantity)) + SHIPPING_COST) * 100)

def calculate_shipping_amt(quantity):
    return int(((SUBSCRIPTION_PRICE * float(quantity))) * 100)

def get_stripe():
    try:
        if settings.DEBUG:
            stripe.api_key = settings.TEST_STRIPE_SECRET_KEY
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY
        logging.info("orders.models.get_stripe:settings.DEBUG=%s api_key=%s" % (settings.DEBUG, stripe.api_key))
        return stripe
    except Exception as e:
        print 'orders.models.get_stripe:e=%s' % (e)

class Customer(models.Model):
    user = models.ForeignKey(User)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    orders = models.ManyToManyField('orders.Order', symmetrical=False, null=True, blank=True)
    addresses = models.ManyToManyField('orders.Address', symmetrical=False, null=True, blank=True)
    contacts = models.ManyToManyField('orders.Contact', symmetrical=False, null=True, blank=True)
    created_date = models.DateTimeField(auto_now=True)

    def get_stripe_customer(self, token):
        if self.user.username == 'anon':
            return None
        if self.stripe_customer_id == '':
            try:
                stripe_customer = get_stripe().Customer.create(
                    card=token,
                    email=self.get_default_contact().email
                )
                self.stripe_customer_id = stripe_customer.id
                self.save()
                return stripe_customer
            except Exception as e:
                logging.error("orders.models.Customer.get_stripe_customer:e=%s" % e)
                return None
        else:
            return get_stripe().Customer.retrieve(self.stripe_customer_id)

    def get_active_orders(self):
        return self.orders.filter(active=True)

    def cancel_subscription(self, stripe_customer):
        try:
            if stripe_customer.subscription != None:
                stripe_customer.cancel_subscription()#cancel any existing subscription
                active_orders = self.get_active_orders()
                for order in active_orders:
                    order.active = False
                    order.save()
                return True
            else:
                return False
        except Exception as e:
            logging.error("orders.models.Customer.cancel_subscription:username=%s error updating subscription e=%s"\
             % (self.user.username, e))

    def update_subscription(self, stripe_customer, plan_id):
        try:
            stripe_customer.update_subscription(plan=plan_id, prorate=False)
            return True
        except Exception as e:
            logging.error("orders.models.Customer.update_subscription:\
                plan_id=%s user_email=%s error updating subscription e=%s" % (plan_id, stripe_customer.email, e))
            return False

    def charge_recurring(self, quantity, token, request):
        try:
            plan = get_latest_plan()
            addr = request.session[ADDR_FORM_KEY]
            contact = request.session[CONTACT_FORM_KEY]
            scustomer = self.get_stripe_customer(token)
            if scustomer != None:
                try:
                    plan = get_plan(quantity)
                    #TODO, when logging back in need to make it clear we are modifying their current subscription plan
                    #or given them teh option to cancel
                    self.cancel_subscription(scustomer)
                    self.update_subscription(scustomer, plan.plan_id)
                    order = Order(order_type=ORDER_OPTIONS[1][1], quantity=quantity,\
                        delivery_address=addr, contact=contact, total_cost=plan.amount,\
                        stripe_plan=plan)
                    order.save()
                except Exception as e:
                    logging.error("orders.models.Customer.charge_recurring:plan_id=%s username=%s error updating subscription e=%s"\
                     % (plan.plan_id, self.user.username, e))
            else:
                logging.error("orders.models.Customer.charge_recurring:user=%s attempting to subscribe but has None" % self.user.username)
        except Exception as e:
            logging.error("orders.models.Customer.charge_recurring:e=%s" % e)
            return False

    def charge_once(self, quantity, token, request):
        try:
            cost = str(calculate_amt(quantity))
            addr = request.session[ADDR_FORM_KEY]
            contact = request.session[CONTACT_FORM_KEY]
            description = '%s buying %s cookies' % (contact.email, quantity)
            logging.info("orders.models.charge_once:cost=%s, email=%s quantity=%s, token=%s, description=%s" %\
                (cost, contact.email, quantity, token, description))
            charge = get_stripe().Charge.create(
                amount=cost, # amount in cents, again
                currency="usd",
                description=str(description),
                card=str(token)
            )
            order = Order(order_type=ORDER_OPTIONS[0][1], quantity=quantity,\
                delivery_address=addr, contact=contact, total_cost=cost)
            order.save()
            self.orders.add(order)
            return True
        except Exception as e:
            logging.error("orders.models.Customer.charge_once:e=%s" % e)
            return False

    def charge(self, option, quantity, token, request):
        logging.info("orders.models.Customer.charge:option=%s, quantity=%s, token=%s username=%s" %\
            (option, quantity, token, self.user.username))
        if option == ORDER_OPTIONS[0][1]:
            self.charge_once(quantity, token, request)
        else:
            self.charge_recurring(quantity, token, request)
        return True

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
        if address.is_default:
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
        if contact.is_default:
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
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)    
    phone_number = PhoneNumberField(max_length=12)
    is_default = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True) 

class Order(models.Model):
    order_type = models.CharField(max_length=10, choices=ORDER_OPTIONS)
    quantity = models.PositiveIntegerField()
    delivery_address = models.ForeignKey('orders.Address')
    contact = models.ForeignKey('orders.Contact')
    total_cost = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    active = models.BooleanField(default=False)
    shipped = models.BooleanField(default=False)
    stripe_plan = models.ForeignKey('orders.StripePlan', null=True, blank=True)
    created_date = models.DateTimeField(auto_now=True) 

INTERVAL = (
        ('M', 'month'),
        ('Y', 'year')
    )

class StripePlan(models.Model):
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=20)
    plan_id = models.CharField(max_length=250)
    name = models.CharField(max_length=250)
    interval = models.CharField(max_length=20, choices=INTERVAL)
    created_date = models.DateTimeField(auto_now=True)
    quantity = models.PositiveIntegerField()

def get_plan(quantity):
    id_str = 'cookie_sub_q_%s' % quantity
    try:
        thisplan = StripePlan.objects.get(plan_id=id_str)
        return thisplan
    except Exception as eone:
        logging.error("orders.models.get_plan: failed to fetch plan id_str=%s e=%s" % (id_str, eone))
        try:
            amount = calculate_shipping_amt(quantity)
            logging.info('orders.models.get_plan:id_str=%s, amount=%s, interval=%s' %\
                (id_str, amount, INTERVAL[0][1]))
            get_stripe().Plan.create(
              amount=str(amount),
              interval=INTERVAL[0][1],
              name=id_str,
              currency='usd',
              id=id_str)
            plan = StripePlan(amount=amount, currency='usd', plan_id=id_str,\
                name=id_str, interval=INTERVAL[0][1], quantity=quantity)
            plan.save()
            return plan
        except Exception as e:
            logging.error("orders.models.get_plan:id_str=%s error creating plane=%s" % (id_str, e))
            return False

def get_latest_plan():
    try:
        return StripePlan.objects.all().order_by('-created_date')[0]
    except Exception as e:
        return None

