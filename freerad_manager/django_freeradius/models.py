import csv
from base64 import encodebytes as encodestring
from hashlib import md5, sha1
from io import StringIO
from os import urandom

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db.models import Count
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from passlib.hash import lmhash, nthash, sha512_crypt


RADOP_CHECK_TYPES = (('=', '='),
                     (':=', ':='),
                     ('==', '=='),
                     ('+=', '+='),
                     ('!=', '!='),
                     ('>', '>'),
                     ('>=', '>='),
                     ('<', '<'),
                     ('<=', '<='),
                     ('=~', '=~'),
                     ('!~', '!~'),
                     ('=*', '=*'),
                     ('!*', '!*'))

RAD_NAS_TYPES = (
    ('Async', 'Async'),
    ('Sync', 'Sync'),
    ('ISDN Sync', 'ISDN Sync'),
    ('ISDN Async V.120', 'ISDN Async V.120'),
    ('ISDN Async V.110', 'ISDN Async V.110'),
    ('Virtual', 'Virtual'),
    ('PIAFS', 'PIAFS'),
    ('HDLC Clear', 'HDLC Clear'),
    ('Channel', 'Channel'),
    ('X.25', 'X.25'),
    ('X.75', 'X.75'),
    ('G.3 Fax', 'G.3 Fax'),
    ('SDSL', 'SDSL - Symmetric DSL'),
    ('ADSL-CAP', 'ADSL-CAP'),
    ('ADSL-DMT', 'ADSL-DMT'),
    ('IDSL', 'IDSL'),
    ('Ethernet', 'Ethernet'),
    ('xDSL', 'xDSL'),
    ('Cable', 'Cable'),
    ('Wireless - Other', 'Wireless - Other'),
    ('IEEE 802.11', 'Wireless - IEEE 802.11'),
    ('Token-Ring', 'Token-Ring'),
    ('FDDI', 'FDDI'),
    ('Wireless - CDMA2000', 'Wireless - CDMA2000'),
    ('Wireless - UMTS', 'Wireless - UMTS'),
    ('Wireless - 1X-EV', 'Wireless - 1X-EV'),
    ('IAPP', 'IAPP'),
    ('FTTP', 'FTTP'),
    ('IEEE 802.16', 'Wireless - IEEE 802.16'),
    ('IEEE 802.20', 'Wireless - IEEE 802.20'),
    ('IEEE 802.22', 'Wireless - IEEE 802.22'),
    ('PPPoA', 'PPPoA - PPP over ATM'),
    ('PPPoEoA', 'PPPoEoA - PPP over Ethernet over ATM'),
    ('PPPoEoE', 'PPPoEoE - PPP over Ethernet over Ethernet'),
    ('PPPoEoVLAN', 'PPPoEoVLAN - PPP over Ethernet over VLAN'),
    ('PPPoEoQinQ', 'PPPoEoQinQ - PPP over Ethernet over IEEE 802.1QinQ'),
    ('xPON', 'xPON - Passive Optical Network'),
    ('Wireless - XGP', 'Wireless - XGP'),
    ('WiMAX', ' WiMAX Pre-Release 8 IWK Function'),
    ('WIMAX-WIFI-IWK', 'WIMAX-WIFI-IWK: WiMAX WIFI Interworking'),
    ('WIMAX-SFF', 'WIMAX-SFF: Signaling Forwarding Function for LTE/3GPP2'),
    ('WIMAX-HA-LMA', 'WIMAX-HA-LMA: WiMAX HA and or LMA function'),
    ('WIMAX-DHCP', 'WIMAX-DHCP: WIMAX DCHP service'),
    ('WIMAX-LBS', 'WIMAX-LBS: WiMAX location based service'),
    ('WIMAX-WVS', 'WIMAX-WVS: WiMAX voice service'),
    ('Other', 'Other'),
)


RADOP_REPLY_TYPES = (('=', '='),
                     (':=', ':='),
                     ('+=', '+='))

