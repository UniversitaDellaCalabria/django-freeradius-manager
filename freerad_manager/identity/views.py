import datetime

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail, mail_admins
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django_freeradius.models import _encode_secret
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django.http import (HttpResponse,
                         Http404,
                         HttpResponseRedirect,
                         HttpResponseNotFound,
                         JsonResponse)

from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils import timezone

from django_freeradius.models import _encode_secret
from django_freeradius.models import (RadiusCheck,
                                      RadiusPostAuth)
from django_freeradius.settings import DEFAULT_SECRET_FORMAT

from . datatables import DjangoDatatablesServerProc
from . forms import IdentityRadiusRenew, RadiusRenew, PasswordReset
from . models import *


def login(request):
    d = {}
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('identity:home'))
    elif request.POST:
        username = request.POST['username'].strip()
        password = request.POST['password'].strip()
        enc_passw = _encode_secret(DEFAULT_SECRET_FORMAT, password)
        radcheck = RadiusCheck.objects.filter(username=username,
                                              valid_until__gte=timezone.now(),
                                              is_active=True,
                                              value=enc_passw
                                              ).first()
        # print(radcheck, enc_passw)
        if not radcheck:
            d['error_msg'] = ('Authentication failed.<br>'
                              #'Your account is expired or not found.<br>'
                              'Please contact HelpDesk support'
                              ' for assistance.')
            return render(request, 'login.html', context=d)

        user = authenticate(username=username, password=password)
        if not user:
            # user.is_active = False
            ir = radcheck.identityradiusaccount_set.first()
            if not ir:
                d['error_msg'] = ('Your account doesn\'t seem to have '
                                  'a valid identity linked to it<br>'
                                  'Please contact HelpDesk support'
                                  ' for assistance.')
                return render(request, 'login.html', context=d)
            identity = ir.identity
            User.objects.create(username=username,
                                first_name=identity.name,
                                last_name=identity.surname,
                                email=identity.email,
                                is_active=True)
            user = authenticate(username=username, password=password)
        login(request, user)
        return HttpResponseRedirect(reverse('identity:home'))
    return render(request, 'login.html', context=d)

