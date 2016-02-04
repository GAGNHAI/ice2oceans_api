'''
A collection of useful responses.
'''
import random
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseServerError, HttpResponseNotFound

def oops_not_your_fault():
    '''
    Hopefully this does not occur often.
    '''
    return HttpResponseNotFound(content="Uh oh. This is likely not your fault. Check in with the server administrator. Tell them I sent you.")

def invalid_parameter():
    '''
    This will likely occur often.
    '''
    return HttpResponseNotFound(content="One of the parameters was invalid. Check that you're using the right datatypes.")

def catastrophe():
    '''
    Use very sparingly
    '''
    resps = ["No good. Very bad.", "This should not have happened... ever.", "The plane has crashed into the mountain.", "I'm sorry, but I can't do that."]
    return HttpResponseNotFound(content=random.choice(resps))