"""
Definitions of administrative views.
"""

from django.shortcuts import render
from django.http import HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from datetime import datetime
from app.adminforms import *
import app.tools.builder as b

def settings(request):
    """
    Renders the settings page.
    """
    assert isinstance(request, HttpRequest)
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PopulateTableForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/admin/settings/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PopulateTableForm()

    return render(request, 'app/settings.html', {
        'form': form,
        'title': 'Settings',
        'message': 'Instance Settings',
        })

    #assert isinstance(request, HttpRequest)
    #return render(
    #    request,
    #    'app/about.html',
    #    RequestContext(request,
    #    {
    #        'title':'About',
    #        'message':'Simplifying access to oceanographic data.',
    #        'year':datetime.now().year,
    #    })
    #)

def cachemon(request):
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/cachemonitor.html',
        RequestContext(request,
        {
            'title':   'Cache Monitor',
            'message': "Details on current Azure blob storage and this server's local cache.",
            # Thought: http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
            # Stub... Kilroy
            'blobs':   b.list_blob_cache().blobs,
            'files':   b.list_local_cache(),
            'year':    datetime.now().year,
        })
    )