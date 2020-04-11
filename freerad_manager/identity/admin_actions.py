from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail, mail_admins
from django.urls import reverse
from django.utils import timezone

from . models import *
from . views import _create_identity_radius_token


def send_email_renew_password(modeladmin, request, queryset):
    for identity in queryset:
        # print(identity)
        accounts = []
        for account in identity.identityradiusaccount_set.filter(radius_account__is_active=True,
                                                                 radius_account__valid_until__gte=timezone.now()):
            if account.radius_account not in accounts:
                accounts.append(account.radius_account)

        # print(accounts)
        for radcheck in accounts:
            identity_token = _create_identity_radius_token(identity, radcheck)
            if identity_token.sent:
                identity_token.sent = False
            # print(identity_token)
            identity_token.sent = send_mail(settings.IDENTITY_TOKEN_MSG_SUBJECT,
                                            settings.IDENTITY_MSG.format(identity.name.capitalize(),
                                                   radcheck.username,
                                                   identity_token.valid_until,
                                                   reverse('identity:renew-radius-password',
                                                           args=[identity_token.token,])
                                               ),
                      settings.DEFAULT_FROM_EMAIL,
                      [identity.email,],
                      fail_silently=False,
                      auth_user=None,
                      auth_password=None,
                      connection=None,
                      html_message=None)

            identity_token.save()
            if identity_token.sent:
                msg_type = messages.INFO
            else:
                msg_type = messages.ERROR
            messages.add_message(request, msg_type,
            '{} {}. Email inviata a {}.'.format(identity, radcheck, identity.email))

send_email_renew_password.short_description = "Invia E-Mail di reset delle credenziali (token)"
