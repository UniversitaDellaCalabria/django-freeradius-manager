import re

from django import forms
from django.conf import settings
from django.core.validators import RegexValidator
from django.forms.utils import ErrorList
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


_passwd_msg = _('The secret must contains lowercase'
                ' and uppercase characters, '
                ' number and at least one of these symbols:'
                '! % - _ + = [ ] { } : , . ? < > ( ) ; '
                'Example: This.Is_A.g00d;P4ssw0rd')

_regexp_pt = '[A-Za-z0-9\.\_\-\\\/]*'


class RadiusRenew(forms.Form):
    password = forms.CharField(label="Password",min_length=8, max_length=64,
                               validators=[RegexValidator(_regexp_pt, 
                                                          message=_passwd_msg)],
                               widget=forms.PasswordInput())
    password_verifica = forms.CharField(label=_("Password verify"),
                                        min_length=8, max_length=64,
                                        validators=[RegexValidator(_regexp_pt, 
                                                                   message=_passwd_msg)],
                                        widget=forms.PasswordInput())

    def clean_password(self):
        password1 = self.data.get('password')
        password2 = self.data.get('password_verifica')
        
        if not password2:
            self._errors["password_verifica"] = ErrorList([_("You must confirm your password")])
            return self._errors
        if password1 != password2:
            self._errors['password'] = ErrorList([_("Your passwords do not match")])
            return self._errors
        
        for regexp in settings.FREERADIUS_RADCHECK_SECRET_VALIDATORS.values():
            found = re.findall(regexp, password1)
            if not found:
                raise ValidationError(_passwd_msg)
        return password1
    
    def clean_password_verifica(self):
        return self.clean_password()


class IdentityRadiusBaseRenew(forms.Form):
    username = forms.CharField(label='Username', max_length=64, 
                               help_text="example: username@{}".format(settings.FQDN))


class IdentityRadiusRenew(RadiusRenew, IdentityRadiusBaseRenew):
    pass


class PasswordReset(forms.Form):
    username = forms.CharField(label='Username', max_length=64, 
                               help_text="example: username@{}".format(getattr(settings, 'FQDN', 'youhost.org')))
    email = forms.EmailField(label='Email', max_length=64, 
                               help_text=_("example: name.surname@thatho.st "
                                           "or google or yahoo or msn or whatever"))
