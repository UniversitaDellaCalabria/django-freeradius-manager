#!/usr/bin/env python3
import csv
import datetime

from django.db import transaction
from django.conf import settings
from django.utils import timezone
from pprint import pprint

from .models import Identity
from django_freeradius.models import RadiusCheck

def clean_field(value):
    if not value: return
    return value.strip()

def parse_date(value):
    if isinstance(value, datetime.datetime): return value
    value = clean_field(value)
    excps = []
    for dformat in settings.DATE_INPUT_FORMATS:
        try:
            value = datetime.datetime.strptime(value, dformat)
            return value
        except Exception as e:
            excps.append(e)
    if not isinstance(value, datetime.date):
        for i in excps: print(i)


@transaction.atomic
def create_accounts_from_csv(csv_file='',
                             realm=settings.FQDN,
                             delimiter=',',
                             test=False,
                             debug=False):
    proc_msg = 'Processing '
    input_file = csv.DictReader(open(csv_file), delimiter=delimiter)
    cnt = 0
    for da in input_file:
        if debug:
            print(proc_msg)
            pprint(da)
        # gets identity from email
        email = clean_field(da['email'])
        identity = Identity.objects.filter(email=email)
        if identity:
            identity = identity.first()
            #if debug:
            msg = 'INFO: Found already stored identity {} from email {}'
            print(msg.format(identity, email))
        else:
            identity = Identity(name = clean_field(da['first_name']),
                                surname = clean_field(da['last_name']),
                                email = clean_field(da['email']),
                                telephone = clean_field(da.get('tel')),
                                codice_fiscale = clean_field(da.get('codice_fiscale')))
            if da.get('date_of_birth'):
                identity.date_of_birth = parse_date(da.get('date_of_birth'))
            identity.place_of_birth = clean_field(da.get('place_of_birth'))
            if not test:
                identity.save()

        if debug:
            print('identity: {}'.format(identity))
        # gets radius account
        username = email.split('@')[0]+'@{}'.format(realm)
        radius_account = RadiusCheck.objects.filter(username=username)
        if radius_account:
            radius_account = radius_account.first()
            if debug:
                msg = 'INFO: Found already stored radius account {} with username {}'
                print(msg.format(radius_account, username))
        else:
            radius_account = RadiusCheck(username=username)

        radius_account.is_active = True
        valid_until = da['valid_until']
        radius_account.valid_until = parse_date(valid_until)
        if not radius_account.valid_until:
            print('Error: not a valid valid_until value on {}'.format(identity))
        if not test:
            radius_account.save()

        # create token
        if test:
            cnt += 1
            continue
        minutes = (settings.IDENTITY_TOKEN_EXPIRATION_DAYS * 24 ) * 60
        valid_until = timezone.now() + timezone.timedelta(minutes=minutes)
        token = identity.identityradiusaccount_set.create(identity=identity,
                                                          radius_account=radius_account,
                                                          valid_until=valid_until)
        #print('Create Token {} for {}'.format(token.token, identity))
        print(';'.join((identity.surname,
                        identity.name,
                        radius_account.username,
                        '/identity/radius_renew/{}'.format(str(token.token)))))
        cnt += 1
    return cnt


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-csv', required=True,
                        help="csv file to import")
    parser.add_argument('-realm', required=False,
                        default=settings.FQDN,
                        help="csv file to import")
    parser.add_argument('-test', required=False, action="store_true",
                        help="do not save imports, just test")
    parser.add_argument('-debug', required=False, action="store_true",
                        help="see debug message")
    args = parser.parse_args()

    create_accounts_from_csv(csv_file=args.csv,
                             realm=args.realm,
                             test=args.test,
                             debug=args.debug)
