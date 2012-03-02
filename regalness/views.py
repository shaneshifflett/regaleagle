from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response


def index(request, template_name='regalness/index.html'):
    context = {}
    return render_to_response(template_name, context, context_instance=RequestContext(request))
