from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.template import RequestContext, Context
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
import logging
from regal.orders.forms import *
from regal.orders.models import *
import simplejson as json
import stripe

#TODO: pull me from DB options
PROCESSING_ERROR_TEMPLATE = 'regalness/processing-error.html'
CUST_KEY = 'customer'    
ADDR_FORM_KEY = 'addr'
CONTACT_FORM_KEY = 'contact'


def fix_error_msg(errors):
    ret_val = []
    for key in errors.keys():
        val = errors[key][0]
        new_val = val.replace('This field', key)
        ret_val.append(new_val)
    return ret_val

def experimental(request, template_name='regalness/caat.html'):
   context = {} 
   return render_to_response(template_name, context, context_instance=RequestContext(request))

def index(request, template_name='regalness/index.html'):
    context = {}
    try:
        try:
            customer = request.session[CUST_KEY]
        except KeyError:
            user, created = User.objects.get_or_create(username='anon')
            customer, created = Customer.objects.get_or_create(user=user)
            request.session[CUST_KEY] = customer
        context['bulk'] = ORDER_OPTIONS[0][1]
        context['sub'] = ORDER_OPTIONS[1][1]
        context['COST_PER_COOKIE'] = COST_PER_COOKIE
        if settings.DEBUG:
            context['key'] = settings.TEST_STRIPE_PUB_KEY
            context['card'] = settings.TEST_CARD_NUM
        else:
            context['key'] = settings.STRIPE_PUB_KEY
            context['card'] = settings.CARD_NUM
    except Exception as e:
        logging.error("regalness.views.index:e=%s" % e)
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def contact(request, template_name='regalness/contact-form.html'):
    context = {}
    try:
        if request.method == 'POST':
            print 'post contact form'
            form = ContactForm(request.POST)
            if form.is_valid():
                print 'contact form is valid'
                obj = form.save()
                obj.is_default = True #make all contacts default for now
                customer = request.session[CUST_KEY]
                customer.add_contact(obj)
                request.session[CONTACT_FORM_KEY] = obj
                vals = ''
                return HttpResponse(json.dumps(vals), mimetype='application/json', status=200)
            else:
                print 'contact form errors'
                errors = fix_error_msg(form.errors)
                err_msg = '  '.join(errors)
                return HttpResponse(err_msg, mimetype='application/json', status=400)
        else:
            form = None
            try:
                obj = request.session[CONTACT_FORM_KEY]
                form = ContactForm(instance=obj)
                print 'CONTACT: finding'
            except KeyError:
                print 'CONTACT: keyerror'
                customer = request.session[CUST_KEY]
                def_contact = customer.get_default_contact()
                print 'CONTACT: looking at customer %s' % customer.user.username
                if customer.user.username != 'anon' and def_contact != None:
                    form = ContactForm(instance=def_contact)
                    print 'CONTACT: found def contact'
                else:
                    print 'CONTACT: creating new contact form'
                    form = ContactForm()
            context['form'] = form
    except Exception as e:
        logging.error("regalness.views.contact:e=%s" % e)
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def order_details(request, template_name='regalness/order-details-form.html'):
    context = {}
    try:
        if request.method == 'POST':
            form = AddressForm(request.POST)
            if form.is_valid():
                obj = form.save()
                customer = request.session[CUST_KEY]
                customer.add_address(obj)
                request.session[ADDR_FORM_KEY] = obj
                vals = ''
                return HttpResponse(json.dumps(vals), mimetype='application/json', status=200)
            else:
                errors = fix_error_msg(form.errors)
                err_msg = '  '.join(errors)
                return HttpResponse(err_msg, mimetype='application/json', status=400)
        else:
            form = None
            try:
                obj =request.session[ADDR_FORM_KEY]
                form = AddressForm(instance=obj)
                print 'ORDER: foudn addr form in sesh'
            except KeyError:
                customer = request.session[CUST_KEY]
                addr = customer.get_default_address()
                print 'ORDER: looking up customer %s' % customer.user.username
                if customer.user.username != 'anon' and addr != None:
                    form = AddressForm(instance=addr)
                    print 'ORDER: found a def addr'
                else:
                    print 'ORDER: creating a new addr'
                    form = AddressForm()
            context['form'] = form
    except Exception as e:
        logging.error("regalness.views.order_details:e=%s" % e)
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def login(request, template_name='regalness/login-form.html'):
    context = {}
    try:
        if request.method == 'POST':
            form = AuthenticationForm(None, request.POST)
            if form.is_valid():
                user = form.get_user()
                customer, created = Customer.objects.get_or_create(user=user)
                request.session[CUST_KEY] = customer
                vals = {'username': user.username}
                return HttpResponse(json.dumps(vals), mimetype='application/json', status=200)
            else:
                errors = fix_error_msg(form.errors)
                err_msg = '  '.join(errors)
                return HttpResponse(err_msg, mimetype='application/json', status=400)
        else:
            form = AuthenticationForm()
            context['form'] = form
    except Exception as e:
        logging.error("regalness.views.login:e=%s" % e)
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def register(request, template_name='regalness/registration-form.html'):
    context = {}
    try:
        if request.method == 'POST':
            vals = {}
            for key in request.POST.keys():
                vals[key] = request.POST.get(key)
            form = UserCreationForm(vals)
            if form.is_valid():
                new_user = form.save()
                customer, created = Customer.objects.get_or_create(user=new_user)
                request.session[CUST_KEY] = customer
                vals = {'username':new_user.username}
                return HttpResponse(json.dumps(vals), mimetype='application/json', status=200)
            else:
                errors = fix_error_msg(form.errors)
                err_msg = '  '.join(errors)
                return HttpResponse(err_msg, mimetype='application/json', status=400)
        else:
            form = UserCreationForm()
            context['form'] = form
    except Exception as e:
        logging.error("regalness.views.register:e=%s" % e)
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def order(request, template_name='regalness/order.html'):
    context = {}
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def review(request, template_name='regalness/review-order.html'):
    context = {}
    try:
        addr = request.session[ADDR_FORM_KEY]
        contact = request.session[CONTACT_FORM_KEY]
        context['fname'] = contact.first_name
        context['lname'] = contact.last_name
        context['email'] = contact.email
        context['phone'] = contact.phone_number
        context['street_address'] = addr.street_address
        context['city'] = addr.city
        context['state'] = addr.state
        context['zip'] = addr.zip
    except Exception as e:
        logging.error("regalness.views.review:e=%s" % e)
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def order_submit(request, option, quantity, token, template_name='regalness/thanks.html'):
    context = {}
    try:
        customer = request.session[CUST_KEY]
        print 'order customer %s' % customer.user.username
        #todo need to catch errors here and percolate error message
        #todo need to handle multiple credit cards?
        customer.charge(option, quantity, token, request)
    except Exception as e:
        logging.error("regalness.views.order_submit:e=%s" % e)
    return render_to_response(template_name, context, context_instance=RequestContext(request))