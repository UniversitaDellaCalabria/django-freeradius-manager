from django import forms
from django.contrib import admin

from django_freeradius.models import RadiusCheck

from .models import *

class IdentityAddressForm(forms.ModelForm):
    class Meta:
        model = IdentityAddress
        fields = ('__all__')

class IdentityAddressInline(admin.StackedInline):
    form  = IdentityAddressForm
    model = IdentityAddress
    extra = 0

class IdentityDeliveryForm(forms.ModelForm):
    class Meta:
        model = IdentityDelivery
        fields = ('__all__')

class IdentityDeliveryInline(admin.StackedInline):
    form  = IdentityDeliveryForm
    model = IdentityDelivery
    extra = 0

class IdentityRadiusAccountForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(IdentityRadiusAccountForm, self).__init__(*args, **kwargs)
        self.fields['radius_account'].queryset = RadiusCheck.objects.filter(is_active=True).order_by('-created')
        
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['token'].widget.attrs['readonly'] = True
            self.fields['token'].widget.attrs['size'] = 29
            self.fields['token'].widget.attrs['disabled'] = True
    
    # def clean_token(self):
        # instance = getattr(self, 'instance', None)
        # if instance and instance.pk:
            # return instance.token
        # else:
            # return self.cleaned_data['token']

    class Meta:
        model = IdentityRadiusAccount
        fields = ('__all__')

class IdentityRadiusAccountInline(admin.StackedInline):
    
    fields = (
              ('radius_account', 'token'),
              ('valid_until', 'used'),
              ('sent', 'is_active')
              )
    
    form  = IdentityRadiusAccountForm
    model = IdentityRadiusAccount
    extra = 0
    autocomplete_fields = ['radius_account',]


class AffiliationInline(admin.StackedInline):
    #form  = IdentityAddressForm
    fields = (
                ('name', 'origin'),
                'description',
                )
    model = Affiliation
    extra = 0
