from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.actions import delete_selected
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from . admin_actions import disable_action, enable_action
from . admin_filters import DuplicateListFilter, ExpiredListFilter
from . forms import RadiusCheckAdminForm, NasModelForm
from . models import *
from . models import _encode_secret


class TimeStampedEditableAdmin(ModelAdmin):
    """
    ModelAdmin for TimeStampedEditableModel
    """

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(TimeStampedEditableAdmin, self).get_readonly_fields(request, obj)
        return readonly_fields + ('created', 'modified')


class ReadOnlyAdmin(ModelAdmin):
    """
    Disables all editing capabilities
    """
    def __init__(self, *args, **kwargs):
        super(ReadOnlyAdmin, self).__init__(*args, **kwargs)
        self.readonly_fields = [f.name for f in self.model._meta.fields]

    def get_actions(self, request):
        actions = super(ReadOnlyAdmin, self).get_actions(request)
        del actions["delete_selected"]
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):  # pragma: nocover
        pass

    def delete_model(self, request, obj):  # pragma: nocover
        pass

    def save_related(self, request, form, formsets, change):  # pragma: nocover
        pass

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super(ReadOnlyAdmin, self).change_view(request,
                                                      object_id,
                                                      extra_context=extra_context)

@admin.register(RadiusGroup)
class RadiusGroupAdmin(TimeStampedEditableAdmin):
    pass


@admin.register(RadiusGroupUsers)
class RadiusGroupUsersAdmin(TimeStampedEditableAdmin):
    pass


@admin.register(RadiusCheck)
class RadiusCheckAdmin(TimeStampedEditableAdmin):
    list_display = ('username', 'attribute', 'is_active',
                    'created', 'valid_until')
    search_fields = ('username', 'value')
    list_filter = (DuplicateListFilter, ExpiredListFilter, 'created',
                   'modified', 'valid_until')
    readonly_fields = ('value',)
    form = RadiusCheckAdminForm
    fields = ['username', 'op', 'attribute', 'value', 'new_value',
              'is_active', 'valid_until', 'notes', 'created', 'modified']

    actions = ModelAdmin.actions + [disable_action, enable_action]

    def save_model(self, request, obj, form, change):
        if get_user_model().objects.filter(username=obj.username):
            messages.set_level(request, messages.ERROR)
            _msg = _('{} username collides with a pre-existent system User').format(obj.username)
            messages.add_message(request, messages.ERROR,
                                 _msg)
            return
            
        if form.data.get('new_value'):
            obj.value = _encode_secret(form.data['attribute'],
                                       form.data.get('new_value'))
        obj.save()

    def get_fields(self, request, obj=None):
        """ do not show raw value (readonly) when adding a new item """
        fields = self.fields[:]
        if not obj:
            fields.remove('value')
        return fields

    class Media:
        js = ('django-freeradius/js/radcheck.js',
              'django-freeradius/js/textarea-autosize.js')
        css = {'all': ('django-freeradius/css/radcheck.css',)}


@admin.register(RadiusReply)
class RadiusReplyAdmin(TimeStampedEditableAdmin):
    pass


@admin.register(RadiusAccounting)
class RadiusAccountingAdmin(ModelAdmin):
    list_display = ('nas_ip_address', 'username', 'session_time',
                    'input_octets', 'output_octets',
                    'start_time', 'stop_time')
    search_fields = ('unique_id', 'username', 'nas_ip_address',
                     'framed_ip_address')
    list_filter = ('start_time', 'stop_time')


@admin.register(Nas)
class NasAdmin(TimeStampedEditableAdmin):
    form = NasModelForm
    fieldsets = (
        (None, {
            'fields': (
                'name', 'short_name',
                ('type', 'custom_type'),
                'ports', 'secret', 'server', 'community', 'description'
            )
        }),
    )
    search_fields = ['name', 'short_name', 'server']
    list_display = ['name', 'short_name', 'server', 'secret', 'created', 'modified']

    def save_model(self, request, obj, form, change):
        data = form.cleaned_data
        obj.type = data.get('custom_type') or data.get('type')
        super(AbstractNasAdmin, self).save_model(request, obj, form, change)

    class Media:
        css = {'all': ('django-freeradius/css/nas.css',)}


@admin.register(RadiusUserGroup)
class RadiusUserGroupAdmin(TimeStampedEditableAdmin):
    pass


@admin.register(RadiusGroupReply)
class RadiusGroupReplyAdmin(TimeStampedEditableAdmin):
    pass


@admin.register(RadiusGroupCheck)
class RadiusGroupCheckAdmin(TimeStampedEditableAdmin):
    pass


@admin.register(RadiusPostAuth)
class RadiusPostAuthAdmin(ModelAdmin):
    list_display = ['username', 'reply', 'date',
                    'calling_station_id', 'nas_identifier',
                    'view_radcheck']
    list_filter = ['date', 'reply']
    search_fields = ['username', 'reply', 'calling_station_id']
    readonly_fields = ('view_radcheck',)

    def view_radcheck(self, obj):
        radcheck = RadiusCheck.objects.filter(username=obj.username).first()
        if not radcheck: return ''
        radcheck_url = reverse('admin:django_freeradius_radiuscheck_change',
                               args=(radcheck.pk,))
        value = '<a href="{}">View Account</a>'.format(radcheck_url)
        return mark_safe(value)
