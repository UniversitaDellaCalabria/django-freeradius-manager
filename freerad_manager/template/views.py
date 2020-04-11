from django.conf import settings
from django.contrib import auth
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import is_safe_url

_template_prefix='unical_echopress/'

def redirect(request):
    return HttpResponseRedirect('http://www.unical.it')

def base_template(request):
    """render the home page"""
    context = {
        "username": '',
        "peer": '',
        "error": "user name e/o password errati"
    }    
    return render(request, "base.html", context=context)

def login_template(request):
    """render the home page"""
    context = {
        "username": '',
        "peer": '',
        "error": "user name e/o password errati"
    }    
    return render(request, "login.html", context=context)

def dashboard_template(request):
    """render the home page"""
    context = {
        "username": '',
        "peer": '',
        "error": "user name e/o password errati"
    }    
    return render(request, "dashboard.html", context=context)
