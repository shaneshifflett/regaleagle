from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
import stripe


ORDER_OPTIONS = ['bulk', 'sub']

def index(request, template_name='regalness/index.html'):
    context = {}
    context['bulk'] = ORDER_OPTIONS[0]
    context['sub'] = ORDER_OPTIONS[1]
    if settings.DEBUG:
        context['key'] = settings.TEST_STRIPE_PUB_KEY
        context['card'] = settings.TEST_CARD_NUM
    return render_to_response(template_name, context, context_instance=RequestContext(request))


def order(request, template_name='regalness/order.html'):
    context = {}
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def order_submit(request, option, quantity, token, template_name='regalness/thanks.html'):
    context = {}
    if option not in ORDER_OPTIONS:
        template_name = 'regalness/error_missing_opt.html'
    stripe.api_key = settings.TEST_STRIPE_SECRET_KEY
    # create the charge on Stripe's servers - this will charge the user's card
    charge = stripe.Charge.create(
        amount=1000, # amount in cents, again
        currency="usd",
        card=token,
        description="payinguser@example.com"
    )
    return render_to_response(template_name, context, context_instance=RequestContext(request))