RADCHECK_PASSWD_TYPE = ['Cleartext-Password',
                        'NT-Password',
                        'LM-Password',
                        'MD5-Password',
                        'SMD5-Password',
                        'SHA-Password',
                        'SSHA-Password',
                        'Crypt-Password']

STRATEGIES = (
    ('prefix', _('Generate from prefix')),
    ('csv', _('Import from CSV'))
)


class TimeStampedModel(models.Model):
    """
    self-updating created and modified fields
    """
    created = models.DateTimeField(_('created'),
                                   auto_now_add=True, editable=False)
    modified = models.DateTimeField(_('modified'),
                                    auto_now=True, editable=False)

    class Meta:
        abstract = True


class RadiusGroup(TimeStampedModel):
    id = models.UUIDField(primary_key=True, db_column='id')
    groupname = models.CharField(verbose_name=_('group name'),
                                 max_length=255,
                                 unique=True,
                                 db_index=True)
    priority = models.IntegerField(verbose_name=_('priority'), default=1)
    notes = models.CharField(verbose_name=_('notes'),
                             max_length=64,
                             blank=True,
                             null=True)

    class Meta:
        db_table = 'radiusgroup'
        verbose_name = _('radius group')
        verbose_name_plural = _('radius groups')

    def __str__(self):
        return self.groupname


class RadiusGroupUsers(TimeStampedModel):
    id = models.UUIDField(primary_key=True,
                          db_column='id')
    username = models.CharField(verbose_name=_('username'),
                                max_length=64,
                                unique=True)
    groupname = models.CharField(verbose_name=_('group name'),
                                 max_length=255,
                                 unique=True)
    radius_reply = models.ManyToManyField('RadiusReply',
                                          verbose_name=_('radius reply'),
                                          blank=True,
                                          db_column='radiusreply')
    radius_check = models.ManyToManyField('RadiusCheck',
                                          verbose_name=_('radius check'),
                                          blank=True,
                                          db_column='radiuscheck')

    class Meta:
        db_table = 'radiusgroupusers'
        verbose_name = _('radius group users')
        verbose_name_plural = _('radius group users')

    def __str__(self):
        return self.username


class RadiusReply(TimeStampedModel):
    username = models.CharField(verbose_name=_('username'),
                                max_length=64,
                                db_index=True)
    value = models.CharField(verbose_name=_('value'), max_length=253)
    op = models.CharField(verbose_name=_('operator'),
                          max_length=2,
                          choices=RADOP_REPLY_TYPES,
                          default='=')
    attribute = models.CharField(verbose_name=_('attribute'), max_length=64)

    class Meta:
        db_table = 'radreply'
        verbose_name = _('radius reply')
        verbose_name_plural = _('radius replies')

    def __str__(self):
        return self.username


class RadiusCheckQueryset(models.query.QuerySet):
    def filter_duplicate_username(self):
        pks = []
        for i in self.values('username').annotate(Count('id')).order_by().filter(id__count__gt=1):
            pks.extend([account.pk for account in self.filter(username=i['username'])])
        return self.filter(pk__in=pks)

    def filter_duplicate_value(self):
        pks = []
        for i in self.values('value').annotate(Count('id')).order_by().filter(id__count__gt=1):
            pks.extend([accounts.pk for accounts in self.filter(value=i['value'])])
        return self.filter(pk__in=pks)

    def filter_expired(self):
        return self.filter(valid_until__lt=now())

    def filter_not_expired(self):
        return self.filter(valid_until__gte=now())


