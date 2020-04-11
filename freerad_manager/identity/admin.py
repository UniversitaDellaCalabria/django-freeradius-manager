from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from .admin_actions import send_email_renew_password
from .admin_inline import *
from .models import *

@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    inlines = [AffiliationInline,
               IdentityRadiusAccountInline,
               IdentityDeliveryInline,
               IdentityAddressInline]
    list_display  = ('name', 'surname', 'email', 'created', 'view_radchecks')
    search_fields = ('name', 'surname','common_name',
                     'email', 'telephone')
    list_filter   = ('personal_title',)
    readonly_fields = ('created', 'modified', 'view_radchecks')
    fields = [  ('personal_title', 'common_name'),
                ('name', 'surname'),
                ('email', 'telephone', ),
                ('country', 'city', ),
                ('codice_fiscale',),
                ('place_of_birth', 'date_of_birth'),
                'description',
                ('created', 'modified')
             ]
    #autocomplete_fields = ['country',]
    actions = [send_email_renew_password,]
    date_hierarchy = 'created'

    def view_radchecks(self, obj):
        active_radchecks = obj.get_active_radchecks()
        expired_radchecks = obj.get_expired_radchecks()

        ico_tmpl = '<img src="/static/admin/img/icon-{}.svg" alt="False">'
        ico_yes = ico_tmpl.format('yes')
        ico_no = ico_tmpl.format('no')
        ico_alert = ico_tmpl.format('alert')

        radchecks_list = []
        for i in expired_radchecks:
            name = i.username
            radcheck_url = reverse('admin:django_freeradius_radiuscheck_change',
                                   args=(i.pk,))
            value = '<li>{} <a href="{}">{}</a></li>'.format(ico_no,
                                                            radcheck_url,
                                                            name)
            radchecks_list.append(value)

        for i in active_radchecks:
            name = i.username
            radcheck_url = reverse('admin:django_freeradius_radiuscheck_change',
                                   args=(i.pk,))
            ico = ico_yes if i.value else ico_alert
            value = '<li>{} <a href="{}">{}</a></li>'.format(ico,
                                                             radcheck_url,
                                                             name)
            radchecks_list.append(value)

        html_ul = '<ol>{}</ol>'.format(''.join(radchecks_list))
        return mark_safe(html_ul)

    class Media:
        js = ('js/textarea-autosize.js',)


class AffiliationAdmin(admin.ModelAdmin):
    list_display  = ('identity', 'name', 'origin')
    search_fields = ('name',)
    list_filter   = ('name',)

    class Media:
        js = ('identity/static/js/textarea-autosize.js',)


# @admin.register(AddressType)
class AddressTypeAdmin(admin.ModelAdmin):
    list_display  = ('name',)
    search_fields = ('name',)
    list_filter   = ('name',)

    class Media:
        js = ('identity/static/js/textarea-autosize.js',)
