from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.template import RequestContext, Context
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from regalness.forms import *
from regalness.models import *
import simplejson as json
import stripe

#TODO: pull me from DB options
PROCESSING_ERROR_TEMPLATE = 'regalness/processing-error.html'
CUST_KEY = 'customer'

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
    user, created = User.objects.get_or_create(username='anon')
    customer, created = Customer.objects.get_or_create(user=user)
    request.session[CUST_KEY] = customer
    context['bulk'] = ORDER_OPTIONS[0][1]
    context['sub'] = ORDER_OPTIONS[1][1]
    context['COST_PER_COOKIE'] = COST_PER_COOKIE
    if settings.DEBUG:
        context['key'] = settings.TEST_STRIPE_PUB_KEY
        context['card'] = settings.TEST_CARD_NUM
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def contact(request, template_name='regalness/contact-form.html'):
    context = {}
    form_key = 'contact'
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            obj = form.save()
            customer = request.session[CUST_KEY]
            customer.add_contact(obj)
            request.session[form_key] = obj
            vals = ''
            return HttpResponse(json.dumps(vals), mimetype='application/json', status=200)
        else:
            errors = fix_error_msg(form.errors)
            err_msg = '  '.join(errors)
            return HttpResponse(err_msg, mimetype='application/json', status=400)
    else:
        customer = request.session[CUST_KEY]
        def_contact = customer.get_default_contact()
        if customer.user.username != 'anon' and def_contact != None:
            form = ContactForm(instance=def_contact)
        else:
            form = ContactForm()
        context['form'] = form
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def order_details(request, template_name='regalness/order-details-form.html'):
    context = {}
    form_key = 'addr'
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            obj = form.save()
            customer = request.session[CUST_KEY]
            customer.add_address(obj)
            request.session[form_key] = obj
            vals = ''
            return HttpResponse(json.dumps(vals), mimetype='application/json', status=200)
        else:
            errors = fix_error_msg(form.errors)
            err_msg = '  '.join(errors)
            return HttpResponse(err_msg, mimetype='application/json', status=400)
    else:
        customer = request.session[CUST_KEY]
        addr = customer.get_default_address()
        form = None
        if customer.user.username != 'anon' and addr != None:
            form = AddressForm(instance=addr)
        else:
            form = AddressForm()
        context['form'] = form
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def login(request, template_name='regalness/login-form.html'):
    context = {}
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
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def register(request, template_name='regalness/registration-form.html'):
    context = {}
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
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def order(request, template_name='regalness/order.html'):
    context = {}
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def customer_check(user, token):
    #TODO lookup cust in our db
    try:
        customer = stripe.Customer.create(
            card=token,
            description="payinguser@example.com"
        )
    except Exception as e:
        print 'customer e=%s' % e
    return customer.id

def charge_customer(cust_id):
    try:
        charge = stripe.Charge.create(
            amount=1000, # amount in cents, again
            currency="usd",
            description="payinguser@example.com",
            customer=cust_id,
        )
    except Exception as e:
        print 'charge e=%s' % e
        return False
    return True

def order_submit(request, option, quantity, token, template_name='regalness/thanks.html'):
    context = {}
    print request.session['customer']
    if option not in ORDER_OPTIONS:
        template_name = 'regalness/error_missing_opt.html'
        return render_to_response(template_name, context, context_instance=RequestContext(request))
    stripe.api_key = settings.TEST_STRIPE_SECRET_KEY
    # create the charge on Stripe's servers - this will charge the user's card
    cust_id = customer_check('RMME', token)
    if not charge_customer(cust_id):
        template_name = PROCESSING_ERROR_TEMPLATE
    return render_to_response(template_name, context, context_instance=RequestContext(request))
