import uuid

from django.conf import settings
from django.db import models
from django_countries.fields import CountryField
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django_freeradius.models import RadiusCheck


class TimeStampedModel(models.Model):
    """
    self-updating created and modified fields
    """
    created = AutoCreatedField(_('created'), editable=False)
    modified = AutoLastModifiedField(_('modified'), editable=False)

    class Meta:
        abstract = True


class IdentityGenericManyToOne(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)

    class Meta:
        abstract = True

# TODO tradurre fields
class AbstractIdentityAddress(models.Model):
    address = models.CharField(_('Indirizzo'),max_length=150, blank=True, null=True)
    locality_name = models.CharField(_('Località'),max_length=135, blank=True, null=True)
    state = models.CharField(_('Comune'), max_length=60, blank=True, null=True)
    postal_code    = models.CharField(_('Cap'),max_length=60, blank=True, null=True)
    country_name = CountryField(_('Nazione'),blank=True, null=True)
    note = models.TextField(max_length=768, blank=True, null=True)
    primary =     models.BooleanField(_('Recapito principale'),default=False)
    class Meta:
        ordering = ['primary',]
        verbose_name_plural = _("Address book")
    def __str__(self):
        return '%s' % (self.persona)


class AttributeProvider(TimeStampedModel):
    """
    Attribute Providers
    json_config let us to never mind about changements in future
    """
    name = models.CharField(max_length=256, blank=False, null=False, help_text=_(''))
    url = models.CharField(max_length=512, blank=False, null=False, help_text=_(''))
    json_config = models.TextField(blank=True, null=True, help_text='')


class Identity(TimeStampedModel):
    """
    Provides registry
    """
    personal_title = models.CharField(max_length=12, blank=True, null=True)
    name = models.CharField(max_length=256, blank=False, null=False, help_text=_('Nome o ragione sociale'))
    surname = models.CharField(max_length=135, blank=False, null=False)
    email = models.EmailField()
    telephone = models.CharField(max_length=135, blank=True, null=True)
    common_name = models.CharField(max_length=256, blank=True, null=True, help_text=_('Nome o ragione sociale'))
    country = CountryField(blank=True, help_text=_('nazionalità, cittadinanza'))
    city = models.CharField(max_length=128, blank=True, null=True, help_text=_('residenza'))
    codice_fiscale = models.CharField(max_length=16, blank=True, null=True, help_text='')
    date_of_birth = models.DateField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=128, blank=True, null=True, help_text='')
    description = models.TextField(max_length=1024, blank=True, null=True)

    class Meta:
        ordering = ['created',]
        verbose_name_plural = _("Identità digitali")

    def create_token(self, radcheck):
        _time_delta = datetime.timedelta(days=validity_days)
        validity_days = settings.IDENTITY_TOKEN_EXPIRATION_DAYS
        identity_token = IdentityRadiusAccount.objects.filter(identity=identity,
                                                              radius_account=radcheck,
                                                              is_active=True,
                                                              valid_until__gte=timezone.now()).last()
        if not identity_token:
            identity_token = IdentityRadiusAccount.objects.create(identity=identity,
                                                   radius_account=radcheck,
                                                   is_active=True,
                                                   valid_until=timezone.now()+_time_delta)
        else:
            identity_token.valid_until = identity_token.valid_until + _time_delta
            identity_token.save()
        return identity_token
    
    def get_tokens(self):
        return IdentityRadiusAccount.objects.filter(identity=self)

    def get_active_tokens(self):
        return self.get_tokens().filter(is_active=True,
                                        valid_until__gte=timezone.now())

    def get_used_tokens(self):
        return self.get_tokens().filter(identity=self,
                                        is_active=False)

    def get_radchecks(self):
        usernames = self.get_tokens().values_list('radius_account__username')
        if not usernames: return RadiusCheck.objects.none()
        return RadiusCheck.objects.filter(username__in=[i[0] for i in usernames])

    def get_active_radchecks(self):
        return self.get_radchecks().filter(is_active=True,
                                           valid_until__gte=timezone.now())

    def get_expired_radchecks(self):
        return self.get_radchecks().filter(is_active=True,
                                           valid_until__lte=timezone.now())

    def __str__(self):
        return '{} {}'.format(self.name, self.surname)


class Affiliation(models.Model):
    AFFILIATION = (
                ('faculty', 'faculty'),
                ('student', 'student'),
                ('staff', 'staff'),
                ('alum', 'alum'),
                ('member', 'member'),
                ('affiliate', 'affiliate'),
                ('employee', 'employee'),
                ('library-walk-in', 'library-walk-in'),
              )
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE,
                                 blank=False, null=True)
    name = models.CharField(choices=AFFILIATION,
                            max_length=32)
    origin = models.CharField(max_length=254, blank=True, default='unical',
                              help_text='istitution of orgin, where the guest came from')
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name


class IdentityThirdPartiesAttribute(TimeStampedModel):
    """
    Which Provider contains other attributes related to that identity
    smart generalization for future implementation
    """
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)
    attribute_provider = models.ForeignKey(AttributeProvider, on_delete=models.CASCADE)


class IdentityAddress(AbstractIdentityAddress, TimeStampedModel):
    """
    many to one, many addresses to one identity
    """
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)

    class Meta:
        ordering = ['primary',]
        verbose_name_plural = _("Addresses")
    def __str__(self):
        return '%s %s' % (self.identity, self.primary)

class AddressType(models.Model):
    name = models.CharField(max_length=12, blank=False,  null=False,  help_text=_('tecnologia usata se email, telefono...'), unique=True)
    description = models.CharField(max_length=256, blank=True)
    def __str__(self):
        return '%s %s' % (self.name, self.description)

class IdentityDelivery(TimeStampedModel):
    """
        Generalized contacts classification
        email, telephone, facebook, twitter
    """
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)
    type     = models.ForeignKey(AddressType,
                                 blank=False, null=False,
                                 on_delete=models.CASCADE)
    value    = models.CharField(max_length=135, blank=False,  null=False,  help_text=_('mario.rossi@yahoo.it oppure 02 3467457, in base al tipo'))

class IdentityRole(IdentityGenericManyToOne):
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)

class IdentityAffilitation(IdentityGenericManyToOne):
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)

class IdentityRadiusAccount(models.Model):
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)
    radius_account = models.ForeignKey(RadiusCheck, on_delete=models.CASCADE)
    token = models.UUIDField(unique=True, default=uuid.uuid4,
                             blank=True, null=True,
                             help_text="https://guest.unical.it/identity/radius_renew/$token")
    sent = models.BooleanField(default=False)
    valid_until = models.DateTimeField(blank=False, null=False)
    used = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created = AutoCreatedField(_('created'), editable=False)

    class Meta:
        verbose_name = _('radius secret reset token')
        verbose_name_plural = _('radius secret reset tokens')

    def __str__(self):
        return '{} {}'.format(self.radius_account, self.is_active)