def encode_secret(attribute=settings.FREERADIUS_DEFAULT_SECRET_FORMAT,
                  new_value=None):
    if attribute == 'Cleartext-Password':
        password_renewed = new_value
    elif attribute == 'NT-Password':
        password_renewed = nthash.hash(new_value)
    elif attribute == 'LM-Password':
        password_renewed = lmhash.hash(new_value)
    elif attribute == 'MD5-Password':
        password_renewed = md5(new_value.encode('utf-8')).hexdigest()
    elif attribute == 'SMD5-Password':
        salt = urandom(4)
        hash = md5(new_value.encode('utf-8'))
        hash.update(salt)
        hash_encoded = encodestring(hash.digest() + salt)
        password_renewed = hash_encoded.decode('utf-8')[:-1]
    elif attribute == 'SHA-Password':
        password_renewed = sha1(new_value.encode('utf-8')).hexdigest()
    elif attribute == 'SSHA-Password':
        salt = urandom(4)
        hash = sha1(new_value.encode('utf-8'))
        hash.update(salt)
        hash_encoded = encodestring(hash.digest() + salt)
        password_renewed = hash_encoded.decode('utf-8')[:-1]
    elif attribute == 'Crypt-Password':
        password_renewed = sha512_crypt.hash(new_value)
    return password_renewed


class RadiusCheckManager(models.Manager):
    def get_queryset(self):
        return RadiusCheckQueryset(self.model, using=self._db)

    def create(self, *args, **kwargs):
        if 'new_value' in kwargs:
            kwargs['value'] = encode_secret(kwargs['attribute'],
                                            kwargs['new_value'])
            del(kwargs['new_value'])
        return super(RadiusCheckManager, self).create(*args, **kwargs)


