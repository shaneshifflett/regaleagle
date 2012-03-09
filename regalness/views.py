from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.template import RequestContext, Context
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.forms import UserCreationForm
from django import forms
import simplejson as json
import stripe

#TODO: pull me from DB options
ORDER_OPTIONS = ['bulk', 'sub']
COST_PER_COOKIE = 1.99
PROCESSING_ERROR_TEMPLATE = 'regalness/processing-error.html'

def experimental(request, template_name='regalness/caat.html'):
   context = {} 
   return render_to_response(template_name, context, context_instance=RequestContext(request))

def index(request, template_name='regalness/index.html'):
    context = {}
    context['bulk'] = ORDER_OPTIONS[0]
    context['sub'] = ORDER_OPTIONS[1]
    context['COST_PER_COOKIE'] = COST_PER_COOKIE
    if settings.DEBUG:
        context['key'] = settings.TEST_STRIPE_PUB_KEY
        context['card'] = settings.TEST_CARD_NUM
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
            vals = {'username':new_user.username}
            return HttpResponse(json.dumps(vals), mimetype='application/json', status=200)
        else:
            err_msg = ''
            for item in form.errors.values():
                err_msg += ''.join(item)
            return HttpResponse(json.dumps(err_msg), mimetype='application/json', status=400)
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
    if option not in ORDER_OPTIONS:
        template_name = 'regalness/error_missing_opt.html'
        return render_to_response(template_name, context, context_instance=RequestContext(request))
    stripe.api_key = settings.TEST_STRIPE_SECRET_KEY
    # create the charge on Stripe's servers - this will charge the user's card
    cust_id = customer_check('RMME', token)
    if not charge_customer(cust_id):
        template_name = PROCESSING_ERROR_TEMPLATE
        print template_name
    return render_to_response(template_name, context, context_instance=RequestContext(request))
