from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
import stripe


def index(request, template_name='regalness/index.html'):
    context = {}
    return render_to_response(template_name, context, context_instance=RequestContext(request))


def order(request, template_name='regalness/order.html'):
    context = {}
    context['key'] = settings.TEST_STRIPE_PUB_KEY
    if settings.DEBUG:
        context['card'] = settings.TEST_CARD_NUM
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def order_submit(request, token, template_name='regalness/thanks.html'):
    context = {}
    print 'submission' 
    stripe.api_key = settings.TEST_STRIPE_SECRET_KEY

    # create the charge on Stripe's servers - this will charge the user's card
    charge = stripe.Charge.create(
        amount=1000, # amount in cents, again
        currency="usd",
        card=token,
        description="payinguser@example.com"
    )
    return render_to_response(template_name, context, context_instance=RequestContext(request))