class RadiusCheck(TimeStampedModel):
    username = models.CharField(verbose_name=_('username'),
                                max_length=64,
                                unique=True)
    value = models.CharField(verbose_name=_('value'), max_length=253)
    op = models.CharField(verbose_name=_('operator'),
                          max_length=2,
                          choices=RADOP_CHECK_TYPES,
                          default=':=')
    attribute = models.CharField(verbose_name=_('attribute'),
                                 max_length=64,
                                 choices=[(i, i) for i in RADCHECK_PASSWD_TYPE
                                          if i not in
                                          settings.FREERADIUS_DISABLED_SECRET_FORMATS],
                                 blank=True,
                                 default=settings.FREERADIUS_DEFAULT_SECRET_FORMAT)
    # additional fields to enable more granular checks
    is_active = models.BooleanField(default=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    # internal notes
    notes = models.TextField(null=True, blank=True)
    # custom manager
    objects = RadiusCheckManager()

    class Meta:
        db_table = 'radcheck'
        ordering = ['-created',]
        verbose_name = _('radius check')
        verbose_name_plural = _('radius checks')

    def __str__(self):
        return self.username


class RadiusAccounting(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='radacctid')
    session_id = models.CharField(verbose_name=_('session ID'),
                                  max_length=64,
                                  db_column='acctsessionid',
                                  db_index=True)
    unique_id = models.CharField(verbose_name=_('accounting unique ID'),
                                 max_length=32,
                                 db_column='acctuniqueid',
                                 unique=True)
    username = models.CharField(verbose_name=_('username'),
                                max_length=64,
                                db_index=True,
                                null=True,
                                blank=True)
    groupname = models.CharField(verbose_name=_('group name'),
                                 max_length=64,
                                 null=True,
                                 blank=True)
    realm = models.CharField(verbose_name=_('realm'),
                             max_length=64,
                             null=True,
                             blank=True)
    nas_ip_address = models.GenericIPAddressField(verbose_name=_('NAS IP address'),
                                                  db_column='nasipaddress',
                                                  db_index=True)
    nas_port_id = models.CharField(verbose_name=_('NAS port ID'),
                                   max_length=15,
                                   db_column='nasportid',
                                   null=True,
                                   blank=True)
    nas_port_type = models.CharField(verbose_name=_('NAS port type'),
                                     max_length=32,
                                     db_column='nasporttype',
                                     null=True,
                                     blank=True)
    start_time = models.DateTimeField(verbose_name=_('start time'),
                                      db_column='acctstarttime',
                                      db_index=True,
                                      null=True,
                                      blank=True)
    update_time = models.DateTimeField(verbose_name=_('update time'),
                                       db_column='acctupdatetime',
                                       null=True,
                                       blank=True)
    stop_time = models.DateTimeField(verbose_name=_('stop time'),
                                     db_column='acctstoptime',
                                     db_index=True,
                                     null=True,
                                     blank=True)
    interval = models.IntegerField(verbose_name=_('interval'),
                                   db_column='acctinterval',
                                   null=True,
                                   blank=True)
    session_time = models.PositiveIntegerField(verbose_name=_('session time'),
                                               db_column='acctsessiontime',
                                               null=True,
                                               blank=True)
    authentication = models.CharField(verbose_name=_('authentication'),
                                      max_length=32,
                                      db_column='acctauthentic',
                                      null=True,
                                      blank=True)
    connection_info_start = models.CharField(verbose_name=_('connection info start'),
                                             max_length=50,
                                             db_column='connectinfo_start',
                                             null=True,
                                             blank=True)
    connection_info_stop = models.CharField(verbose_name=_('connection info stop'),
                                            max_length=50,
                                            db_column='connectinfo_stop',
                                            null=True,
                                            blank=True)
    input_octets = models.BigIntegerField(verbose_name=_('input octets'),
                                          db_column='acctinputoctets',
                                          null=True,
                                          blank=True)
    output_octets = models.BigIntegerField(verbose_name=_('output octets'),
                                           db_column='acctoutputoctets',
                                           null=True,
                                           blank=True)
    called_station_id = models.CharField(verbose_name=_('called station ID'),
                                         max_length=50,
                                         db_column='calledstationid',
                                         blank=True,
                                         null=True)
    calling_station_id = models.CharField(verbose_name=_('calling station ID'),
                                          max_length=50,
                                          db_column='callingstationid',
                                          blank=True,
                                          null=True)
    terminate_cause = models.CharField(verbose_name=_('termination cause'),
                                       max_length=32,
                                       db_column='acctterminatecause',
                                       blank=True,
                                       null=True)
    service_type = models.CharField(verbose_name=_('service type'),
                                    max_length=32,
                                    db_column='servicetype',
                                    null=True,
                                    blank=True)
    framed_protocol = models.CharField(verbose_name=_('framed protocol'),
                                       max_length=32,
                                       db_column='framedprotocol',
                                       null=True,
                                       blank=True)
    framed_ip_address = models.GenericIPAddressField(verbose_name=_('framed IP address'),
                                                     db_column='framedipaddress',
                                                     db_index=True,
                                                     # the default MySQL freeradius schema defines
                                                     # this as NOT NULL but defaulting to empty string
                                                     # but that wouldn't work on PostgreSQL
                                                     null=True,
                                                     blank=True)

    def save(self, *args, **kwargs):
        if not self.start_time:
            self.start_time = now()
        super(RadiusAccounting, self).save(*args, **kwargs)

    class Meta:
        db_table = 'radacct'
        verbose_name = _('accounting')
        verbose_name_plural = _('accountings')

    def __str__(self):
        return self.unique_id


class Nas(TimeStampedModel):
    name = models.CharField(verbose_name=_('name'),
                            max_length=128,
                            help_text=_('NAS Name (or IP address)'),
                            db_index=True,
                            db_column='nasname')
    short_name = models.CharField(verbose_name=_('short name'),
                                  max_length=32,
                                  db_column='shortname')
    type = models.CharField(verbose_name=_('type'),
                            max_length=30,
                            default='other')
    ports = models.PositiveIntegerField(verbose_name=_('ports'),
                                        blank=True,
                                        null=True)
    secret = models.CharField(verbose_name=_('secret'),
                              max_length=60,
                              help_text=_('Shared Secret'))
    server = models.CharField(verbose_name=_('server'),
                              max_length=64,
                              blank=True,
                              null=True)
    community = models.CharField(verbose_name=_('community'),
                                 max_length=50,
                                 blank=True,
                                 null=True)
    description = models.CharField(verbose_name=_('description'),
                                   max_length=200,
                                   null=True,
                                   blank=True)

    class Meta:
        db_table = 'nas'
        verbose_name = _('NAS')
        verbose_name_plural = _('NAS')

    def __str__(self):
        return self.name


class RadiusUserGroup(TimeStampedModel):
    username = models.CharField(verbose_name=_('username'),
                                max_length=64,
                                db_index=True)
    groupname = models.CharField(verbose_name=_('group name'),
                                 max_length=64)
    priority = models.IntegerField(verbose_name=_('priority'), default=1)

    class Meta:
        db_table = 'radusergroup'
        verbose_name = _('radius user group association')
        verbose_name_plural = _('radius user group associations')

    def __str__(self):
        return str(self.username)


class RadiusGroupReply(TimeStampedModel):
    groupname = models.CharField(verbose_name=_('group name'),
                                 max_length=64,
                                 db_index=True)
    attribute = models.CharField(verbose_name=_('attribute'), max_length=64)
    op = models.CharField(verbose_name=_('operator'),
                          max_length=2,
                          choices=RADOP_REPLY_TYPES,
                          default='=')
    value = models.CharField(verbose_name=_('value'), max_length=253)

    class Meta:
        db_table = 'radgroupreply'
        verbose_name = _('radius group reply')
        verbose_name_plural = _('radius group replies')

    def __str__(self):
        return str(self.groupname)


class RadiusGroupCheck(TimeStampedModel):
    groupname = models.CharField(verbose_name=_('group name'),
                                 max_length=64,
                                 db_index=True)
    attribute = models.CharField(verbose_name=_('attribute'), max_length=64)
    op = models.CharField(verbose_name=_('operator'),
                          max_length=2,
                          choices=RADOP_CHECK_TYPES,
                          default=':=')
    value = models.CharField(verbose_name=_('value'), max_length=253)

    class Meta:
        db_table = 'radgroupcheck'
        verbose_name = _('radius group check')
        verbose_name_plural = _('radius group checks')

    def __str__(self):
        return str(self.groupname)


class RadiusPostAuth(models.Model):
    username = models.CharField(verbose_name=_('username'),
                                max_length=64)
    password = models.CharField(verbose_name=_('password'),
                                max_length=64,
                                db_column='pass',
                                blank=True)
    reply = models.CharField(verbose_name=_('reply'),
                             max_length=32)
    called_station_id = models.CharField(verbose_name=_('called station ID'),
                                         max_length=50,
                                         db_column='calledstationid',
                                         blank=True,
                                         null=True)
    calling_station_id = models.CharField(verbose_name=_('calling station ID'),
                                          max_length=50,
                                          db_column='callingstationid',
                                          blank=True,
                                          null=True)
    date = models.DateTimeField(verbose_name=_('date'),
                                db_column='authdate',
                                auto_now_add=True)
    # additional fields for better auditing (thanks to daniele albrizio unitrieste)
    outerid = models.CharField(verbose_name=_('OuterID'),
                               max_length=254, null=True, blank=True)
    innerid = models.CharField(verbose_name=_('InnerID'),
                               max_length=254, null=True, blank=True)
    cui = models.CharField(verbose_name=_('ChargeableUserIdentity'),
                           max_length=254, null=True, blank=True)
    eduroam_sp_country = models.CharField(verbose_name=_('eduroamSPCountry'),
                                          max_length=254, null=True, blank=True)
    operator_name = models.CharField(verbose_name=_('OperatorName'),
                                     max_length=254, null=True, blank=True)
    nas_identifier = models.CharField(verbose_name=_('NASIdentifier'),
                                     max_length=254, null=True, blank=True)

    class Meta:
        db_table = 'radpostauth'
        verbose_name = _('radius post authentication log')
        verbose_name_plural = _('radius post authentication logs')

    def __str__(self):
        return str(self.username)