def logout(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(reverse('identity:login'))

def _get_radius_accounts(request, radcheck):
    # check for digital identity and additional accounts linked to it
    radius_accounts = []
    rr = radcheck.identityradiusaccount_set.first()
    iid = Identity.objects.filter(pk=rr.identity.pk).first()
    if iid:
        for i in iid.identityradiusaccount_set.filter(radius_account__is_active=True,
                                                      radius_account__valid_until__gte = timezone.now()):
            if i.radius_account not in radius_accounts:
                radius_accounts.append(i.radius_account)
    else:
        radius_accounts.append(radcheck)
    return radius_accounts

def get_radcheck_active(request):
    radcheck = RadiusCheck.objects.filter(username=request.user.username,
                                          valid_until__gte=timezone.now(),
                                          is_active=True)
    if radcheck:
        radcheck = radcheck.last()
    else:
        return render(request, 'radius_account_not_found.html')
    return radcheck

@login_required
def _get_post_auth(request, radcheck):
    radius_accounts = _get_radius_accounts(request, radcheck)
    # collect all the postauth logged events regarding all the radiuscheck accounts
    radius_post_auths = []
    latest_range = datetime.timedelta(days=365)
    for i in radius_accounts:
        radius_post_auths_control = []
        pas_all = RadiusPostAuth.objects.filter(username=i.username,
                                                date__gte=timezone.now()-latest_range,
                                                ).exclude(calling_station_id='').order_by('-date')
        for p in pas_all:
            # if p.date.strftime('%Y-%m-%d %H:%M') not in radius_post_auths_control:
            # radius_post_auths_control.append(p.date.strftime('%Y-%m-%d %H:%M'))
            # print(type(p.date), type(p), p.date.strftime('%Y-%m-%d %H:%M'))
            radius_post_auths.append(p)
            # if p.date not in radius_post_auths: radius_post_auths.append(p)
    radius_post_auths.sort(key=lambda r: r.date)
    return radius_post_auths


@login_required
def home(request):
    radcheck = get_radcheck_active(request)
    # radius_post_auths = _get_post_auth(request, radcheck)
    radius_accounts = _get_radius_accounts(request, radcheck)
    context = {
        "accounts": radius_accounts if request.user.is_staff else [radcheck],
        # "post_auths": radius_post_auths[::-1],
        # "post_auths_count": len(radius_post_auths),
    }
    return render(request, "dashboard_radius.html", context=context)

@login_required
def change_password(request, radcheck_id):
    radiuscheck=get_object_or_404(RadiusCheck,
                                  pk = radcheck_id,
                                  is_active = True,
                                  valid_until__gte = timezone.now())

    identity = radiuscheck.identityradiusaccount_set.first()
    if not identity: raise Http404()

    available_accounts = [i[0].strip() for i in identity.identity.identityradiusaccount_set.values_list('radius_account__username')]
    # print(request.user.username, available_accounts)

    # check if the user is the real owner of the account!
    if request.user.username not in available_accounts:
        mail_admins('guest.unical.it, {} tried to change {} password!'.format(request.user.username, radiuscheck.username),
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            fail_silently=False,
            connection=None,
            html_message=None)
        raise Http404('It seems that you tryed to change '
                      'an account different from your. '
                      'Your action has been notified to security staff. '
                      'Please do not do this anymore.')

    # If this is a POST request then process the Form data
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request (binding):
        form = RadiusRenew(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # encode value in NT-Password format
            radiuscheck.value = _encode_secret(DEFAULT_SECRET_FORMAT,
                                               form.cleaned_data['password'])
            radiuscheck.save()
            return render(request, 'radius_account_renewed.html')
        else:
            d = {'radius_account': radiuscheck.username,
                 'form': form}
            return render(request, 'radius_account_renew.html', d)
    # If this is a GET (or any other method) create the default form.
    else:
        form = RadiusRenew()
    d = {'radius_account': radiuscheck.username,
         'form': form}
    return render(request, 'radius_account_renew.html', d)

def _create_identity_radius_token(identity, radcheck):
    validity_days = settings.IDENTITY_TOKEN_EXPIRATION_DAYS
    identity_token = IdentityRadiusAccount.objects.filter(identity=identity,
                                                          radius_account=radcheck,
                                                          is_active=True,
                                                          valid_until__gte=timezone.now()).last()
    if not identity_token:
        identity_token = IdentityRadiusAccount.objects.create(identity=identity,
                                               radius_account=radcheck,
                                               is_active=True,
                                               valid_until=timezone.now()+datetime.timedelta(days=validity_days))
    else:
        identity_token.valid_until = identity_token.valid_until + datetime.timedelta(days=validity_days)
        identity_token.save()
    return identity_token

def reset_password(request):
    # If this is a POST request then process the Form data
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request (binding):
        form = PasswordReset(request.POST)
        # Check if the form is valid:
        if form.is_valid():
            # check existence of the username
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            radcheck = RadiusCheck.objects.filter(username=username,
                                                  is_active=True,
                                                  valid_until__gte=timezone.now()
                                                  ).first()
            # return HttpResponse(radcheck)
            if not radcheck:
                # return as everything worked fine! (anti crack behaviour)
                return render(request, 'radius_account_email_sent.html',
                              {'enabled': settings.EMAIL_SEND_TOKEN})

            # fetch digital identity linked to the radius account
            identity = radcheck.identityradiusaccount_set.first()
            if not identity:
                # warning to admins, a radius account is still without identity!
                mail_admins('guest.unical.it, missing identity',
                            ('{} does not have any token actived. '
                             'Check if he have a valid identity '
                             'and at least a new or used token, '
                             'or create it. Its mandatory to have one.'
                             'Then send a reset request to him again.').format(username),
                             fail_silently=False,
                             connection=None,
                             html_message=None)
                return render(request, 'radius_account_email_sent.html',
                              {'enabled': settings.EMAIL_SEND_TOKEN})
            else:
                identity = identity.identity

            # create token here
            identity_token = _create_identity_radius_token(identity, radcheck)
            #print(identity_token, identity_token.token)
            # Send email here
            # https://docs.djangoproject.com/en/2.0/topics/email/
            # check https://docs.djangoproject.com/en/2.0/topics/email/#topic-email-backends
            if identity.email == email:
                send_mail(settings.IDENTITY_TOKEN_MSG_SUBJECT,
                          settings.IDENTITY_MSG.format(identity.name.capitalize(),
                                                       username,
                                                       identity_token.valid_until,
                                                       reverse('identity:renew-radius-password',
                                                               args=[identity_token.token,])),
                          settings.DEFAULT_FROM_EMAIL,
                          [identity.email,],
                          fail_silently=False,
                          auth_user=None,
                          auth_password=None,
                          connection=None,
                          html_message=None)
            else:
                mail_admins('guest.unical.it, wrong email submitted',
                            settings.IDENTITY_MSG_WRONG_EMAIL.format(username,
                                                                     email,
                                                                     identity.email),
                            fail_silently=False,
                            connection=None,
                            html_message=None)
            return render(request, 'radius_account_email_sent.html',
                          {'enabled': settings.EMAIL_SEND_TOKEN})
        else:
            return render(request, 'radius_account_reset_request.html',
                          {'form': form, 'enabled': settings.EMAIL_SEND_TOKEN})
    # If this is a GET (or any other method) create the default form.
    else:
        # every account needs an old pre-existent token!
        form = PasswordReset()

    return render(request, 'radius_account_reset_request.html',
                  {'form': form, 'enabled': settings.EMAIL_SEND_TOKEN})

@login_required
def datatable_data(request):
    radcheck = get_radcheck_active(request)
    radius_accounts = _get_radius_accounts(request, radcheck)

    model               = RadiusPostAuth
    columns             = ['pk', 'username', 'reply',
                           'calling_station_id', 'date']
    base_query = model.objects.filter(username__in=[i.username for i in radius_accounts]).exclude(calling_station_id='').order_by('-date')

    class DTD(DjangoDatatablesServerProc):
        def get_queryset(self):
            if self.search_key:
                self.aqs = base_query.filter(
                                        Q(username__icontains=self.search_key) | \
                                        Q(reply__icontains=self.search_key)    | \
                                        Q(calling_station_id__icontains=self.search_key))
            else:
                self.aqs = base_query.filter(username=radcheck.username)


    dtd = DTD( request, model, columns )
    return JsonResponse(dtd.get_dict())


def renew_radius_password(request, token_value):
    identity_radius=get_object_or_404(IdentityRadiusAccount, 
                                      token = token_value,
                                      is_active = True,
                                      valid_until__gte = timezone.now())
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request (binding):
        form = IdentityRadiusRenew(request.POST)
        # Check if the form is valid:
        if form.is_valid():
            if identity_radius.radius_account.username != request.POST['username']:
                form.add_error('password_verifica', ValidationError(_('wrong username'), code='invalid'))
                return render(request, 'radius_account_renew.html', {'form': form})
            
            # process the data in form.cleaned_data as required
            # encode value in NT-Password format
            identity_radius.radius_account.value = _encode_secret(settings.DEFAULT_SECRET_FORMAT,
                                                                  form.cleaned_data['password'])
            identity_radius.radius_account.save()
            
            identity_radius.used = timezone.now()
            identity_radius.is_active = False
            identity_radius.save()
            return render(request, 'radius_account_renewed.html')
        else:
            d = {'form': form}
            return render(request, 'radius_account_renew.html', d)
    # If this is a GET (or any other method) create the default form.
    d = {# disabled for preventing brute force over tokens
         #'radius_account': identity_radius.radius_account.username,
         'form': IdentityRadiusRenew()}
    return render(request, 'radius_account_renew.html', d)
