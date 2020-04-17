"""freerad_manager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.urls import path, include
from django.utils.translation import gettext_lazy as _


admin.site.site_header = _('Amministrazione')
admin.site.site_title  = _('Pannello di amministrazione')


urlpatterns = [
    path(getattr(settings, 'ADMIN_PATH', 'admin/'), admin.site.urls),
    path('', RedirectView.as_view(url=(getattr(settings, 'LOGIN_URL', '/')), permanent=False))
]

if 'identity' in settings.INSTALLED_APPS:
    import identity.urls
    urlpatterns += path('identity/', include((identity.urls, 'identity'))),

#if 'template' in settings.INSTALLED_APPS:
    #import template.urls
    #urlpatterns += path('template/', include((template.urls, 'template'))),
